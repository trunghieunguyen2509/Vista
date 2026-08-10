// Site-wide: app shell (sidebar collapse, user menu dropdown, mobile nav) plus toast auto-dismiss on every page

const sidebar = document.getElementById('app-sidebar');
const sidebarToggle = document.getElementById('app-sidebar-collapse');

if (sidebar && sidebarToggle) {
    if (localStorage.getItem('adminSidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }

    sidebarToggle.addEventListener('click', () => {
        const collapsed = sidebar.classList.toggle('collapsed');
        localStorage.setItem('adminSidebarCollapsed', String(collapsed));
    });
}

const userMenuTrigger = document.getElementById('app-user-menu-trigger');
const userMenuPanel = document.getElementById('app-user-menu-panel');

if (userMenuTrigger && userMenuPanel) {
    userMenuTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = !userMenuPanel.hidden;
        userMenuPanel.hidden = isOpen;
        userMenuTrigger.setAttribute('aria-expanded', String(!isOpen));
    });

    document.addEventListener('click', (e) => {
        if (!document.getElementById('app-user-menu').contains(e.target)) {
            userMenuPanel.hidden = true;
            userMenuTrigger.setAttribute('aria-expanded', 'false');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            userMenuPanel.hidden = true;
            userMenuTrigger.setAttribute('aria-expanded', 'false');
        }
    });
}

const mobileMenuToggle = document.getElementById('app-sidebar-toggle');
const sidebarBackdrop = document.getElementById('app-sidebar-backdrop');

if (sidebar && mobileMenuToggle && sidebarBackdrop) {
    const closeMobileMenu = () => {
        sidebar.classList.remove('mobile-open');
        sidebarBackdrop.classList.remove('mobile-open');
    };

    mobileMenuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('mobile-open');
        sidebarBackdrop.classList.toggle('mobile-open');
    });

    sidebarBackdrop.addEventListener('click', closeMobileMenu);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeMobileMenu();
    });
}

document.querySelectorAll('.app-toast').forEach((toast) => {
    const dismiss = () => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
    };

    const closeBtn = toast.querySelector('.app-toast-close');
    if (closeBtn) closeBtn.addEventListener('click', dismiss);

    setTimeout(dismiss, 6000);
});
