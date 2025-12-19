# core/jinja2.py
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

def environment(**options):
    env = Environment(**options)
    # Esto permite usar {% static %} y {% url %} en tus HTMLs
    env.globals.update({
        'static': static,
        'url': reverse,
    })
    return env