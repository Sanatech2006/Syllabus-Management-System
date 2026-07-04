from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pandas as pd
import io
from openpyxl.styles import Font, PatternFill, Alignment
from .models import HodProgramMap
from modules.program_manage.models import Program
from django.contrib.auth import get_user_model

User = get_user_model()

# ---------------------------------------------------------------------------------------------------
# HOD Program Map Management - Main Page
# ---------------------------------------------------------------------------------------------------

@login_required
def hod_program_map_management(request):
    
    mappings = HodProgramMap.objects.select_related('user', 'program').all().order_by('-created_at')
    
    # HODs are represented by staff users who are not superusers.
    hods = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    
    # Print for debugging (check your console)
    print(f"Found {hods.count()} HODs")
    for hod in hods:
        print(f"HOD: ID={hod.id}, Username={hod.username}, Email={hod.email}")
    
    # Get all active programs
    programs = Program.objects.filter(is_active=True).order_by('prog_code')
    
    print(f"Found {programs.count()} programs")
    for prog in programs:
        print(f"Program: ID={prog.id}, Code={prog.prog_code}, Name={prog.branch}")
    
    context = {
        "mappings": mappings,
        "total_mappings": mappings.count(),
        "hods": hods,
        "programs": programs,
    }
    return render(request, "hod_management.html", context)

# ---------------------------------------------------------------------------------------------------
# AJAX endpoints for HOD Program Map CRUD operations
# ---------------------------------------------------------------------------------------------------

@login_required
def get_mapping(request, mapping_id):
    try:
        mapping = get_object_or_404(HodProgramMap, id=mapping_id)
        
        data = {
            'success': True,
            'mapping': {
                'id': mapping.id,
                'user_id': mapping.user.id,
                'user_name': mapping.user.username,  # Use username instead of get_full_name
                'user_display': f"{mapping.user.username} ({mapping.user.email})",
                'program_id': mapping.program.id,
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
        program_id = request.POST.get("program_id")
        
        print(f"Add mapping - user_id: {user_id}, program_id: {program_id}")  # Debug print
        
        # Validate required fields
        if not user_id or not program_id:
            return JsonResponse({'success': False, 'error': 'HOD and Program are required fields.'})
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
            print(f"Found user: {user.username} (ID: {user.id})")
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Selected HOD with ID {user_id} does not exist.'})
        
        # Check if program exists
        try:
            program = Program.objects.get(id=program_id, is_active=True)
            print(f"Found program: {program.prog_code} (ID: {program.id})")
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist or is inactive.'})
        
        # Check if mapping already exists
        if HodProgramMap.objects.filter(user=user, program=program).exists():
            return JsonResponse({'success': False, 'error': f'Mapping already exists for {user.username} - {program.prog_code}.'})
        
        # Create mapping
        mapping = HodProgramMap.objects.create(
            user=user,
            program=program
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'HOD-Program mapping created successfully.',
            'mapping_id': mapping.id
        })
        
    except Exception as e:
        print(f"Error in add_mapping: {str(e)}")  # Debug print
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def edit_mapping(request, mapping_id):
    try:
        mapping = get_object_or_404(HodProgramMap, id=mapping_id)
        
        user_id = request.POST.get("user_id")
        program_id = request.POST.get("program_id")
        
        print(f"Edit mapping {mapping_id} - user_id: {user_id}, program_id: {program_id}")  # Debug print
        
        # Validate required fields
        if not user_id or not program_id:
            return JsonResponse({'success': False, 'error': 'HOD and Program are required fields.'})
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected HOD does not exist.'})
        
        # Check if program exists
        try:
            program = Program.objects.get(id=program_id, is_active=True)
        except Program.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected program does not exist or is inactive.'})
        
        # Check if mapping already exists for another record
        if HodProgramMap.objects.exclude(id=mapping_id).filter(user=user, program=program).exists():
            return JsonResponse({'success': False, 'error': f'Mapping already exists for {user.username} - {program.prog_code}.'})
        
        # Update mapping
        mapping.user = user
        mapping.program = program
        mapping.save()
        
        return JsonResponse({'success': True, 'message': 'Mapping updated successfully.'})
        
    except Exception as e:
        print(f"Error in edit_mapping: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def delete_mapping(request, mapping_id):
    
    try:
        mapping = get_object_or_404(HodProgramMap, id=mapping_id)
        mapping.delete()
        return JsonResponse({'success': True, 'message': 'Mapping deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------
# Helper endpoint to get HODs (users with staff role)
# ---------------------------------------------------------------------------------------------------

@login_required
def get_hods_list(request):
   
    try:
        hods = User.objects.filter(is_staff=True).values('id', 'username', 'first_name', 'last_name', 'email')
        hod_list = []
        for hod in hods:
            hod_list.append({
                'id': hod['id'],
                'username': hod['username'],
                'name': f"{hod['first_name']} {hod['last_name']}".strip() or hod['username'],
                'email': hod['email']
            })
        return JsonResponse({'success': True, 'hods': hod_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
# Excel Operations for HOD Program Map - Simplified
# ---------------------------------------------------------------------------------------------------

@login_required
def download_sample_mapping_excel(request):

    sample_data = {
        'hod_username': ['john_doe', 'jane_smith'],
        'program_code': ['CS101', 'IT201']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Hod Program Sample', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Hod Program Sample.xlsx"'
    return response

# ---------------------------------------------------------------------------------------------------

@login_required
def download_mappings_excel(request):

    mappings = HodProgramMap.objects.select_related('user', 'program').all().order_by('user__username')
    
    # Prepare data for Excel - only username and program code
    mapping_data = []
    for mapping in mappings:
        mapping_data.append({
            'hod_username': mapping.user.username,
            'program_code': mapping.program.prog_code,
        })
    
    df = pd.DataFrame(mapping_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Hod Program Mappings', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Hod Program Mappings.xlsx"'
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
        required_columns = ['hod_username', 'program_code']
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
            username = str(row.get('hod_username', '')).strip()
            program_code = str(row.get('program_code', '')).strip()
            
            # Skip if required fields are missing
            if not username or not program_code:
                errors.append(f'Row {index + 2}: Missing HOD username or program code')
                continue
            
            # Find user by username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                errors.append(f'Row {index + 2}: HOD with username "{username}" not found')
                continue
            
            # Find program by program code
            try:
                program = Program.objects.get(prog_code=program_code, is_active=True)
            except Program.DoesNotExist:
                errors.append(f'Row {index + 2}: Program with code "{program_code}" not found or inactive')
                continue
            
            # Check if mapping already exists
            if HodProgramMap.objects.filter(user=user, program=program).exists():
                errors.append(f'Row {index + 2}: Mapping already exists for {username} - {program_code}')
                continue
            
            try:
                mapping = HodProgramMap.objects.create(
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
