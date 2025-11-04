/* ========================================
   VERIFICACIÓN DEL ACORTADOR DE NOMBRES
   ======================================== */

// Función para verificar que el acortador de nombres funcione correctamente
function verifyNameShortener() {
    console.log('🔍 Verificando acortador de nombres...');
    
    const checks = {
        scriptLoaded: false,
        greetingFound: false,
        nameShortened: false,
        originalSaved: false
    };
    
    // Verificar si el script está cargado
    if (typeof shortenUserName !== 'undefined' || window.debugNameShortener) {
        checks.scriptLoaded = true;
        console.log('✅ Script de acortador de nombres cargado');
    } else {
        console.log('❌ Script de acortador de nombres NO encontrado');
    }
    
    // Verificar elemento de saludo
    const greetingElement = document.querySelector('.fw-bold1');
    if (greetingElement) {
        checks.greetingFound = true;
        console.log('✅ Elemento de saludo encontrado');
        
        // Verificar si tiene texto original guardado
        if (greetingElement.dataset.originalText) {
            checks.originalSaved = true;
            console.log('✅ Texto original guardado:', greetingElement.dataset.originalText);
        } else {
            console.log('⚠️ Texto original no guardado aún');
        }
        
        // Verificar si el nombre está acortado
        const currentText = greetingElement.textContent || greetingElement.innerText;
        const isShortened = /Hola\s+[^\s]+[,!]\s+[Tt]ienes/.test(currentText);
        
        if (isShortened) {
            checks.nameShortened = true;
            console.log('✅ Nombre acortado correctamente:', currentText);
        } else {
            console.log('⚠️ Nombre no parece estar acortado:', currentText);
        }
        
    } else {
        console.log('❌ Elemento de saludo NO encontrado');
    }
    
    // Resumen
    const passedChecks = Object.values(checks).filter(Boolean).length;
    const totalChecks = Object.keys(checks).length;
    
    console.log(`\n📊 RESUMEN ACORTADOR DE NOMBRES: ${passedChecks}/${totalChecks} verificaciones pasadas`);
    
    if (passedChecks === totalChecks) {
        console.log('🎉 ¡Acortador de nombres funcionando perfectamente!');
        return true;
    } else {
        console.log('⚠️ Hay problemas con el acortador de nombres');
        return false;
    }
}

// Función para mostrar ejemplos de cómo debería verse
function showNameShortenerExamples() {
    console.log(`
📋 EJEMPLOS DE ACORTAMIENTO DE NOMBRES:
=====================================

📱 ANTES (nombre completo):
   "Hola Juan Esteban García, tienes"

✅ DESPUÉS PC:
   "Hola Juan, tienes"

✅ DESPUÉS MÓVIL:
   "Hola Juan! Tienes:"

🎯 REGLAS:
   • Solo se muestra el primer nombre
   • PC mantiene formato formal: "Hola Juan, tienes"
   • Móvil usa formato amigable: "Hola Juan! Tienes:"
   • Funciona en tiempo real al cambiar tamaño de ventana
    `);
}

// Función para probar el acortamiento manualmente
function testNameShortening() {
    const greetingElement = document.querySelector('.fw-bold1');
    
    if (!greetingElement) {
        console.log('❌ No se encontró elemento de saludo para probar');
        return;
    }
    
    console.log('🧪 Probando acortamiento de nombres...');
    
    // Simular diferentes nombres para probar
    const testNames = [
        'Hola Juan Esteban García, tienes',
        'Hola María José Rodríguez, tienes',
        'Hola Carlos, tienes',
        'Hola Ana Sofía, tienes'
    ];
    
    testNames.forEach((testName, index) => {
        setTimeout(() => {
            console.log(`\n🔄 Test ${index + 1}: ${testName}`);
            
            // Simular texto original
            greetingElement.dataset.originalText = testName;
            greetingElement.textContent = testName;
            
            // Aplicar acortamiento
            if (window.debugNameShortener) {
                // Trigger the shortening function
                const event = new Event('resize');
                window.dispatchEvent(event);
                
                setTimeout(() => {
                    console.log(`✅ Resultado: ${greetingElement.textContent}`);
                }, 100);
            }
        }, index * 1000);
    });
}

// Auto-ejecutar verificación en desarrollo
document.addEventListener('DOMContentLoaded', function() {
    // Solo en desarrollo
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        setTimeout(() => {
            verifyNameShortener();
            showNameShortenerExamples();
        }, 2000);
    }
});

// Exportar funciones
window.NameShortenerVerification = {
    verify: verifyNameShortener,
    showExamples: showNameShortenerExamples,
    test: testNameShortening
};

// Atajos de teclado para testing (solo en desarrollo)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    document.addEventListener('keydown', function(e) {
        // Ctrl + Shift + N = Verificar acortador de nombres
        if (e.ctrlKey && e.shiftKey && e.key === 'N') {
            e.preventDefault();
            verifyNameShortener();
        }
        
        // Ctrl + Shift + E = Mostrar ejemplos
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            e.preventDefault();
            showNameShortenerExamples();
        }
    });
    
    console.log(`
🎮 ATAJOS DE TECLADO ACORTADOR DE NOMBRES:
• Ctrl + Shift + N = Verificar funcionamiento
• Ctrl + Shift + E = Mostrar ejemplos
    `);
}