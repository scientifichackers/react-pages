from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from react_pages.cli import run_subproc


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('mode', type=str)

    def handle(self, *args, **options):
        try:
            project_dir = Path(settings.REACT_PAGES_PROJECT_DIR).resolve()
        except AttributeError:
            raise ImproperlyConfigured('React Pages: Please specify "REACT_PAGES_PROJECT_DIR" in your settings.py!')
        else:
            run_subproc(['react-pages', 'develop', '--static-url', static('/') + '{page name}'], cwd=project_dir)
