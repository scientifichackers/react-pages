import shlex
import shutil
import subprocess
from pathlib import Path

import click
import toml
from crayons import *
from halo import Halo

# paths
ROOT = Path(__file__).parent.parent
PROJECT = ROOT.joinpath('boilerplate', 'project')
PAGE = ROOT.joinpath('boilerplate', 'page')

PROJECT_FILES = (
    'react-pages.toml',
    'package.json',
    'package-lock.json',
    '.babelrc'
)

# beauty stuff
SPINNER = 'moon'

# try to load local config. Fallback to default if necessary
try:
    config = toml.load(str(Path.cwd().joinpath('react-pages.toml')))
except FileNotFoundError:
    config = toml.load(str(PROJECT.joinpath('react-pages.toml')))

DEMO_HTML = '<div id="root"></div><script src="{}"></script>'


def create_demo_html(js_path: Path) -> Path:
    """
    Generate a demo html file, containing reference to the given js file,
    then return the path to generated html file
    """

    try:
        html_filename = js_path.name.split('.')[0] + '.html'
    except IndexError:
        html_filename = 'demo.html'
    html_path = js_path.parent.joinpath(html_filename)

    with open(html_path, 'w') as fp:
        fp.write(DEMO_HTML.format(str(js_path.absolute())))

    return html_path


@click.group()
def cli():
    pass


@click.command('project',
               short_help='Create a new project, inside a new directory')
@click.argument('project-name', type=click.Path())
def init(project_name):
    print(
        '{} {}…'.format(
            white('Creating new project', bold=True),
            green(project_name, bold=True),
        )
    )
    project_dir = Path.cwd().joinpath(project_name)

    if not project_dir.exists():
        project_dir.mkdir(parents=True)

    if any(project_dir.joinpath(i).exists() for i in PROJECT_FILES):
        print(red('The directory ') + green(project_dir) + red(' contains files that could conflict:\n'))

        for i in PROJECT_FILES:
            if project_dir.joinpath(i).exists():
                print(f'\t{i.name}')
        print('\nEither try using a new directory name, or remove the files listed above.')
    else:
        for i in PROJECT_FILES:
            shutil.copy(PROJECT.joinpath(i), project_dir)

        print(blue(f'Copied project boilerplate to {project_dir}'))

        print(white('Installing node dependencies…'))
        with Halo(spinner=SPINNER):
            result = subprocess.run(
                ['npm', 'install'],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )

        if result.stdout:
            print(blue(result.stdout))
        if result.stderr:
            print(red(result.stderr))

        if result.returncode == 0:
            print(cyan('Successfully created project ', bold=True) + green(project_name, bold=True), '!')
        else:
            print(red('Failed!'))


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
        shutil.copytree(PAGE, page_dir)
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
    # fallback to default destination location
    if dest is None:
        dest = Path.cwd().joinpath('build')

        if not dest.exists():
            dest.mkdir(parents=True)
    else:
        dest = Path(dest)

    # fallback to default source location
    if src is None:
        src = Path().cwd()
    else:
        src = Path(src)

    for src_path in resolve_src_paths(src):
        yield src_path.absolute(), resolve_dest_path(src_path, dest).absolute()


def recursive_search(to_find, path, num=0):
    found = list(path.glob(f'{"*/" * num}{to_find}'))
    num += 1

    if found:
        return found
    else:
        return recursive_search(to_find, path, num)


def resolve_src_paths(src: Path):
    # search for "index.js" if src is a dir
    if src.is_dir():
        return recursive_search('index.js', src)
    else:
        return src


def resolve_dest_path(src: Path, dest: Path) -> Path:
    # If dest is a dir, put proper filename
    if dest.is_dir():
        dest = dest.joinpath(f'{src.parent.name}.bundle.js')

    # Ensure parent dir exists
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True)

    return dest


import os


def get_npm_bin():
    return subprocess.check_output(shlex.split(config['commands']['bin']), encoding='utf-8').strip()


@click.command(short_help='Bundle everything into a single .js file, suitable for use in production.')
@click.option('--src', '--source',
              type=click.Path(exists=True),
              help='directory to look for "index.js", or path to file')
@click.option('--dest', '--destination',
              type=click.Path(),
              is_flag=True,
              help='destination directory, or filename')
