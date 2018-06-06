import json
import os
import shutil
import subprocess
from functools import wraps
from pathlib import Path
from typing import Iterable, Tuple

import click
import dotenv
from crayons import *
from halo import Halo

SPINNER = 'moon'

NODEJS = Path(__file__).parent.joinpath('nodejs')

PACKAGE_JSON = {
    "name": "",
    "version": "1.0.0",
    "description": "",
    "author": "",
    "license": "MIT",
}


def handle_subproc_result(result, enable_spinner):
    if result is not None:
        if enable_spinner:
            if result.stdout:
                print(blue(result.stdout))

            if result.stderr:
                print(red(result.stderr))

        if result.returncode != 0:
            exit(red('Failed!'))


def run_subproc(cmd, *, enable_spinner=False, **kwargs):
    kwargs.setdefault('cwd', Path.cwd())
    if enable_spinner:
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)

    print(yellow('Run: ' + ' '.join(map(str, cmd))))

    result = None
    try:
        if enable_spinner:
            with Halo(spinner=SPINNER):
                result = subprocess.run(cmd, encoding='utf-8', **kwargs)
        else:
            result = subprocess.run(cmd, encoding='utf-8', **kwargs)
    except FileNotFoundError as e:
        print(red(e))
        exit(red("Are you sure you're at the right place?", bold=True))
    finally:
        handle_subproc_result(result, enable_spinner)


def get_npm_bin(cwd=Path.cwd()):
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'bin'], encoding='utf-8', cwd=cwd).strip())


def get_npm_root(cwd=Path.cwd()):
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'root'], encoding='utf-8', cwd=cwd).strip())


def get_npm_prefix(cwd=Path.cwd()):
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'prefix'], encoding='utf-8', cwd=cwd).strip())


def resolve_paths(src: str, dest: str) -> Iterable[Tuple[Path, Path, Path or None]]:
    """Given src and dest str, yield some src paths and dest dirs"""

    global_public = Path.cwd() / 'public'

    for src_path in resolve_src_paths(src):
        local_public = src_path.parent / 'public'

        if local_public.exists():
            yield src_path, resolve_dest_dir(src_path, dest), local_public
        elif global_public.exists():
            yield src_path, resolve_dest_dir(src_path, dest), global_public
        else:
            courtesy_notice('"public" folder not found, fall-back to default!')

            yield src_path, resolve_dest_dir(src_path, dest), NODEJS / 'public'


def resolve_dest_dir(src_path: Path, dest: str) -> Path:
    # fallback to default destination location
    if dest is None:
        dest_dir = get_npm_prefix() / 'build'
    else:
        dest_dir = Path(dest)

    dest_dir = dest_dir / src_path.parent.name

    if dest_dir.exists():
        if not dest_dir.is_dir():
            exit(red('destination must be a directory.'))
    else:
        dest_dir.mkdir(parents=True)

    return dest_dir.resolve()


def resolve_src_paths(src: str) -> Iterable[Path]:
    # fallback to default source location
    if src is None:
        src = Path().cwd()
    else:
        src = Path(src)

    # search for "index.js" if src is a dir
    if src.is_dir():
        yield from list(src.glob('index.js')) or src.glob('*/index.js')
    else:
        yield src


def copy_files_safe(src_dir: Path, names: Iterable[str], dest_dir: Path):
    for filename in names:
        src = src_dir / filename

        if src.exists():
            if src.is_dir():
                dest = dest_dir / src.name

                if not dest.exists():
                    shutil.copytree(src, dest)
            else:
                dest = dest_dir / filename

                if not dest.exists():
                    shutil.copy(src, dest)


def courtesy_notice(msg):
    print(cyan(f"Courtesy Notice: {msg}", bold=True))


