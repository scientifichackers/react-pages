import json
from pathlib import Path

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()


@register.inclusion_tag('react_pages.html')
def render_react_page(page_name, **kwargs):
    # https://stackoverflow.com/questions/38473545/how-to-get-string-from-a-django-utils-safestring-safetext
    page_name += ''

    try:
        project_dir = Path(settings.REACT_PAGES_PROJECT_DIR).resolve()
    except AttributeError:
        raise ImproperlyConfigured('React Pages: Please specify "REACT_PAGES_PROJECT_DIR" in your settings.py!')
    else:
        page_dir = project_dir / page_name

        if page_dir.exists():
            for k, v in kwargs.items():
                try:  # If already JSON serialized, we don't do it again.
                    json.loads(v)
                except (ValueError, TypeError):
                    try:
                        kwargs[k] = json.dumps(v, skipkeys=True, cls=DjangoJSONEncoder)
                    except TypeError as e:
                        raise TypeError(
                            f"React Pages: Couldn't serialize the kwarg {repr(k)}, having value {repr(kwargs[k])}.\n"
                            f"Either manually serialize it, or provide a JSON serializable value.\n"
                            f"While rendering page {repr(page_name)} - {repr(e)}"
                        )
                else:
                    pass

            with open(project_dir / 'build' / page_name / 'index.html', "r") as f:
                html = f.read()

            return {
                'vars': kwargs,
                'html': html
            }
        else:
            raise ValueError(f"React Pages: The page {repr(page_name)} doesn't exist! "
                             f"Run react-pages page {repr(page_name)} from {repr(project_dir)} to create this page")
