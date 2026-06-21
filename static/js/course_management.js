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

// Course syllabus file input handling
function initializeCourseSyllabusFileInput() {
    const fileInput = document.getElementById('courseSyllabusPdf');
    const emptyState = document.getElementById('courseSyllabusFileEmptyState');
    const selectedState = document.getElementById('courseSyllabusFileSelectedState');
    const nameDisplay = document.getElementById('courseSyllabusFileNameDisplay');
    const removeBtn = document.getElementById('courseSyllabusRemoveFileBtn');

    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

            if (fileExt !== '.pdf') {
                showToast('Please select a valid PDF file', 'error');
                resetCourseSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
                return;
            }

            if (nameDisplay) nameDisplay.textContent = file.name;
            if (emptyState) emptyState.classList.add('hidden');
            if (selectedState) selectedState.classList.remove('hidden');
        } else {
            resetCourseSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
        }
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetCourseSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
        });
    }
}

function resetCourseSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay) {
    if (fileInput) fileInput.value = '';
    if (nameDisplay) nameDisplay.textContent = 'No file selected';
    if (selectedState) selectedState.classList.add('hidden');
    if (emptyState) emptyState.classList.remove('hidden');
}

const courseSearchState = {
    active: false,
    term: '',
    page: 1,
    perPage: 10,
    data: [],
    serverRowsHtml: '',
    serverPaginationHtml: '',
    serverSummaryHtml: '',
};

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function getCourseSearchData() {
    if (courseSearchState.data.length > 0) return courseSearchState.data;
    const dataElement = document.getElementById('course-search-data');
    if (!dataElement) return [];

    try {
        courseSearchState.data = JSON.parse(dataElement.textContent || '[]');
    } catch (error) {
        console.error('Error parsing course search data:', error);
        courseSearchState.data = [];
    }

    return courseSearchState.data;
}

function normalizeCourseField(value) {
    return String(value ?? '').toLowerCase();
}

function courseMatchesSearch(course, searchTerm) {
    if (!searchTerm) return true;
    const lowered = searchTerm.toLowerCase();
    return [
        course.course_code,
        course.course_title,
        course.program__prog_code,
        course.program__degree,
        course.program__branch,
        course.year,
        course.sem,
        course.part,
    ].some(field => normalizeCourseField(field).includes(lowered));
}

