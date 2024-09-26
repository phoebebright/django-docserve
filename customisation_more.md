Full docs from chatgpt on customisation:

Certainly! Here is the updated markdown documentation for this feature, which you can copy into your `README.md` file:

```markdown
### Customizing MkDocs Configuration via Django Settings

You can customize the appearance and functionality of your MkDocs-generated documentation directly through your Django `settings.py` file. This approach allows you to define default and role-specific customizations without modifying the codebase.

#### 1. Define Customization Settings in `settings.py`

Add a new dictionary called `MKDOCS_CUSTOM_SETTINGS` to your `settings.py` file:

```python
# settings.py

# MkDocs customization settings (optional)
MKDOCS_CUSTOM_SETTINGS = {
    'default': {
        'theme': {
            'name': 'material',
            'palette': {
                'primary': 'blue',
                'accent': 'light blue'
            },
            'font': {
                'text': 'Open Sans',
                'code': 'Source Code Pro'
            },
            'icon': {
                'logo': 'cloud',
                'repo': 'github'
            }
        },
        'extra_css': [
            'overrides/extra.css'
        ],
        'extra_javascript': [
            'overrides/extra.js'
        ],
        'plugins': [
            'search',
            'minify'
        ]
    },
    'admin': {
        'theme': {
            'palette': {
                'primary': 'red',
                'accent': 'blue'
            }
        }
    },
    'user': {
        'theme': {
            'palette': {
                'primary': 'green',
                'accent': 'teal'
            }
        }
    }
}
```

- **Note**: The `'default'` key contains settings that apply to all roles unless overridden.
- **Role-Specific Customizations**: Define customizations for specific roles (e.g., `'admin'`, `'user'`).

#### 2. How It Works

The `generate_mkdocs_yml.py` management command has been modified to read the `MKDOCS_CUSTOM_SETTINGS` from `settings.py` and apply them when generating the MkDocs configuration files for each role.

- **Default Configuration**: If `MKDOCS_CUSTOM_SETTINGS` is not defined, default settings are used.
- **Merging Settings**:
  - Default settings under `'default'` are applied first.
  - Role-specific settings override defaults where specified.

#### 3. Modify `generate_mkdocs_yml.py`

The management command uses a helper function `deep_update` to recursively merge dictionaries:

```python
def deep_update(self, original, update):
    """
    Recursively update a dictionary.
    """
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            self.deep_update(original[key], value)
        else:
            original[key] = value
```

This ensures that nested dictionaries in your settings are merged correctly.

#### 4. Regenerate and Rebuild Documentation

After defining your custom settings, regenerate your MkDocs configuration files and rebuild the documentation:

```bash
python manage.py generate_mkdocs_yml
python manage.py build_docs
```

#### 5. Verify the Customizations

- **Serve the Documentation Locally**:

  ```bash
  mkdocs serve -f docs/mkdocs_admin.yml
  ```

- **Check the Appearance**:
  - Open the documentation in your browser to verify that the customizations are applied.
  - Repeat for other roles if necessary.

#### 6. Example: Role-Specific Customizations

Here is how you can define different customizations for each role:

```python
# settings.py

MKDOCS_CUSTOM_SETTINGS = {
    'default': {
        'theme': {
            'name': 'material',
            'palette': {
                'primary': 'indigo',
                'accent': 'indigo'
            }
        },
        'plugins': ['search']
    },
    'admin': {
        'theme': {
            'palette': {
                'primary': 'red',
                'accent': 'orange'
            },
            'font': {
                'text': 'Roboto',
                'code': 'Fira Code'
            }
        },
        'plugins': ['search', 'minify']
    },
    'user': {
        'theme': {
            'palette': {
                'primary': 'blue',
                'accent': 'light blue'
            }
        },
        'extra_css': ['overrides/user_extra.css']
    }
}
```

#### 7. Customization Options

You can customize various aspects of MkDocs:

- **Theme Settings**: Change colors, fonts, icons, etc.
- **Extra CSS and JavaScript**: Add custom styles and scripts.
- **Plugins**: Add MkDocs plugins for additional features.

#### 8. Defaults and Optional Settings

- **Defaults**: If `MKDOCS_CUSTOM_SETTINGS` is not defined in `settings.py`, the default MkDocs settings are used.
- **Optional**: All customization settings are optional. You can specify as much or as little as you need.

#### 9. Additional Resources

- **MkDocs Configuration Options**: [MkDocs Configuration](https://www.mkdocs.org/user-guide/configuration/)
- **Material Theme Customization**: [Material Theme](https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/)
- **MkDocs Plugins**: [MkDocs Plugins](https://github.com/mkdocs/mkdocs/wiki/MkDocs-Plugins)

---

By following these steps, you can easily customize the look and feel of your MkDocs-generated documentation directly from your Django `settings.py` file, with the flexibility to provide default and role-specific configurations.

```
