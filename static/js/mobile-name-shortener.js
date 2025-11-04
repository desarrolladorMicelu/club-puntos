/**
 * Name Shortener - Acorta el nombre del usuario en PC y móvil
 * Solo muestra el primer nombre en lugar del nombre completo
 * PC: "Hola Juan, tienes" | Móvil: "Hola Juan! Tienes:"
 */

(function() {
    'use strict';
    
    // Función para detectar si es móvil
    function isMobile() {
        return window.innerWidth <= 991;
    }
    
    // Función para acortar el nombre (AHORA APLICA EN PC Y MÓVIL)
    function shortenUserName() {
        const greetingElement = document.querySelector('.fw-bold1');
        
        if (!greetingElement) return;
        
        const currentText = greetingElement.textContent || greetingElement.innerText;
        
        // Guardar el texto original si no está guardado
        if (!greetingElement.dataset.originalText) {
            greetingElement.dataset.originalText = currentText;
        }
        
        // USAR SIEMPRE EL TEXTO ORIGINAL GUARDADO
        const originalText = greetingElement.dataset.originalText;
        
        // APLICAR ACORTAMIENTO TANTO EN MÓVIL COMO EN PC
        // Extraer el primer nombre del texto original
        const match = originalText.match(/Hola\s+([^\s]+)/i);
        if (match && match[1]) {
            const firstName = match[1];
            if (isMobile()) {
                // En móvil: "Hola Juan! Tienes:"
                greetingElement.textContent = `Hola ${firstName}! Tienes:`;
            } else {
                // En PC: "Hola Juan, tienes" (mantiene el formato original pero con primer nombre)
                greetingElement.textContent = `Hola ${firstName}, tienes`;
            }
        }
    }
    
    // Función para aplicar los cambios
    function applyMobileNameShortener() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', shortenUserName);
        } else {
            shortenUserName();
        }
        
        // Aplicar cambios cuando se redimensiona la ventana
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(shortenUserName, 150);
        });
        
        // Observar cambios en el DOM por si el contenido se actualiza dinámicamente
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const greetingElement = document.querySelector('.fw-bold1');
                    if (greetingElement && !greetingElement.dataset.originalText) {
                        setTimeout(shortenUserName, 100);
                    }
                }
            });
        });
        
        // Observar cambios en el body
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }
    
    // Inicializar
    applyMobileNameShortener();
    
    // FORZAR EJECUCIÓN INMEDIATA PARA PC
    setTimeout(function() {
        shortenUserName();
        console.log('🔧 Acortador de nombres ejecutado para PC');
    }, 100);
    
    // FORZAR EJECUCIÓN ADICIONAL
    setTimeout(function() {
        shortenUserName();
        console.log('🔧 Acortador de nombres ejecutado nuevamente');
    }, 500);
    
    // FUNCIÓN GLOBAL PARA EJECUTAR MANUALMENTE
    window.forceNameShortening = function() {
        shortenUserName();
        console.log('✅ Acortamiento de nombres forzado');
    };
    
    // Función de debug (solo en desarrollo)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.debugNameShortener = function() {
            const greetingElement = document.querySelector('.fw-bold1');
            console.log('Name Shortener Debug:', {
                isMobile: isMobile(),
                greetingElement: greetingElement,
                originalText: greetingElement ? greetingElement.dataset.originalText : 'No encontrado',
                currentText: greetingElement ? greetingElement.textContent : 'No encontrado',
                windowWidth: window.innerWidth,
                platform: isMobile() ? 'Móvil' : 'PC'
            });
        };
    }
    
})();