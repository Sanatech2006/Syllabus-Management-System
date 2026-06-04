// Excel dropdown menu
function toggleExcelMenu() {
    const menu = document.getElementById('excelMenu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('excelMenu');
    const button = event.target.closest('.relative.inline-block button');
    if (!button && menu && !menu.classList.contains('hidden')) {
        menu.classList.add('hidden');
    }
});

// File input handling for Excel upload
function initializeFileInput() {
    const fileInput = document.getElementById('excelFile');
    const emptyState = document.getElementById('fileEmptyState');
    const selectedState = document.getElementById('fileSelectedState');
    const nameDisplay = document.getElementById('fileNameDisplay');
    const removeBtn = document.getElementById('removeFileBtn');

    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            
            const validExtensions = ['.xlsx', '.xls'];
            const fileName = file.name;
            const fileExt = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
            
            if (!validExtensions.includes(fileExt)) {
                showToast('Please select a valid Excel file (.xlsx or .xls)', 'error');
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }
            
            const maxSize = 10 * 1024 * 1024;
            if (file.size > maxSize) {
                showToast('File size must be less than 10MB', 'error');
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }
            
            nameDisplay.textContent = file.name;
            
            if (emptyState) emptyState.classList.add('hidden');
            if (selectedState) selectedState.classList.remove('hidden');
        } else {
            resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
        }
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
        });
    }
}

function resetFileInput(fileInput, emptyState, selectedState, nameDisplay) {
    if (fileInput) fileInput.value = '';
    if (nameDisplay) nameDisplay.textContent = 'No file selected';
    
    if (selectedState) selectedState.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                if (row.querySelector('td[colspan]')) return;
                
                const hodName = row.querySelector('.text-md.font-bold.text-slate-900')?.innerText.toLowerCase() || '';
                const hodEmail = row.querySelector('.text-sm.text-purple-600')?.innerText.toLowerCase() || '';
                const programCode = row.querySelector('.font-bold.text-slate-900')?.innerText.toLowerCase() || '';
                
                if (hodName.includes(searchTerm) || hodEmail.includes(searchTerm) || programCode.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Drawer functions
function openDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        const panel = drawer.querySelector('.absolute.inset-y-0.right-0');
        if (panel) {
            panel.style.transform = 'translateX(0)';
        }
        
        if (drawerId === 'uploadDrawer') {
            const fileInput = document.getElementById('excelFile');
            const emptyState = document.getElementById('fileEmptyState');
            const selectedState = document.getElementById('fileSelectedState');
            const nameDisplay = document.getElementById('fileNameDisplay');
            
            if (fileInput && emptyState && selectedState && nameDisplay) {
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
            }
        }
    }
}

function closeDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.add('hidden');
        document.body.style.overflow = '';
        
        if (drawerId === 'mappingDrawer') {
            resetMappingForm();
        }
        
        if (drawerId === 'uploadDrawer') {
            const fileInput = document.getElementById('excelFile');
            const emptyState = document.getElementById('fileEmptyState');
            const selectedState = document.getElementById('fileSelectedState');
            const nameDisplay = document.getElementById('fileNameDisplay');
            
            if (fileInput && emptyState && selectedState && nameDisplay) {
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
            }
        }
    }
}

function resetMappingForm() {
    const form = document.getElementById('mappingForm');
    if (form) form.reset();
    
    const editMappingId = document.getElementById('editMappingId');
    if (editMappingId) editMappingId.value = '';
    
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New HOD-Program Mapping';
    
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) drawerSubtitle.innerText = 'Assign a HOD to oversee a specific program';
}

