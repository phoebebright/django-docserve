# docserve/views.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render
from django.conf import settings
import os
import mimetypes

import logging
logger = logging.getLogger(__name__)


@login_required
def docs_home(request):
    role_definitions = getattr(settings, 'DOCSERVE_ROLE_DEFINITIONS', {})
    role_default = getattr(settings, 'DOCSERVE_ROLE_DEFAULT', None)
    roles = [d for d in os.listdir(os.path.join(settings.BASE_DIR, 'docs')) if os.path.isdir(os.path.join(settings.BASE_DIR, 'docs', d))]
    available_roles = []

    for role in roles:
        role_check = role_definitions.get(role, role_default)
        if role_check(request.user):
            available_roles.append(role)

    return render(request, 'docserve/docs_home.html', {'roles': available_roles})

@login_required
def serve_docs(request, role, path=''):
    '''serve the documentation and associated files'''

    # allow a directories to bypass role checks, eg. have an overrides directory for custom css and js
    overrides = getattr(settings, 'DOCSERVE_OVERRIDE_DIRS', ['overrides'])
    if not role in overrides:

        # check this user has the role required by the first part of the path, eg. docs/role/getting-started/first/page.html
        role_definitions = getattr(settings, 'DOCSERVE_ROLE_DEFINITIONS', {})
        role_default = getattr(settings, 'DOCSERVE_ROLE_DEFAULT', None)
        if not role in role_definitions:
            logger.error(f"Role '{role}' not defined in DOCSERVE_ROLE_DEFINITIONS. Using default role {DOCSERVE_ROLE_DEFAULT}.")

        role_check = role_definitions.get(role,role_default)

        if not role_check(request.user):
            return HttpResponseForbidden("You do not have access to this documentation.")

    docs_root = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role)

    if path == '':
        # Serve the documentation home page
        path = 'index.html'
    else:
        file_path = os.path.join(docs_root, path)
        if os.path.isdir(file_path):
            # If the path is a directory, append 'index.html'
            path = os.path.join(path, 'index.html')
        elif not os.path.splitext(path)[1]:
            # If the path has no file extension, it's a page; append '.html'
            path += '.html'
        # If the path has a file extension, assume it's an asset file and leave it as is

    file_path = os.path.join(docs_root, path)

    if not os.path.exists(file_path):
        raise Http404("Page not found")

    with open(file_path, 'rb') as f:
        content = f.read()

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    return HttpResponse(content, content_type=content_type)
