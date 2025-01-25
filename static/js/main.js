// Main JavaScript file for Math Fluency app
document.addEventListener('DOMContentLoaded', function() {
    // Handle bulk upload section collapse
    const bulkUploadSection = document.getElementById('bulkUploadSection');
    if (bulkUploadSection) {
        bulkUploadSection.addEventListener('show.bs.collapse', function() {
            const icon = document.querySelector('[data-bs-target="#bulkUploadSection"] .collapse-icon');
            if (icon) {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        });

        bulkUploadSection.addEventListener('hide.bs.collapse', function() {
            const icon = document.querySelector('[data-bs-target="#bulkUploadSection"] .collapse-icon');
            if (icon) {
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
    }
});
