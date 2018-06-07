import json
import os
import shutil
import subprocess
from functools import wraps
from pathlib import Path

import click
import dotenv
from crayons import *

from react_pages.core import build, build_cache, clear_cahce, \
    CACHE_DIR, PACKAGE_JSON, copy_files_safe, print_truncated

SPINNER = 'moon'


def get_build_decorator(*, deploy):
    def build_decorator(func):
        @click.option('--src', '--source',
                      type=click.Path(exists=True),
                      help='directory to look for "index.js", or path to file')
        @click.option('--dest', '--destination',
                      type=click.Path(),
                      is_flag=True,
                      help='destination directory')
        @click.option('--no-watch',
                      is_flag=True,
                      help='Disable file watcher')
        @click.option('-v', '--verbose',
                      is_flag=True,
                      help='Verbose compiler output')
        @click.option('--static-url',
                      help='''
                      The base url for static assets (css / js/ media). 
                      Accepts the wildcard `{page name}`, 
                      which will be replaced by the name of page.
                      By default, it is the relative file path.
                      ''')
        @wraps(func)
        def wrapper(*args, **kwargs):
            val = func()
            build(*args, **kwargs, deploy=deploy)
            return val

        return wrapper

    return build_decorator


def check_cache():
    if not CACHE_DIR.exists():
        print(red('Missing react-pages cache dir!', bold=True))
        build_cache()


@click.group()
def cli():
    pass


@click.command('project', short_help='Create a new project')
@click.argument('project-name', type=click.Path())
def init_project(project_name):
    """
    Create a new project (inside a new directory),
    or Patch an existing one.

    Creates the following directory structure -

    """

    check_cache()

    project_dir = Path.cwd().joinpath(project_name)
    project_name = project_dir.name

    package_json_path = project_dir / 'package.json'

    if project_dir.exists():
        # try to get project name from package.json
        try:
            with open(package_json_path, 'r') as fp:
                package_json = json.load(fp)
            project_name = package_json['name']
        except (FileNotFoundError, KeyError):
            pass

        print(
            '{} {}…'.format(
                white('Use existing project', bold=True),
                green(project_name, bold=True),
            )
        )
    else:
        print(
            '{} {}…'.format(
                white('Creating new project', bold=True),
                green(project_name, bold=True),
            )
        )

        project_dir.mkdir(parents=True)

    # package.json
    if not package_json_path.exists():
        PACKAGE_JSON['name'] = project_name
        with open(package_json_path, 'w') as fp:
            json.dump(PACKAGE_JSON, fp)

    # other files
    copy_files_safe(CACHE_DIR, ('.env', '.gitignore', 'public'), project_dir)

    print(cyan('Done!'))
    print()
    print(white('To get started, create a page:'))
    print(
        '$ {}'.format(
            magenta(f'cd {project_dir.name}')
        )
    )
    print(
        '$ {}'.format(
            magenta(f'react-pages page my_page')
        )
    )


@click.command('page',
               short_help='Create a new page, inside a new directory, '
                          'containing boiler-plate for react')
@click.argument('page-name', type=click.Path())
def init_page(page_name):
    check_cache()

    page_dir = Path.cwd() / page_name
    print(
        '{} {}…'.format(
            white('Creating new page', bold=True),
            green(page_name, bold=True),
        )
    )
    try:
        shutil.copytree(CACHE_DIR / 'src', page_dir)
    except FileExistsError:
        print(red('Error: Directory already exists!'))
    else:
        print(blue(f'Copied page boilerplate to {page_dir}'))

        # update .env
        dotenv_path = Path.cwd() / '.env'
        if dotenv_path.exists():
            node_path = dotenv.get_key(str(dotenv_path), 'NODE_PATH') or "."
            page_node_path = os.path.relpath(page_dir, dotenv_path.parent)

            if page_node_path not in node_path.split(os.pathsep):
                node_path += os.pathsep + page_node_path
                dotenv.set_key(str(dotenv_path), 'NODE_PATH', node_path)

        print(
            '{} {} {}'.format(
                white('Run', bold=True),
                magenta('react-pages develop', bold=True),
                white('to use this page.', bold=True)
            )
        )


@click.command(short_help='Start the Production build environment')
@get_build_decorator(deploy=True)
def deploy():
    """
    Start the development environment,
    which transpiles react JSX to js,
    suitable for running in browser.

    Also creates an `index.html`, which can be used in the browser.

    By default, this shall -
    Look for "index.js" in current directory, and immediate sub-directory.
    Start a file watcher,
    and create a production build when a file change is observed.

    Output location: {npm prefix}/build/{page name}/js/bundle.js.

    {npm prefix} is the output of the "npm prefix" command.
    Generally, it points to the directory that contains "package.json"

    {page name} is the name of directory containing "index.js"
    """

    check_cache()


@click.command(short_help='Start the Development build environment')
@get_build_decorator(deploy=False)
def develop():
    """
    Start the development environment,
    which transpiles react JSX to js,
    suitable for running in browser.

    Also creates an `index.html`, which can be used in the browser.

    By default, this shall-
    Look for "index.js" in current directory, and immediate sub-directory.
    Start a file watcher,
    and create a development build when a file change is observed.

    Output location: {npm prefix}/build/{page name}/js/bundle.js.

    {npm prefix} is the output of the "npm prefix" command.
    Generally, it points to the directory that contains "package.json"

    {page name} is the name of directory containing "index.js"
    """

    check_cache()


@click.command(
    short_help='A combination of django `manage.py runserver` '
               'and `react-pages develop`',
    context_settings={'ignore_unknown_options': True,
                      'allow_extra_args': True})
@click.argument('runserver_args', nargs=-1)
def runserver(runserver_args):
    """
    A combination of django's `manage.py runserver` and `react-pages develop`.
    Must be run in a directory containing `manage.py`.


    Example:

        react-pages runserver 0.0.0.0:7000

        Here, "0.0.0.0:7000" will be passed to `manage.py runserver`
    """

    check_cache()

    if (Path.cwd() / 'manage.py').exists():
        cmd = ['python', 'manage.py', 'react_pages_develop']
        print_truncated(cmd)
        proc1 = subprocess.Popen(cmd)

        cmd = ['python', 'manage.py', 'runserver', *runserver_args]
        print_truncated(cmd)
        proc2 = subprocess.run(cmd)

        proc1.terminate()
        proc1.wait()

        if proc1.returncode == 0 and proc2.returncode == 0:
            print(cyan('Done!'))
        else:
            exit(red('Failed!'))
    else:
        print(red(
            '"manage.py" not found. '
            'Please run this command from a '
            'directory containing "manage.py".'))


@click.command('clear-cache', short_help="Clear the cache")
def _clear_cache():
    clear_cahce()


@click.command(short_help="Rebuild the cache")
def cache():
    build_cache()


cli.add_command(init_project)
cli.add_command(init_page)
cli.add_command(deploy)
cli.add_command(develop)
cli.add_command(runserver)
cli.add_command(_clear_cache)
cli.add_command(cache)

if __name__ == '__main__':
    cli()
