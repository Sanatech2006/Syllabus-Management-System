import openpyxl
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from openpyxl.styles import Font, PatternFill
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json, os
from .models import CourseStr, CourseContent
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from django.contrib import messages

def upload_center(request):
    courses = CourseStr.objects.all().order_by('-created_at')

    prog_code = request.GET.get("prog_code")
    year = request.GET.get("year")
    prog_type = request.GET.get("prog_type")
    sem = request.GET.get("sem")
    course_code = request.GET.get("course_code")
    category = request.GET.get("course_category")
    title = request.GET.get("course_title")

    filters_used = any([prog_code, year, prog_type, sem, course_code, category, title])

    # --- COURSE CODE IS PRIMARY UNIQUE FILTER ---
    if course_code:
        filtered = courses.filter(course_code__iexact=course_code.strip())

        if not filtered.exists():
            messages.error(request, "Please give the correct subject code.")
            courses = CourseStr.objects.none()
        else:
            courses = filtered
            messages.success(request, "Course filtered successfully.")

    # --- OTHER FILTERS ONLY IF NO COURSE CODE ---
    elif filters_used:
        if prog_code:
            courses = courses.filter(prog_code=prog_code)
        if year:
            courses = courses.filter(year=year)
        if prog_type:
            courses = courses.filter(prog_type=prog_type)
        if sem:
            courses = courses.filter(sem=sem)
        if category:
            courses = courses.filter(course_category=category)
        if title:
            courses = courses.filter(course_title__icontains=title)

        if not courses.exists():
            messages.warning(request, "No such course available.")
        else:
            messages.success(request, "Course filtered successfully.")

    finalized = request.session.get('courses_finalized', False)

    return render(request, 'upload_center.html', {
        'courses': courses,
        'finalized': finalized
    })

