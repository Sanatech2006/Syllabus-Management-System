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
    if (!searchInput) return;

    let searchDebounceTimer = null;
    searchInput.addEventListener('input', function() {
        window.clearTimeout(searchDebounceTimer);
        searchDebounceTimer = window.setTimeout(() => {
            const url = new URL(window.location.href);
            const value = searchInput.value.trim();

            if (value) {
                url.searchParams.set('search', value);
            } else {
                url.searchParams.delete('search');
            }
            url.searchParams.delete('page');

            window.location.href = url.toString();
        }, 300);
    });
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
            resetUploadFeedback();
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
            resetUploadFeedback();
        }
    }
}

function resetMappingForm() {
    const form = document.getElementById('mappingForm');
    if (form) form.reset();
    
    const editMappingId = document.getElementById('editMappingId');
    if (editMappingId) editMappingId.value = '';
    
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New Verification Mapping';
    
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) drawerSubtitle.innerText = 'Assign a verifier to oversee one or more programs';

    closeProgramMenu();
    clearProgramSelections();
}

function getProgramSelectionElements() {
    return {
        wrapper: document.getElementById('programSelectionWrapper'),
        trigger: document.getElementById('programSelectionTrigger'),
        menu: document.getElementById('programSelectionMenu'),
        label: document.getElementById('programSelectionLabel'),
    };
}

function updateProgramSelectionLabel() {
    const { label } = getProgramSelectionElements();
    if (!label) return;

    const checkedLabels = Array.from(document.querySelectorAll('input[name="program_ids"]:checked'))
        .map(checkbox => {
            const row = checkbox.closest('label');
            const title = row?.querySelector('.text-sm.font-semibold.text-slate-900')?.textContent?.trim();
            return title || '';
        })
        .filter(Boolean);

    if (checkedLabels.length === 0) {
        label.textContent = '-- Select Program --';
        return;
    }

    if (checkedLabels.length === 1) {
        label.textContent = checkedLabels[0];
        return;
    }

    label.textContent = `${checkedLabels.length} programs selected`;
}

function openProgramMenu() {
    const { menu } = getProgramSelectionElements();
    if (menu) menu.classList.remove('hidden');
}

function closeProgramMenu() {
    const { menu } = getProgramSelectionElements();
    if (menu) menu.classList.add('hidden');
}

function toggleProgramMenu() {
    const { menu } = getProgramSelectionElements();
    if (!menu) return;
    menu.classList.toggle('hidden');
}

