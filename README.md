# React Pages
##### A zero-fuss way to create non single page apps with react.

- Zero Configuration required.
- Go from development to production with ease.

## Features
- [custom react scripts](https://github.com/kitze/custom-react-scripts)
- Imports from other pages (create-react-app doesn't allow that)
- Natively use react in django.
- Ready-to-serve production builds with the proper paths. (using `--static-url` option)

## Terminology

#### Project
The project contains the node.js modules necessary to use react and the pages you create.

```
└── project
    ├── package.json
    ├── package-lock.json
    ├── .env
    ├── .gitignore
    ├── public
    │   ├── favicon.ico
    │   ├── index.html
    │   └── manifest.json
    <pages>
```

#### Page:

A page is a directory containing at least an `index.js` file, (and other css/js files specific to your application.)

```
└── page
    ├── App.css
    ├── App.js
    ├── App.test.js
    ├── index.css
    ├── index.js
    ├── logo.svg
    └── registerServiceWorker.js
```

## QuickStart

[![PyPI version (tag)](https://img.shields.io/badge/pip-0.3.7-blue.svg?longCache=true&style=for-the-badge)](https://pypi.org/project/react-pages/)

`pip install react-pages`

*Commands :*

```sh
$ react-pages project poll_react_pages # create a project

$ cd poll_react_pages

$ react-pages page vote # create a page

$ react-pages react_pages # development

$ react-pages deploy # production

$ react-pages runserver # django runserver alternative
```

## Django Integration

__settings.py__
```
INSTALLED_APPS = [
    ...
    'react_pages',
    ...
]

# React Pages
REACT_PAGES_PROJECT_DIR = os.path.join(BASE_DIR, 'my_project')  # specify the react-pages project

STATICFILES_DIRS = [
    ...
    os.path.join(REACT_PAGES_PROJECT_DIR, 'build')  # mark the build dir as static file dir
    ...
]
```

__template.html__
```
{% load react_pages %}
...
{% render_react_page 'vote' %}
...
```

**Remeber to use `react-pages runserver` instead of `manage.py runserver`!**

That's it!
React Pages will pick-up the "vote" page from "poll_react_pages" project and do the necessary work to transpire react JSX.

##### Django Context

You can pass django template context varialbes like so -

__views.py__
`context['foo'] = [1, 2, 3]`

__template.html__
`{% render_react_page 'vote' foo=foo %}`

Then access these anywhere in react code
`console.log(foo);`

*Note: These must be JSON serialize-able*

For production, just put `DEBUG=False` in `settings.py` and relax.

## Existing projects

React Pages will automatically patch itsef into any existing project,
that was created using `create-react-app`.

Just run `react-pages project .` from your project directory!

Projects not using `create-react-app` will probably work, but no guarantees can be made.

## Issues

- It might not uninstall using pip. As a temporary fix, Run `react-pages uninstall` once, and then `pip uninstall react-pages` will work.