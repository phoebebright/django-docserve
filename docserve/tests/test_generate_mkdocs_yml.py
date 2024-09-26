# docserve/tests/test_generate_mkdocs_yml.py

import os
import shutil
import tempfile
import yaml

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.conf import settings


class GenerateMkdocsYmlCommandTest(TestCase):
    def setUp(self):
        # Create a temporary directory to act as DOCSERVE_DOCS_ROOT
        self.temp_dir = tempfile.mkdtemp()
        # Mock settings
        self.docs_root = self.temp_dir
        # Create sample documentation structure
        # Let's create two roles: 'user' and 'admin'
        self.roles = ['user', 'admin']
        for role in self.roles:
            role_dir = os.path.join(self.docs_root, role)
            os.makedirs(role_dir)
            # Create some markdown files
            index_md = os.path.join(role_dir, 'index.md')
            with open(index_md, 'w') as f:
                f.write(f'# {role.capitalize()} Documentation\n')
            # Create a subdirectory with another markdown file
            sub_dir = os.path.join(role_dir, 'getting_started')
            os.makedirs(sub_dir)
            sub_md = os.path.join(sub_dir, 'intro.md')
            with open(sub_md, 'w') as f:
                f.write(f'# Getting Started with {role.capitalize()}\n')

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    @override_settings(DOCSERVE_DOCS_ROOT=None)  # We'll set it explicitly
    def test_generate_mkdocs_yml(self):
        with self.settings(DOCSERVE_DOCS_ROOT=self.docs_root):
            # Call the management command
            call_command('generate_mkdocs_yml')

            # Check that mkdocs_<role>.yml files are created
            for role in self.roles:
                mkdocs_yml_path = os.path.join(self.docs_root, f'mkdocs_{role}.yml')
                self.assertTrue(os.path.exists(mkdocs_yml_path), f"{mkdocs_yml_path} does not exist")

                # Load the generated YAML file
                with open(mkdocs_yml_path, 'r') as f:
                    config = yaml.safe_load(f)

                # Check that the site_name is correct
                expected_site_name = f"{role.capitalize()} Documentation"
                self.assertEqual(config.get('site_name'), expected_site_name)

                # Check that the nav structure is correct
                expected_nav = [
                    {'Index': 'index.md'},
                    {'Getting Started': [
                        {'Intro': 'getting_started/intro.md'}
                    ]}
                ]
                self.assertEqual(config.get('nav'), expected_nav)

                # Check that theme is set to 'material'
                self.assertEqual(config.get('theme', {}).get('name'), 'material')

                # Check that use_directory_urls is False
                self.assertFalse(config.get('use_directory_urls', True))

    @override_settings(DOCSERVE_DOCS_ROOT=None)
    def test_no_docs_directory(self):
        # Remove the docs_root directory
        shutil.rmtree(self.docs_root)
        with self.settings(DOCSERVE_DOCS_ROOT=self.docs_root):
            with self.assertRaises(CommandError) as cm:
                call_command('generate_mkdocs_yml')
            self.assertIn(f"The docs directory '{self.docs_root}' does not exist.", str(cm.exception))

    @override_settings(DOCSERVE_DOCS_ROOT=None)
    def test_no_roles_found(self):
        # Remove role directories
        for role in self.roles:
            shutil.rmtree(os.path.join(self.docs_root, role))
        with self.settings(DOCSERVE_DOCS_ROOT=self.docs_root):
            # Capture stdout
            from io import StringIO
            out = StringIO()
            call_command('generate_mkdocs_yml', stdout=out)
            output = out.getvalue()
            self.assertIn("No subdirectories found in the docs directory.", output)
