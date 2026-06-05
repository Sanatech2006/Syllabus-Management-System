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

// Syllabus file input handling
function initializeSyllabusFileInput() {
    const fileInput = document.getElementById('syllabusPdf');
    const emptyState = document.getElementById('syllabusFileEmptyState');
    const selectedState = document.getElementById('syllabusFileSelectedState');
    const nameDisplay = document.getElementById('syllabusFileNameDisplay');
    const removeBtn = document.getElementById('syllabusRemoveFileBtn');

    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            
            if (fileExt !== '.pdf') {
                showToast('Please select a valid PDF file', 'error');
                resetSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }
            
            nameDisplay.textContent = file.name;
            emptyState.classList.add('hidden');
            selectedState.classList.remove('hidden');
        } else {
            resetSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
        }
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
        });
    }
}

function resetSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay) {
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
            const rows = document.querySelectorAll('.course-row');
            
            rows.forEach(row => {
                const courseCode = row.getAttribute('data-course-code') || '';
                const courseTitle = row.getAttribute('data-course-title') || '';
                
                if (courseCode.includes(searchTerm) || courseTitle.includes(searchTerm)) {
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
        if (drawerId === 'courseDrawer') resetCourseForm();
        if (drawerId === 'uploadDrawer') {
            const fileInput = document.getElementById('excelFile');
            const emptyState = document.getElementById('fileEmptyState');
            const selectedState = document.getElementById('fileSelectedState');
            const nameDisplay = document.getElementById('fileNameDisplay');
            if (fileInput && emptyState && selectedState && nameDisplay) {
                resetFileInput(fileInput, emptyState, selectedState, nameDisplay);
            }
        }
        if (drawerId === 'syllabusDrawer') {
            const fileInput = document.getElementById('syllabusPdf');
            const emptyState = document.getElementById('syllabusFileEmptyState');
            const selectedState = document.getElementById('syllabusFileSelectedState');
            const nameDisplay = document.getElementById('syllabusFileNameDisplay');
            if (fileInput && emptyState && selectedState && nameDisplay) {
                resetSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
            }
        }
    }
}

function resetCourseForm() {
    const form = document.getElementById('courseForm');
    if (form) form.reset();
    const editId = document.getElementById('editCourseId');
    if (editId) editId.value = '';
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New Course';
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) drawerSubtitle.innerHTML = 'Fields marked with <span class="text-rose-500 font-bold">*</span> are required.';
}

// Edit course function
function editCourse(courseId) {
    fetch(`/course-management/get-course/${courseId}/`)  // Changed to hyphen
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('editCourseId').value = data.course.id;
                document.getElementById('programId').value = data.course.program_id;
                document.getElementById('courseCode').value = data.course.course_code;
                document.getElementById('courseTitle').value = data.course.course_title;
                document.getElementById('yearSelect').value = data.course.year;
                document.getElementById('semSelect').value = data.course.sem;
                document.getElementById('courseCategory').value = data.course.course_category;
                document.getElementById('partSelect').value = data.course.part;
                document.getElementById('hrsPerWeek').value = data.course.hrs_per_week;
                document.getElementById('credit').value = data.course.credit;
                document.getElementById('marksCia').value = data.course.marks_cia;
                document.getElementById('marksEse').value = data.course.marks_ese;
                document.getElementById('totalMarks').value = data.course.total_marks;
                document.getElementById('drawer-title').innerText = 'Edit Course';
                document.getElementById('drawer-subtitle').innerHTML = 'Update course information below.';
                openDrawer('courseDrawer');
            } else {
                showToast('Error loading course data', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading course data', 'error');
        });
}

// Syllabus management
let currentSyllabusCourseId = null;
let currentSyllabusCourseCode = null;

