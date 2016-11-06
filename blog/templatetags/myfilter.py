from django import template
register = template.Library()
def key(d, key_name):
        try:
                value = d[key_name]
        except KeyError:
                value = 0
        return value
key = register.filter('key', key)
