import openpyxl
import pandas as pd
import io
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from modules.core.utils import set_upload_progress, delete_upload_progress


from modules.core.decorators import admin_required
from .models import Program


PROGRAM_FILTER_FIELDS = (
    "prog_type",
    "prog_category",
    "degree",
    "branch",
    "prog_code",
)

PROGRAM_BULK_REQUIRED_COLUMNS = (
    "prog_type",
    "prog_category",
    "degree",
    "branch",
    "prog_code",
)


def _distinct_non_empty(queryset, field_name):
    return list(
        queryset.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{field_name: ""})
        .values_list(field_name, flat=True)
        .distinct()
        .order_by(field_name)
    )


def _apply_program_filters(queryset, filters, exclude_field=None):
    for field in PROGRAM_FILTER_FIELDS:
        if field == exclude_field:
            continue
        value = filters.get(field)
        if value:
            queryset = queryset.filter(**{field: value})
    return queryset


def _build_program_filter_options(base_queryset, filters):
    option_querysets = {
        field: _apply_program_filters(base_queryset, filters, exclude_field=field)
        for field in PROGRAM_FILTER_FIELDS
    }
    return {
        "prog_types": _distinct_non_empty(option_querysets["prog_type"], "prog_type"),
        "prog_categories": _distinct_non_empty(option_querysets["prog_category"], "prog_category"),
        "degrees": _distinct_non_empty(option_querysets["degree"], "degree"),
        "branches": _distinct_non_empty(option_querysets["branch"], "branch"),
        "prog_codes": _distinct_non_empty(option_querysets["prog_code"], "prog_code"),
    }


@admin_required
def program_management(request):
    
    # Get pagination and per page parameters
    per_page = int(request.GET.get('per_page', 10))
    page = request.GET.get('page', 1)
    
    # Apply filters
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    base_queryset = Program.objects.filter(is_active=True)
    programs = _apply_program_filters(base_queryset, filters)
    
    # Get filter options for dropdowns
    filter_options = _build_program_filter_options(base_queryset, filters)
    
    # Pagination
    paginator = Paginator(programs.order_by('prog_code'), per_page)
    page_obj = paginator.get_page(page)
    
    # Preserve query parameters for pagination
    query_params = request.GET.copy()
    query_params.pop('page', None)
    
    # Calculate stats
    stats = {
        'ug_count': base_queryset.filter(prog_type="UG").count(),
        'pg_count': base_queryset.filter(prog_type="PG").count(),
        'arts_count': base_queryset.filter(prog_category="Arts").count(),
        'science_count': base_queryset.filter(prog_category="Science").count(),
    }
    
    context = {
        "programs": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "pagination_query": query_params.urlencode(),
        **filter_options,
        **stats,
    }
    return render(request, "program_management.html", context)


@admin_required
def get_filter_options(request):
    filters = {field: request.GET.get(field) for field in PROGRAM_FILTER_FIELDS}
    queryset = Program.objects.filter(is_active=True)
    return JsonResponse(_build_program_filter_options(queryset, filters))

