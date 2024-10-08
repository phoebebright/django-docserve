# docserve/mixins.py

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
        return context

    def get_docserve_url(self, page):
        """
        Constructs the URL to the documentation page.
        """
        # Determine the user's role (you can customize this method)
        role = self.get_user_role()
        # Build the URL to the documentation page
        url = f"/docs/{role}/{page}"
        return url

    def get_user_role(self):
        """
        Determines the user's role.
        Override this method if necessary.
        """
        # Example implementation based on user groups
        if self.request.user.groups.filter(name='admin').exists():
            return 'admin'
        elif self.request.user.groups.filter(name='manager').exists():
            return 'manager'
        elif self.request.user.groups.filter(name='organiser').exists():
            return 'organiser'
        else:
            return 'competitor'
