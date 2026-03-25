from django.shortcuts import render
from modules.upload_center.models import CourseStr, CourseContent

def work_progress_report(request):
    courses = CourseStr.objects.all()
    contents = CourseContent.objects.all()

    content_map = {c.course_code: c for c in contents}

    total = courses.count()
    uploaded = 0

    for course in courses:
        content = content_map.get(course.course_code)
        if content and content.pdf:
            uploaded += 1

    percentage = int((uploaded / total) * 100) if total > 0 else 0

    context = {
        "courses": courses,
        "content_map": content_map,
        "total": total,
        "uploaded": uploaded,
        "percentage": percentage,
    }

    return render(request, "reports.html", context)