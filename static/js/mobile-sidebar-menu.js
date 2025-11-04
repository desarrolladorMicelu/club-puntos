/* ========================================
   JAVASCRIPT PARA MENÚ LATERAL MÓVIL
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {
    // Solo ejecutar en móvil
    if (window.innerWidth >= 992) return;
    
    // Crear el menú lateral si no existe
    createMobileSidebar();
    
    // Configurar event listeners
    setupMobileSidebarEvents();
    
    // Ocultar el navbar collapse original en móvil
    hideMobileNavbarCollapse();
});

function createMobileSidebar() {
    // Verificar si ya existe
    if (document.getElementById('mobileSidebar')) return;
    
    // DETECTAR SI EL USUARIO ESTÁ LOGUEADO
    const userGreeting = document.querySelector('.user-greeting-container .fw-bold1');
    const userPoints = document.querySelector('#nav-points');
    const loginButton = document.querySelector('.login-button');
    const isLoggedIn = userGreeting && userPoints && !loginButton;
    
    console.log('Estado de login:', isLoggedIn ? 'Logueado' : 'No logueado');
    
    // Obtener la página actual para marcar el item activo
    const currentPath = window.location.pathname;
    
    let sidebarHTML;
    
    if (isLoggedIn) {
        // USUARIO LOGUEADO - Menú completo
        const userName = userGreeting.textContent.replace('Hola ', '').replace(', tienes', '').trim();
        const points = userPoints.textContent.trim();
        
        sidebarHTML = `
            <!-- Overlay -->
            <div class="mobile-sidebar-overlay" id="mobileSidebarOverlay"></div>
            
            <!-- Menú Lateral -->
            <div class="mobile-sidebar" id="mobileSidebar">
                <!-- Header del sidebar -->
                <div class="mobile-sidebar-header">
                    <button class="mobile-sidebar-close" id="mobileSidebarClose">
                        <i class="fas fa-times"></i>
                    </button>
                    
                    <div class="mobile-sidebar-logo">
                        <img src="${document.querySelector('.navbar-brand img').src}" alt="Logo">
                        <span class="mobile-sidebar-logo-text">Micelu.co</span>
                    </div>
                    
                    <div class="mobile-sidebar-user-info">
                        <div class="mobile-sidebar-user-greeting">
                            <i class="fas fa-user"></i>
                            <span class="mobile-sidebar-user-name">Hola ${userName}</span>
                        </div>
                        <div class="mobile-sidebar-points">${points}</div>
                    </div>
                </div>
                
                <!-- Contenido del sidebar -->
                <div class="mobile-sidebar-content">
                    <!-- Navegación Principal -->
                    <div class="mobile-sidebar-section">
                        <div class="mobile-sidebar-section-title">Navegación</div>
                        ${generateNavigationItems(currentPath)}
                    </div>
                    
                    <!-- Sección de Usuario -->
                    <div class="mobile-sidebar-section mobile-sidebar-user-section">
                        <div class="mobile-sidebar-section-title">Mi Cuenta</div>
                        <a href="/miperfil" class="mobile-sidebar-item ${currentPath === '/miperfil' ? 'active' : ''}">
                            <i class="fas fa-user-circle"></i>
                            Mi Perfil
                        </a>
                        <button class="mobile-sidebar-logout" id="mobileSidebarLogout">
                            <i class="fas fa-sign-out-alt"></i>
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // USUARIO NO LOGUEADO - Menú simple
        sidebarHTML = `
            <!-- Overlay -->
            <div class="mobile-sidebar-overlay" id="mobileSidebarOverlay"></div>
            
            <!-- Menú Lateral -->
            <div class="mobile-sidebar" id="mobileSidebar">
                <!-- Header del sidebar -->
                <div class="mobile-sidebar-header">
                    <button class="mobile-sidebar-close" id="mobileSidebarClose">
                        <i class="fas fa-times"></i>
                    </button>
                    
                    <div class="mobile-sidebar-logo">
                        <img src="${document.querySelector('.navbar-brand img').src}" alt="Logo">
                        <span class="mobile-sidebar-logo-text">Micelu.co</span>
                    </div>
                </div>
                
                <!-- Contenido del sidebar -->
                <div class="mobile-sidebar-content">
                    <!-- Navegación Principal -->
                    <div class="mobile-sidebar-section">
                        <div class="mobile-sidebar-section-title">Navegación</div>
                        ${generatePublicNavigationItems(currentPath)}
                    </div>
                    
                    <!-- Sección de Login -->
                    <div class="mobile-sidebar-section mobile-sidebar-user-section">
                        <div class="mobile-sidebar-section-title">Acceso</div>
                        <a href="/iniciosesion" class="mobile-sidebar-item cobertura-item">
                            <i class="fas fa-sign-in-alt"></i>
                            Iniciar Sesión
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Insertar en el DOM
    document.body.insertAdjacentHTML('beforeend', sidebarHTML);
}

function generateNavigationItems(currentPath) {
    const navigationItems = [
        { href: '/quesonpuntos', icon: 'fas fa-question-circle', text: '¿Qué son Puntos?', paths: ['/quesonpuntos', '/homepuntos'] },
        { href: '/mhistorialcompras', icon: 'fas fa-shopping-cart', text: 'Compras Realizadas', paths: ['/mhistorialcompras'] },
        { href: '/cobertura', icon: 'fas fa-shield-alt', text: 'Activa Cobertura', paths: ['/cobertura'], special: 'cobertura-item' }
    ];
    
    return navigationItems.map(item => {
        const isActive = item.paths.includes(currentPath);
        const specialClass = item.special ? ` ${item.special}` : '';
        const activeClass = isActive ? ' active' : '';
        
        return `
            <a href="${item.href}" class="mobile-sidebar-item${specialClass}${activeClass}">
                <i class="${item.icon}"></i>
                ${item.text}
            </a>
        `;
    }).join('');
}

function generatePublicNavigationItems(currentPath) {
    const publicNavigationItems = [
        { href: '/homepuntos', icon: 'fas fa-home', text: 'Personas', paths: ['/homepuntos', '/'] },
        { href: '/redimir', icon: 'fas fa-gift', text: 'Redimir', paths: ['/redimir'] },
        { href: '/acumulapuntos', icon: 'fas fa-coins', text: 'Acumula', paths: ['/acumulapuntos'] }
    ];
    
    return publicNavigationItems.map(item => {
        const isActive = item.paths.includes(currentPath);
        const activeClass = isActive ? ' active' : '';
        
        return `
            <a href="${item.href}" class="mobile-sidebar-item${activeClass}">
                <i class="${item.icon}"></i>
                ${item.text}
            </a>
        `;
    }).join('');
}

function setupMobileSidebarEvents() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.getElementById('mobileSidebarOverlay');
    const closeBtn = document.getElementById('mobileSidebarClose');
    const logoutBtn = document.getElementById('mobileSidebarLogout');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    if (!sidebar || !overlay || !closeBtn || !navbarToggler) return;
    
    // Abrir menú al hacer click en el botón hamburguesa
    navbarToggler.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        openMobileSidebar();
    });
    
    // Cerrar menú
    closeBtn.addEventListener('click', closeMobileSidebar);
    overlay.addEventListener('click', closeMobileSidebar);
    
    // Cerrar con tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeMobileSidebar();
        }
    });
    
    // Cerrar menú al hacer click en un enlace
    const sidebarLinks = sidebar.querySelectorAll('.mobile-sidebar-item[href]');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Pequeño delay para que se vea la animación
            setTimeout(closeMobileSidebar, 150);
        });
    });
    
    // Manejar logout (solo si existe)
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            handleMobileLogout();
        });
    }
    
    // Prevenir scroll del body cuando el menú está abierto
    sidebar.addEventListener('transitionend', function() {
        if (sidebar.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    });
}

function openMobileSidebar() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.getElementById('mobileSidebarOverlay');
    
    if (sidebar && overlay) {
        sidebar.classList.add('active');
        overlay.classList.add('active');
        
        // Animar los items del menú
        const items = sidebar.querySelectorAll('.mobile-sidebar-item');
        items.forEach((item, index) => {
            item.style.animationDelay = `${0.1 + (index * 0.05)}s`;
        });
        
        // Prevenir scroll del body
        document.body.style.overflow = 'hidden';
        
        // Focus en el botón de cerrar para accesibilidad
        setTimeout(() => {
            document.getElementById('mobileSidebarClose')?.focus();
        }, 100);
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.getElementById('mobileSidebarOverlay');
    
    if (sidebar && overlay) {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        
        // Restaurar scroll del body
        document.body.style.overflow = '';
        
        // Devolver focus al botón hamburguesa
        setTimeout(() => {
            document.querySelector('.navbar-toggler')?.focus();
        }, 100);
    }
}

function hideMobileNavbarCollapse() {
    const navbarCollapse = document.getElementById('navbarSupportedContent');
    if (navbarCollapse && window.innerWidth < 992) {
        // Ocultar completamente el navbar collapse en móvil
        navbarCollapse.style.display = 'none';
        
        // Asegurar que el botón hamburguesa no active Bootstrap
        const navbarToggler = document.querySelector('.navbar-toggler');
        if (navbarToggler) {
            navbarToggler.removeAttribute('data-toggle');
            navbarToggler.removeAttribute('data-target');
            navbarToggler.removeAttribute('data-bs-toggle');
            navbarToggler.removeAttribute('data-bs-target');
        }
    }
}

function handleMobileLogout() {
    // Usar SweetAlert2 si está disponible, sino usar confirm nativo
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: '¿Cerrar sesión?',
            text: '¿Estás seguro de que deseas cerrar tu sesión?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#31C0CA',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, cerrar sesión',
            cancelButtonText: 'Cancelar',
            background: '#1a1a1a',
            color: '#ffffff'
        }).then((result) => {
            if (result.isConfirmed) {
                // Buscar el enlace de logout existente o redirigir
                const logoutLink = document.querySelector('a[href*="logout"]');
                if (logoutLink) {
                    window.location.href = logoutLink.href;
                } else {
                    window.location.href = '/logout';
                }
            }
        });
    } else {
        if (confirm('¿Estás seguro de que deseas cerrar tu sesión?')) {
            const logoutLink = document.querySelector('a[href*="logout"]');
            if (logoutLink) {
                window.location.href = logoutLink.href;
            } else {
                window.location.href = '/logout';
            }
        }
    }
}

// Función para actualizar los puntos en el sidebar
function updateMobileSidebarPoints(newPoints) {
    const sidebarPoints = document.querySelector('.mobile-sidebar-points');
    if (sidebarPoints) {
        const formattedPoints = new Intl.NumberFormat('es-CO').format(newPoints);
        sidebarPoints.textContent = `${formattedPoints} Puntos`;
        
        // Animación de actualización
        sidebarPoints.style.transform = 'scale(1.1)';
        setTimeout(() => {
            sidebarPoints.style.transform = 'scale(1)';
        }, 200);
    }
}

// Función para mostrar notificaciones en el sidebar
function showMobileSidebarNotification(message, type = 'info') {
    const sidebar = document.getElementById('mobileSidebar');
    if (!sidebar) return;
    
    const notification = document.createElement('div');
    notification.className = `mobile-sidebar-notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#31C0CA'};
        color: white;
        padding: 12px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        transform: translateY(-100%);
        opacity: 0;
        transition: all 0.3s ease;
    `;
    
    sidebar.appendChild(notification);
    
    // Mostrar notificación
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 100);
    
    // Ocultar después de 3 segundos
    setTimeout(() => {
        notification.style.transform = 'translateY(-100%)';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Manejar cambios de tamaño de ventana
window.addEventListener('resize', function() {
    if (window.innerWidth >= 992) {
        // En desktop, ocultar el sidebar si está abierto
        closeMobileSidebar();
        
        // Restaurar el navbar collapse
        const navbarCollapse = document.getElementById('navbarSupportedContent');
        if (navbarCollapse) {
            navbarCollapse.style.display = '';
        }
    } else {
        // En móvil, ocultar el navbar collapse
        hideMobileNavbarCollapse();
    }
});

// Exportar funciones para uso global
window.MobileSidebar = {
    open: openMobileSidebar,
    close: closeMobileSidebar,
    updatePoints: updateMobileSidebarPoints,
    showNotification: showMobileSidebarNotification
};