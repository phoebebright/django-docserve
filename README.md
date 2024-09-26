# Docserve

**Docserve** purpose is to make it easier to produce documentation for a project where you want to show different documentation to users with different roles.

**Warning (or not)**: much of this code produced with gpt 01-preview

This simple library solves the following problems:
- serve docs appropriate to the user's role, and only those docs.
- avoid having to create yml files for the docs I create, just assume all the docs in a role folder are to be included

## Features

- **Role-Based Access Control**: Serve documentation to users based on their group memberships.
- **Reusable App**: Easily integrate into multiple Django projects.
- **MkDocs Integration**: Supports documentation generated by MkDocs, including themes like Material Design.
- **Easy Configuration**: Minimal setup required to get started.
- **Static Files Handling**: Manages static assets (CSS, JS) required by MkDocs documentation.

## Requirements

- Python 3.7 or higher
- Django 3.2 or higher
- MkDocs 1.4.2 or higher
- Optional: MkDocs Material theme if used

## Installation

1. **Install the Package**

   You can install `docserve` directly from your local source or via a package repository if published.

   ```bash
   pip install django-docserve

## Add to Installed Apps

In your project's settings.py, add docserve to the INSTALLED_APPS list:

    INSTALLED_APPS = [
        # ... other installed apps ...
        'docserve',
    ]

Point to the location of your source docs:

    DOCSERVE_DOCS_ROOT = os.path.join(BASE_DIR, 'docs')

Include URLs

In your project's urls.py, include docserve URLs:

    from django.urls import path, include

    urlpatterns = [
        # ... other URL patterns ...
        path('docs/', include('docserve.urls', namespace='docserve')),
    ]

Configure Static Files

Ensure your settings.py is configured to handle static files:

    
    import os
    
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    
    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]
    Collect Static Files

Run the following command to collect static files:


    python manage.py collectstatic

Create User Groups

Ensure that the necessary user groups (roles) are created in your Django project. You can create groups via the Django admin interface or programmatically:


    from django.contrib.auth.models import Group
    
    roles = ['admin', 'factory', 'distributor', 'support', 'user']
    for role in roles:
        Group.objects.get_or_create(name=role)
    Assign Users to Groups

Use the Django admin interface or scripts to assign users to the appropriate groups.


## Management Commands

### Generating MkDocs Configuration Files

Use the `generate_mkdocs_yml` command to generate `mkdocs.yml` files for each role:

```bash
python manage.py generate_mkdocs_yml

This command creates MkDocs configuration files for each role based on the templates provided in the docserve app. You can customize these templates as needed.


---

### 6. Ensure MkDocs is Available

Since the management commands call `mkdocs` via subprocess, ensure that `mkdocs` is installed in your environment.

Add `mkdocs` to your `requirements.txt`:

```txt
Django>=3.2,<5.0
mkdocs>=1.4.2
mkdocs-material>=9.1.15
PyYAML>=5.4


Usage
Generate Documentation with MkDocs

Build your documentation for each role using MkDocs:

bash
Copy code
mkdocs build -v -f mkdocs_admin.yaml -d docserve/static/docserve/docs/admin/
mkdocs build -v -f mkdocs_factory.yaml -d docserve/static/docserve/docs/factory/
mkdocs build -v -f mkdocs_distributor.yaml -d docserve/static/docserve/docs/distributor/
mkdocs build -v -f mkdocs_support.yaml -d docserve/static/docserve/docs/support/
mkdocs build -v -f mkdocs_user.yaml -d docserve/static/docserve/docs/user/
Access the Documentation

Documentation Home: Users can navigate to /docs/ to see a list of documentation available to them based on their roles.
Direct Access: Users can access documentation for a specific role at /docs/<role>/.
Role-Based Access Control

The app checks if a user is part of the group corresponding to the requested role before serving the documentation. If the user lacks the necessary role, they receive a 403 Forbidden response.

Customization
Templates

You can customize the templates used by docserve by copying them into your project's template directory and modifying them as needed.

Static Files

If you need to serve additional static files or customize the styling, place your files in your project's static directory and ensure they do not conflict with docserve's static files.

Middleware (Optional)
If you prefer to centralize access control, you can implement custom middleware in your project to handle role checking.

Deployment
When deploying to production:

Static Files Serving

Ensure your web server (e.g., Nginx, Apache) is configured to serve static files from STATIC_ROOT.

Security

Use HTTPS to secure user data.
Ensure that your web server does not serve the documentation files directly, bypassing Django's authentication and authorization checks.
Example Nginx Configuration
nginx
Copy code
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /docs/ {
        proxy_pass http://localhost:8000;
        include proxy_params;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://localhost:8000;
        include proxy_params;
        proxy_set_header Host $host;
    }
}
###mContributing
Contributions are welcome! Please submit issues and pull requests for any features or bug fixes.

### License
This project is licensed under the MIT License.

### Contact
For questions or support, please contact Your Name.

Note: Replace yourdomain.com, /path/to/your/project/, and [Your Name](mailto:your.email@example.com) with your actual domain, project path, and contact information.
