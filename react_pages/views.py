from django.middleware import csrf
from time import time
from django.forms import Form
from django.shortcuts import render
from django.template.defaulttags import CsrfTokenNode
from django.views.generic import View, FormView

from react_pages.templatetags.react_pages import render_react_page, project_dir


class ReactPageView(View):
    page_name = None
    extra_js_context = {}

    def get_js_context(self):
        return {}

    def get(self, *args, **kwargs):
        if not self.page_name:
            raise ValueError(
                "React Pages: "
                f'Did you forget to specify a "page_name" '
                f"in {self.__class__}?"
            )
        else:
            page_dir = project_dir / self.page_name

            if page_dir.exists():
                js_context = self.get_js_context()

                if type(js_context) != dict:
                    raise ValueError('"get_js_context()" must return a dict!')

                js_context.update(self.extra_js_context)

                s = time()
                context = render_react_page(page_name=self.page_name, **js_context)
                print((time() - s) * 1000)

                return render(
                    template_name="react_pages_include_tag.html",
                    context=context,
                    request=self.request,
                )
            else:
                raise ValueError(
                    f"React Pages: The page {repr(self.page_name)} "
                    f"doesn't exist! "
                    f"Run react-pages page {repr(self.page_name)} "
                    f"from {repr(project_dir)} to create this page"
                )


########
# Forms
########

FORM_FIELD_ATTRS = {
    "label",
    "id_for_label",
    "html_name",
    "help_text",
    "errors",
    "is_hidden",
    "data",
    "auto_id",  # not sure whether this is relevant
}

FORM_FIELD_METHODS = {"value", "label_tag", "css_classes", "as_widget", "as_hidden"}


FORM_METHODS = {"as_p", "as_table", "as_ul", "non_field_errors"}


def serialize_form(form: Form):
    form_json = dict(as_html=str(form))

    for i in ("hidden_fields", "visible_fields"):
        fields = getattr(form, i)()
        form_json.update({i: [field.name for field in fields]})

    # serialize form fields
    form_json["fields"] = []
    for field in form:
        name = field.name

        # form field attributes
        form_json[name] = {
            attr_name: getattr(field, attr_name) for attr_name in FORM_FIELD_ATTRS
        }
        # form field methods
        form_json[name].update(
            {
                method_name: getattr(field, method_name)()
                for method_name in FORM_FIELD_METHODS
            }
        )

        form_json[name]["as_html"] = str(field)

        form_json["fields"].append(form_json[name])

    form_json.update(
        {method_name: getattr(form, method_name)() for method_name in FORM_METHODS}
    )

    return form_json


class ReactPagesFormView(ReactPageView, FormView):
    def get_js_context(self):
        js_ctx = super().get_js_context()

        ctx = super().get_context_data()
        ctx["csrf_token"] = csrf.get_token(self.request)

        s = time()
        js_ctx["form"] = serialize_form(ctx["form"])

        print((time() - s) * 1000)

        js_ctx["csrf_token"] = {
            "as_html": CsrfTokenNode().render(context=ctx),
            "value": ctx["csrf_token"],
        }

        return js_ctx