function clearProgramSelections() {
    document.querySelectorAll('input[name="program_ids"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateProgramSelectionLabel();
}

function setProgramSelections(programIds) {
    const selectedIds = new Set((programIds || []).map(String));
    document.querySelectorAll('input[name="program_ids"]').forEach(checkbox => {
        checkbox.checked = selectedIds.has(String(checkbox.value));
    });
    updateProgramSelectionLabel();
}

// Edit mapping function
function editMapping(mappingId) {
    console.log('Editing mapping ID:', mappingId);
    
    fetch(`/verification-management/get-mapping/${mappingId}/`)
        .then(response => response.json())
        .then(data => {
            console.log('Edit response:', data);
            if (data.success) {
                document.getElementById('editMappingId').value = data.mapping.id;
                document.getElementById('userId').value = data.mapping.user_id;
                setProgramSelections(data.mapping.program_ids || []);
                
                document.getElementById('drawer-title').innerText = 'Edit Verification Mapping';
                document.getElementById('drawer-subtitle').innerHTML = 'Update the verifier and selected programs below.';
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

function confirmDelete(mappingId, verifierName, programCode) {
    currentDeleteMappingId = mappingId;
    const mappingInfoSpan = document.getElementById('deleteDrawerMappingInfo');
    if (mappingInfoSpan) mappingInfoSpan.innerText = `${verifierName} → ${programCode}`;
    openDrawer('deleteDrawer');
}

function initializeDeleteButton() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (currentDeleteMappingId) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/verification-management/delete-mapping/${currentDeleteMappingId}/`, {
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
            const selectedProgramIds = Array.from(document.querySelectorAll('input[name="program_ids"]:checked')).map(checkbox => checkbox.value);
            
            if (!userId || selectedProgramIds.length === 0) {
                showToast('Please select both a Verifier and at least one program', 'error');
                return;
            }
            
            let url;
            if (mappingId) {
                url = `/verification-management/edit-mapping/${mappingId}/`;
            } else {
                url = `/verification-management/add-mapping/`;
            }
            
            const formData = new FormData(this);
            formData.delete('program_ids');
            selectedProgramIds.forEach(programId => formData.append('program_ids', programId));
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
                if (data.success) {
                    const successMessage = data.message || (mappingId ? 'Mapping updated successfully!' : 'Mapping created successfully!');
                    showToast(successMessage);
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

function resetUploadFeedback() {
    const progressContainer = document.getElementById('uploadProgressContainer');
    const progressText = document.getElementById('uploadProgressText');
    const progressPercent = document.getElementById('uploadProgressPercent');
    const progressBar = document.getElementById('uploadProgressBar');
    const resultContainer = document.getElementById('uploadResultContainer');
    const resultTitle = document.getElementById('uploadResultTitle');
    const resultMessage = document.getElementById('uploadResultMessage');
    const resultIcon = document.getElementById('uploadResultIcon');
    const successCount = document.getElementById('uploadSuccessCount');
    const errorCount = document.getElementById('uploadErrorCount');
    const errorsListContainer = document.getElementById('uploadErrorsListContainer');
    const errorsList = document.getElementById('uploadErrorsList');

    if (progressContainer) progressContainer.classList.add('hidden');
    if (progressText) progressText.innerText = 'Uploading...';
    if (progressPercent) progressPercent.innerText = '0%';
    if (progressBar) progressBar.style.width = '0%';
    if (resultContainer) resultContainer.classList.add('hidden');
    if (resultTitle) resultTitle.innerText = 'Upload Status';
    if (resultMessage) resultMessage.innerText = '';
    if (resultIcon) resultIcon.className = 'p-2 rounded-lg';
    if (successCount) successCount.innerText = '0';
    if (errorCount) errorCount.innerText = '0';
    if (errorsListContainer) errorsListContainer.classList.add('hidden');
    if (errorsList) errorsList.innerHTML = '';
}

function updateUploadProgress(percent) {
    const progressContainer = document.getElementById('uploadProgressContainer');
    const progressText = document.getElementById('uploadProgressText');
    const progressPercent = document.getElementById('uploadProgressPercent');
    const progressBar = document.getElementById('uploadProgressBar');

    if (progressContainer) progressContainer.classList.remove('hidden');
    if (progressText) progressText.innerText = percent >= 100 ? 'Processing response...' : 'Uploading...';
    if (progressPercent) progressPercent.innerText = `${Math.min(percent, 100)}%`;
    if (progressBar) progressBar.style.width = `${Math.min(percent, 100)}%`;
}

function showUploadResult(data, isSuccess) {
    const progressContainer = document.getElementById('uploadProgressContainer');
    const resultContainer = document.getElementById('uploadResultContainer');
    const resultTitle = document.getElementById('uploadResultTitle');
    const resultMessage = document.getElementById('uploadResultMessage');
    const resultIcon = document.getElementById('uploadResultIcon');
    const successCount = document.getElementById('uploadSuccessCount');
    const errorCount = document.getElementById('uploadErrorCount');
    const errorsListContainer = document.getElementById('uploadErrorsListContainer');
    const errorsList = document.getElementById('uploadErrorsList');
    const createdCount = Number(data?.created || 0);
    const errors = Array.isArray(data?.errors) ? data.errors : [];

    if (progressContainer) progressContainer.classList.add('hidden');
    if (resultContainer) resultContainer.classList.remove('hidden');
    if (resultTitle) resultTitle.innerText = isSuccess ? 'Upload completed' : 'Upload finished with errors';
    if (resultMessage) resultMessage.innerText = data?.message || data?.error || '';
    if (resultIcon) {
        resultIcon.className = `p-2 rounded-lg ${isSuccess ? 'bg-green-50 text-green-600' : 'bg-rose-50 text-rose-600'}`;
        resultIcon.innerHTML = isSuccess
            ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
            : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v4m0 4h.01M10.29 3.86l-8.1 14.04A2 2 0 003.92 21h16.16a2 2 0 001.73-3.1l-8.1-14.04a2 2 0 00-3.46 0z"/></svg>';
    }
    if (successCount) successCount.innerText = String(createdCount);
    if (errorCount) errorCount.innerText = String(errors.length);
    if (errorsListContainer) errorsListContainer.classList.toggle('hidden', errors.length === 0);
    if (errorsList) errorsList.innerHTML = errors.slice(0, 10).map(error => `<div>${error}</div>`).join('');
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
            const submitButton = document.querySelector('button[type="submit"][form="uploadForm"]');
            if (submitButton) submitButton.disabled = true;
            resetUploadFeedback();
            updateUploadProgress(0);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/verification-management/upload-mappings/', true);
            if (csrfToken) xhr.setRequestHeader('X-CSRFToken', csrfToken);

            xhr.upload.onprogress = function(event) {
                if (event.lengthComputable) {
                    updateUploadProgress(Math.round((event.loaded / event.total) * 100));
                } else {
                    updateUploadProgress(85);
                }
            };

            xhr.onload = function() {
                if (submitButton) submitButton.disabled = false;
                updateUploadProgress(100);

                let data = {};
                try {
                    data = JSON.parse(xhr.responseText || '{}');
                } catch (error) {
                    console.error('Error parsing upload response:', error);
                    showToast('Error uploading file', 'error');
                    return;
                }

                const isSuccess = xhr.status >= 200 && xhr.status < 300 && data.success;
                showUploadResult(data, isSuccess);

                if (isSuccess) {
                    showToast(data.message || 'Mappings imported successfully!');
                } else {
                    showToast(data.error || 'Error uploading file', 'error');
                }
            };

            xhr.onerror = function() {
                if (submitButton) submitButton.disabled = false;
                resetUploadFeedback();
                showToast('Error uploading file', 'error');
            };

            xhr.send(formData);
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
    console.log('DOM loaded - initializing Verifier Management');
    initializeFileInput();
    initializeSearch();
    initializeDeleteButton();
    initializeMappingForm();
    initializeUploadForm();
    initializeEscapeKey();
    const closeUploadResultBtn = document.getElementById('closeUploadResultBtn');
    if (closeUploadResultBtn) {
        closeUploadResultBtn.addEventListener('click', function() {
            closeDrawer('uploadDrawer');
            location.reload();
        });
    }

    document.addEventListener('change', function(event) {
        if (event.target && event.target.matches('input[name="program_ids"]')) {
            updateProgramSelectionLabel();
        }
    });

    document.addEventListener('click', function(event) {
        const { wrapper, trigger, menu } = getProgramSelectionElements();
        if (!wrapper || !menu) return;

        const clickedInside = wrapper.contains(event.target);
        const clickedTrigger = trigger && trigger.contains(event.target);

        if (!clickedInside && !clickedTrigger && !menu.classList.contains('hidden')) {
            closeProgramMenu();
        }
    });

    updateProgramSelectionLabel();
    
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

