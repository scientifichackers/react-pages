import shutil
import subprocess
from pathlib import Path

import click
from crayons import *
from halo import Halo

# paths
ROOT = Path(__file__).parent
PROJECT = ROOT.joinpath('boilerplate', 'project')
PAGE = ROOT.joinpath('boilerplate', 'page')

# beauty stuff
SPINNER = 'moon'


@click.group()
def cli():
    pass


@click.command('project', short_help='create a new project, inside a new directory')
@click.argument('project-name', type=click.Path(exists=False))
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
        print(red('Directory already exists!'))
    else:
        print(blue(f'Copied project boilerplate to {project_dir}'))

        print(white('Installing npm dependencies…'))
        with Halo(spinner=SPINNER):
            proc_result = subprocess.run(['npm', 'i'], cwd=project_dir, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, encoding='utf-8')

        if proc_result.stdout:
            print(blue(proc_result.stdout))
        if proc_result.stderr:
            print(red(proc_result.stderr))

        if proc_result.returncode == 0:
            print(cyan('Successfully created project ', bold=True) + green(project_name, bold=True), '!')
        else:
            print(red('Failed!'))


@click.command('page',
               short_help='init a new page, inside a new directory, containing boiler-plate for react')
@click.argument('page-name', type=click.Path(exists=False))
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
        print(red('Directory already exists!'))
    else:
        print(blue(f'Copied page boilerplate to {page_dir}'))
        print(
            '{} {} {}'.format(
                magenta('Run'),
                magenta(f'react-pages deploy {page_dir.name}', bold=True),
                magenta('to use this page')
            )
        )


@click.command('deploy', short_help='bundle everything into a single .js file, suitable for use in production')
@click.option('--input', '-i',
              type=click.Path(exists=True),
              help='directory containing `index.jsx`, or path to `index.jsx`')
@click.option('--output', '-o',
              type=click.Path(exists=True),
              help='output directory, or output filename')
def deploy(input, output):
    if input is None:
        pass


def develop(input, output):
    pass


cli.add_command(init)
cli.add_command(init_page)
cli.add_command(deploy)
if __name__ == '__main__':
    cli()
