from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
import pandas as pd
import io
from openpyxl.styles import Font, PatternFill, Alignment
from .models import VerifierProgramMap
from modules.program_manage.models import Program
from modules.core.decorators import admin_required
from django.contrib.auth import get_user_model
from modules.core.roles import VERIFIER_GROUP_NAME, is_verifier_user
from modules.reports.views import (
    _verification_base_courses,
    _apply_verification_filters,
    _build_verification_filter_options,
    _decorate_verification_report_courses,
    _verification_course_stats,
    _base_verifier_queryset,
)

User = get_user_model()

# ---------------------------------------------------------------------------------------------------
# Verification Program Map Management - Main Page
# ---------------------------------------------------------------------------------------------------

@admin_required
def verification_program_map_management(request):
    search_term = request.GET.get("search", "").strip()
    filters = {
        "year": request.GET.get("year", ""),
        "program": request.GET.get("program", "__all__"),
        "prog_type": request.GET.get("prog_type", "__all__"),
        "prog_category": request.GET.get("prog_category", "__all__"),
        "degree": request.GET.get("degree", "__all__"),
        "branch": request.GET.get("branch", "__all__"),
        "syllabus_status": request.GET.get("syllabus_status", "__all__"),
    }

    base_queryset = _verification_base_courses(request.user)
    filtered_queryset = _apply_verification_filters(
        base_queryset,
        {
            **filters,
            "sem": "__all__",
            "part": "__all__",
            "course_category": "__all__",
        "course_title": "__all__",
    },
    ).order_by("program__prog_code", "year", "sem", "course_code")
    if search_term:
        filtered_queryset = filtered_queryset.filter(
            Q(course_code__icontains=search_term)
            | Q(course_title__icontains=search_term)
            | Q(program__prog_code__icontains=search_term)
            | Q(program__degree__icontains=search_term)
            | Q(program__branch__icontains=search_term)
        ).distinct()

    course_list = list(_decorate_verification_report_courses(filtered_queryset))

    from django.core.paginator import Paginator
    paginator = Paginator(course_list, int(request.GET.get("per_page", 100)))
    page_obj = paginator.get_page(request.GET.get("page", 1))

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_params.pop("per_page", None)

    filter_options = _build_verification_filter_options(
        base_queryset,
        {
            **filters,
            "sem": "__all__",
            "part": "__all__",
            "course_category": "__all__",
            "course_title": "__all__",
        },
    )

    context = {
        "courses": page_obj,
        "records": page_obj,
        "page_obj": page_obj,
        "per_page": int(request.GET.get("per_page", 100)),
        "pagination_query": query_params.urlencode(),
        "has_applied_filters": True,
        "selected_year": filters["year"],
        "selected_program": filters["program"],
        "selected_prog_type": filters["prog_type"],
        "selected_prog_category": filters["prog_category"],
        "selected_degree": filters["degree"],
        "selected_branch": filters["branch"],
        "selected_syllabus_status": filters["syllabus_status"],
        "selected_search": request.GET.get("search", ""),
        "all_courses_for_search": filter_options["course_options"],
        "all_courses_list": filter_options["course_options"],
        "page_mode": "report",
        "page_title": "Verification Management",
        "page_subtitle": "Review verifier assignments and report status by program.",
        "compact_verification_filters": True,
        "verification_management_mode": True,
        "verifier_users": [
            {
                "id": verifier.id,
                "name": verifier.get_full_name() or verifier.username,
            }
            for verifier in _base_verifier_queryset()
        ],
        **filter_options,
        **_verification_course_stats(course_list),
    }
    return render(request, "verification_page.html", context)

# ---------------------------------------------------------------------------------------------------
# AJAX endpoints for Verification Program Map CRUD operations
# ---------------------------------------------------------------------------------------------------

