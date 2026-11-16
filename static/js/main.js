// SMART LOST & FOUND - Main Client JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Image Upload Preview Handler
    const imageInput = document.getElementById('imageUploadInput');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');

    if (imageInput && imagePreview && uploadPlaceholder) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                // File size check (5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size exceeds the 5MB limit. Please upload a smaller image.');
                    this.value = '';
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.classList.remove('d-none');
                    uploadPlaceholder.classList.add('d-none');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 3. Clear Filter Helper
    const clearFilterBtn = document.getElementById('clearFiltersBtn');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', function () {
            const form = clearFilterBtn.closest('form');
            if (form) {
                const inputs = form.querySelectorAll('input, select');
                inputs.forEach(input => {
                    if (input.type === 'text') input.value = '';
                    if (input.tagName.toLowerCase() === 'select') input.selectedIndex = 0;
                });
                form.submit();
            }
        });
    }

    // 4. Auto-dismiss flash messages after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });
});
