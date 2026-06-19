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

const programSearchState = {
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

function getProgramSearchData() {
    if (programSearchState.data.length > 0) return programSearchState.data;
    const dataElement = document.getElementById('program-search-data');
    if (!dataElement) return [];

    try {
        programSearchState.data = JSON.parse(dataElement.textContent || '[]');
    } catch (error) {
        console.error('Error parsing program search data:', error);
        programSearchState.data = [];
    }

    return programSearchState.data;
}

function programMatchesSearch(program, searchTerm) {
    if (!searchTerm) return true;
    const lowered = searchTerm.toLowerCase();
    return [
        program.prog_code,
        program.degree,
        program.branch,
        program.prog_type,
        program.prog_category,
    ].some(value => String(value ?? '').toLowerCase().includes(lowered));
}

function buildProgramRow(program, displayNumber) {
    const typeBadge = program.prog_type === 'UG'
        ? '<span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-green-50 text-green-700 text-xs font-semibold">UG</span>'
        : '<span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-yellow-50 text-yellow-700 text-xs font-semibold">PG</span>';

    const categoryBadge = program.prog_category === 'Arts'
        ? '<span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-pink-50 text-pink-700 text-xs font-semibold">Arts</span>'
        : '<span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold">Science</span>';

    return `
        <tr class="group hover:bg-slate-50 transition">
            <td class="px-6 py-4 text-center text-sm text-slate-500 whitespace-nowrap">${displayNumber}</td>
            <td class="px-6 py-4 text-center whitespace-nowrap">${typeBadge}</td>
            <td class="px-6 py-4 text-center whitespace-nowrap">${categoryBadge}</td>
            <td class="px-6 py-4 text-center font-medium text-slate-900 whitespace-nowrap">${escapeHtml(program.degree)}</td>
            <td class="px-6 py-4 text-center text-slate-600 whitespace-nowrap">${escapeHtml(program.branch)}</td>
            <td class="px-6 py-4 text-center font-mono font-bold text-blue-600 whitespace-nowrap">${escapeHtml(program.prog_code)}</td>
            <td class="px-6 py-4 text-center whitespace-nowrap">
                <div class="flex items-center justify-center gap-2">
                    <button onclick="editProgram(${program.id})" class="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition" title="Edit">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                        </svg>
                    </button>
                    <button onclick="confirmDelete(${program.id}, ${JSON.stringify(program.prog_code || '')})" class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition" title="Delete">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

function renderProgramPagination(totalResults, page, perPage) {
    const paginationContainer = document.getElementById('programPagination');
    if (!paginationContainer) return;

    const totalPages = Math.max(1, Math.ceil(totalResults / perPage));
    const start = totalResults === 0 ? 0 : ((page - 1) * perPage) + 1;
    const end = totalResults === 0 ? 0 : Math.min(page * perPage, totalResults);

    paginationContainer.innerHTML = `
        <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p id="programResultsSummary" class="text-sm text-slate-600">
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
                        <option value="all"${String(perPage) === 'all' ? ' selected' : ''}>All</option>
                    </select>
                </div>
                ${totalPages > 1 ? `
                <nav class="flex gap-1">
                    <button type="button" data-program-search-page="${Math.max(1, page - 1)}" ${page <= 1 ? 'disabled' : ''} class="px-3 py-1 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition disabled:opacity-50 disabled:cursor-not-allowed">Previous</button>
                    <span class="px-3 py-1 bg-blue-600 text-white rounded-lg">${page}</span>
                    <button type="button" data-program-search-page="${Math.min(totalPages, page + 1)}" ${page >= totalPages ? 'disabled' : ''} class="px-3 py-1 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition disabled:opacity-50 disabled:cursor-not-allowed">Next</button>
                </nav>` : ''}
            </div>
        </div>
    `;

    attachProgramPaginationHandlers();
    attachProgramPerPageHandler();
}

function restoreProgramServerView() {
    const tableBody = document.getElementById('programTableBody');
    const paginationContainer = document.getElementById('programPagination');
    const summary = document.getElementById('programResultsSummary');

    if (tableBody && programSearchState.serverRowsHtml) tableBody.innerHTML = programSearchState.serverRowsHtml;
    if (paginationContainer && programSearchState.serverPaginationHtml) paginationContainer.innerHTML = programSearchState.serverPaginationHtml;
    if (summary && programSearchState.serverSummaryHtml) summary.innerHTML = programSearchState.serverSummaryHtml;

    programSearchState.active = false;
    programSearchState.term = '';
    programSearchState.page = 1;
    attachProgramPaginationHandlers();
    attachProgramPerPageHandler();
}

function renderProgramSearchResults() {
    const tableBody = document.getElementById('programTableBody');
    const searchInput = document.getElementById('searchInput');
    if (!tableBody || !searchInput) return;

    const searchTerm = searchInput.value.trim().toLowerCase();
    const allPrograms = getProgramSearchData();
    let perPageValue = document.getElementById('perPageSelect')?.value || programSearchState.perPage || 10;
    const perPage = perPageValue === 'all' ? allPrograms.length || 1 : Number(perPageValue);

    programSearchState.perPage = perPage;

    if (!searchTerm) {
        restoreProgramServerView();
        return;
    }

    const filtered = allPrograms.filter(program => programMatchesSearch(program, searchTerm));
    const totalResults = filtered.length;
    const totalPages = Math.max(1, Math.ceil(totalResults / perPage));
    const page = Math.min(programSearchState.page || 1, totalPages);
    const startIndex = (page - 1) * perPage;
    const pageItems = filtered.slice(startIndex, startIndex + perPage);

    programSearchState.active = true;
    programSearchState.term = searchTerm;
    programSearchState.page = page;

    if (pageItems.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-12 text-center">
                    <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                    </div>
                    <h3 class="mt-4 text-sm font-bold text-slate-900">No programs found</h3>
                    <p class="mt-1 text-xs text-slate-400">Try a different search term.</p>
                </td>
            </tr>
        `;
    } else {
        tableBody.innerHTML = pageItems.map((program, index) => buildProgramRow(program, startIndex + index + 1)).join('');
    }

    renderProgramPagination(totalResults, page, perPage);
}

