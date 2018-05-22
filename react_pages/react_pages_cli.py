import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from crayons import *
from halo import Halo

# beauty stuff
SPINNER = 'moon'

# TODO handle manifest.json

NODEJS = Path(__file__).parent.parent.joinpath('nodejs')

PACKAGE_JSON = {
    "name": "",
    "version": "1.0.0",
    "description": "",
    "author": "",
    "license": "MIT",
}


def handle_subproc_result(result, printout):
    if result is not None:
        if printout:
            if result.stdout:
                print(blue(result.stdout))

            if result.stderr:
                print(red(result.stderr))

        if result.returncode != 0:
            sys.exit(red('Failed!'))


def run_subproc(cmd, spin=True, **kwargs):
    kwargs.setdefault('cwd', Path.cwd())
    if spin:
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)

    print(yellow('Run: ' + ' '.join(map(str, cmd))))

    result = None
    try:
        if spin:
            with Halo(spinner=SPINNER):
                result = subprocess.run(cmd, encoding='utf-8', **kwargs)
        else:
            result = subprocess.run(cmd, encoding='utf-8', **kwargs)
    except FileNotFoundError as e:
        print(red(e))
        sys.exit(red("Are you sure you're at the right place?", bold=True))
    finally:
        handle_subproc_result(result, spin)


@click.group()
def cli():
    pass


@click.command('project',
               short_help='Create a new project, inside a new directory')
@click.argument('project-name', type=click.Path())
def init(project_name):
    project_dir = Path.cwd().joinpath(project_name)
    project_name = project_dir.name

    if project_dir.exists():
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

        PACKAGE_JSON['name'] = project_name

        with open(project_dir.joinpath('package.json'), 'w') as f:
            json.dump(PACKAGE_JSON, f)

    print(white('Installing node dependencies…'))

    run_subproc(
        ['npm', 'install', '--save', 'react', 'react-dom'],
        cwd=project_dir,
    )

    print(cyan('Successfully created project', bold=True), green(project_name, bold=True) + '!')


@click.command('page', short_help='Create a new page, inside a new directory, containing boiler-plate for react')
@click.argument('page-name', type=click.Path())
def init_page(page_name):
    page_dir = Path.cwd().joinpath(page_name)
    print(
        '{} {}…'.format(
            white('Creating new page', bold=True),
            green(page_name, bold=True),
        )
    )
    try:
        shutil.copytree(NODEJS.joinpath('src'), page_dir)
    except FileExistsError:
        print(red('Error: Directory already exists!'))
    else:
        print(blue(f'Copied page boilerplate to {page_dir}'))
        print(
            '{} {} {}'.format(
                magenta('Run'),
                magenta(f'react-pages develop', bold=True),
                magenta('to use this page')
            )
        )


def resolve_paths(src, dest):
    dest_dir = resolve_dest_dir(dest)

    for src_path in resolve_src_paths(src):
        yield src_path.absolute(), dest_dir


def resolve_dest_dir(dest):
    # fallback to default destination location
    if dest is None:
        dest_dir = Path.cwd().joinpath('build')
    else:
        dest_dir = Path(dest)

    if not dest_dir.exists():
        dest_dir.mkdir(parents=True)

    return dest_dir.absolute()


def resolve_src_paths(src: Path):
    # fallback to default source location
    if src is None:
        src = Path().cwd()
    else:
        src = Path(src)

    # search for "index.js" if src is a dir
    if src.is_dir():
        yield from src.glob('*/index.js')
    else:
        yield src


def get_npm_bin(cwd=Path.cwd()):
    return Path(subprocess.check_output(['npm', 'bin'], encoding='utf-8', cwd=cwd).strip())


def get_npm_root(cwd=Path.cwd()):
    return Path(subprocess.check_output(['npm', 'root'], encoding='utf-8', cwd=cwd).strip())


def get_package_json(cwd=Path.cwd()):
    package_json = cwd.joinpath('package.json')

    if package_json.exists():
        return package_json
    else:
        print(cyan("Courtesy Notice: Couldn't find package.json in current dir, so using the default one!"))
        return NODEJS.joinpath('package.json')


DEMO_HTML = '<div id="root"></div><script src="{}"></script>'


def create_index_html(dest_dir: Path) -> Path:
    """
    Generate a demo html file, containing reference to the given js file,
    then return the path to generated html file
    """
    js_path = dest_dir.joinpath('js', 'bundle.js')
    html_path = dest_dir.joinpath('index.html')

    with open(html_path, 'w') as fp:
        fp.write(DEMO_HTML.format(str(js_path.absolute())))

    return html_path


@click.command(short_help='"Inspect" the current directory and print out relevant info in JSON format')
def inspect():
    pass


@click.command(short_help='Bundle everything into a single .js file, suitable for use in production.')
@click.option('-s', '--src', '--source',
              type=click.Path(exists=True),
              help='directory to look for "index.js", or path to file')
@click.option('--dest', '--destination',
              type=click.Path(),
              is_flag=True,
              help='destination directory, or filename')
def deploy(source: str, destination: str, html: bool):
    """
    Bundle everything into a single .js file, suitable for use in production.

    By default, this shall -
    Look for "index.js" in current directory, and incrementally in sub-directories if nothing can be found.
    Build at ./build/<page>.bundle.js.
    """

    raise NotImplementedError

    npm_bin = get_npm_bin()
    npm_root = get_npm_root()

    env = os.environ.copy()
    env['NODE_ENV'] = 'production'
    env['BABEL_ENV'] = 'production'

    for src_path, dest_path in resolve_paths(source, destination):
        if html:
            create_index_html(dest_path)

        print(
            '{} {} ~> {}…'.format(
                white('Deploy:', bold=True),
                magenta(src_path),
                green(dest_path)
            )
        )

        result = run_subproc(
            config['commands']['deploy']['webpack'],
            {'bin': npm_bin,
             'root': npm_root,
             'source': src_path,
             'destination': dest_path},
            env
        )

        if not result:
            return

    print(cyan('done!'))


@click.command(short_help='Start the development environment')
@click.option('-s', '--src', '--source',
              type=click.Path(exists=True),
              help='directory to look for "index.js", or path to file')
@click.option('-d', '--dest', '--destination',
              type=click.Path(),
              help='destination directory')
@click.option('--no-watch',
              is_flag=True,
              help='Disable file watcher')
def develop(source: str, destination: str, no_watch: bool):
    """
    Start the development environment,
    Bundles everything into a singe .js file

    By default, this shall-
    Look for "index.js" in current directory, and incrementally in sub-directories if nothing can be found.
    Watchify file, output-ing to./build/<page>.bundle.js.
    """

    for src_path, dest_dir in list(resolve_paths(source, destination)):
        print(
            '{} {} ~> {}…'.format(
                white('Develop:', bold=True),
                magenta(src_path, bold=True),
                green(dest_dir, bold=True)
            )
        )
        root = get_npm_root()

        run_subproc(
            [
                NODEJS.joinpath('scripts', 'develop.js'),
                json.dumps({
                    'src': str(src_path),
                    'src dir': str(src_path.parent),
                    'dest dir': str(dest_dir),
                    'npm root': str(root),
                    'watch': not no_watch,
                    'html_template': str(NODEJS.joinpath('public', 'index.html'))
                }),
            ],
            spin=False,
        )

    print(cyan('done!'))


cli.add_command(init)
cli.add_command(init_page)
cli.add_command(deploy)
cli.add_command(develop)

if __name__ == '__main__':
    cli()