@login_required
def get_mapping(request, mapping_id):
    try:
        mapping = get_object_or_404(VerifierProgramMap, id=mapping_id)
        verifier = mapping.user
        
        data = {
            'success': True,
            'mapping': {
                'id': mapping.id,
                'user_id': verifier.id,
                'user_name': verifier.username,
                'user_display': f"{verifier.username} ({verifier.email})",
                'program_ids': list(VerifierProgramMap.objects.filter(user=verifier).values_list('program_id', flat=True).distinct()),
                'program_name': str(mapping.program),
                'created_at': mapping.created_at.strftime('%Y-%m-%d %H:%M:%S') if mapping.created_at else '',
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def add_mapping(request):
    
    try:
        user_id = request.POST.get("user_id")
        program_ids = [program_id for program_id in request.POST.getlist("program_ids") if str(program_id).isdigit()]
        
        # Validate required fields
        if not user_id or not program_ids:
            return JsonResponse({'success': False, 'error': 'Verifier and at least one program are required fields.'})

        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Selected verifier with ID {user_id} does not exist.'})

        if not is_verifier_user(user):
            return JsonResponse({'success': False, 'error': 'Selected user is not a verifier.'})
        
        # Check if program exists
        programs = list(Program.objects.filter(id__in=program_ids, is_active=True))
        if len(programs) != len(set(program_ids)):
            return JsonResponse({'success': False, 'error': 'One or more selected programs do not exist or are inactive.'})

        created_count = 0
        with transaction.atomic():
            for program in programs:
                _, created = VerifierProgramMap.objects.get_or_create(user=user, program=program)
                created_count += int(created)

        if created_count == 0:
            return JsonResponse({'success': False, 'error': 'Selected verifier already has mappings for all chosen programs.'})

        return JsonResponse({
            'success': True,
            'message': f'Verifier-program mapping created successfully for {created_count} program(s).',
            'mapping_id': None,
            'created_count': created_count,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def edit_mapping(request, mapping_id):
    try:
        mapping = get_object_or_404(VerifierProgramMap, id=mapping_id)
        
        user_id = request.POST.get("user_id")
        program_ids = [program_id for program_id in request.POST.getlist("program_ids") if str(program_id).isdigit()]
        
        # Validate required fields
        if not user_id or not program_ids:
            return JsonResponse({'success': False, 'error': 'Verifier and at least one program are required fields.'})
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected verifier does not exist.'})

        if not is_verifier_user(user):
            return JsonResponse({'success': False, 'error': 'Selected user is not a verifier.'})
        
        # Check if program exists
        programs = list(Program.objects.filter(id__in=program_ids, is_active=True))
        if len(programs) != len(set(program_ids)):
            return JsonResponse({'success': False, 'error': 'Selected program does not exist or is inactive.'})

        with transaction.atomic():
            # Remove the current mapping row from the old combination so edits behave like a real replace.
            mapping.delete()

            existing_program_ids = set(
                VerifierProgramMap.objects.filter(user=user).values_list('program_id', flat=True)
            )
            created_count = 0
            for program in programs:
                if program.id in existing_program_ids:
                    continue
                VerifierProgramMap.objects.create(user=user, program=program)
                created_count += 1

        return JsonResponse({
            'success': True,
            'message': 'Mapping updated successfully.',
            'created_count': created_count,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def delete_mapping(request, mapping_id):
    
    try:
        mapping = get_object_or_404(VerifierProgramMap, id=mapping_id)
        mapping.delete()
        return JsonResponse({'success': True, 'message': 'Mapping deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------
# Helper endpoint to get verifiers (users with verifier role)
# ---------------------------------------------------------------------------------------------------

@login_required
def get_verifiers_list(request):
   
    try:
        verifiers = _get_verifier_users().values('id', 'username', 'first_name', 'last_name', 'email')
        verifier_list = []
        for verifier in verifiers:
            verifier_list.append({
                'id': verifier['id'],
                'username': verifier['username'],
                'name': f"{verifier['first_name']} {verifier['last_name']}".strip() or verifier['username'],
                'email': verifier['email']
            })
        return JsonResponse({'success': True, 'verifiers': verifier_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def _get_verifier_users():
    return User.objects.filter(groups__name=VERIFIER_GROUP_NAME).distinct().order_by('username')

# ---------------------------------------------------------------------------------------------------

@login_required
def get_programs_list(request):
   
    try:
        programs = Program.objects.filter(is_active=True).values('id', 'prog_code', 'branch', 'degree', 'prog_type')
        program_list = []
        for prog in programs:
            program_list.append({
                'id': prog['id'],
                'code': prog['prog_code'],
                'name': f"{prog['prog_code']} - {prog['branch']}",
                'branch': prog['branch'],
                'degree': prog['degree'],
                'type': prog['prog_type']
            })
        return JsonResponse({'success': True, 'programs': program_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------
# Excel Operations for Verification Program Map - Simplified
# ---------------------------------------------------------------------------------------------------

@login_required
def download_sample_mapping_excel(request):

    sample_data = {
        'verifier_username': ['john_doe', 'jane_smith'],
        'program_code': ['CS101', 'IT201']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Verifier Program Sample', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Verifier Program Sample.xlsx"'
    return response

# ---------------------------------------------------------------------------------------------------

@login_required
def download_mappings_excel(request):

    mappings = VerifierProgramMap.objects.select_related('user', 'program').all().order_by('user__username')
    
    # Prepare data for Excel - only username and program code
    mapping_data = []
    for mapping in mappings:
        mapping_data.append({
            'verifier_username': mapping.user.username,
            'program_code': mapping.program.prog_code,
        })
    
    df = pd.DataFrame(mapping_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Verifier Program Mappings', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Verifier Program Mappings.xlsx"'
    return response

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def upload_mappings_excel(request):
   
    try:
        if 'excel_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded.'})
        
        excel_file = request.FILES['excel_file']
        
        # Check file extension
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'error': 'Please upload an Excel file (.xlsx or .xls).'})
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Validate required columns
        required_columns = ['verifier_username', 'program_code']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing_columns)}. Your file has: {", ".join(df.columns)}'
            })
        
        # Track import results
        created_mappings = []
        errors = []
        
        for index, row in df.iterrows():
            username = str(row.get('verifier_username', '')).strip()
            program_code = str(row.get('program_code', '')).strip()
            
            # Skip if required fields are missing
            if not username or not program_code:
                errors.append(f'Row {index + 2}: Missing verifier username or program code')
                continue
            
            # Find user by username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                errors.append(f'Row {index + 2}: Verifier with username "{username}" not found')
                continue

            if not is_verifier_user(user):
                errors.append(f'Row {index + 2}: User "{username}" is not a verifier')
                continue
            
            # Find program by program code
            try:
                program = Program.objects.get(prog_code=program_code, is_active=True)
            except Program.DoesNotExist:
                errors.append(f'Row {index + 2}: Program with code "{program_code}" not found or inactive')
                continue
            
            # Check if mapping already exists
            if VerifierProgramMap.objects.filter(user=user, program=program).exists():
                errors.append(f'Row {index + 2}: Mapping already exists for {username} - {program_code}')
                continue
            
            try:
                mapping = VerifierProgramMap.objects.create(
                    user=user,
                    program=program
                )
                created_mappings.append(f'{username} -> {program_code}')
            except Exception as e:
                errors.append(f'Row {index + 2}: Error creating mapping - {str(e)}')
        
        # Prepare response message
        if created_mappings:
            message = f'Successfully created {len(created_mappings)} mappings.'
            if errors:
                message += f' {len(errors)} errors encountered.'
            return JsonResponse({
                'success': True,
                'message': message,
                'created': len(created_mappings),
                'errors': errors[:10]
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'No mappings were created. Errors: {", ".join(errors[:5])}'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
