from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupérer un élément d'un dictionnaire"""
    return dictionary.get(key, [])
