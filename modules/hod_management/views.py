from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import HodProgramMap

# Import models from other apps - adjust paths based on your structure
try:
    from modules.program_manage.models import Program
except ImportError:
    from program_manage.models import Program  # Fallback import

from django.contrib.auth import get_user_model

User = get_user_model()


@staff_member_required
def hod_program_map_list(request):
    """Display list of HOD-Program mappings"""
    mappings = HodProgramMap.objects.select_related('user', 'program').all()
    
    # Get unique HODs count for statistics
    unique_hods = mappings.values('user').distinct().count()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        mappings = mappings.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(program__name__icontains=search_query) |
            Q(program__code__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(mappings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_mappings': mappings.count(),
        'total_hods': unique_hods,
    }
    return render(request, 'hod_management/map_list.html', context)


@staff_member_required
def hod_program_map_create(request):
    """Create new HOD-Program mapping"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        program_id = request.POST.get('program_id')
        
        if not user_id or not program_id:
            messages.error(request, 'Please select both HOD and Program.')
        elif HodProgramMap.objects.filter(user_id=user_id, program_id=program_id).exists():
            messages.error(request, 'This mapping already exists!')
        else:
            try:
                HodProgramMap.objects.create(
                    user_id=user_id,
                    program_id=program_id
                )
                messages.success(request, 'HOD-Program mapping created successfully!')
                return redirect('hod_management:hod_program_map_list')
            except Exception as e:
                messages.error(request, f'Error creating mapping: {str(e)}')
    
    # Get users with staff access (potential HODs) - exclude superusers
    hods = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    
    # Try to get programs from the correct location
    try:
        from modules.program_manage.models import Program
        programs = Program.objects.all().order_by('name')
    except ImportError:
        try:
            from program_manage.models import Program
            programs = Program.objects.all().order_by('name')
        except ImportError:
            programs = []
            messages.warning(request, 'Program model not found. Please check your program_manage app.')
    
    context = {
        'hods': hods,
        'programs': programs,
        'title': 'Create HOD-Program Mapping',
    }
    return render(request, 'hod_management/map_form.html', context)


@staff_member_required
def hod_program_map_edit(request, pk):
    """Edit existing HOD-Program mapping"""
    mapping = get_object_or_404(HodProgramMap, pk=pk)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        program_id = request.POST.get('program_id')
        
        if not user_id or not program_id:
            messages.error(request, 'Please select both HOD and Program.')
        elif HodProgramMap.objects.exclude(pk=pk).filter(
            user_id=user_id, program_id=program_id
        ).exists():
            messages.error(request, 'This mapping already exists!')
        else:
            try:
                mapping.user_id = user_id
                mapping.program_id = program_id
                mapping.save()
                messages.success(request, 'Mapping updated successfully!')
                return redirect('hod_management:hod_program_map_list')
            except Exception as e:
                messages.error(request, f'Error updating mapping: {str(e)}')
    
    hods = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    
    try:
        from modules.program_manage.models import Program
        programs = Program.objects.all().order_by('name')
    except ImportError:
        try:
            from program_manage.models import Program
            programs = Program.objects.all().order_by('name')
        except ImportError:
            programs = []
    
    context = {
        'mapping': mapping,
        'hods': hods,
        'programs': programs,
        'title': 'Edit HOD-Program Mapping',
    }
    return render(request, 'hod_management/map_form.html', context)


@staff_member_required
def hod_program_map_delete(request, pk):
    """Delete HOD-Program mapping"""
    mapping = get_object_or_404(HodProgramMap, pk=pk)
    
    if request.method == 'POST':
        mapping.delete()
        messages.success(request, 'Mapping deleted successfully!')
        return redirect('hod_management:hod_program_map_list')
    
    context = {
        'mapping': mapping,
    }
    return render(request, 'hod_management/map_confirm_delete.html', context)


@staff_member_required
def get_hod_programs_api(request, user_id):
    """API endpoint to get programs mapped to a specific HOD"""
    program_ids = HodProgramMap.objects.filter(user_id=user_id).values_list('program_id', flat=True)
    
    try:
        from modules.program_manage.models import Program
        programs = Program.objects.filter(id__in=program_ids).values('id', 'name', 'code')
    except ImportError:
        try:
            from program_manage.models import Program
            programs = Program.objects.filter(id__in=program_ids).values('id', 'name', 'code')
        except ImportError:
            programs = []
    
    return JsonResponse(list(programs), safe=False)