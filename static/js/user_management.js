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

    // Handle file selection change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            
            // Validate file type
            const validExtensions = ['.xlsx', '.xls'];
            const fileName = file.name;
            const fileExt = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
            
            if (!validExtensions.includes(fileExt)) {
                showToast('Please select a valid Excel file (.xlsx or .xls)', 'error');
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }
            
            // Validate file size (max 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
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

    // Handle manual removal of selected file
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Prevents triggering input click via event bubbling
            resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
        });
    }
}

function resetFileInput(fileInput, emptyState, selectedState, nameDisplay) {
    if (fileInput) fileInput.value = ''; // Clear native DOM reference
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
                // Skip empty rows
                if (row.querySelector('td[colspan]')) return;
                
                const nameElement = row.querySelector('.text-md.font-bold.text-slate-900');
                const emailElement = row.querySelector('.text-sm.text-indigo-600');
                const usernameElement = row.querySelector('.bg-slate-50.text-md');
                
                const name = nameElement?.innerText.toLowerCase() || '';
                const email = emailElement?.innerText.toLowerCase() || '';
                const username = usernameElement?.innerText.toLowerCase() || '';
                
                if (name.includes(searchTerm) || username.includes(searchTerm) || email.includes(searchTerm)) {
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
        
        // Animate drawer panel
        const panel = drawer.querySelector('.absolute.inset-y-0.right-0');
        if (panel) {
            panel.style.transform = 'translateX(0)';
        }
        
        // Reset file input when opening upload drawer
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
        
        if (drawerId === 'userDrawer') {
            resetUserForm();
        }
        
        // Reset file input when closing upload drawer
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

function resetUserForm() {
    const form = document.getElementById('userForm');
    if (form) form.reset();
    
    const editUserId = document.getElementById('editUserId');
    if (editUserId) editUserId.value = '';
    
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New User Record';
    
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) {
        drawerSubtitle.innerHTML = 'Fields marked with <span class="text-rose-500 font-bold">*</span> are required.';
    }
    
    const passwordRequired = document.getElementById('passwordRequired');
    if (passwordRequired) passwordRequired.innerHTML = '*';
    
    const passwordHint = document.getElementById('passwordHint');
    if (passwordHint) passwordHint.classList.add('hidden');
    
    const drawerPassword = document.getElementById('drawerPassword');
    if (drawerPassword) {
        drawerPassword.required = true;
        drawerPassword.value = '';
    }
}

// Edit user function
function editUser(userId) {
    fetch(`/users/get_user/${userId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('editUserId').value = data.user.id;
                document.getElementById('drawerFirstName').value = data.user.first_name || '';
                document.getElementById('drawerLastName').value = data.user.last_name || '';
                document.getElementById('drawerUsername').value = data.user.username;
                document.getElementById('drawerEmail').value = data.user.email;
                document.getElementById('drawerPassword').value = '';
                document.getElementById('drawerPassword').required = false;
                document.getElementById('passwordRequired').innerHTML = '(Optional)';
                document.getElementById('passwordHint').classList.remove('hidden');
                document.getElementById('drawer-title').innerText = 'Edit User Record';
                document.getElementById('drawer-subtitle').innerHTML = 'Update user information below.';
                openDrawer('userDrawer');
            } else {
                showToast('Error loading user data', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading user data', 'error');
        });
}

// Delete confirmation
let currentDeleteUserId = null;

function confirmDelete(userId, username) {
    currentDeleteUserId = userId;
    const usernameSpan = document.getElementById('deleteDrawerUsername');
    if (usernameSpan) usernameSpan.innerText = username;
    openDrawer('deleteDrawer');
}

function initializeDeleteButton() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (currentDeleteUserId) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/users/delete/${currentDeleteUserId}/`, {
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
                        showToast('User deleted successfully!');
                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    } else {
                        showToast(data.error || 'Error deleting user', 'error');
                    }
                    closeDrawer('deleteDrawer');
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Error deleting user', 'error');
                });
            }
        });
    }
}

// Handle user form submission (Add/Edit)
function initializeUserForm() {

    const form = document.getElementById('userForm');

    if (form) {

        form.addEventListener('submit', function(e) {
            
            e.preventDefault();
            
            const userId = document.getElementById('editUserId').value;
            let url;
            
            if (userId) {
                url = `/users/edit/${userId}/`;
            } else {
                url = `/users/add/`;
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
                if (data.success) {
                    showToast(userId ? 'User updated successfully!' : 'User created successfully!');
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                    closeDrawer('userDrawer');
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
            xhr.open('POST', '/users/upload-users/', true);
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
                    showToast(data.message || 'Users imported successfully!');
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
            const drawers = ['userDrawer', 'deleteDrawer', 'uploadDrawer'];
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

// Fix for import dropdown - ensure proper z-index and positioning
function fixDropdownPosition() {
    const dropdownButton = document.querySelector('.relative.inline-block button');
    const dropdownMenu = document.getElementById('excelMenu');
    
    if (dropdownButton && dropdownMenu) {
        // Ensure dropdown appears above other elements
        dropdownMenu.style.zIndex = '9999';
        
        // Adjust position if needed
        const buttonRect = dropdownButton.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const menuHeight = dropdownMenu.offsetHeight;
        
        // Check if dropdown would go off screen
        if (buttonRect.bottom + menuHeight > viewportHeight) {
            dropdownMenu.style.top = 'auto';
            dropdownMenu.style.bottom = '100%';
            dropdownMenu.style.marginTop = '0';
            dropdownMenu.style.marginBottom = '8px';
        } else {
            dropdownMenu.style.top = '100%';
            dropdownMenu.style.bottom = 'auto';
            dropdownMenu.style.marginTop = '8px';
            dropdownMenu.style.marginBottom = '0';
        }
    }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileInput();
    initializeSearch();
    initializeDeleteButton();
    initializeUserForm();
    initializeUploadForm();
    initializeEscapeKey();
    const closeUploadResultBtn = document.getElementById('closeUploadResultBtn');
    if (closeUploadResultBtn) {
        closeUploadResultBtn.addEventListener('click', function() {
            closeDrawer('uploadDrawer');
            location.reload();
        });
    }
    fixDropdownPosition();
    
    // Re-fix dropdown position on window resize
    window.addEventListener('resize', fixDropdownPosition);
    
    // Fix for table sticky headers z-index issues
    const style = document.createElement('style');
    style.textContent = `
        /* Fix for dropdown menu clipping */
        #excelMenu {
            position: absolute;
            z-index: 9999;
            min-width: 200px;
        }
        
        /* Ensure table sticky elements don't overlap dropdown */
        .sticky {
            z-index: 20;
        }
        
        /* Better drawer animations */
        .drawer .absolute.inset-y-0.right-0 {
            transform: translateX(0);
            transition: transform 0.3s ease-in-out;
        }
        
        .drawer.hidden .absolute.inset-y-0.right-0 {
            transform: translateX(100%);
        }
        
        /* Fix for table header sticky positioning */
        thead.sticky th {
            z-index: 30;
        }
        
        /* Ensure dropdown appears above table */
        .z-50 {
            z-index: 50;
        }
        
        /* Fix for partial hiding issue */
        .overflow-x-auto {
            overflow-x: auto;
            position: relative;
        }
        
        .relative.inline-block {
            position: relative;
            z-index: 40;
        }
        
        /* File input styling improvements */
        #fileSelectedState, #fileEmptyState {
            transition: all 0.2s ease;
        }
        
        #removeFileBtn:hover {
            background-color: #fee2e2;
            color: #dc2626;
        }
    `;
    document.head.appendChild(style);
});
