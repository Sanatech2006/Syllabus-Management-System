from django import template

from modules.core.roles import is_verifier_user


register = template.Library()


@register.simple_tag
def user_is_verifier(user):
    return is_verifier_user(user)