def build(source: str, destination: str, no_watch: bool, verbose: bool, static_url: str, *, deploy=False):
    settings_list = []
    for src_path, dest_dir, public_dir in resolve_paths(source, destination):
        npm_root = get_npm_root()
        npm_prefix = get_npm_prefix()

        copy_files_safe(public_dir, ('favicon.ico', 'manifest.json'), dest_dir)

        if static_url is None:
            public_url = '.'
        else:
            public_url = static_url.format(**{
                'page name': src_path.parent.name,
            })

        settings_list.append({
            'start msg': '{} {} ~> {}…'.format(
                white('Deploy:' if deploy else 'Develop:', bold=True),
                magenta(src_path, bold=True),
                green(dest_dir, bold=True)
            ),
            'inbuilt node_modules': str(NODEJS / 'node_modules'),
            'complete msg': str(green(src_path.parent.name, bold=True)),
            'deploy': deploy,
            'src': str(src_path),
            'src dir': str(src_path.parent),
            'dest dir': str(dest_dir),
            'npm root': str(npm_root),
            'watch': not no_watch,
            'html template': str(public_dir / 'index.html'),
            'public url': public_url,
            'package.json': str(npm_prefix / 'package.json'),
            'npm prefix': str(npm_prefix),
            'verbose': verbose,
        })

    if len(settings_list):
        run_subproc(
            [
                '/usr/bin/env', 'node',
                get_npm_root() / 'react-pages' / 'scripts' / 'react_pages.js',
                json.dumps(settings_list)
            ],
            cwd=get_npm_prefix()
        )

        print(cyan('Done!'))
    else:
        print(red('You must create a page first!'))

        print('{} {} {}'.format(
            white('Run', bold=True),
            magenta('react-pages page <page name>', bold=True),
            white('to create a page.', bold=True)
        ))


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
                      Accepts the wildcard `{page name}`, which will be replaced by the name of page.
                      By default, it is the relative file path.
                      ''')
        @wraps(func)
        def wrapper(*args, **kwargs):
            return build(*args, **kwargs, deploy=deploy)

        return wrapper

    return build_decorator


@click.group()
def cli():
    pass


@click.command('project', short_help='Create a new project')
@click.argument('project-name', type=click.Path())
def init(project_name):
    """
    Create a new project (inside a new directory),
    or Patch an existing one.

    Creates the following directory structure -

    """

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
                white('Patching existing project', bold=True),
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
    copy_files_safe(NODEJS, ('.env', '.gitignore', 'public'), project_dir)

    print(white('Installing node modules…'))
    print(white('Grab a coffee, this usually takes some time.', bold=True))
    run_subproc(
        ['/usr/bin/env', 'npm', 'install', '--save', NODEJS],
        cwd=project_dir,
        enable_spinner=True,
    )

    print(cyan('Created project', bold=True), green(project_name, bold=True) + '!')


@click.command('page', short_help='Create a new page, inside a new directory, containing boiler-plate for react')
@click.argument('page-name', type=click.Path())
def init_page(page_name):
    page_dir = Path.cwd() / page_name
    print(
        '{} {}…'.format(
            white('Creating new page', bold=True),
            green(page_name, bold=True),
        )
    )
    try:
        shutil.copytree(NODEJS / 'src', page_dir)
    except FileExistsError:
        print(red('Error: Directory already exists!'))
    else:
        print(blue(f'Copied page boilerplate to {page_dir}'))

        # update .env
        dotenv_path = Path.cwd() / '.env'
        if dotenv_path.exists():
            node_path = dotenv.get_key(str(dotenv_path), 'NODE_PATH') or ""
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
def deploy(*args, **kwargs):
    """
    Start the development environment, which transpiles react JSX to js, suitable for running in browser.

    Also creates an `index.html`, which can be used in the browser.

    By default, this shall -
    Look for "index.js" in current directory, and immediate sub-directory.
    Start a file watcher, and create a production build when a file change is observed.

    Output location: {npm prefix}/build/{page name}/js/bundle.js.

    {npm prefix} is the output of the "npm prefix" command.
    Generally, it points to the directory that contains "package.json"

    {page name} is the name of directory containing "index.js"
    """

    pass


@click.command(short_help='Start the Development build environment')
@get_build_decorator(deploy=False)
def develop(*args, **kwargs):
    """
    Start the development environment, which transpiles react JSX to js, suitable for running in browser.

    Also creates an `index.html`, which can be used in the browser.

    By default, this shall-
    Look for "index.js" in current directory, and immediate sub-directory.
    Start a file watcher, and create a development build when a file change is observed.

    Output location: {npm prefix}/build/{page name}/js/bundle.js.

    {npm prefix} is the output of the "npm prefix" command.
    Generally, it points to the directory that contains "package.json"

    {page name} is the name of directory containing "index.js"
    """

    pass


@click.command(short_help='A combination of django `manage.py runserver` and `react-pages develop`',
               context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@click.argument('runserver_args', nargs=-1)
def runserver(runserver_args):
    """
    A combination of django's `manage.py runserver` and `react-pages develop`.
    Must be run in a directory containing `manage.py`.


    Example:

        react-pages runserver 0.0.0.0:7000

        Here, "0.0.0.0:7000" will be passed to `manage.py runserver`
    """

    if (Path.cwd() / 'manage.py').exists():
        proc1 = subprocess.Popen(['python', 'manage.py', 'react_pages', 'develop'])
        proc2 = subprocess.run(['python', 'manage.py', 'runserver', *runserver_args])

        proc1.terminate()
        proc1.wait()

        if proc1.returncode == 0 and proc2.returncode == 0:
            print(cyan('Done!'))
        else:
            exit(red('Failed!'))
    else:
        print(red('"manage.py" not found. Please run this command from a directory containing "manage.py".'))


@click.command('clear-cache', short_help="Fix a bug where react-pages can't be uninstalled using pip")
def clear_cache():
    """
    Because of react-pages's structure, react-pages may not uninstall using pip.

    To overcome this, this handy script is provided.
    """

    print(white('Removing node modules…'))

    shutil.rmtree(NODEJS / 'node_modules', ignore_errors=True)

    print(cyan('Done!'))
    print('{} {}{}'.format(
        white('If you were trying to uninstall, Please run', bold=True),
        magenta('pip uninstall react-pages', bold=True),
        white('.\nIt should work now.')
    ))


cli.add_command(init)
cli.add_command(init_page)
cli.add_command(deploy)
cli.add_command(develop)
cli.add_command(runserver)
cli.add_command(clear_cache)

if __name__ == '__main__':
    cli()
