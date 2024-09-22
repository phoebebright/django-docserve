# docserve/management/commands/build_docs.py

import os
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Build MkDocs documentation for all roles.'

    def handle(self, *args, **options):
        docs_root = getattr(settings, 'DOCSERVE_DOCS_ROOT', os.path.join(settings.BASE_DIR, 'docs'))
        static_root = os.path.join(settings.BASE_DIR, 'static', 'docs')

        roles = [d for d in os.listdir(docs_root) if os.path.isdir(os.path.join(docs_root, d))]

        if not roles:
            self.stdout.write(self.style.WARNING("No documentation to build."))
            return

        for role in roles:
            mkdocs_yml = os.path.join(docs_root, f'mkdocs_{role}.yml')
            docs_dir = os.path.join(docs_root, role)
            output_dir = os.path.join(static_root, role)

            if not os.path.exists(mkdocs_yml):
                self.stdout.write(self.style.WARNING(f"Configuration file '{mkdocs_yml}' not found. Generating..."))
                subprocess.run(['python', 'manage.py', 'generate_mkdocs_yml'], check=True)

            build_command = [
                'mkdocs', 'build',
                '-f', mkdocs_yml,
                '-d', output_dir,
                '-s', docs_dir
            ]

            self.stdout.write(f"Building documentation for role '{role}'...")
            subprocess.run(build_command, check=True)
            self.stdout.write(self.style.SUCCESS(f"Documentation for role '{role}' built successfully."))
