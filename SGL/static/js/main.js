document.addEventListener('DOMContentLoaded', function() {
    // ==================== Sidebar Functionality ====================
    const sidebar = document.querySelector('.sidebar');
    const sidebarTogglers = document.querySelectorAll('.sidebar-toggle');
    const body = document.body;

    // Toggle sidebar state
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));

        // Update toggle button icon
        const icons = document.querySelectorAll('.sidebar-toggle i');
        icons.forEach(icon => {
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-chevron-right');
        });
    }

    // Initialize sidebar state
    function initSidebar() {
        // Check localStorage for collapsed state
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('collapsed');
            body.classList.add('sidebar-collapsed');

            // Set correct icon if collapsed
            const icons = document.querySelectorAll('.sidebar-toggle i');
            icons.forEach(icon => {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-chevron-right');
            });
        }

        // Add click event to all toggle buttons
        sidebarTogglers.forEach(toggler => {
            toggler.addEventListener('click', function(e) {
                e.preventDefault();
                toggleSidebar();
            });
        });

        // Set active menu item
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
                if (sidebar.classList.contains('collapsed')) {
                    link.scrollIntoView({ block: 'center' });
                }
            }
        });

        // Add hover tooltips for collapsed state
        if (window.innerWidth > 768) {
            const navItems = document.querySelectorAll('.nav-item');

            navItems.forEach(item => {
                const link = item.querySelector('.nav-link');

                item.addEventListener('mouseenter', () => {
                    if (sidebar.classList.contains('collapsed')) {
                        const tooltip = document.createElement('div');
                        tooltip.className = 'sidebar-tooltip';
                        tooltip.textContent = link.querySelector('.nav-text').textContent;
                        item.appendChild(tooltip);

                        const rect = item.getBoundingClientRect();
                        tooltip.style.left = `${rect.width + 10}px`;
                        tooltip.style.top = `${rect.height/2 - tooltip.offsetHeight/2}px`;
                    }
                });

                item.addEventListener('mouseleave', () => {
                    const tooltip = item.querySelector('.sidebar-tooltip');
                    if (tooltip) tooltip.remove();
                });
            });
        }
    }

    // ==================== Alert Management ====================
    function initAlerts() {
        const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        });
    }

    // ==================== Dropdown Menus ====================
    function initDropdowns() {
        document.querySelectorAll('.dropdown-toggle').forEach(dropdownToggle => {
            dropdownToggle.addEventListener('click', function(e) {
                e.preventDefault();
                const dropdownMenu = this.nextElementSibling;
                dropdownMenu.classList.toggle('show');
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.matches('.dropdown-toggle') && !e.target.closest('.dropdown-menu')) {
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });
    }

    // ==================== Dashboard Layout ====================
    function adjustDashboardLayout() {
        const dashboard = document.querySelector('.dashboard-grid');
        if (!dashboard) return;

        // Calculate available space
        const availableHeight = window.innerHeight - 200;
        const cards = dashboard.querySelectorAll('.dashboard-card');

        // Set card heights
        cards.forEach(card => {
            const content = card.querySelector('.card-content') || card;
            const header = card.querySelector('.card-header');
            const body = card.querySelector('.card-body');

            if (header && body) {
                const headerHeight = header.offsetHeight;
                const remainingHeight = (availableHeight / 3) - headerHeight - 40;
                body.style.minHeight = `${Math.max(remainingHeight, 200)}px`;
            }
        });

        // Adjust chart containers
        const charts = document.querySelectorAll('.chart-container');
        charts.forEach(chart => {
            const card = chart.closest('.dashboard-card');
            if (card) {
                const cardHeight = card.offsetHeight;
                chart.style.height = `${cardHeight - 100}px`;
            }
        });
    }

    // ==================== Table Enhancements ====================
    function enhanceTables() {
        document.querySelectorAll('.table-spacing').forEach(table => {
            const rows = table.querySelectorAll('tr:not(:first-child)');
            rows.forEach(row => {
                row.style.marginBottom = '12px';
                row.style.display = 'table-row';
            });
        });
    }

    // ==================== Helper Functions ====================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ==================== Initialize Everything ====================
    function initAll() {
        initSidebar();
        initAlerts();
        initDropdowns();
        adjustDashboardLayout();
        enhanceTables();

        // Add smooth transitions to cards
        document.querySelectorAll('.dashboard-card').forEach(card => {
            card.style.transition = 'all 0.3s ease';
        });
    }

    // Run initializations
    initAll();

    // Resize event listeners
    window.addEventListener('resize', function() {
        adjustDashboardLayout();
    });
});
// Initialize form validation and enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Add required field markers
    document.querySelectorAll('form').forEach(form => {
        form.querySelectorAll('[required]').forEach(field => {
            const label = form.querySelector(`label[for="${field.id}"]`);
            if (label) {
                label.classList.add('required');
            }
        });
    });

    // Phone number validation and formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9+]/g, '');
        });
    });

    // Date validation (must be in the past)
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();

            if (selectedDate > today) {
                this.setCustomValidity('La date doit être dans le passé');
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Initialize Choices.js for select elements
    if (typeof Choices !== 'undefined') {
        const selectElements = document.querySelectorAll('select:not([multiple])');
        selectElements.forEach(select => {
            new Choices(select, {
                removeItemButton: true,
                searchEnabled: true,
                placeholder: true,
                placeholderValue: 'Sélectionner...',
                noResultsText: 'Aucun résultat trouvé',
                itemSelectText: 'Cliquer pour sélectionner',
                classNames: {
                    containerInner: 'choices__inner',
                    input: 'choices__input',
                    item: 'choices__item',
                    button: 'choices__button'
                }
            });
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();

                // Scroll to first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });

                    // Focus the first invalid field
                    setTimeout(() => {
                        firstInvalid.focus();
                    }, 300);
                }
            }

            form.classList.add('was-validated');
        }, false);

        // Real-time validation on blur
        form.querySelectorAll('.form-control, .form-select').forEach(input => {
            input.addEventListener('blur', function() {
                if (form.classList.contains('was-validated')) {
                    this.classList.add('was-validated');
                    this.reportValidity();
                }
            });
        });
    });

    // File input preview (for QR code)
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Aucun fichier sélectionné';
            const label = this.nextElementSibling;
            if (label && label.classList.contains('input-group-text')) {
                label.textContent = fileName;
            }
        });
    });
});