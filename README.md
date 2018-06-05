# React Pages
##### A zero-fuss way to create non single page apps with react.

- Zero Configuration required. Mostly thanks to [create-react-app](https://github.com/facebook/create-react-app).
- [Custom react scripts](https://github.com/kitze/custom-react-scripts) inbuilt.
- Cross-page import (create-react-app [doesn't allow this](https://github.com/facebook/create-react-app/issues/834)).
- Ready-to-serve production builds with the proper paths. (using `--static-url` option)
- Natively use react in django.
- Go from development to production with ease.
- Caches npm stuff. You'll notice that the command `react-pages project` runs much after the 1st time.

## Terminology

#### Project
The project contains the node.js modules necessary to use react and the pages you create.

```
└── my_project
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
└── my_page
    ├── App.css
    ├── App.js
    ├── App.test.js
    ├── index.css
    ├── index.js
    ├── logo.svg
    └── registerServiceWorker.js
```

## QuickStart

You need npm on your machine!

[![PyPI version (tag)](https://img.shields.io/badge/pip-0.1.5-blue.svg?longCache=true&style=for-the-badge)](https://pypi.org/project/react-pages/)

`pip install react-pages`

*Commands :*

```sh
$ react-pages project my_project # create a project

$ cd my_project # Don't forget to do this!

$ react-pages page my_page # create a page

$ react-pages develop # development

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
{% render_react_page 'my_page' %}
...
```

### Remember to use `react-pages runserver` instead of `manage.py runserver`!
(This was done to remove the manual build step).

That's it!<br>
React Pages will pick-up the "my_page" page from "my_project"
 project and do the necessary work to transpire react JSX.

#### Django Context

You can pass django template context varialbes like so -

__views.py__
`context['py_numbers'] = [1, 2, 3]`

__template.html__
`{% render_react_page 'my_page' js_numbers=py_numbers %}`

Then access these anywhere in JS
`console.log(js_numbers);`

*Note: These must be JSON serialize-able*

For production, just put `DEBUG=False` in `settings.py` and relax.

## Existing projects

React Pages will automatically patch itsef into any existing project,
that was created using `create-react-app`.

Just run `react-pages project .` from your project directory!

Projects not using `create-react-app` will probably work,
 but no guarantees can be made.

## Issues

- It might not uninstall using pip.

  This is a side-effect of react-page's caching.<br>
  As a temporary fix, Run `react-pages clear-cache`,
  and then `pip uninstall react-pages` will work as expected.