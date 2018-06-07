import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from crayons import *
from halo import Halo

SPINNER = 'moon'


def _get_path_hash(location):
    hash = hashlib.sha256(str(location).encode()).digest()
    encoded_hash = base64.urlsafe_b64encode(hash).decode()
    return encoded_hash


CACHE_DIR = (
        Path.home() /
        '.react-pages' /
        _get_path_hash(Path(__file__)) /
        'nodejs'
)

PACKAGE_JSON = {
    "name": "",
    "version": "1.0.0",
    "description": "",
    "author": "",
    "license": "MIT",
}


def overwrite_cache_files():
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)

    shutil.copytree(Path(__file__).parent.joinpath('nodejs'), CACHE_DIR)

    return CACHE_DIR


def do_build_cache():
    print(white('Building cache…', bold=True))
    print(blue(f'Cache dir: {CACHE_DIR}'))

    overwrite_cache_files()

    print(white('Installing node modules…'))

    run_subproc(
        ['/usr/bin/env', 'npm', 'install'],
        cwd=CACHE_DIR,
        enable_spinner=True,
    )

    print(cyan('Done!'))


def clear_cahce():
    print(white('Clearing cache…', bold=True))
    print(blue(f'Cache dir: {CACHE_DIR}'))

    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR, ignore_errors=True)

    print(cyan('Done!'))


def handle_subproc_result(result, enable_spinner):
    if result is not None:
        if enable_spinner:
            if result.stdout:
                print(blue(result.stdout))

            if result.stderr:
                print(red(result.stderr))

        if result.returncode != 0:
            exit(red('Failed!'))


def print_truncated(cmd):
    strcmd = ' '.join(map(str, cmd))

    if len(strcmd) > 200:
        strcmd = strcmd[:200] + ' ...'

    print(yellow('Run: ' + strcmd))


def run_subproc(cmd, *, enable_spinner=False, **kwargs):
    kwargs.setdefault('cwd', Path.cwd())
    if enable_spinner:
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)

    print_truncated(cmd)

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
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'bin'],
                                        encoding='utf-8', cwd=cwd).strip())


def get_npm_root(cwd=Path.cwd()):
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'root'],
                                        encoding='utf-8', cwd=cwd).strip())


def get_npm_prefix(cwd=Path.cwd()):
    return Path(subprocess.check_output(['/usr/bin/env', 'npm', 'prefix'],
                                        encoding='utf-8', cwd=cwd).strip())


def resolve_paths(src: str, dest: str):
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

            yield (src_path,
                   resolve_dest_dir(src_path, dest),
                   CACHE_DIR / 'public')


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


def resolve_src_paths(src: str):
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


def copy_files_safe(src_dir: Path, names, dest_dir: Path):
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


def build(source: str, destination: str, no_watch: bool, verbose: bool,
          static_url: str, *, deploy=False):
    npm_root = get_npm_root()
    npm_prefix = get_npm_prefix()

    settings_list = []
    for src_path, dest_dir, public_dir in resolve_paths(source, destination):
        print(
            '{} {} ~> {}…'.format(
                white('Deploy:' if deploy else 'Develop:', bold=True),
                magenta(src_path, bold=True),
                green(dest_dir, bold=True)
            )
        )

        copy_files_safe(public_dir, ('favicon.ico', 'manifest.json'), dest_dir)

        if static_url is None:
            public_url = '.'
        else:
            public_url = static_url.format(**{
                'page name': src_path.parent.name,
            })

        settings_list.append({
            'spinner': SPINNER,
            'deploy': deploy,
            'watch': not no_watch,
            'verbose': verbose,
            'public url': public_url,
            'page name': str(green(src_path.parent.name, bold=True)),
            'src path': str(src_path),
            'dest dir': str(dest_dir),
            'html template': str(public_dir / 'index.html'),
            'package.json': str(npm_prefix / 'package.json'),
            'node_modules': str(npm_root),
            'npm prefix': str(npm_prefix),
            'react-pages node_modules': str(CACHE_DIR / 'node_modules'),
        })

    if len(settings_list):
        run_subproc(
            [
                '/usr/bin/env', 'node',
                CACHE_DIR / 'scripts' / 'react_pages.js',
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
