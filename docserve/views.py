# docserve/views.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, Http404, FileResponse
from django.shortcuts import render
from django.conf import settings
import os
import mimetypes
from pathlib import Path
from django.views.static import serve as static_serve

import logging
from django.utils.cache import patch_cache_control

logger = logging.getLogger(__name__)



def serve_docs_asset(request, role, path):
    # assets are in the built site directory
    document_root = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role, "assets")
    resp = static_serve(request, path, document_root=document_root)
    patch_cache_control(resp, public=True, max_age=31536000, immutable=True)
    return resp

@login_required
def docs_home(request):
    role_definitions = getattr(settings, 'DOCSERVE_ROLE_DEFINITIONS', {})
    role_default = getattr(settings, 'DOCSERVE_ROLE_DEFAULT', None)
    available_roles = []

    # used to hold static data like css that will be used to override other data - a bit confusing to have it here
    ignore = {"overrides"}

    roles = [
        d for d in os.listdir(os.path.join(settings.BASE_DIR, 'docs'))
        if os.path.isdir(os.path.join(settings.BASE_DIR, 'docs', d)) and d not in ignore
    ]

    for role in roles:
        role_check = role_definitions.get(role, role_default)
        if role_check(request.user):
            available_roles.append(role)

    return render(request, 'docserve/docs_home.html', {'roles': available_roles})

@login_required
def serve_docs(request, role, path=''):
    '''serve the documentation and associated files'''

    # if extensions are min.js or min.css then just serve them directly
    if path.endswith('.js'):
        content_type = 'text/javascript'
        full_path = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(open(full_path, "rb"), content_type=content_type)
        else:
            logger.warning(f"File does NOT exist: {full_path}")

    if path.endswith('.css'):
        content_type = 'text/css'
        full_path = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(open(full_path, "rb"), content_type=content_type)
        else:
            logger.warning(f"File does NOT exist: {full_path}")

    if path.endswith('.png'):
        content_type = 'image/png'
        full_path = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(open(full_path, "rb"), content_type=content_type)
        else:
            logger.warning(f"File does NOT exist: {full_path}")

    # does this still apply?  trying to load css but role is still a role
    # allow a directories to bypass role checks, eg. have an overrides directory for custom css and js
    overrides = getattr(settings, 'DOCSERVE_OVERRIDE_DIRS', ['overrides'])
    if not role in overrides:

        # check this user has the role required by the first part of the path, eg. docs/role/getting-started/first/page.html
        role_definitions = getattr(settings, 'DOCSERVE_ROLE_DEFINITIONS', {})
        role_default = getattr(settings, 'DOCSERVE_ROLE_DEFAULT', None)
        if not role in role_definitions:
            if role_default:
                logger.error(f"Role '{role}' not defined in DOCSERVE_ROLE_DEFINITIONS. Using default role {role_default}.")
                role = role_default
            else:
                return HttpResponseForbidden(f"Your role {role} has not been defined so we cannot give you access.")

        role_check = role_definitions.get(role)

        if not role_check(request.user):
            return HttpResponseForbidden("You do not have access to this documentation.")

    docs_root = os.path.join(settings.DOCSERVE_DOCS_SITE_ROOT, role)

    if path == '':
        # Serve the documentation home page
        path = 'index.html'
    else:
        # remove trailing slash if it is there
        if path.endswith('/'):
            path = path[:-1]

        file_path = os.path.join(docs_root, path)
        if os.path.isdir(file_path):
            # If the path is a directory, append 'index.html'
            path = os.path.join(path, 'index.html')
        elif not os.path.splitext(path)[1]:
            # If the path has no file extension, it's a page; append '.html'
            path += '.html'
        # If the path has a file extension, assume it's an asset file and leave it as is

    # If path.endswith('.md'), it's likely a source file link that wasn't converted
    # We should try to serve the .html version instead if it exists
    if path.endswith('.md'):
        path = path[:-3] + '.html'

    file_path = os.path.join(docs_root, path)

    if not os.path.exists(file_path):
        raise Http404(f"Page not found: {path}")

    with open(file_path, 'rb') as f:
        content = f.read()

    content_type, _ = mimetypes.guess_type(file_path)
    logger.info(f"Serving {file_path} with content type {content_type}")
    if not content_type:
        content_type = 'application/octet-stream'

    return HttpResponse(content, content_type=content_type)
