/* ========================================
   INICIALIZADOR GLOBAL DEL MENÚ LATERAL
   ======================================== */

// Función para inicializar el menú lateral en cualquier página
function initMobileSidebar() {
    // Solo en móvil
    if (window.innerWidth >= 992) return;
    
    // Verificar si ya está inicializado
    if (document.getElementById('mobileSidebar')) return;
    
    // Cargar el CSS si no está cargado
    if (!document.querySelector('link[href*="mobile-sidebar-menu.css"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/css/mobile-sidebar-menu.css';
        document.head.appendChild(link);
    }
    
    // Cargar el JavaScript si no está cargado
    if (!window.MobileSidebar) {
        const script = document.createElement('script');
        script.src = '/static/js/mobile-sidebar-menu.js';
        script.onload = function() {
            console.log('Menú lateral móvil inicializado correctamente');
        };
        document.head.appendChild(script);
    }
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileSidebar);
} else {
    initMobileSidebar();
}

// Re-inicializar en cambios de tamaño de ventana
window.addEventListener('resize', function() {
    if (window.innerWidth < 992 && !document.getElementById('mobileSidebar')) {
        initMobileSidebar();
    }
});

// Exportar para uso manual si es necesario
window.initMobileSidebar = initMobileSidebar;