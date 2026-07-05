from django import template

from modules.core.roles import is_verifier_user
from modules.course_management.access import is_hod_user


register = template.Library()


@register.simple_tag
def user_is_verifier(user):
    return is_verifier_user(user)


@register.simple_tag
def user_is_hod(user):
    return is_hod_user(user)
