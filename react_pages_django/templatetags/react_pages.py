import json
import subprocess
from pathlib import Path

from crayons import *
from django import template
from django.apps import apps
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import mark_safe, escapejs

from react_pages.react_pages_cli import resolve_output_path

register = template.Library()


@register.simple_tag(takes_context=True)
def render_react_page(context, page_name, **kwargs):
    app_name = context['request'].resolver_match.func.__module__.split('.')[0]
    app_path = Path(apps.get_app_config(app_name).path)
    output_dir = app_path.joinpath('static', 'js')

    try:
        react_pages_project_dir = Path(settings.REACT_PAGES_PROJECT_DIR)
    except AttributeError:
        print(red('React Pages Courtesy Notice: Please specify "REACT_PAGES_PROJECT_DIR" in your settings.py!'))
    else:
        input_path = react_pages_project_dir.joinpath(page_name, 'page.js')

        if input_path.exists():
            output_path = resolve_output_path(output_dir, input_path)

            if settings.DEBUG:
                subprocess.Popen(
                    ['react-pages', 'develop', '--input', input_path, '--output', output_path],
                    cwd=react_pages_project_dir
                )
            else:
                raise NotImplementedError

            return mark_safe(
                '<script>{}</script><script src="{}"></script>'.format(
                    ''.join(
                        f"""{escapejs(k)} = "{escapejs(json.dumps(v, skipkeys=True))}";""" for k, v in kwargs.items()
                    ),
                    static(output_path)
                )
            )
        else:
            print(red(f"React Pages: {input_path} doesn't exist!"))
