# docserve/management/commands/build_docs.py

import os
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Build MkDocs documentation for all roles.'

    def handle(self, *args, **options):
        docs_root = getattr(settings, 'DOCSERVE_DOCS_ROOT', os.path.join(settings.BASE_DIR, 'docs'))
        output_root = getattr(settings, 'DOCSERVE_DOCS_SITE_ROOT', os.path.join(settings.BASE_DIR, 'docs_site'))

        # create output_root directory if it does not exist
        if not os.path.exists(output_root):
            os.makedirs(output_root)

        roles = [d for d in os.listdir(docs_root) if os.path.isdir(os.path.join(docs_root, d))]

        if not roles:
            self.stdout.write(self.style.WARNING("No documentation to build."))
            return

        for role in roles:
            mkdocs_yml = os.path.join(docs_root, f'mkdocs_{role}.yml')
            output_dir = os.path.join(output_root, role)

            if not os.path.exists(mkdocs_yml):
                self.stdout.write(self.style.WARNING(f"Configuration file '{mkdocs_yml}' not found. Generating..."))
                subprocess.run(['python', 'manage.py', 'generate_mkdocs_yml'], check=True)

            build_command = [
                'mkdocs', 'build',
                '--config-file', mkdocs_yml,
                '--site-dir', output_dir
            ]

            self.stdout.write(f"Building documentation for role '{role}'...")
            result = subprocess.run(build_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                self.stderr.write(self.style.ERROR(f"Error building documentation for role '{role}':"))
                self.stderr.write(result.stdout)
                self.stderr.write(result.stderr)
                raise CommandError(f"Failed to build documentation for role '{role}'.")
            else:
                self.stdout.write(self.style.SUCCESS(f"Documentation for role '{role}' built successfully."))
