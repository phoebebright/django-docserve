# docserve/views.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render
from django.conf import settings
import os
import mimetypes


@login_required
def docs_home(request):
    # Get the list of roles the user has
    user_roles = request.user.groups.values_list('name', flat=True)
    return render(request, 'docs_home.html', {'roles': user_roles})


@login_required
def serve_docs(request, role, path=''):
    if not request.user.groups.filter(name=role).exists():
        return HttpResponseForbidden("You do not have access to this documentation.")

    docs_root = os.path.join(settings.DOCSERVE_DOCS_SITE, role)

    if path == '':
        path = 'index.html'
    else:
        file_path = os.path.join(docs_root, path)
        if os.path.isdir(file_path):
            path = os.path.join(path, 'index.html')
        else:
            path += '.html'

    file_path = os.path.join(docs_root, path)

    if not os.path.exists(file_path):
        raise Http404("Page not found")

    with open(file_path, 'rb') as f:
        content = f.read()
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    return HttpResponse(content, content_type=content_type)
