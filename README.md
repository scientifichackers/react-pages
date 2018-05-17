# React Pages
##### A zero-fuss way to create non single page apps with react.


- Zero Configuration required.
- Go from development to production with ease.
- Natively use react in django.

## QuickStart

- `react-pages project poll_react_pages` # create a project

- `cd poll_react_pages`

- `react-pages page vote` # create a page

- `react-pages develop` # start development environent

- `react-pages deploy` # deploy into production

## Django Integration

 React Pages allows you to access django template context variables inside react!


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

Now, you can just do

`python manage.py react_pages develop`

or, in production,

`python manage.py react_pages deploy`

That's it!

React Pages will pick-up the 'vote' page from 'poll_react_pages' project and do the nessecary work to make your react code available.


### Feel free to access the global variable `context` from your react jsx code.
###### Yeah, That's the the django template context!