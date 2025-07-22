# docserve/mixins.py
from django.conf import settings

class DocServeMixin:
    docserve_page = None  # Specify the documentation page path or name

    def get_docserve_page(self):
        """
        Returns the documentation page path or name.
        Override this method to customize how the documentation page is determined.
        """
        return self.docserve_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docserve_page = self.get_docserve_page()
        if docserve_page:
            # Construct the documentation URL
            context['docserve_url'] = self.get_docserve_url(docserve_page)

        if 'extra_context' in settings.MKDOCS_CUSTOM_SETTINGS:
            # Add any extra context from settings
            context.update(settings.MKDOCS_CUSTOM_SETTINGS['extra_context'])
        return context

    def get_docserve_url(self, page):
        """
        Constructs the URL to the documentation page.
        This requires the SITE_URL setting to be set and the value used in including your docs url.
        eg.     path('docs/', include(('docserve.urls', 'docserve'), namespace='docserve')),
        add 'docs' to your url
        """
        if not page.startswith('/'):
            page = '/' + page

        return settings.SITE_URL + '/docs' + page
