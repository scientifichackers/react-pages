from django import template
from django.utils.html import format_html
register = template.Library()


@register.simple_tag(takes_context=True)
def current_time(context, ):
    pass