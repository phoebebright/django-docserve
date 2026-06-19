# docserve/management/commands/generate_mkdocs_yml.py

import os
import re
import yaml
from ruamel.yaml import YAML
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# PyYAML serialises a Python callable as `!!python/name:module.func ''`, but
# MkDocs' loader requires the python/name tag to carry an *empty* value and
# rejects the trailing ''. This pattern strips it so the tag is valid YAML for
# MkDocs (used for the mermaid superfence `format`).
_PYTHON_NAME_EMPTY = re.compile(r"(!!python/name:[\w.]+) ''")


def _round_trip_yaml() -> YAML:
    """
    A ruamel.yaml round-trip parser used when preserving a hand-crafted
    mkdocs_{role}.yml so comments, key order and formatting survive an append.
    """
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # don't wrap long lines (e.g. urls)
    y.indent(mapping=2, sequence=4, offset=2)
    return y


class Command(BaseCommand):
    help = 'Generate mkdocs.yml files for each top-level subdirectory in the docs directory.'

    def handle(self, *args, **options):
        #TODO: currently failes if overrides directory does not exist in docs
        '''
        Aborted with a configuration error!
ERROR   -  Config value 'theme': The path set in custom_dir ('/home/django/fish/docs/overrides') does not exist.
CommandError: Failed to build documentation for role 'judge'.
        '''
        docs_root = getattr(settings, 'DOCSERVE_DOCS_ROOT', os.path.join(settings.BASE_DIR, 'docs'))
        overrides = getattr(settings, 'DOCSERVE_OVERRIDE_DIRS', ['overrides'])
        site_name_prefix = getattr(settings, 'DOCSERVE_SITE_NAME_PREFIX', '')
        domain = settings.DOCSERVE_SITE_URL.lstrip('/')

        # When True (the default), an existing mkdocs_{role}.yml is treated as
        # hand-crafted: it is not regenerated/overwritten. Instead we only append
        # markdown files that are not already referenced in its nav to the bottom of
        # the list. Set to False to always regenerate from scratch.
        preserve_yml = getattr(settings, 'DOCSERVE_PRESERVE_YML', True)

        # make domain available in generate_mkdocs_yml
        self.domain = domain

        if not os.path.exists(docs_root):
            raise CommandError(f"The docs directory '{docs_root}' does not exist.")

        roles = [d for d in os.listdir(docs_root) if os.path.isdir(os.path.join(docs_root, d)) and not d in overrides]
        if not roles:
            self.stdout.write(self.style.WARNING("No subdirectories found in the docs directory."))
            return

        for role in roles:
            docs_dir = os.path.join(docs_root, role)
            output_file = os.path.join(docs_root, f'mkdocs_{role}.yml')
            site_name = f"{site_name_prefix}{role.capitalize()} Documentation"

            if preserve_yml and os.path.exists(output_file):
                added = self.append_missing_to_existing(output_file, docs_dir)
                if added:
                    self.stdout.write(self.style.SUCCESS(
                        f"Updated {output_file} for role '{role}': appended {len(added)} new file(s)."
                    ))
                    for rel in added:
                        self.stdout.write(self.style.WARNING(f"  + {rel}"))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"Preserved {output_file} for role '{role}': no new files to add."
                    ))
                continue

            nav = self.build_nav(docs_dir, role, rel_base='')
            config = self.make_config(nav, site_name, role)

            self._write_config(config, output_file)

            self.stdout.write(self.style.SUCCESS(f"Generated {output_file} for role '{role}'."))

    # -------------------------
    # NAV BUILDING
    # -------------------------

    def build_nav(self, dir_abs: str, role: str, rel_base: str) -> list:
        """
        Build nav for a directory. If a .pages file exists with `nav:`, use it as the
        primary order; warn and append any unlisted files/dirs to the end alphabetically.
        """
        pages_cfg = self._load_pages(dir_abs)
        if pages_cfg and isinstance(pages_cfg.get('nav'), list):
            return self._build_nav_from_pages(dir_abs, role, rel_base, pages_cfg['nav'])
        else:
            # fallback: alphabetical (index.md first), recursive
            return self._build_nav_from_fs(dir_abs, role, rel_base)

    def _build_nav_from_pages(self, dir_abs: str, role: str, rel_base: str, nav_list: list) -> list:
        """
        Build nav using the order specified in a .pages file (`nav:` list).
        Supports entries like:
          - "file.md"
          - "subdir"
          - { "Custom Title": "file.md" }
          - { "Section Title": "subdir" }
        Any md files or subdirs not listed are appended (with warnings) at the end alphabetically.
        """
        entries = []
        seen = set()

        # Discover actual items in the directory
        subdirs = [d for d in os.listdir(dir_abs) if os.path.isdir(os.path.join(dir_abs, d)) and not d.startswith('.')]
        files = [f for f in os.listdir(dir_abs) if os.path.isfile(os.path.join(dir_abs, f)) and not f.startswith('.')]
        md_files = [f for f in files if f.lower().endswith('.md')]

        # helper to normalize names
        def titleize(name: str) -> str:
            return name.replace('_', ' ').replace('-', ' ').title()

        # First pass: process items listed in .pages
        for item in nav_list:
            label, target = self._parse_pages_item(item)

            if not isinstance(target, str):
                self.stdout.write(self.style.WARNING(f"[.pages] Skipping invalid nav entry in {dir_abs!r}: {item!r}"))
                continue

            target_abs = os.path.join(dir_abs, target)
            if os.path.isdir(target_abs):
                # Section
                seen.add(('dir', target))
                section_title = label or titleize(os.path.basename(target))
                child_rel = os.path.join(rel_base, target).replace('\\', '/')
                child_abs = target_abs
                child_nav = self.build_nav(child_abs, role, child_rel)
                if child_nav:
                    entries.append({section_title: child_nav})
                else:
                    self.stdout.write(self.style.WARNING(f"[.pages] Directory listed but empty: {target_abs}"))
            else:
                # Assume file
                if not target.lower().endswith('.md'):
                    # allow bare name "foo" to mean "foo.md" if it exists
                    if os.path.exists(target_abs + '.md'):
                        target += '.md'
                        target_abs = target_abs + '.md'

                if os.path.isfile(target_abs) and target.lower().endswith('.md'):
                    seen.add(('file', target))
                    page_title = label or titleize(os.path.splitext(os.path.basename(target))[0])
                    rel_file = os.path.join(rel_base, target).replace('\\', '/')
                    entries.append({page_title: rel_file})
                else:
                    self.stdout.write(self.style.WARNING(f"[.pages] Listed item not found in {dir_abs!r}: {target!r}"))

        # Second pass: append unlisted files/dirs (alphabetically), with warnings
        # index.md first for files
        remaining_files = [f for f in md_files if ('file', f) not in seen]
        if 'index.md' in remaining_files:
            remaining_files.remove('index.md')
            remaining_files.insert(0, 'index.md')
        remaining_files.sort(key=lambda x: (x != 'index.md', x.lower()))

        remaining_dirs = [d for d in subdirs if ('dir', d) not in seen]
        remaining_dirs.sort(key=lambda d: d.lower())

        for f in remaining_files:
            self.stdout.write(self.style.WARNING(f"[.pages] Unlisted file (appending): {os.path.join(dir_abs, f)}"))
            rel_file = os.path.join(rel_base, f).replace('\\', '/')
            entries.append({self._default_page_title(f): rel_file})

        for d in remaining_dirs:
            self.stdout.write(self.style.WARNING(f"[.pages] Unlisted directory (appending): {os.path.join(dir_abs, d)}"))
            child_rel = os.path.join(rel_base, d).replace('\\', '/')
            child_abs = os.path.join(dir_abs, d)
            section_title = self._default_section_title(d)
            child_nav = self.build_nav(child_abs, role, child_rel)
            if child_nav:
                entries.append({section_title: child_nav})

        return entries

    def _build_nav_from_fs(self, dir_abs: str, role: str, rel_base: str) -> list:
        """
        Original behavior: alphabetical, with index.md first, recursive for subdirs.
        """
        entries = []

        # list dirs/files
        subdirs = [d for d in os.listdir(dir_abs) if os.path.isdir(os.path.join(dir_abs, d)) and not d.startswith('.')]
        files = [f for f in os.listdir(dir_abs) if os.path.isfile(os.path.join(dir_abs, f)) and not f.startswith('.')]
        md_files = [f for f in files if f.lower().endswith('.md')]

        # index.md first
        if 'index.md' in md_files:
            md_files.remove('index.md')
            md_files.insert(0, 'index.md')

        # sort case-insensitively
        subdirs.sort(key=lambda d: d.lower())
        # keep index.md at 0, sort the rest
        md_files[1:] = sorted(md_files[1:], key=lambda f: f.lower())

        # files first (to match your earlier flat expectation), then dirs
        for f in md_files:
            rel_file = os.path.join(rel_base, f).replace('\\', '/')
            entries.append({self._default_page_title(f): rel_file})

        for d in subdirs:
            child_abs = os.path.join(dir_abs, d)
            child_rel = os.path.join(rel_base, d).replace('\\', '/')
            section_title = self._default_section_title(d)
            child_nav = self.build_nav(child_abs, role, child_rel)
            if child_nav:
                entries.append({section_title: child_nav})

        return entries

    # -------------------------
    # PRESERVE / APPEND-ONLY MODE
    # -------------------------

    def append_missing_to_existing(self, output_file: str, docs_dir: str) -> list:
        """
        Load an existing mkdocs_{role}.yml, leave it otherwise untouched, and append
        any markdown files under docs_dir that are not already referenced in its nav
        to the bottom of the top-level nav list. Returns the list of relative paths
        appended (empty if nothing changed).
        """
        ryaml = _round_trip_yaml()
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                config = ryaml.load(f)
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"[preserve] Failed to parse {output_file!r}, regenerating instead: {e}"
            ))
            return []

        if config is None:
            config = {}

        if not isinstance(config, dict):
            self.stdout.write(self.style.WARNING(
                f"[preserve] {output_file!r} is not a mapping, skipping."
            ))
            return []

        nav = config.get('nav')
        if not isinstance(nav, list):
            nav = []
            config['nav'] = nav

        referenced = self._collect_referenced_md(nav)
        on_disk = self._scan_md_files(docs_dir)

        missing = [rel for rel in on_disk if rel not in referenced]
        # index.md first, then alphabetical, so appended order is predictable
        missing.sort(key=lambda x: (os.path.basename(x).lower() != 'index.md', x.lower()))

        if not missing:
            return []

        for rel in missing:
            nav.append({self._default_page_title(rel): rel})

        with open(output_file, 'w') as f:
            ryaml.dump(config, f)

        return missing

    def _collect_referenced_md(self, nav) -> set:
        """
        Walk an mkdocs nav structure and collect every markdown path it references
        (normalised to posix-style relative paths).
        """
        referenced = set()

        def walk(node):
            if isinstance(node, str):
                if node.lower().endswith('.md'):
                    referenced.add(node.replace('\\', '/'))
            elif isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                for value in node.values():
                    walk(value)

        walk(nav)
        return referenced

    def _scan_md_files(self, docs_dir: str) -> list:
        """
        Recursively list all markdown files under docs_dir as posix-style paths
        relative to docs_dir, skipping hidden files/directories.
        """
        found = []
        for root, dirs, files in os.walk(docs_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.startswith('.') or not f.lower().endswith('.md'):
                    continue
                rel = os.path.relpath(os.path.join(root, f), docs_dir).replace('\\', '/')
                found.append(rel)
        return found

    def _parse_pages_item(self, item):
        """
        Normalize a .pages nav item to (label, target_str).
        - "file.md" -> (None, "file.md")
        - {"Label": "file.md"} -> ("Label", "file.md")
        - "subdir" -> (None, "subdir")
        - {"Section": "subdir"} -> ("Section", "subdir")
        """
        if isinstance(item, str):
            return None, item
        if isinstance(item, dict) and len(item) == 1:
            label, target = next(iter(item.items()))
            return label, target
        return None, None

    def _default_page_title(self, filename: str) -> str:
        base = os.path.splitext(os.path.basename(filename))[0]
        return base.replace('_', ' ').replace('-', ' ').title()

    def _default_section_title(self, dirname: str) -> str:
        return dirname.replace('_', ' ').replace('-', ' ').title()

    def _load_pages(self, dir_abs: str) -> dict | None:
        """
        Load and return .pages YAML dict if present; otherwise None.
        We only care about the 'nav' key, but we ignore silently if missing.
        """
        pages_path = os.path.join(dir_abs, '.pages')
        if not os.path.exists(pages_path):
            return None
        try:
            with open(pages_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    self.stdout.write(self.style.WARNING(f"[.pages] Ignoring non-dict config in {pages_path!r}"))
                    return None
                return data
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[.pages] Failed to parse {pages_path!r}: {e}"))
            return None

    # -------------------------
    # CONFIG
    # -------------------------

    def make_config(self, nav: list, site_name: str, role: str) -> dict:
        """
        Build final mkdocs config (merging your existing MKDOCS_CUSTOM_SETTINGS).
        """
        config = {
            'site_name': site_name,
            'nav': nav,
            'theme': {
                'name': 'material',
                'custom_dir': 'overrides',
            },
            'use_directory_urls': False,
            'docs_dir': role,
            'site_url': f'{self.domain}/docs/{role}/',
        }

        # Merge default and role-specific overrides
        settings_dict = getattr(settings, 'MKDOCS_CUSTOM_SETTINGS', {})
        default_settings = settings_dict.get('default', {})
        # Get custom settings for the role
        custom_settings = settings_dict.get(role, {})

        # Merge default settings into config
        self.deep_update(config, default_settings)
        # Then merge role-specific settings
        self.deep_update(config, custom_settings)

        # Ensure mermaid diagrams render (material bundles mermaid.js; it just
        # needs the superfence wired up). Added after merges so it survives any
        # user-supplied markdown_extensions.
        if getattr(settings, 'DOCSERVE_ENABLE_MERMAID', True):
            self._ensure_mermaid(config)

        return config

    def _ensure_mermaid(self, config: dict) -> None:
        """
        Inject the mkdocs-material mermaid superfence into config's
        `markdown_extensions`, merging with whatever the user already declared.
        Produces:
            markdown_extensions:
              - pymdownx.superfences:
                  custom_fences:
                    - name: mermaid
                      class: mermaid
                      format: !!python/name:pymdownx.superfences.fence_code_format
        """
        try:
            from pymdownx.superfences import fence_code_format
        except ImportError:
            self.stdout.write(self.style.WARNING(
                "[mermaid] pymdown-extensions not installed; skipping mermaid "
                "fence config. Install it (it ships with mkdocs-material)."
            ))
            return

        exts = config.setdefault('markdown_extensions', [])
        if not isinstance(exts, list):
            self.stdout.write(self.style.WARNING(
                "[mermaid] markdown_extensions is not a list; skipping."
            ))
            return

        # Locate (or create) the pymdownx.superfences entry as a dict so we can
        # attach options. It may be present as a bare string or as a dict.
        superfences = None
        for i, item in enumerate(exts):
            if item == 'pymdownx.superfences':
                superfences = {'pymdownx.superfences': {}}
                exts[i] = superfences
                break
            if isinstance(item, dict) and 'pymdownx.superfences' in item:
                if not isinstance(item.get('pymdownx.superfences'), dict):
                    item['pymdownx.superfences'] = {}
                superfences = item
                break
        if superfences is None:
            superfences = {'pymdownx.superfences': {}}
            exts.append(superfences)

        opts = superfences['pymdownx.superfences']
        fences = opts.setdefault('custom_fences', [])
        if any(isinstance(f, dict) and f.get('name') == 'mermaid' for f in fences):
            return  # already configured — don't duplicate

        fences.append({
            'name': 'mermaid',
            'class': 'mermaid',
            'format': fence_code_format,
        })

    def _write_config(self, config: dict, output_file: str) -> None:
        """
        Dump config to YAML, repairing the python/name tag PyYAML emits for the
        mermaid fence callable so MkDocs can load it.
        """
        raw = yaml.dump(config, sort_keys=False)
        raw = _PYTHON_NAME_EMPTY.sub(r'\1', raw)
        with open(output_file, 'w') as f:
            f.write(raw)

    def deep_update(self, original, update):
        """
        Recursively update a dictionary.
        """
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(original.get(key), dict):
                self.deep_update(original[key], value)
            else:
                original[key] = value
