from django.contrib.staticfiles.management.commands import collectstatic
from django.conf import settings
import subprocess
from pathlib import Path

class Command(collectstatic.Command):
    def handle(self, *args, **options):
        react_pages_project_dir = Path(settings.REACT_PAGES_PROJECT_DIR)
        static_dir = app_path.joinpath('static', 'js')

        subprocess.run(
            ['react-pages', 'deploy', '--source', '--destination', dest_path],
            cwd=react_pages_project_dir
        )
        super(Command, self).handle(*args, **options)
