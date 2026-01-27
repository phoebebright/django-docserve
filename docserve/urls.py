# docserve/urls.py

from django.urls import path
from . import views

app_name = 'docserve'

urlpatterns = [
    path('', views.docs_home, name='docs_home'),
    path('<str:role>/assets/<path:path>', views.serve_docs_asset, name='serve_docs_asset'),

    path('<str:role>/', views.serve_docs, name='serve_docs_index'),
    path('<str:role>/<path:path>', views.serve_docs, name='serve_docs'),
]
