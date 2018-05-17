# React Pages
##### A zero-fuss way to create non single page apps with react.


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


###### settings.py
```
INSTALLED_APPS = [
    ...
    'react_pages_django',
    ...
]

# Assuming your React Pages project is at BASE_DIR,
REACT_PAGES_PROJECT_DIR = os.path.join(BASE_DIR, 'poll_react_pages')
```

###### templates
```
{% load react_pages %}
...
{% render_react_page 'vote' %}
...
```

That's it!
React Pages will pick-up the "vote" page from "poll_react_pages" project and do the nessecary work to transpile react code.

#### BTW, Feel free to access the global variable `context` from your react jsx code.
##### (That'll be the the django template context!)

For production, just put `DEBUG=False` in `settings.py` and relax.

