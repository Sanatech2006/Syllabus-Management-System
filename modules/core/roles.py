VERIFIER_GROUP_NAME = "Verifier"

ROLE_ADMIN = "admin"
ROLE_HOD = "hod"
ROLE_VERIFIER = "verifier"
ROLE_USER = "user"

VALID_USER_ROLES = {ROLE_ADMIN, ROLE_HOD, ROLE_VERIFIER, ROLE_USER}


def is_verifier_user(user):
    if not user or not user.is_authenticated:
        return False

    return user.groups.filter(name=VERIFIER_GROUP_NAME).exists()


def get_user_role(user):
    if user.is_superuser:
        return ROLE_ADMIN
    if user.is_staff or _has_hod_program_mapping(user):
        return ROLE_HOD
    if is_verifier_user(user):
        return ROLE_VERIFIER
    return ROLE_USER


def _has_hod_program_mapping(user):
    if not user or not user.pk:
        return False

    from django.apps import apps

    HodProgramMap = apps.get_model("hod_management", "HodProgramMap")
    return HodProgramMap.objects.filter(user=user).exists()


def get_user_role_label(user):
    role = get_user_role(user)
    return {
        ROLE_ADMIN: "Administrator",
        ROLE_HOD: "Head of Department",
        ROLE_VERIFIER: "Verifier",
        ROLE_USER: "User",
    }.get(role, "User")


def get_user_role_labels(user):
    labels = [get_user_role_label(user)]
    if get_user_role(user) == ROLE_HOD and is_verifier_user(user):
        labels.append("Verifier")
    return labels


def set_user_role(user, role, additional_roles=None):
    from django.contrib.auth.models import Group

    normalized_role = role if role in VALID_USER_ROLES else ROLE_USER
    normalized_additional_roles = {
        additional_role for additional_role in (additional_roles or []) if additional_role in VALID_USER_ROLES
    }

    user.is_superuser = normalized_role == ROLE_ADMIN
    user.is_staff = normalized_role in {ROLE_ADMIN, ROLE_HOD}

    user.save()

    verifier_group, _ = Group.objects.get_or_create(name=VERIFIER_GROUP_NAME)
    user.groups.remove(verifier_group)
    if normalized_role == ROLE_VERIFIER or ROLE_VERIFIER in normalized_additional_roles:
        user.groups.add(verifier_group)

    return user
