# docserve/management/commands/generate_mkdocs_yml.py

import os
import yaml
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate mkdocs.yml files for each top-level subdirectory in the docs directory.'


    def handle(self, *args, **options):
            self.stdout.write(self.style.NOTICE("Starting generate_mkdocs_yml..."))
            call_command("generate_mkdocs_yml")

            self.stdout.write(self.style.NOTICE("Starting build_docs..."))
            call_command("build_docs")

            self.stdout.write(self.style.SUCCESS("All tasks completed successfully!"))