function buildCourseRow(course, displayNumber) {
    const courseTitle = course.course_title ? escapeHtml(course.course_title) : '—';
    const programCode = course.program__prog_code ? escapeHtml(course.program__prog_code) : '—';
    const programDegree = course.program__degree ? escapeHtml(course.program__degree) : '';
    const programBranch = course.program__branch ? escapeHtml(course.program__branch) : '';
    const courseCode = escapeHtml(course.course_code || '—');
    const year = escapeHtml(course.year || '—');
    const sem = escapeHtml(course.sem || '—');
    const credit = course.credit === null || course.credit === undefined || course.credit === '' ? '—' : escapeHtml(course.credit);
    const syllabusClass = course.has_syllabus_pdf ? 'text-green-600 bg-green-50 hover:bg-green-100' : 'text-blue-600 bg-blue-50 hover:bg-blue-100';

    return `
        <tr class="group hover:bg-slate-50 transition">
            <td class="px-6 py-4 text-center text-sm text-slate-500">${displayNumber}</td>
            <td class="px-6 py-4 text-center">
                <div class="text-sm font-medium text-slate-900">${programCode}</div>
                <div class="text-xs text-slate-500">${programDegree}${programDegree && programBranch ? ' - ' : ''}${programBranch}</div>
            </td>
            <td class="px-6 py-4 text-center font-mono font-bold text-blue-600">${courseCode}</td>
            <td class="px-6 py-4 text-center text-slate-700">${courseTitle}</td>
            <td class="px-6 py-4 text-center">
                <span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold">${year}</span>
            </td>
            <td class="px-6 py-4 text-center">
                <span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold">${sem}</span>
            </td>
            <td class="px-6 py-4 text-center font-semibold">${credit}</td>
            <td class="px-6 py-4 text-center">
                <button onclick='manageSyllabus(${course.id}, ${JSON.stringify(course.course_code || '')})' class="p-2 ${syllabusClass} rounded-lg transition" title="Manage Syllabus">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </button>
            </td>
            <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="editCourse(${course.id})" class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition" title="Edit">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                        </svg>
                    </button>
                    <button onclick='confirmDelete(${course.id}, ${JSON.stringify(course.course_code || '')})' class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition" title="Delete">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

function renderCourseSearchPagination(totalResults, page, perPage) {
    const paginationContainer = document.getElementById('coursePagination');
    if (!paginationContainer) return;

    const totalPages = Math.max(1, Math.ceil(totalResults / perPage));
    const start = totalResults === 0 ? 0 : ((page - 1) * perPage) + 1;
    const end = totalResults === 0 ? 0 : Math.min(page * perPage, totalResults);

    paginationContainer.innerHTML = `
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p id="courseResultsSummary" class="text-sm text-slate-600">
                Showing <span class="font-medium">${start}</span> to
                <span class="font-medium">${end}</span> of
                <span class="font-medium">${totalResults}</span> results
            </p>
            <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                    <label class="text-sm text-slate-600">Items per page:</label>
                    <select id="perPageSelect" class="p-1.5 border border-slate-200 rounded-lg text-sm">
                        <option value="10"${perPage === 10 ? ' selected' : ''}>10</option>
                        <option value="20"${perPage === 20 ? ' selected' : ''}>20</option>
                        <option value="50"${perPage === 50 ? ' selected' : ''}>50</option>
                        <option value="100"${perPage === 100 ? ' selected' : ''}>100</option>
                    </select>
                </div>
                ${totalPages > 1 ? `
                <nav class="flex gap-1">
                    <button type="button" data-course-search-page="${Math.max(1, page - 1)}" ${page <= 1 ? 'disabled' : ''} class="px-3 py-1 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition disabled:opacity-50 disabled:cursor-not-allowed">Previous</button>
                    <span class="px-3 py-1 bg-blue-600 text-white rounded-lg">${page}</span>
                    <button type="button" data-course-search-page="${Math.min(totalPages, page + 1)}" ${page >= totalPages ? 'disabled' : ''} class="px-3 py-1 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
                </nav>` : ''}
            </div>
        </div>
    `;

    attachSearchPaginationHandlers();
    attachSearchPerPageHandler();
}

function restoreCourseServerView() {
    const tableBody = document.getElementById('courseTableBody');
    const paginationContainer = document.getElementById('coursePagination');
    const summary = document.getElementById('courseResultsSummary');

    if (tableBody && courseSearchState.serverRowsHtml) tableBody.innerHTML = courseSearchState.serverRowsHtml;
    if (paginationContainer && courseSearchState.serverPaginationHtml) paginationContainer.innerHTML = courseSearchState.serverPaginationHtml;
    if (summary && courseSearchState.serverSummaryHtml) summary.innerHTML = courseSearchState.serverSummaryHtml;

    courseSearchState.active = false;
    courseSearchState.term = '';
    courseSearchState.page = 1;
    attachSearchPaginationHandlers();
    attachSearchPerPageHandler();
}

function renderCourseSearchResults() {
    const tableBody = document.getElementById('courseTableBody');
    const searchInput = document.getElementById('searchInput');
    if (!tableBody || !searchInput) return;

    const searchTerm = searchInput.value.trim().toLowerCase();
    const allCourses = getCourseSearchData();
    const perPage = Number(document.getElementById('perPageSelect')?.value || courseSearchState.perPage || 10);

    courseSearchState.perPage = perPage;

    if (!searchTerm) {
        restoreCourseServerView();
        return;
    }

    const filtered = allCourses.filter(course => courseMatchesSearch(course, searchTerm));
    const totalResults = filtered.length;
    const totalPages = Math.max(1, Math.ceil(totalResults / perPage));
    const page = Math.min(courseSearchState.page || 1, totalPages);
    const startIndex = (page - 1) * perPage;
    const pageItems = filtered.slice(startIndex, startIndex + perPage);

    courseSearchState.active = true;
    courseSearchState.term = searchTerm;
    courseSearchState.page = page;

    if (pageItems.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="px-6 py-16 text-center bg-gradient-to-b from-slate-50 to-white">
                    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400 border border-slate-200">
                        <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"/>
                        </svg>
                    </div>
                    <h3 class="mt-4 text-sm font-bold text-slate-900">No courses found</h3>
                    <p class="mt-1 text-xs text-slate-400">Try a different search term.</p>
                </td>
            </tr>
        `;
    } else {
        tableBody.innerHTML = pageItems.map((course, index) => buildCourseRow(course, startIndex + index + 1)).join('');
    }

    renderCourseSearchPagination(totalResults, page, perPage);
}