function manageSyllabus(courseId, courseCode) {
    currentSyllabusCourseId = courseId;
    currentSyllabusCourseCode = courseCode;
    
    document.getElementById('syllabusCourseId').value = courseId;
    document.getElementById('syllabusCourseCode').innerText = `Course: ${courseCode}`;
    
    // Check if syllabus exists
    fetch(`/course-management/get-course/${courseId}/`)  // Changed to hyphen
        .then(response => response.json())
        .then(data => {
            const statusEl = document.getElementById('syllabusStatus');
            const messageEl = document.getElementById('syllabusMessage');
            const downloadBtn = document.getElementById('downloadSyllabusBtn');
            const deleteBtn = document.getElementById('deleteSyllabusBtn');
            
            if (data.course.has_syllabus) {
                statusEl.innerText = 'Syllabus Uploaded';
                messageEl.innerText = 'A syllabus PDF is available for this course.';
                downloadBtn.classList.remove('hidden');
                deleteBtn.classList.remove('hidden');
            } else {
                statusEl.innerText = 'No Syllabus Uploaded';
                messageEl.innerText = 'Upload a PDF syllabus for this course.';
                downloadBtn.classList.add('hidden');
                deleteBtn.classList.add('hidden');
            }
            openDrawer('syllabusDrawer');
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error checking syllabus', 'error');
        });
}

// Download syllabus
function initializeDownloadSyllabus() {
    const downloadBtn = document.getElementById('downloadSyllabusBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            if (currentSyllabusCourseId) {
                window.location.href = `/course-management/download-syllabus/${currentSyllabusCourseId}/`;  // Changed to hyphen
            }
        });
    }
}

// Delete syllabus
function initializeDeleteSyllabus() {
    const deleteSyllabusBtn = document.getElementById('deleteSyllabusBtn');
    if (deleteSyllabusBtn) {
        deleteSyllabusBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this syllabus?')) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/course-management/get-course/${currentSyllabusCourseId}/`)  // Changed to hyphen
                    .then(response => response.json())
                    .then(data => {
                        showToast('Please implement syllabus deletion in the backend', 'error');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('Error deleting syllabus', 'error');
                    });
            }
        });
    }
}

// Delete confirmation
let currentDeleteCourseId = null;

function confirmDelete(courseId, courseCode) {
    currentDeleteCourseId = courseId;
    const deleteSpan = document.getElementById('deleteCourseCode');
    if (deleteSpan) deleteSpan.innerText = courseCode;
    openDrawer('deleteDrawer');
}

function initializeDeleteButton() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (currentDeleteCourseId) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/course-management/delete/${currentDeleteCourseId}/`, {  // Changed to hyphen
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
                        showToast('Course deleted successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showToast(data.error || 'Error deleting course', 'error');
                    }
                    closeDrawer('deleteDrawer');
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Error deleting course', 'error');
                });
            }
        });
    }
}

// Handle course form submission
function initializeCourseForm() {
    const form = document.getElementById('courseForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const courseId = document.getElementById('editCourseId').value;
            const url = courseId ? `/course-management/edit/${courseId}/` : '/course-management/add/';  // Changed to hyphen
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
                    showToast(courseId ? 'Course updated successfully!' : 'Course created successfully!');
                    setTimeout(() => location.reload(), 1500);
                    closeDrawer('courseDrawer');
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

// Handle syllabus upload
function initializeSyllabusForm() {
    const form = document.getElementById('syllabusForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('syllabusPdf');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                showToast('Please select a PDF file to upload', 'error');
                return;
            }
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const courseId = document.getElementById('syllabusCourseId').value;
            
            fetch(`/course-management/upload-syllabus/${courseId}/`, {  // Changed to hyphen
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Syllabus uploaded successfully!');
                    setTimeout(() => location.reload(), 1500);
                    closeDrawer('syllabusDrawer');
                } else {
                    showToast(data.error || 'Error uploading syllabus', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error uploading syllabus', 'error');
            });
        });
    }
}

// Handle Excel upload - UPDATED WITH CORRECT URL
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
            
            // Use hyphen instead of underscore
            fetch('/course-management/upload-courses/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message || 'Courses imported successfully!');
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
            const drawers = ['courseDrawer', 'deleteDrawer', 'uploadDrawer', 'syllabusDrawer'];
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
    initializeSyllabusFileInput();
    initializeSearch();
    initializeDeleteButton();
    initializeCourseForm();
    initializeSyllabusForm();
    initializeUploadForm();
    initializePerPage();
    initializeClearFilters();
    initializeEscapeKey();
    initializeDownloadSyllabus();
    initializeDeleteSyllabus();
});