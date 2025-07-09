from django import template
import json

register = template.Library()

@register.filter(name='pretty_json')
def pretty_json(value):
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return value