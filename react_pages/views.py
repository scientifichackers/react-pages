from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View

from react_pages.templatetags.react_pages import render_react_page, project_dir


class ReactPageView(View):
    page_name = None
    js_context = {}

    def get_js_context(self):
        pass

    def get(self, request):
        if not self.page_name:
            raise ValueError(
                'React Pages: '
                f'Did you forget to specify a "page_name" '
                f"in {self.__class__}?"
            )
        else:
            page_dir = project_dir / self.page_name

            if page_dir.exists():
                js_context = self.get_js_context()

                if js_context is None:
                    js_context = self.js_context

                return HttpResponse(
                    render_to_string(
                        "react_pages_include_tag.html",
                        render_react_page(
                            page_name=self.page_name, **js_context
                        )
                    )
                )
            else:
                raise ValueError(
                    f"React Pages: The page {repr(self.page_name)} "
                    f"doesn't exist! "
                    f"Run react-pages page {repr(self.page_name)} "
                    f"from {repr(project_dir)} to create this page")
