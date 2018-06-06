import json
from pathlib import Path

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model

register = template.Library()

try:
    project_dir = Path(settings.REACT_PAGES_PROJECT_DIR).resolve()
except AttributeError:
    raise ImproperlyConfigured(
        'React Pages: Please specify "REACT_PAGES_PROJECT_DIR" '
        'in your settings.py!'
    )


def serialize_django_model_instance(obj):
    return serialize("json", [obj], ensure_ascii=False)[1:-1]


@register.inclusion_tag('react_pages_include_tag.html')
def render_react_page(page_name, **js_context):
    # https://stackoverflow.com/questions/38473545/how-to-get-string-from-a-django-utils-safestring-safetext
    page_name += ''

    page_dir = project_dir / page_name

    if not page_name:
        raise ValueError("React Pages: Page name cant't be empty!")

    if page_dir.exists():
        index_html_path = project_dir / 'build' / page_name / 'index.html'

        with open(index_html_path, "r") as f:
            html_str = f.read()

        for key, val in js_context.items():
            # If its a django model instance, we can handle that.
            if issubclass(val, Model):
                js_context[key] = serialize_django_model_instance(val)
            else:
                # If already JSON serialized, we don't do it again.
                try:
                    json.loads(val)
                except (ValueError, TypeError):
                    try:
                        js_context[key] = json.dumps(val, skipkeys=True,
                                                     cls=DjangoJSONEncoder)
                    except TypeError as e:
                        raise TypeError(
                            f"React Pages: Couldn't serialize the kwarg "
                            f"{repr(key)}, having value {repr(js_context[key])}.\n"
                            f"Either manually serialize it, "
                            f"or provide a JSON serializable value.\n"
                            f"While rendering page "
                            f"{repr(page_name)} - {repr(e)}"
                        )
                else:
                    pass

        return {
            'html': html_str,
            'vars': js_context,
        }
    else:
        raise ValueError(
            f"React Pages: The page {repr(page_name)} "
            f"doesn't exist! "
            f"Run react-pages page {repr(page_name)} "
            f"from {repr(project_dir)} to create this page")