function attachSearchPaginationHandlers() {
    const paginationContainer = document.getElementById('coursePagination');
    if (!paginationContainer) return;

    paginationContainer.querySelectorAll('[data-course-search-page]').forEach(button => {
        button.addEventListener('click', function() {
            courseSearchState.page = Number(this.getAttribute('data-course-search-page')) || 1;
            renderCourseSearchResults();
        });
    });
}

function attachSearchPerPageHandler() {
    const perPageSelect = document.getElementById('perPageSelect');
    if (!perPageSelect) return;

    perPageSelect.onchange = function() {
        if (courseSearchState.active) {
            courseSearchState.page = 1;
            renderCourseSearchResults();
            return;
        }

        const url = new URL(window.location.href);
        url.searchParams.set('per_page', this.value);
        url.searchParams.delete('page');
        window.location.href = url.toString();
    };
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('courseTableBody');
    const paginationContainer = document.getElementById('coursePagination');
    const summary = document.getElementById('courseResultsSummary');

    if (!searchInput || !tableBody || !paginationContainer || !summary) return;

    courseSearchState.serverRowsHtml = tableBody.innerHTML;
    courseSearchState.serverPaginationHtml = paginationContainer.innerHTML;
    courseSearchState.serverSummaryHtml = summary.innerHTML;

    let searchTimer = null;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            courseSearchState.page = 1;
            renderCourseSearchResults();
        }, 250);
    });

    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            clearTimeout(searchTimer);
            courseSearchState.page = 1;
            renderCourseSearchResults();
        }
    });

    attachSearchPaginationHandlers();
    attachSearchPerPageHandler();
}

