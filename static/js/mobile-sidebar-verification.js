/* ========================================
   VERIFICACIÓN DEL MENÚ LATERAL MÓVIL
   ======================================== */

// Función para verificar que todos los archivos estén correctamente cargados
function verifyMobileSidebarSetup() {
    console.log('🔍 Verificando configuración del menú lateral móvil...');
    
    const checks = {
        css: false,
        js: false,
        responsive: false,
        header: false,
        userInfo: false
    };
    
    // Verificar CSS
    const cssLink = document.querySelector('link[href*="mobile-sidebar-menu.css"]');
    if (cssLink) {
        checks.css = true;
        console.log('✅ CSS del menú lateral cargado');
    } else {
        console.log('❌ CSS del menú lateral NO encontrado');
    }
    
    // Verificar JavaScript
    if (window.MobileSidebar) {
        checks.js = true;
        console.log('✅ JavaScript del menú lateral cargado');
    } else {
        console.log('❌ JavaScript del menú lateral NO encontrado');
    }
    
    // Verificar modo responsive
    if (window.innerWidth < 992) {
        checks.responsive = true;
        console.log('✅ Modo móvil activo');
    } else {
        console.log('ℹ️ Modo desktop - El menú lateral solo funciona en móvil');
    }
    
    // Verificar header
    const header = document.querySelector('.header_section');
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (header && navbarToggler) {
        checks.header = true;
        console.log('✅ Header y botón hamburguesa encontrados');
    } else {
        console.log('❌ Header o botón hamburguesa NO encontrados');
    }
    
    // Verificar información del usuario
    const userGreeting = document.querySelector('.user-greeting-container .fw-bold1');
    const userPoints = document.querySelector('#nav-points');
    if (userGreeting && userPoints) {
        checks.userInfo = true;
        console.log('✅ Información del usuario encontrada');
        console.log(`   Usuario: ${userGreeting.textContent}`);
        console.log(`   Puntos: ${userPoints.textContent}`);
    } else {
        console.log('❌ Información del usuario NO encontrada');
    }
    
    // Resumen
    const passedChecks = Object.values(checks).filter(Boolean).length;
    const totalChecks = Object.keys(checks).length;
    
    console.log(`\n📊 RESUMEN: ${passedChecks}/${totalChecks} verificaciones pasadas`);
    
    if (passedChecks === totalChecks) {
        console.log('🎉 ¡Todo configurado correctamente!');
        return true;
    } else {
        console.log('⚠️ Hay problemas en la configuración');
        return false;
    }
}

// Función para mostrar las opciones del menú
function showMenuOptions() {
    console.log(`
📋 OPCIONES DEL MENÚ LATERAL:
============================

🏠 Navegación Principal:
   • ¿Qué son Puntos? (/quesonpuntos)
   • Compras Realizadas (/mhistorialcompras)  
   • Activa Cobertura (/cobertura) [Destacado]

👤 Sección de Usuario:
   • Mi Perfil (/miperfil)
   • Cerrar Sesión

💡 Estas opciones coinciden exactamente con el header de PC
    `);
}

// Función para probar el menú en diferentes páginas
function testMenuOnAllPages() {
    const pages = ['/quesonpuntos', '/mhistorialcompras', '/cobertura', '/miperfil'];
    
    console.log('🧪 Probando detección de página activa...');
    
    pages.forEach(page => {
        const isActive = window.location.pathname === page;
        console.log(`${isActive ? '✅' : '⚪'} ${page} ${isActive ? '(ACTIVA)' : ''}`);
    });
}

// Auto-ejecutar verificación en desarrollo
document.addEventListener('DOMContentLoaded', function() {
    // Solo en desarrollo
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        setTimeout(() => {
            verifyMobileSidebarSetup();
            showMenuOptions();
            testMenuOnAllPages();
        }, 1500);
    }
});

// Exportar funciones
window.MobileSidebarVerification = {
    verify: verifyMobileSidebarSetup,
    showOptions: showMenuOptions,
    testPages: testMenuOnAllPages
};