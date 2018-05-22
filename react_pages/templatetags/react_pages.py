import json
import subprocess
from pathlib import Path

from django import template
from django.apps import apps
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import mark_safe, escapejs

from react_pages.react_pages_cli import resolve_paths

register = template.Library()


@register.simple_tag(takes_context=True)
def render_react_page(context, page_name, **kwargs):
    # https://stackoverflow.com/questions/38473545/how-to-get-string-from-a-django-utils-safestring-safetext
    page_name += ''

    try:
        react_pages_project_dir = Path(settings.REACT_PAGES_PROJECT_DIR)
    except AttributeError:
        raise ValueError('React Pages Courtesy Notice: Please specify "REACT_PAGES_PROJECT_DIR" in your settings.py!')
    else:
        try:
            if settings.DEBUG:
                # resolve paths
                src_dir = react_pages_project_dir.joinpath(page_name)
                app_name = context['request'].resolver_match.func.__module__.split('.')[0]
                app_path = Path(apps.get_app_config(app_name).path)
                static_dir = app_path.joinpath('static', 'js')
                src_path, dest_path = next(resolve_paths(src_dir, static_dir))

                subprocess.run(
                    ['react-pages', 'develop', '--source', src_dir, '--destination', dest_path, '--no-watch'],
                    cwd=react_pages_project_dir
                )

                static_path = static(str(dest_path.relative_to(app_path.joinpath('static'))))
            else:
                raise NotImplementedError

            return mark_safe(
                '<div id="root"></div><script>{}</script><script src="{}"></script>'.format(
                    ''.join(
                        f"""{escapejs(k)} = "{escapejs(json.dumps(v, skipkeys=True))}";""" for k, v in kwargs.items()
                    ),
                    static_path
                )
            )
        except StopIteration:
            raise FileNotFoundError(f"React Pages: Couldn't find the requested page at {react_pages_project_dir}")
