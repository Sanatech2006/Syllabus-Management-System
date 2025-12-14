document.addEventListener('DOMContentLoaded', function() {
    const saveBtn = document.getElementById('saveBtn');
    const confirmDialog = document.getElementById('confirmDialog');
    const cancelBtn = document.getElementById('cancelBtn');
    const confirmBtn = document.getElementById('confirmBtn');
    const courseForm = document.getElementById('courseForm');

    if (!saveBtn || !confirmDialog) return;

    // Show confirmation on Save button click
    saveBtn.addEventListener('click', function(e) {
        e.preventDefault();
        confirmDialog.classList.add('active');
    });

    // Cancel - close dialog
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            confirmDialog.classList.remove('active');
        });
    }

    // Confirm - submit form
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            courseForm.submit();
        });
    }

    // Close dialog when clicking outside
    confirmDialog.addEventListener('click', function(e) {
        if (e.target === confirmDialog) {
            confirmDialog.classList.remove('active');
        }
    });
});