@click.option('--html', is_flag=True, help='Generate boiler-plate html along-side the .js, for quick demo')
def deploy(source: str, destination: str, html: bool):
    """
    Bundle everything into a single .js file, suitable for use in production.

    By default, this shall -
    Look for "index.js" in current directory, and incrementally in sub-directories if nothing can be found.
    Browserify everything to ./build/<page>.bundle.js.
    """

    npm_bin = get_npm_bin()

    env = os.environ.copy()
    env['NODE_ENV'] = 'production'
    env['BABEL_ENV'] = 'production'

    for src_path, dest_path in resolve_paths(source, destination):
        if html:
            create_demo_html(dest_path)

        browserify = shlex.split(config['commands']['deploy']['browserify'].format(**{
            'bin': npm_bin,
            'source': src_path,
            'destination': dest_path,
        }))
        uglify = shlex.split(config['commands']['deploy']['uglify'].format(**{
            'bin': npm_bin,
            'source': src_path,
            'destination': dest_path,
        }))

        print(
            '{} {} ~> {}…'.format(
                white('Deploy:', bold=True),
                magenta(src_path),
                green(dest_path)
            )
        )

        with Halo(spinner=SPINNER) as halo:
            try:
                halo.stop()
                print(blue(browserify))
                halo.start()

                result = subprocess.run(
                    browserify,
                    cwd=Path.cwd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    env=env
                )

                if result.stderr:
                    halo.stop()
                    print(red(result.stderr))
                    halo.start()

                if result.returncode == 0:
                    halo.stop()
                    print(blue(uglify))
                    halo.start()

                    result = subprocess.run(
                        uglify,
                        input=result.stdout,
                        cwd=Path.cwd(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',
                        env=env
                    )

                    if result.stderr:
                        halo.stop()
                        print(red(result.stderr))
                        halo.start()

                    if result.returncode != 0:
                        halo.stop()
                        print(red('Failed!'))
                        return
                else:
                    halo.stop()
                    print(red('Failed!'))
                    return
            except FileNotFoundError as e:
                halo.stop()
                print(red(e))
                print(red("Are you sure you're at the right place?", bold=True))
                return
    else:
        print(cyan('done!'))


@click.command(short_help='Start the development environment')
@click.option('-s', '--src', '--source',
              type=click.Path(exists=True),
              help='directory to look for "index.js", or path to file')
@click.option('-d', '--dest', '--destination',
              type=click.Path(),
              help='destination directory, or filename')
@click.option('-D', '--disable-watch',
              is_flag=True,
              help='Disable file watcher / auto-reloader')
@click.option('--html', is_flag=True, help='Generate boiler-plate html along-side the .js, for quick demo')
def develop(source: str, destination: str, disable_watch: bool, html: bool):
    """
    Start the development environment,
    Bundles everything into a singe .js file

    By default, this shall-
    Look for "index.js" in current directory, and incrementally in sub-directories if nothing can be found.
    Watchify file, output-ing to./build/<page>.bundle.js.
    """

    env = os.environ.copy()
    env['NODE_ENV'] = 'development'
    env['BABEL_ENV'] = 'development'

    npm_bin = get_npm_bin()
    procs = []
    for src_path, dest_path in list(resolve_paths(source, destination)):
        if html:
            create_demo_html(dest_path)

        print(
            '{} {} ~> {}…'.format(
                white('Develop:', bold=True),
                magenta(src_path),
                green(dest_path)
            )
        )

        if disable_watch:
            browserify = shlex.split(config['commands']['develop']['browserify'].format(**{
                'bin': npm_bin,
                'source': src_path,
                'destination': dest_path,
            }))
            print(blue(browserify))

            with Halo(spinner=SPINNER):
                subprocess.run(browserify, env=env)
        else:
            watchify = shlex.split(config['commands']['develop']['watchify'].format(**{
                'bin': npm_bin,
                'source': str(src_path),
                'destination': str(dest_path),
            }))
            print(blue(watchify))

            procs.append(subprocess.run(watchify, env=env))
    if not disable_watch:
        for proc in procs:
            proc.wait()

        print(cyan('done!'))


cli.add_command(init)
cli.add_command(init_page)
cli.add_command(deploy)
cli.add_command(develop)

if __name__ == '__main__':
    cli()