function attachProgramPaginationHandlers() {
    const paginationContainer = document.getElementById('programPagination');
    if (!paginationContainer) return;

    paginationContainer.querySelectorAll('[data-program-search-page]').forEach(button => {
        button.addEventListener('click', function() {
            programSearchState.page = Number(this.getAttribute('data-program-search-page')) || 1;
            renderProgramSearchResults();
        });
    });
}

function attachProgramPerPageHandler() {
    const perPageSelect = document.getElementById('perPageSelect');
    if (!perPageSelect) return;

    perPageSelect.onchange = function() {
        if (programSearchState.active) {
            programSearchState.page = 1;
            renderProgramSearchResults();
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
    const tableBody = document.getElementById('programTableBody');
    const paginationContainer = document.getElementById('programPagination');
    const summary = document.getElementById('programResultsSummary');

    if (!searchInput || !tableBody || !paginationContainer || !summary) return;

    programSearchState.serverRowsHtml = tableBody.innerHTML;
    programSearchState.serverPaginationHtml = paginationContainer.innerHTML;
    programSearchState.serverSummaryHtml = summary.innerHTML;

    let searchTimer = null;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            programSearchState.page = 1;
            renderProgramSearchResults();
        }, 250);
    });

    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            clearTimeout(searchTimer);
            programSearchState.page = 1;
            renderProgramSearchResults();
        }
    });

    attachProgramPaginationHandlers();
    attachProgramPerPageHandler();
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
    const degreeInput = document.getElementById('programDegree');
    const branchInput = document.getElementById('programBranch');
    if (degreeInput) degreeInput.value = '';
    if (branchInput) branchInput.value = '';
    const drawerTitle = document.getElementById('drawer-title');
    if (drawerTitle) drawerTitle.innerText = 'New Program';
    const drawerSubtitle = document.getElementById('drawer-subtitle');
    if (drawerSubtitle) drawerSubtitle.innerHTML = 'Fields marked with <span class="text-rose-500 font-bold">*</span> are required.';
}