def upload_course_content(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        course_code = request.POST.get('course_code', '').strip()
        pdf_file = request.FILES['pdf_file']

        if not course_code:
            messages.error(request, 'Missing course code.')
            return redirect('upload_center')

        safe_code = course_code.replace(' ', '')
        course_content, created = CourseContent.objects.get_or_create(
            course_code=safe_code
        )
        course_content.pdf = pdf_file  # Assign file to FileField
        course_content.save()  # Save to database
        
        verb = "Created" if created else "Updated"
        messages.success(request, f'PDF {verb.lower()} for {safe_code}.')
        return redirect('upload_center')

    messages.error(request, 'No file uploaded.')
    return redirect('upload_center')

def delete_course(request, course_id):
    """Delete a CourseStr entry by id. Expects POST."""
    if request.method == 'POST':
        try:
            course = CourseStr.objects.get(id=course_id)
            course.delete()
            messages.success(request, 'Course deleted successfully.')
        except CourseStr.DoesNotExist:
            messages.error(request, 'Course not found.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('upload_center')
def add_course(request):
    if request.method == "POST":
        # Shared 4 fields
        prog_code = (request.POST.get("prog_code") or '').strip()
        year = (request.POST.get("year") or '').strip()
        prog_type = (request.POST.get("prog_type") or '').strip()
        sem = (request.POST.get("sem") or '').strip()

        # 9 course fields
        course_code = (request.POST.get("course_code") or '').strip()
        part = (request.POST.get("part") or '').strip()
        course_category = (request.POST.get("course_category") or '').strip()
        course_title = (request.POST.get("course_title") or '').strip()
        hrs_per_week = request.POST.get("hrs_per_week")
        credit = request.POST.get("credit")
        marks_cia = request.POST.get("marks_cia")
        marks_ese = request.POST.get("marks_ese")
        total_marks = request.POST.get("total_marks")

        # Save one Course record
        CourseStr.objects.create(
            prog_code=prog_code,
            year=year,
            prog_type=prog_type,
            sem=sem,
            course_code=course_code,
            part=part,
            course_category=course_category,
            course_title=course_title,
            hrs_per_week=hrs_per_week or 0,
            credit=credit or 0,
            marks_cia=marks_cia or 0,
            marks_ese=marks_ese or 0,
            total_marks=total_marks or 0,
        )

        # Check which button was clicked
        if "add_next" in request.POST:
            # Stay on same page, keep top fields
            context = {
                "prog_code": prog_code,
                "year": year,
                "prog_type": prog_type,
                "sem": sem,
            }
            return render(request, "add_course.html", context)
        else:
            # Save & confirm -> back to main Upload Center
            return redirect("upload_center")

    # GET: first time, empty form
    return render(request, "add_course.html")

def save_courses(request):
    if request.method == "POST":
        # Filter current batch (not all courses) - use session or form data
        CourseStr.objects.filter(is_saved=False).update(is_saved=True)  # Add filter!
        messages.success(request, "Courses saved successfully.")
    return redirect("upload_center")

def finalize_courses(request):
    if request.method == "POST":
        request.session['courses_finalized'] = True
        
        # Update ALL courses that are not yet finalized
        # This will include both saved and unsaved courses
        updated_count = CourseStr.objects.filter(is_finalized=False).update(is_finalized=True)
        
        if updated_count > 0:
            messages.success(request, f"{updated_count} courses have been finalized and are now visible in Course Management.")
        else:
            messages.info(request, "All courses are already finalized.")
            
    return redirect("course_management")


def download_template(request):
    """
    Download an Excel template with the required column headings
    for bulk course uploads.
    """
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Course Template"
    
    # Define the column headings
    headings = [
        'prog_code',
        'year',
        'prog_type',
        'sem',
        'course_code',
        'part',
        'course_category',
        'course_title',
        'hrs_per_week',
        'credit',
        'marks_cia',
        'marks_ese',
        'total_marks'
    ]
    
    # Add headings to the first row
    for col_num, heading in enumerate(headings, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = heading
        # Make the heading bold
        cell.font = Font(bold=True)
        # Add a light yellow background to headings
        cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    # Add a note row with instructions (optional)
    instruction_row = 2
    ws.cell(row=instruction_row, column=1, value="INSTRUCTIONS:")
    ws.cell(row=instruction_row, column=2, value="Fill in your data below. Delete this row before uploading.")
    # Merge cells for instruction
    ws.merge_cells(start_row=instruction_row, start_column=1, end_row=instruction_row, end_column=13)
    
    # Add sample data starting from row 4
    sample_row = 4
    
    # Sample 1
    sample_data_1 = [
        'CS101',           # prog_code
        '2024-2025',       # year
        'UG',              # prog_type
        'I',               # sem
        'CS101',           # course_code
        'I',               # part
        'Core',            # course_category
        'Introduction to Computer Science',  # course_title
        '4',               # hrs_per_week
        '4',               # credit
        '25',              # marks_cia
        '75',              # marks_ese
        '100'              # total_marks
    ]
    
    for col_num, value in enumerate(sample_data_1, 1):
        ws.cell(row=sample_row, column=col_num, value=value)
    
    # Sample 2
    sample_data_2 = [
        'MAT201',          # prog_code
        '2024-2025',       # year
        'UG',              # prog_type
        'III',             # sem
        'MAT201',          # course_code
        'II',              # part
        'Allied',          # course_category
        'Calculus and Linear Algebra',  # course_title
        '5',               # hrs_per_week
        '4',               # credit
        '25',              # marks_cia
        '75',              # marks_ese
        '100'              # total_marks
    ]
    
    for col_num, value in enumerate(sample_data_2, 1):
        ws.cell(row=sample_row + 1, column=col_num, value=value)
    
    # Add data validation for better user experience
    # Year validation dropdown
    year_validation = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"2023-2024,2024-2025,2025-2026"',
        allow_blank=True
    )
    ws.add_data_validation(year_validation)
    year_validation.add(f"B5:B1048576")  # Apply from row 5 onwards
    
    # Programme Type validation
    prog_type_validation = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"UG,PG"',
        allow_blank=True
    )
    ws.add_data_validation(prog_type_validation)
    prog_type_validation.add(f"C5:C1048576")
    
    # Semester validation
    sem_validation = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"I,II,III,IV,V,VI"',
        allow_blank=True
    )
    ws.add_data_validation(sem_validation)
    sem_validation.add(f"D5:D1048576")
    
    # Part validation
    part_validation = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"I,II,III"',
        allow_blank=True
    )
    ws.add_data_validation(part_validation)
    part_validation.add(f"F5:F1048576")
    
    # Course Category validation
    category_validation = openpyxl.worksheet.datavalidation.DataValidation(
        type="list",
        formula1='"Core,Elective,Allied,Skill Enhancement"',
        allow_blank=True
    )
    ws.add_data_validation(category_validation)
    category_validation.add(f"G5:G1048576")
    
    # Adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 40)  # Cap at 40 characters for better visibility
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Freeze the header row
    ws.freeze_panes = 'A5'  # Freeze after the instruction row
    
    # Create the HTTP response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="course_upload_template.xlsx"'
    
    # Save the workbook to the response
    wb.save(response)
    
    return response