// Edit mapping function
function editMapping(mappingId) {
    console.log('Editing mapping ID:', mappingId);
    
    fetch(`/hod-management/get-mapping/${mappingId}/`)
        .then(response => response.json())
        .then(data => {
            console.log('Edit response:', data);
            if (data.success) {
                document.getElementById('editMappingId').value = data.mapping.id;
                document.getElementById('userId').value = data.mapping.user_id;
                document.getElementById('programId').value = data.mapping.program_id;
                
                // Verify values are set
                console.log('Set user_id to:', document.getElementById('userId').value);
                console.log('Set program_id to:', document.getElementById('programId').value);
                
                document.getElementById('drawer-title').innerText = 'Edit HOD-Program Mapping';
                document.getElementById('drawer-subtitle').innerHTML = 'Update the HOD or Program assignment below.';
                openDrawer('mappingDrawer');
            } else {
                showToast('Error loading mapping data: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading mapping data', 'error');
        });
}

// Delete confirmation
let currentDeleteMappingId = null;

function confirmDelete(mappingId, hodName, programCode) {
    currentDeleteMappingId = mappingId;
    const mappingInfoSpan = document.getElementById('deleteDrawerMappingInfo');
    if (mappingInfoSpan) mappingInfoSpan.innerText = `${hodName} → ${programCode}`;
    openDrawer('deleteDrawer');
}

function initializeDeleteButton() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (currentDeleteMappingId) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/hod-management/delete-mapping/${currentDeleteMappingId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast('Mapping deleted successfully!');
                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    } else {
                        showToast(data.error || 'Error deleting mapping', 'error');
                    }
                    closeDrawer('deleteDrawer');
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Error deleting mapping', 'error');
                });
            }
        });
    }
}

// Handle mapping form submission (Add/Edit)
function initializeMappingForm() {
    const form = document.getElementById('mappingForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const mappingId = document.getElementById('editMappingId').value;
            const userId = document.getElementById('userId').value;
            const programId = document.getElementById('programId').value;
            
            console.log('Form submission - mappingId:', mappingId, 'userId:', userId, 'programId:', programId);
            
            if (!userId || !programId) {
                showToast('Please select both HOD and Program', 'error');
                return;
            }
            
            let url;
            if (mappingId) {
                url = `/hod-management/edit-mapping/${mappingId}/`;
            } else {
                url = `/hod-management/add-mapping/`;
            }
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Submit response:', data);
                if (data.success) {
                    showToast(mappingId ? 'Mapping updated successfully!' : 'Mapping created successfully!');
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                    closeDrawer('mappingDrawer');
                } else {
                    showToast(data.error || 'Error processing request', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error processing request', 'error');
            });
        });
    }
}

// Handle Excel upload
function initializeUploadForm() {
    const form = document.getElementById('uploadForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('excelFile');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                showToast('Please select a file to upload', 'error');
                return;
            }
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            fetch('/hod-management/upload-mappings/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message || 'Mappings imported successfully!');
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                    closeDrawer('uploadDrawer');
                } else {
                    showToast(data.error || 'Error uploading file', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error uploading file', 'error');
            });
        });
    }
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    const toastMessage = document.getElementById('toastMessage');
    const toastDiv = toast.querySelector('div');
    
    if (toastMessage) toastMessage.innerText = message;
    
    if (toastDiv) {
        if (type === 'error') {
            toastDiv.classList.remove('bg-green-500');
            toastDiv.classList.add('bg-red-500');
        } else {
            toastDiv.classList.remove('bg-red-500');
            toastDiv.classList.add('bg-green-500');
        }
    }
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Close drawers on escape key
function initializeEscapeKey() {
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const drawers = ['mappingDrawer', 'deleteDrawer', 'uploadDrawer'];
            drawers.forEach(drawer => {
                const drawerElement = document.getElementById(drawer);
                if (drawerElement && !drawerElement.classList.contains('hidden')) {
                    closeDrawer(drawer);
                }
            });
            const menu = document.getElementById('excelMenu');
            if (menu && !menu.classList.contains('hidden')) {
                menu.classList.add('hidden');
            }
        }
    });
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing HOD Management');
    initializeFileInput();
    initializeSearch();
    initializeDeleteButton();
    initializeMappingForm();
    initializeUploadForm();
    initializeEscapeKey();
    
    // Add styles for dropdown
    const style = document.createElement('style');
    style.textContent = `
        #excelMenu {
            position: absolute;
            z-index: 9999;
            min-width: 200px;
        }
        
        .sticky {
            z-index: 20;
        }
        
        .drawer .absolute.inset-y-0.right-0 {
            transform: translateX(0);
            transition: transform 0.3s ease-in-out;
        }
        
        .drawer.hidden .absolute.inset-y-0.right-0 {
            transform: translateX(100%);
        }
        
        thead.sticky th {
            z-index: 30;
        }
        
        .z-50 {
            z-index: 50;
        }
        
        .overflow-x-auto {
            overflow-x: auto;
            position: relative;
        }
        
        .relative.inline-block {
            position: relative;
            z-index: 40;
        }
    `;
    document.head.appendChild(style);
});