// Edit program function
function editProgram(programId) {

    fetch(`/programs/get-program/${programId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Set the hidden ID field
                document.getElementById('editProgramId').value = data.program.id;
                
                // Set the form field values (using the NEW IDs)
                document.getElementById('progType').value = data.program.prog_type;
                document.getElementById('progCategory').value = data.program.prog_category;
                document.getElementById('programDegree').value = data.program.degree || '';
                document.getElementById('programBranch').value = data.program.branch || '';
                document.getElementById('progCode').value = data.program.prog_code;
                
                // Update drawer title and subtitle
                document.getElementById('drawer-title').innerText = 'Edit Program';
                document.getElementById('drawer-subtitle').innerHTML = 'Update program information below.';
                
                // Open the drawer
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
                
                fetch(`/programs/delete/${currentDeleteProgramId}/`, {
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
            const url = programId ? `/programs/edit/${programId}/` : '/programs/add/';
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
            
            const submitBtn = form.querySelector('button[type="submit"]') || document.querySelector('button[form="uploadForm"]');
            if (submitBtn) submitBtn.disabled = true;
            
            // Generate a unique upload ID
            const uploadId = 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            const formData = new FormData(this);
            formData.append('upload_id', uploadId);
            
            // Show and reset progress container
            const progressContainer = document.getElementById('uploadProgressContainer');
            const progressBar = document.getElementById('uploadProgressBar');
            const progressPercent = document.getElementById('uploadProgressPercent');
            const progressDetails = document.getElementById('uploadProgressDetails');
            
            if (progressContainer) {
                progressContainer.classList.remove('hidden');
                // Scroll container to bottom to show progress bar
                const scrollContainer = progressContainer.closest('.overflow-y-auto');
                if (scrollContainer) {
                    setTimeout(() => {
                        scrollContainer.scrollTop = scrollContainer.scrollHeight;
                    }, 50);
                }
            }
            if (progressBar) progressBar.style.width = '0%';
            if (progressPercent) progressPercent.innerText = '0%';
            if (progressDetails) progressDetails.innerText = '0 of 0 records uploaded';
            
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
            
            fetch('/programs/upload-programs/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(pollInterval);
                if (submitBtn) submitBtn.disabled = false;
                
                if (data.success) {
                    if (progressBar) progressBar.style.width = '100%';
                    if (progressPercent) progressPercent.innerText = '100%';
                    
                    showToast(data.message || 'Programs imported successfully!');
                    setTimeout(() => location.reload(), 2000);
                    closeDrawer('uploadDrawer');
                } else {
                    if (progressContainer) progressContainer.classList.add('hidden');
                    showToast(data.error || 'Error uploading file', 'error');
                }
            })
            .catch(error => {
                clearInterval(pollInterval);
                if (submitBtn) submitBtn.disabled = false;
                if (progressContainer) progressContainer.classList.add('hidden');
                console.error('Error:', error);
                showToast('Error uploading file', 'error');
            });
        });
    }
}

// Per page change
function initializePerPage() {
    attachProgramPerPageHandler();
}

// Clear filters
function initializeClearFilters() {
    const clearBtn = document.getElementById('clearFilters');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.querySelectorAll('#filterForm select').forEach(select => select.value = '');
            const searchInput = document.getElementById('searchInput');
            if (searchInput) searchInput.value = '';
            if (programSearchState.active) {
                restoreProgramServerView();
            }
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
    try { initializeFileInput(); } catch (e) { console.error('Error initializing file input:', e); }
    try { initializeSearch(); } catch (e) { console.error('Error initializing search:', e); }
    try { initializeDeleteButton(); } catch (e) { console.error('Error initializing delete button:', e); }
    try { initializeProgramForm(); } catch (e) { console.error('Error initializing program form:', e); }
    try { initializeUploadForm(); } catch (e) { console.error('Error initializing upload form:', e); }
    try { initializePerPage(); } catch (e) { console.error('Error initializing per page:', e); }
    try { initializeClearFilters(); } catch (e) { console.error('Error initializing clear filters:', e); }
    try { initializeEscapeKey(); } catch (e) { console.error('Error initializing escape key:', e); }
});
