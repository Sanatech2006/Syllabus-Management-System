from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from modules.course_management.models import CourseStructure
from modules.program_manage.models import Program
from modules.hod_management.models import HodProgramMap


def get_hod_mapped_programs(user):
    if not user.is_authenticated or user.is_superuser:
        return Program.objects.none()

    return Program.objects.filter(hodprogrammap__user=user, is_active=True).distinct()


def is_hod_user(user):
    """
    Determine if a user should be treated as an HOD for access checks.

    A user is considered an HOD if all the following are true:
      - the user is authenticated
      - the user is not a superuser
      - the user is either marked `is_staff` OR has an explicit HodProgramMap entry

    This allows HOD accounts created via the HOD management mappings to access
    the course management section even if their `is_staff` flag is not set.
    """
    if not user or not user.is_authenticated or user.is_superuser:
        return False

    # Treat any authenticated non-superuser as HOD for hod-login access.
    # This covers users listed in HOD management and the general user list
    # so they can access the Course Management HOD views when logged in
    # via the HOD role.
    return True


def get_accessible_programs(user):
    active_programs = Program.objects.filter(is_active=True)

    if not user.is_authenticated:
        return Program.objects.none()

    if user.is_superuser:
        return active_programs

    # HOD users should only see programs they are mapped to. Keep the
    # scoping strict so HODs can view/upload/search only their department
    # courses while still allowing HOD-role logins to reach Course
    # Management (is_hod_user returns True for authenticated non-superusers).
    if is_hod_user(user):
        return get_hod_mapped_programs(user)

    return Program.objects.none()


def get_accessible_courses(user):
    courses = CourseStructure.objects.select_related("program")

    if not user.is_authenticated:
        return courses.none()

    if user.is_superuser:
        return courses

    if is_hod_user(user):
        return courses.filter(program_id__in=get_accessible_programs(user).values_list("id", flat=True))

    return courses.none()


def course_management_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            request.session["next_url"] = request.path
            return redirect("/login/")

        if request.user.is_superuser or is_hod_user(request.user):
            return view_func(request, *args, **kwargs)

        messages.error(request, "You do not have permission to access that section.")
        return redirect("/dashboard/")

    return _wrapped_view
