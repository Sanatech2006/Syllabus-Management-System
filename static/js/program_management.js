// program_management.js - Complete JavaScript for Program Management

// Excel dropdown menu
function toggleExcelMenu() {
    const menu = document.getElementById('excelMenu');
    if (menu) menu.classList.toggle('hidden');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('excelMenu');
    const button = event.target.closest('.relative.inline-block button');
    if (!button && menu && !menu.classList.contains('hidden')) {
        menu.classList.add('hidden');
    }
});

// File input handling
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
            const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            
            if (!validExtensions.includes(fileExt)) {
                showToast('Please select a valid Excel file (.xlsx or .xls)', 'error');
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }
            
            nameDisplay.textContent = file.name;
            emptyState.classList.add('hidden');
            selectedState.classList.remove('hidden');
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
            const rows = document.querySelectorAll('.program-row');
            
            rows.forEach(row => {
                const programCode = row.getAttribute('data-program-code') || '';
                const degree = row.getAttribute('data-degree') || '';
                const branch = row.getAttribute('data-branch') || '';
                
                if (programCode.includes(searchTerm) || degree.includes(searchTerm) || branch.includes(searchTerm)) {
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
    }
}

function closeDrawer(drawerId) {
    const drawer = document.getElementById(drawerId);
    if (drawer) {
        drawer.classList.add('hidden');
        document.body.style.overflow = '';
        if (drawerId === 'programDrawer') resetProgramForm();
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

function resetProgramForm() {
    const form = document.getElementById('programForm');
    if (form) form.reset();
    const editId = document.getElementById('editProgramId');
    if (editId) editId.value = '';
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New Program';
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) drawerSubtitle.innerHTML = 'Fields marked with <span class="text-rose-500 font-bold">*</span> are required.';
}

// Edit program function
function editProgram(programId) {
    fetch(`/program_manage/get-program/${programId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('editProgramId').value = data.program.id;
                document.getElementById('progType').value = data.program.prog_type;
                document.getElementById('progCategory').value = data.program.prog_category;
                document.getElementById('degree').value = data.program.degree;
                document.getElementById('branch').value = data.program.branch;
                document.getElementById('progCode').value = data.program.prog_code;
                document.getElementById('drawer-title').innerText = 'Edit Program';
                document.getElementById('drawer-subtitle').innerHTML = 'Update program information below.';
                openDrawer('programDrawer');
            } else {
                showToast('Error loading program data', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading program data', 'error');
        });
}

// Delete confirmation
let currentDeleteProgramId = null;

function confirmDelete(programId, programCode) {
    currentDeleteProgramId = programId;
    const deleteSpan = document.getElementById('deleteProgramCode');
    if (deleteSpan) deleteSpan.innerText = programCode;
    openDrawer('deleteDrawer');
}

function initializeDeleteButton() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (currentDeleteProgramId) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/program_manage/delete/${currentDeleteProgramId}/`, {
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
                        showToast('Program deleted successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showToast(data.error || 'Error deleting program', 'error');
                    }
                    closeDrawer('deleteDrawer');
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Error deleting program', 'error');
                });
            }
        });
    }
}

// Handle program form submission
function initializeProgramForm() {
    const form = document.getElementById('programForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const programId = document.getElementById('editProgramId').value;
            const url = programId ? `/program_manage/edit/${programId}/` : '/program_manage/add/';
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(programId ? 'Program updated successfully!' : 'Program created successfully!');
                    setTimeout(() => location.reload(), 1500);
                    closeDrawer('programDrawer');
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
            
            fetch('/program_manage/upload-programs/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message || 'Programs imported successfully!');
                    setTimeout(() => location.reload(), 2000);
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

// Per page change
function initializePerPage() {
    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('per_page', this.value);
            url.searchParams.delete('page');
            window.location.href = url.toString();
        });
    }
}

// Clear filters
function initializeClearFilters() {
    const clearBtn = document.getElementById('clearFilters');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.querySelectorAll('#filterForm select').forEach(select => select.value = '');
            document.getElementById('filterForm').submit();
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
        toastDiv.classList.remove('bg-green-500', 'bg-red-500');
        toastDiv.classList.add(type === 'error' ? 'bg-red-500' : 'bg-green-500');
    }
    toast.classList.remove('hidden');
    
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

// Close drawers on escape key
function initializeEscapeKey() {
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const drawers = ['programDrawer', 'deleteDrawer', 'uploadDrawer'];
            drawers.forEach(drawer => {
                const drawerElement = document.getElementById(drawer);
                if (drawerElement && !drawerElement.classList.contains('hidden')) {
                    closeDrawer(drawer);
                }
            });
            const menu = document.getElementById('excelMenu');
            if (menu && !menu.classList.contains('hidden')) menu.classList.add('hidden');
        }
    });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', function() {
    initializeFileInput();
    initializeSearch();
    initializeDeleteButton();
    initializeProgramForm();
    initializeUploadForm();
    initializePerPage();
    initializeClearFilters();
    initializeEscapeKey();
});