@admin_required
def get_program(request, program_id):
    try:
        program = get_object_or_404(Program, id=program_id)
        
        data = {
            'success': True,
            'program': {
                'id': program.id,
                'prog_code': program.prog_code,
                'degree': program.degree,
                'branch': program.branch,
                'prog_type': program.prog_type,
                'prog_category': program.prog_category,
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
@require_http_methods(["POST"])
def add_program(request):

    try:
        prog_code = request.POST.get("prog_code", "").strip().upper().replace(" ", "")
        degree = request.POST.get("degree", "").strip()
        branch = request.POST.get("branch", "").strip()
        prog_type = request.POST.get("prog_type", "").strip()
        prog_category = request.POST.get("prog_category", "").strip()
        
        # Validate required fields
        if not all([prog_code, degree, branch, prog_type, prog_category]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})
        
        # Validate program type
        if prog_type not in ["UG", "PG"]:
            return JsonResponse({'success': False, 'error': 'Program type must be UG or PG.'})
        
        # Validate program category
        if prog_category not in ["Arts", "Science"]:
            return JsonResponse({'success': False, 'error': 'Program category must be Arts or Science.'})
        
        # Check if program code exists
        if Program.objects.filter(prog_code=prog_code).exists():
            return JsonResponse({'success': False, 'error': f'Program code "{prog_code}" already exists.'})
        
        # Create program
        program = Program.objects.create(
            prog_code=prog_code,
            degree=degree,
            branch=branch,
            prog_type=prog_type,
            prog_category=prog_category,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Program created successfully.',
            'program_id': program.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
@require_http_methods(["POST"])
def edit_program(request, program_id):

    try:
        program = get_object_or_404(Program, id=program_id)
        prog_code = request.POST.get("prog_code", "").strip().upper().replace(" ", "")
        degree = request.POST.get("degree", "").strip()
        branch = request.POST.get("branch", "").strip()
        prog_type = request.POST.get("prog_type", "").strip()
        prog_category = request.POST.get("prog_category", "").strip()
        
        # Validate required fields
        if not all([prog_code, degree, branch, prog_type, prog_category]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})
        
        # Validate program type
        if prog_type not in ["UG", "PG"]:
            return JsonResponse({'success': False, 'error': 'Program type must be UG or PG.'})
        
        # Validate program category
        if prog_category not in ["Arts", "Science"]:
            return JsonResponse({'success': False, 'error': 'Program category must be Arts or Science.'})
        
        # Check if program code exists for other programs
        if Program.objects.exclude(id=program_id).filter(prog_code=prog_code).exists():
            return JsonResponse({'success': False, 'error': f'Program code "{prog_code}" already exists.'})
        
        # Update program
        program.prog_code = prog_code
        program.degree = degree
        program.branch = branch
        program.prog_type = prog_type
        program.prog_category = prog_category
        program.save()
        
        return JsonResponse({'success': True, 'message': 'Program updated successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
@require_http_methods(["POST"])
def delete_program(request, program_id):
    try:
        program = get_object_or_404(Program, id=program_id)
        program.delete()
        return JsonResponse({'success': True, 'message': 'Program deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
def download_sample_excel(request):

    sample_data = {
        'prog_type': ['UG', 'PG', 'UG'],
        'prog_category': ['Science', 'Arts', 'Science'],
        'degree': ['B.Sc', 'M.A', 'B.Com'],
        'branch': ['Computer Science', 'English', 'Commerce'],
        'prog_code': ['BSC-CS', 'MA-ENG', 'BCOM']
    }
    
    df = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Programs', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Program Sample.xlsx"'
    return response


@admin_required
def download_programs_excel(request):

    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    
    program_data = []
    for program in programs:
        program_data.append({
            'Program Type': program.get_prog_type_display(),
            'Program Category': program.get_prog_category_display(),
            'Degree': program.degree,
            'Branch': program.branch,
            'Program Code': program.prog_code,
        })
    
    df = pd.DataFrame(program_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Programs', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Programs List.xlsx"'
    return response


@admin_required
@require_http_methods(["POST"])
def upload_programs_excel(request):
    upload_id = request.POST.get('upload_id') or request.GET.get('upload_id')
    try:
        if 'excel_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded.'})
        
        excel_file = request.FILES['excel_file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'})
        
        df = pd.read_excel(excel_file)
        
        required_columns = ['prog_type', 'prog_category', 'degree', 'branch', 'prog_code']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            })
        
        created_programs = []
        errors = []
        
        total_rows = len(df)
        if upload_id:
            set_upload_progress(upload_id, 0, total_rows, status="processing")
        
        for index, row in df.iterrows():
            current_row = index + 1
            if upload_id:
                set_upload_progress(upload_id, current_row, total_rows, status="processing")
            
            prog_type = str(row.get('prog_type', '')).strip().upper()
            prog_category = str(row.get('prog_category', '')).strip().title()
            degree = str(row.get('degree', '')).strip()
            branch = str(row.get('branch', '')).strip()
            prog_code = str(row.get('prog_code', '')).strip().upper().replace(" ", "")
            
            # Validate required fields
            if not all([prog_type, prog_category, degree, branch, prog_code]):
                errors.append(f'Row {index + 2}: All fields are required')
                continue
            
            # Validate program type
            if prog_type not in ["UG", "PG"]:
                errors.append(f'Row {index + 2}: Invalid program type "{prog_type}". Must be UG or PG')
                continue
            
            # Validate program category
            if prog_category not in ["Arts", "Science"]:
                errors.append(f'Row {index + 2}: Invalid program category "{prog_category}". Must be Arts or Science')
                continue
            
            # Check if program exists
            if Program.objects.filter(prog_code=prog_code).exists():
                errors.append(f'Row {index + 2}: Program code "{prog_code}" already exists')
                continue
            
            try:
                Program.objects.create(
                    prog_code=prog_code,
                    degree=degree,
                    branch=branch,
                    prog_type=prog_type,
                    prog_category=prog_category,
                    is_active=True
                )
                created_programs.append(prog_code)
            except Exception as e:
                errors.append(f'Row {index + 2}: Error - {str(e)}')
        
        if upload_id:
            set_upload_progress(upload_id, total_rows, total_rows, status="completed")
            
        if created_programs:
            message = f'Successfully imported {len(created_programs)} programs.'
            if errors:
                message += f' {len(errors)} errors encountered.'
            return JsonResponse({'success': True, 'message': message, 'created': len(created_programs), 'errors': errors[:10]})
        else:
            return JsonResponse({'success': False, 'error': f'No programs imported. Errors: {", ".join(errors[:5])}'})
        
    except Exception as e:
        if upload_id:
            set_upload_progress(upload_id, 0, 0, status="failed")
        return JsonResponse({'success': False, 'error': str(e)})