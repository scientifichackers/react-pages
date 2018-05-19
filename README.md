# React Pages
##### TLDR; A wrapper over common react utilities, giving you a package that just works.
#### DOES NOT WORK RIGHT NOW.

- Zero Configuration required.
- Go from development to production with ease.
- Natively use react in django.

## QuickStart

```sh
$ react-pages project poll_react_pages # create a project

$ cd poll_react_pages

$ react-pages page vote # create a page

$ react-pages develop # development

$ react-pages deploy # production
```

## Django Integration

__settings.py__
```
INSTALLED_APPS = [
    ...
    'react_pages_django',
    ...
]

# Assuming your React Pages project is at BASE_DIR,
REACT_PAGES_PROJECT_DIR = os.path.join(BASE_DIR, 'poll_react_pages')
```

__template.html__
```
{% load react_pages %}
...
{% render_react_page 'vote' %}
...
```

That's it!
React Pages will pick-up the "vote" page from "poll_react_pages" project and do the nessecary work to transpile react code.

###### Django Context

You can pass django template context varialbes like so -

__views.py__
`context['foo'] = [1, 2, 3]`

__template.html__
`{% render_react_page 'vote' foo=foo %}`

Then access these anywhere in react code
`console.log(foo);`

*Note: These must be JSON serialize-able*

For production, just put `DEBUG=False` in `settings.py` and relax.

