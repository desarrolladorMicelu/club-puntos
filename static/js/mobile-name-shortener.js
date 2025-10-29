/**
 * Mobile Name Shortener - Acorta el nombre del usuario en móvil
 * Solo muestra el primer nombre + "Tienes:" en lugar del nombre completo
 */

(function() {
    'use strict';
    
    // Función para detectar si es móvil
    function isMobile() {
        return window.innerWidth <= 991;
    }
    
    // Función para acortar el nombre
    function shortenUserName() {
        const greetingElement = document.querySelector('.fw-bold1');
        
        if (!greetingElement) return;
        
        const originalText = greetingElement.textContent || greetingElement.innerText;
        
        // Guardar el texto original si no está guardado
        if (!greetingElement.dataset.originalText) {
            greetingElement.dataset.originalText = originalText;
        }
        
        if (isMobile()) {
            // Extraer el primer nombre del texto original
            const match = originalText.match(/Hola\s+([^\s]+)/i);
            if (match && match[1]) {
                const firstName = match[1];
                greetingElement.textContent = `Hola ${firstName}! Tienes:`;
            }
        } else {
            // Restaurar texto original en desktop
            greetingElement.textContent = greetingElement.dataset.originalText;
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
    
    // Función de debug (solo en desarrollo)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.debugMobileNameShortener = function() {
            const greetingElement = document.querySelector('.fw-bold1');
            console.log('Mobile Name Shortener Debug:', {
                isMobile: isMobile(),
                greetingElement: greetingElement,
                originalText: greetingElement ? greetingElement.dataset.originalText : 'No encontrado',
                currentText: greetingElement ? greetingElement.textContent : 'No encontrado',
                windowWidth: window.innerWidth
            });
        };
    }
    
})();