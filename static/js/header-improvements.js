// Header Improvements JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Mejorar la funcionalidad del dropdown
    const dropdownToggle = document.getElementById('userDropdown');
    const dropdownMenu = dropdownToggle?.nextElementSibling;
    
    if (dropdownToggle && dropdownMenu) {
        // Manejar el click en el toggle
        dropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle del dropdown
            const isOpen = dropdownMenu.classList.contains('show');
            
            // Cerrar todos los dropdowns abiertos
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
            
            // Abrir/cerrar el dropdown actual
            if (!isOpen) {
                dropdownMenu.classList.add('show');
            }
        });
        
        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', function(e) {
            if (!dropdownToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
        
        // Cerrar dropdown al presionar Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                dropdownMenu.classList.remove('show');
            }
        });
    }
    
    // Mejorar la animación del badge de puntos
    const pointsBadge = document.getElementById('nav-points');
    if (pointsBadge) {
        // Agregar efecto de hover suave
        pointsBadge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        pointsBadge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
    
    // Mejorar la responsividad del navbar
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            // Agregar clase para animación personalizada
            navbarCollapse.classList.toggle('collapsing-custom');
        });
    }
    
    // Smooth scroll para los enlaces del navbar
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            // Solo aplicar smooth scroll si es un enlace interno
            const href = this.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Mejorar la accesibilidad del header
    const userGreeting = document.querySelector('.user-greeting-container');
    if (userGreeting) {
        // Agregar atributos ARIA
        userGreeting.setAttribute('role', 'banner');
        userGreeting.setAttribute('aria-label', 'Información del usuario');
    }
    
    // Optimizar el rendimiento con throttling para eventos de scroll
    let ticking = false;
    
    function updateHeader() {
        const header = document.querySelector('.header_section');
        if (header) {
            const scrollY = window.scrollY;
            
            // Agregar sombra al header cuando se hace scroll
            if (scrollY > 10) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateHeader);
            ticking = true;
        }
    });
});

// Función para actualizar los puntos dinámicamente (si es necesario)
function updateUserPoints(newPoints) {
    const pointsBadge = document.getElementById('nav-points');
    if (pointsBadge) {
        // Formatear los puntos con separadores de miles
        const formattedPoints = new Intl.NumberFormat('es-CO').format(newPoints);
        pointsBadge.textContent = `${formattedPoints} Puntos`;
        
        // Agregar animación de actualización
        pointsBadge.classList.add('updating');
        setTimeout(() => {
            pointsBadge.classList.remove('updating');
        }, 300);
    }
}

// Función para mostrar notificaciones en el header
function showHeaderNotification(message, type = 'info') {
    const header = document.querySelector('.header_section');
    if (header) {
        const notification = document.createElement('div');
        notification.className = `header-notification ${type}`;
        notification.textContent = message;
        
        header.appendChild(notification);
        
        // Mostrar la notificación
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}