// Enable filters only after all dropdown values are selected
function initializeFilterSubmitState() {
    const form = document.getElementById('filterForm');
    const applyFiltersBtn = document.getElementById('courseApplyFiltersBtn');

    if (!applyFiltersBtn || !form) return;

    const hiddenInputIds = [
        'yearValue', 'progTypeValue', 'progCategoryValue', 'degreeValue',
        'branchValue', 'programValue', 'semValue', 'partValue',
        'courseCategoryValue', 'courseTitleValue'
    ];
    const hiddenInputs = hiddenInputIds
        .map(id => document.getElementById(id))
        .filter(Boolean);
    const selects = Array.from(form.querySelectorAll('select'));

    const updateApplyButtonState = () => {
        const controls = hiddenInputs.length > 0 ? hiddenInputs : selects;
        const allSelected = controls.length > 0 && controls.every(control => control.value && control.value !== '');
        applyFiltersBtn.disabled = !allSelected;
    };

    hiddenInputs.forEach(input => input.addEventListener('change', updateApplyButtonState));
    selects.forEach(select => select.addEventListener('change', updateApplyButtonState));
    window.updateApplyButtonState = updateApplyButtonState;
    updateApplyButtonState();
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
        if (drawerId === 'courseDrawer') {
            const fileInput = document.getElementById('courseSyllabusPdf');
            const emptyState = document.getElementById('courseSyllabusFileEmptyState');
            const selectedState = document.getElementById('courseSyllabusFileSelectedState');
            const nameDisplay = document.getElementById('courseSyllabusFileNameDisplay');
            if (fileInput && emptyState && selectedState && nameDisplay) {
                resetCourseSyllabusFileInput(fileInput, emptyState, selectedState, nameDisplay);
            }
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
            const viewBtn = document.getElementById('viewSyllabusBtn');
            const downloadBtn = document.getElementById('downloadSyllabusBtn');
            const deleteBtn = document.getElementById('deleteSyllabusBtn');
            
            if (data.course.has_syllabus) {
                statusEl.innerText = 'Syllabus Uploaded';
                messageEl.innerText = 'A syllabus PDF is available for this course.';
                viewBtn.classList.remove('hidden');
                downloadBtn.classList.remove('hidden');
                deleteBtn.classList.remove('hidden');
            } else {
                statusEl.innerText = 'No Syllabus Uploaded';
                messageEl.innerText = 'Upload a PDF syllabus for this course.';
                viewBtn.classList.add('hidden');
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

// View syllabus
function initializeViewSyllabus() {
    const viewBtn = document.getElementById('viewSyllabusBtn');
    if (viewBtn) {
        viewBtn.addEventListener('click', function() {
            if (currentSyllabusCourseId) {
                window.open(`/course-management/view-syllabus/${currentSyllabusCourseId}/`, '_blank');
            }
        });
    }
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
            if (!currentSyllabusCourseId) {
                showToast('No course selected for syllabus deletion', 'error');
                return;
            }

            if (confirm('Are you sure you want to delete this syllabus?')) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch(`/course-management/delete-syllabus/${currentSyllabusCourseId}/`, {
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
                            showToast('Syllabus deleted successfully!');
                            setTimeout(() => location.reload(), 1500);
                            closeDrawer('syllabusDrawer');
                        } else {
                            showToast(data.error || 'Error deleting syllabus', 'error');
                        }
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
    if (progressText) progressText.innerText = 'Importing records...';
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
    if (progressText) progressText.innerText = percent >= 100 ? 'Processing response...' : 'Importing records...';
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
    const message = data?.message || data?.error || '';

    if (progressContainer) progressContainer.classList.add('hidden');
    if (resultContainer) resultContainer.classList.remove('hidden');
    if (resultTitle) resultTitle.innerText = isSuccess ? 'Upload completed' : 'Upload finished with errors';
    if (resultMessage) resultMessage.innerText = message;
    if (resultIcon) {
        resultIcon.className = `p-2 rounded-lg ${isSuccess ? 'bg-green-50 text-green-600' : 'bg-rose-50 text-rose-600'}`;
        resultIcon.innerHTML = isSuccess
            ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
            : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v4m0 4h.01M10.29 3.86l-8.1 14.04A2 2 0 003.92 21h16.16a2 2 0 001.73-3.1l-8.1-14.04a2 2 0 00-3.46 0z"/></svg>';
    }
    if (successCount) successCount.innerText = String(createdCount);
    if (errorCount) errorCount.innerText = String(errors.length);
    if (errorsListContainer) errorsListContainer.classList.toggle('hidden', errors.length === 0);
    if (errorsList) {
        errorsList.innerHTML = errors.length
            ? errors.slice(0, 10).map(error => `<div class="text-rose-700 whitespace-pre-wrap">${error}</div>`).join('')
            : '';
    }
}

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
            
            const submitBtn = form.querySelector('button[type="submit"]') || document.querySelector('button[form="uploadForm"]');
            if (submitBtn) submitBtn.disabled = true;
            resetUploadFeedback();
            
            // Generate a unique upload ID
            const uploadId = 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            const formData = new FormData(this);
            formData.append('upload_id', uploadId);
            
            // Show and reset progress container
            const progressContainer = document.getElementById('uploadProgressContainer');
            const progressBar = document.getElementById('uploadProgressBar');
            const progressPercent = document.getElementById('uploadProgressPercent');
            const progressDetails = document.getElementById('uploadProgressDetails');
            
            updateUploadProgress(0);
            if (progressContainer) {
                const scrollContainer = progressContainer.closest('.overflow-y-auto');
                if (scrollContainer) {
                    setTimeout(() => {
                        scrollContainer.scrollTop = scrollContainer.scrollHeight;
                    }, 50);
                }
            }
            
            // Periodically poll the upload progress
            let pollInterval = setInterval(() => {
                fetch(`/upload-progress/?upload_id=${uploadId}`)
                    .then(res => res.json())
                    .then(progress => {
                        if (progress && progress.total > 0) {
                            const percent = Math.round((progress.current / progress.total) * 100);
                            if (progressBar) progressBar.style.width = percent + '%';
                            if (progressPercent) progressPercent.innerText = percent + '%';
                            if (progressDetails) {
                                progressDetails.innerText = `${progress.current} of ${progress.total} records uploaded`;
                            }
                        }
                    })
                    .catch(err => console.error('Error polling progress:', err));
            }, 400);
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            // Use hyphen instead of underscore
            fetch('/course-management/upload-courses/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(pollInterval);
                if (submitBtn) submitBtn.disabled = false;
                
                if (data.success) {
                    updateUploadProgress(100);
                    showUploadResult(data, true);
                    showToast(data.message || 'Courses imported successfully!');
                    setTimeout(() => location.reload(), 2500);
                } else {
                    showUploadResult(data, false);
                    showToast(data.error || 'Error uploading file', 'error');
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                if (submitBtn) submitBtn.disabled = false;
                resetUploadFeedback();
                console.error('Error:', error);
                showToast('Error uploading file', 'error');
            });
        });
    }
}

