/* ========================================
   DEMO Y TESTING DEL MENÚ LATERAL MÓVIL
   ======================================== */

// Función para simular el menú lateral en desktop (solo para testing)
function enableMobileSidebarDemo() {
    console.log('🚀 Activando demo del menú lateral móvil...');
    
    // Forzar el comportamiento móvil temporalmente
    const originalWidth = window.innerWidth;
    Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768
    });
    
    // Reinicializar el menú lateral
    if (window.MobileSidebar) {
        console.log('✅ Menú lateral ya disponible');
    } else {
        // Cargar el menú lateral si no está disponible
        const script = document.createElement('script');
        script.src = '/static/js/mobile-sidebar-menu.js';
        script.onload = function() {
            console.log('✅ Menú lateral cargado correctamente');
        };
        document.head.appendChild(script);
    }
    
    // Restaurar el ancho original después de un momento
    setTimeout(() => {
        Object.defineProperty(window, 'innerWidth', {
            writable: true,
            configurable: true,
            value: originalWidth
        });
    }, 1000);
}

// Función para mostrar información del menú lateral
function showMobileSidebarInfo() {
    console.log(`
🎯 MENÚ LATERAL MÓVIL - INFORMACIÓN
=====================================

📱 Activación: Solo en pantallas < 992px
🎨 Diseño: Inspirado en YouTube
🚀 Animaciones: Suaves y profesionales
🎯 Funcionalidades:
   • Menú deslizante desde la derecha
   • Información del usuario en la parte superior
   • Navegación: ¿Qué son Puntos?, Compras Realizadas, Activa Cobertura
   • Mi Perfil y Cerrar Sesión
   • Overlay con blur
   • Animaciones escalonadas

🔧 Controles disponibles:
   • window.MobileSidebar.open() - Abrir menú
   • window.MobileSidebar.close() - Cerrar menú
   • window.MobileSidebar.updatePoints(puntos) - Actualizar puntos
   • window.MobileSidebar.showNotification(msg, tipo) - Mostrar notificación

📋 Para probar en desktop:
   • Abre las herramientas de desarrollador (F12)
   • Activa el modo responsive
   • Selecciona un dispositivo móvil
   • Recarga la página
   • Haz clic en el botón hamburguesa

🎨 Personalización:
   • CSS: /static/css/mobile-sidebar-menu.css
   • JS: /static/js/mobile-sidebar-menu.js
   • Colores principales: #31C0CA (turquesa)
   • Fondo: Gradiente negro
    `);
}

// Función para testing rápido
function testMobileSidebar() {
    if (window.MobileSidebar) {
        console.log('🧪 Iniciando test del menú lateral...');
        
        // Test 1: Abrir menú
        setTimeout(() => {
            console.log('📱 Test 1: Abriendo menú...');
            window.MobileSidebar.open();
        }, 1000);
        
        // Test 2: Mostrar notificación
        setTimeout(() => {
            console.log('🔔 Test 2: Mostrando notificación...');
            window.MobileSidebar.showNotification('¡Menú lateral funcionando correctamente!', 'success');
        }, 2000);
        
        // Test 3: Actualizar puntos
        setTimeout(() => {
            console.log('💰 Test 3: Actualizando puntos...');
            window.MobileSidebar.updatePoints(15000);
        }, 3000);
        
        // Test 4: Cerrar menú
        setTimeout(() => {
            console.log('❌ Test 4: Cerrando menú...');
            window.MobileSidebar.close();
        }, 4000);
        
        console.log('✅ Test completado. Revisa las animaciones.');
    } else {
        console.log('❌ Menú lateral no disponible. Asegúrate de estar en modo móvil.');
    }
}

// Auto-ejecutar información al cargar
document.addEventListener('DOMContentLoaded', function() {
    // Solo mostrar info en desarrollo
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        setTimeout(showMobileSidebarInfo, 1000);
    }
});

// Exportar funciones para uso en consola
window.MobileSidebarDemo = {
    enable: enableMobileSidebarDemo,
    info: showMobileSidebarInfo,
    test: testMobileSidebar
};

// Atajos de teclado para testing (solo en desarrollo)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('keydown', function(e) {
        // Ctrl + Shift + M = Abrir menú lateral
        if (e.ctrlKey && e.shiftKey && e.key === 'M') {
            e.preventDefault();
            if (window.MobileSidebar) {
                window.MobileSidebar.open();
            } else {
                console.log('💡 Tip: Activa el modo responsive para probar el menú lateral');
            }
        }
        
        // Ctrl + Shift + T = Test completo
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            testMobileSidebar();
        }
    });
    
    console.log(`
🎮 ATAJOS DE TECLADO DISPONIBLES:
• Ctrl + Shift + M = Abrir menú lateral
• Ctrl + Shift + T = Test completo
    `);
}