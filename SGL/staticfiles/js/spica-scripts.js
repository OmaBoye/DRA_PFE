// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Close alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Sidebar toggle functionality
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainPanel = document.querySelector('.main-panel');

    sidebar.classList.toggle('active');
    mainPanel.classList.toggle('wide');

    // Store state in localStorage
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('active'));
}

// Check for saved sidebar state on page load
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const mainPanel = document.querySelector('.main-panel');

    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('active');
        mainPanel.classList.add('wide');
    }

    // Add event listener to sidebar toggler
    const toggler = document.querySelector('.sidebar-toggler');
    if (toggler) {
        toggler.addEventListener('click', toggleSidebar);
    }
});