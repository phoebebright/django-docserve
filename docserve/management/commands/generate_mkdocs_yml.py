# docserve/management/commands/generate_mkdocs_yml.py

import os
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate mkdocs.yml files for each top-level subdirectory in the docs directory.'

    def handle(self, *args, **options):
        docs_root = getattr(settings, 'DOCSERVE_DOCS_ROOT', os.path.join(settings.BASE_DIR, 'docs'))

        if not os.path.exists(docs_root):
            raise CommandError(f"The docs directory '{docs_root}' does not exist.")

        roles = [d for d in os.listdir(docs_root) if os.path.isdir(os.path.join(docs_root, d))]
        if not roles:
            self.stdout.write(self.style.WARNING("No subdirectories found in the docs directory."))
            return

        for role in roles:
            docs_dir = os.path.join(docs_root, role)
            output_file = os.path.join(docs_root, f'mkdocs_{role}.yml')
            site_name = f"{role.capitalize()} Documentation"

            self.generate_mkdocs_yml(docs_dir, output_file, site_name)
            self.stdout.write(self.style.SUCCESS(f"Generated {output_file} for role '{role}'."))

    def generate_mkdocs_yml(self, docs_dir, output_file, site_name):
        nav = []

        for root, dirs, files in os.walk(docs_dir):
            # Ignore hidden directories and files
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

            # Sort directories and files
            dirs.sort()
            files.sort()

            for file in files:
                if file.endswith('.md'):
                    # Get the relative path
                    rel_dir = os.path.relpath(root, docs_dir)
                    rel_file = os.path.join(rel_dir, file) if rel_dir != '.' else file

                    # Remove file extension for display
                    page_name = os.path.splitext(file)[0].replace('_', ' ').title()

                    # Build navigation entry
                    if rel_dir != '.':
                        # Nested directories
                        sections = rel_dir.split(os.sep)
                        current_level = nav
                        for section in sections:
                            section_title = section.replace('_', ' ').title()
                            for item in current_level:
                                if section_title in item:
                                    current_level = item[section_title]
                                    break
                            else:
                                # Section not found, create it
                                new_section = {section_title: []}
                                current_level.append(new_section)
                                current_level = new_section[section_title]
                        # Add the page to the current level
                        current_level.append({page_name: rel_file.replace('\\', '/')})
                    else:
                        # Top-level files
                        nav.append({page_name: rel_file.replace('\\', '/')})

        # Create the mkdocs configuration
        config = {
            'site_name': site_name,
            'nav': nav,
            'theme': {
                'name': 'material'
            },
            'use_directory_urls': False
        }

        # Write the configuration to the output file
        with open(output_file, 'w') as f:
            yaml.dump(config, f, sort_keys=False)
