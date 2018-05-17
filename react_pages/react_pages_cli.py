import shlex
import shutil
import subprocess
from pathlib import Path

import click
import toml
from crayons import *
from halo import Halo

# paths
FILE = Path(__file__)
ROOT = FILE.parent.parent
PROJECT = ROOT.joinpath('boilerplate', 'project')
PAGE = ROOT.joinpath('boilerplate', 'page')

# beauty stuff
SPINNER = 'moon'

try:
    config = toml.load(str(Path.cwd().joinpath('react_pages.toml')))
except FileNotFoundError:
    config = toml.load(str(Path(__file__).parent.joinpath('react_pages.toml')))


@click.group()
def cli():
    pass


@click.command('project',
               short_help='Create a new project, inside a new directory')
@click.argument('project-name', type=click.Path())
def init(project_name):
    project_dir = Path.cwd().joinpath(project_name)
    print(
        '{} {}…'.format(
            white('Creating new project', bold=True),
            green(project_name, bold=True),
        )
    )

    try:
        shutil.copytree(PROJECT, project_dir)
    except FileExistsError:
        print(red('Error: Directory already exists!'))
    else:
        shutil.copy(FILE.parent.joinpath('react_pages.toml'), project_dir)

        print(blue(f'Copied project boilerplate to {project_dir}'))

        print(white('Installing node dependencies…'))
        with Halo(spinner=SPINNER):
            result = subprocess.run(
                ['npm', 'i'],
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


@click.command('page',
               short_help='Create a new page, inside a new directory, containing boiler-plate for react')
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
                magenta(f'react-pages deploy', bold=True),
                magenta('to use this page')
            )
        )


@click.command('deploy',
               short_help='Bundle everything into a single .js file, suitable for use in production.')
@click.option('--input', '-i',
              type=click.Path(exists=True),
              help='directory to find "page.js", or path to file')
@click.option('--output', '-o',
              type=click.Path(),
              help='output directory, or output filename')
def deploy(input, output):
    """
    Bundle everything into a single .js file, suitable for use in production.

    By default,
    - look for "page.js" in current directory, recursively.
    - Browserify everything to ./build/<page>.bundle.js.
    """
    if input is None:
        input_path = Path().cwd()
    else:
        input_path = Path(input)

    if input_path.is_dir():
        input_paths = [Path(i) for i in input_path.rglob('page.js')]
    else:
        input_paths = [Path(input)]

    for input_path in input_paths:
        if output is None:
            output_path = Path.cwd().joinpath('build/')
        else:
            output_path = Path(output)

        if not output_path.exists():
            output_path.mkdir(parents=True)

        if output_path.is_dir():
            output_path = output_path.joinpath(f'{input_path.parent.name}.bundle.js')

        npm_bin = subprocess.check_output(shlex.split(config['commands']['bin']), encoding='utf-8').strip()

        browserify = shlex.split(config['commands']['browserify'].format(**{
            'bin': npm_bin,
            'input': str(input_path),
            'output': str(output_path),
        }))

        uglify = shlex.split(config['commands']['uglify'].format(**{
            'bin': npm_bin,
            'input': str(input_path),
            'output': str(output_path),
        }))

        print(
            '{} {} ~> {}…'.format(
                white('Deploy', bold=True),
                magenta(input_path),
                green(output_path)
            )
        )
        with Halo(spinner=SPINNER) as halo:
            try:
                result = subprocess.run(
                    browserify,
                    cwd=Path.cwd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8'
                )

                if result.stderr:
                    print(red(result.stderr))

                if result.returncode == 0:
                    result = subprocess.run(
                        uglify,
                        input=result.stdout,
                        cwd=Path.cwd(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8'
                    )

                    if result.stderr:
                        print(red(result.stderr))

                    if result.returncode == 0:
                        with open(output_path, 'w') as fp:
                            fp.write(result.stdout)
                    else:
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


def develop(input, output):
    pass


cli.add_command(init)
cli.add_command(init_page)
cli.add_command(deploy)
if __name__ == '__main__':
    cli()
