from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import pandas as pd
import io
from datetime import datetime

User = get_user_model()

# ---------------------------------------------------------------------------------------------------
# Display the user management page with list of users and total count
# ---------------------------------------------------------------------------------------------------

@login_required
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        "users": users,
        "total_users": users.count(),
    }
    return render(request, "user_management.html", context)

# ---------------------------------------------------------------------------------------------------
# AJAX endpoints for user CRUD operations
# ---------------------------------------------------------------------------------------------------

@login_required
def get_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        
        data = {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined.strftime('%Y-%m-%d') if user.date_joined else '',
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def add_user(request):
    try:
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        # Validate required fields
        if not all([username, password]):
            return JsonResponse({'success': False, 'error': 'Username and password are required.'})

        # Validate email format only if provided
        if email:
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Invalid email format.'})
            
            # Check if email exists only if provided
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already exists.'})
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists.'})
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already exists.'})
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email if email else '',
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        
        return JsonResponse({'success': True, 'message': 'User created successfully.', 'user_id': user.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def edit_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get form data
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()

        # Validate required fields 
        if not username:
            return JsonResponse({'success': False, 'error': 'Username is required.'})
        
        # Validate email format only if provided
        if email:
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Invalid email format.'})
            
            # Check if email exists for other users only if provided
            if User.objects.exclude(id=user_id).filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already exists.'})
        
        # Check if username exists for other users
        if User.objects.exclude(id=user_id).filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists.'})
        
        # Update user fields
        user.username = username
        user.email = email if email else '',
        user.first_name = first_name
        user.last_name = last_name
        
        # Handle password update
        new_password = request.POST.get("password")
        if new_password:
            user.set_password(new_password)
            if request.user == user:
                update_session_auth_hash(request, user)
        
        user.save()
        
        return JsonResponse({'success': True, 'message': 'User updated successfully.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def delete_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        if request.user.id == user_id:
            return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'})
        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ---------------------------------------------------------------------------------------------------
# Excel Operations - Simplified (No styling)
# ---------------------------------------------------------------------------------------------------

@login_required
def download_sample_excel(request):
    
    sample_data = {
        'username': ['john_doe', 'jane_smith', 'mike_wilson'],
        'first_name': ['John', 'Jane', 'Mike'],
        'password': ['TempPass@123', 'TempPass@123', 'TempPass@123']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Users', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Users Sample.xlsx"'
    return response
# ---------------------------------------------------------------------------------------------------

@login_required
def download_users_excel(request):
    
    users = User.objects.all().order_by('username')
    
    # Prepare data for Excel with only three columns
    user_data = []
    for user in users:

        plain_password = getattr(user, 'plain_password', 'Not Available')
        
        user_data.append({
            'Username': user.username,
            'First Name': user.first_name,
            'Password': plain_password if plain_password else '********'
        })
    
    df = pd.DataFrame(user_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Users', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="User List.xlsx"'
    return response

# ---------------------------------------------------------------------------------------------------
# Handle Excel file upload for bulk user import
# ---------------------------------------------------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def upload_users_excel(request):

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
        required_columns = ['username', 'first_name', 'password']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing_columns)}. Your file has: {", ".join(df.columns)}'
            })
        
        # Track import results
        created_users = []
        errors = []
        skipped = 0
        
        for index, row in df.iterrows():
            username = str(row.get('username', '')).strip()
            first_name = str(row.get('first_name', '')).strip() if pd.notna(row.get('first_name')) else ''
            password = str(row.get('password', '')).strip() if pd.notna(row.get('password')) else 'TempPass@123'
            
            # Skip if username is missing
            if not username:
                skipped += 1
                errors.append(f'Row {index + 2}: Missing username')
                continue
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                errors.append(f'Row {index + 2}: Username "{username}" already exists - skipped')
                continue
            
            try:
                # Create user with default email if not provided
                email = f"{username}@example.com"  
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name='',  
                    is_active=True,
                    is_staff=False,
                    is_superuser=False
                )
                created_users.append(username)
            except Exception as e:
                errors.append(f'Row {index + 2}: Error creating user {username} - {str(e)}')
        
        # Prepare response message
        if created_users:
            message = f'Successfully imported {len(created_users)} users.'
            if errors:
                message += f' {len(errors)} errors encountered.'
            return JsonResponse({
                'success': True,
                'message': message,
                'created': len(created_users),
                'skipped': skipped,
                'errors': errors[:10]
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'No users were imported. Errors: {", ".join(errors[:5])}'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})