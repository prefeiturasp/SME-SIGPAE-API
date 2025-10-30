from django import template
from django.utils.safestring import mark_safe

register = template.Library()

register.filter("safe_content", mark_safe)
