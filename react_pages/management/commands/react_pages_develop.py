from pathlib import Path

from crayons import *
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from react_pages.cli import run_subproc


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            project_dir = Path(settings.REACT_PAGES_PROJECT_DIR).resolve()
        except AttributeError:
            raise ImproperlyConfigured('React Pages: Please specify "REACT_PAGES_PROJECT_DIR" in your settings.py!')
        else:
            cmd = ['react-pages', 'develop', '--static-url', static('/') + '{page name}']

            if options.get('verbosity') > 1:
                cmd.append('--verbose')

            print(yellow(f'Run: {cmd}'))
            run_subproc(cmd, cwd=project_dir)