// Per page change
function initializePerPage() {
    attachSearchPerPageHandler();
}

// Clear filters
function initializeClearFilters() {
    const clearBtn = document.getElementById('clearFilters');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            const filterForm = document.getElementById('filterForm');
            if (!filterForm) return;

            filterForm.querySelectorAll('select').forEach(select => {
                if (select.tomselect) {
                    select.tomselect.setValue('');
                } else {
                    select.value = '';
                }
            });
            filterForm.querySelectorAll('input').forEach(input => {
                if (input.type !== 'hidden' || input.name !== 'csrfmiddlewaretoken') {
                    input.value = '';
                }
            });
            const searchInput = document.getElementById('searchInput');
            if (searchInput) searchInput.value = '';
            if (courseSearchState.active) {
                restoreCourseServerView();
            }
            filterForm.submit();
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
    try { initializeFileInput(); } catch (e) { console.error('Error initializing file input:', e); }
    try { initializeSyllabusFileInput(); } catch (e) { console.error('Error initializing syllabus file input:', e); }
    try { initializeCourseSyllabusFileInput(); } catch (e) { console.error('Error initializing course syllabus file input:', e); }
    try { initializeSearch(); } catch (e) { console.error('Error initializing search:', e); }
    try { initializeFilterSubmitState(); } catch (e) { console.error('Error initializing filter submit state:', e); }
    try { initializeDeleteButton(); } catch (e) { console.error('Error initializing delete button:', e); }
    try { initializeCourseForm(); } catch (e) { console.error('Error initializing course form:', e); }
    try { initializeSyllabusForm(); } catch (e) { console.error('Error initializing syllabus form:', e); }
    try { initializeUploadForm(); } catch (e) { console.error('Error initializing upload form:', e); }
    try { initializePerPage(); } catch (e) { console.error('Error initializing per page:', e); }
    try { initializeClearFilters(); } catch (e) { console.error('Error initializing clear filters:', e); }
    try { initializeEscapeKey(); } catch (e) { console.error('Error initializing escape key:', e); }
    try { initializeViewSyllabus(); } catch (e) { console.error('Error initializing view syllabus:', e); }
    try { initializeDownloadSyllabus(); } catch (e) { console.error('Error initializing download syllabus:', e); }
    try { initializeDeleteSyllabus(); } catch (e) { console.error('Error initializing delete syllabus:', e); }
});
