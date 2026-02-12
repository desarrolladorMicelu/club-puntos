/**
 * Control del Modal de Consentimiento Digital
 * Maneja la validación de lectura completa y aceptación del contrato
 */

(function() {
    'use strict';

    let scrollCompletado = false;
    let contratoAceptado = false;

    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        const btnRegistrar = document.getElementById('btn-registrar');
        const formularioRegistro = document.getElementById('registro-form');
        const modalConsentimiento = new bootstrap.Modal(document.getElementById('modalConsentimiento'));
        const contenidoContrato = document.getElementById('contenidoContrato');
        const checkAceptoContrato = document.getElementById('checkAceptoContrato');
        const btnAceptarContrato = document.getElementById('btnAceptarContrato');
        const mensajeScroll = document.getElementById('mensajeScroll');
        const inputAceptaConsentimiento = document.getElementById('acepta_consentimiento');

        // Interceptar el click del botón de registro
        if (btnRegistrar) {
            btnRegistrar.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Validar campos obligatorios del formulario
                if (!validarFormulario()) {
                    return;
                }
                
                // Resetear estado del modal
                scrollCompletado = false;
                contratoAceptado = false;
                checkAceptoContrato.checked = false;
                checkAceptoContrato.disabled = true;
                btnAceptarContrato.disabled = true;
                mensajeScroll.style.display = 'block';
                contenidoContrato.scrollTop = 0;
                
                // Resaltar enumeraciones (a., b., c., etc.)
                resaltarEnumeraciones();
                
                // Mostrar el modal
                modalConsentimiento.show();
            });
        }

        // Detectar scroll en el contenido del contrato
        if (contenidoContrato) {
            contenidoContrato.addEventListener('scroll', function() {
                const scrollTop = contenidoContrato.scrollTop;
                const scrollHeight = contenidoContrato.scrollHeight;
                const clientHeight = contenidoContrato.clientHeight;
                
                // Verificar si llegó al final (con margen de 50px)
                if (scrollTop + clientHeight >= scrollHeight - 50) {
                    if (!scrollCompletado) {
                        scrollCompletado = true;
                        checkAceptoContrato.disabled = false;
                        mensajeScroll.innerHTML = '<i class="fas fa-check-circle text-success"></i> Has leído el documento completo';
                        
                        // Animación de habilitación
                        checkAceptoContrato.parentElement.classList.add('animate__animated', 'animate__pulse');
                    }
                }
            });
        }

        // Detectar cambio en el checkbox
        if (checkAceptoContrato) {
            checkAceptoContrato.addEventListener('change', function() {
                if (this.checked) {
                    btnAceptarContrato.disabled = false;
                    contratoAceptado = true;
                } else {
                    btnAceptarContrato.disabled = true;
                    contratoAceptado = false;
                }
            });
        }

        // Botón de aceptar contrato
        if (btnAceptarContrato) {
            btnAceptarContrato.addEventListener('click', function() {
                if (contratoAceptado && scrollCompletado) {
                    // Marcar que aceptó el consentimiento
                    inputAceptaConsentimiento.value = 'true';
                    
                    // Cerrar modal
                    modalConsentimiento.hide();
                    
                    // Mostrar spinner de carga
                    mostrarSpinnerCarga();
                    
                    // Enviar formulario
                    formularioRegistro.submit();
                }
            });
        }

        // Si cierra el modal sin aceptar, resetear
        document.getElementById('modalConsentimiento').addEventListener('hidden.bs.modal', function() {
            if (!contratoAceptado) {
                inputAceptaConsentimiento.value = 'false';
            }
        });
    });

    /**
     * Valida que todos los campos obligatorios estén llenos
     */
    function validarFormulario() {
        const documento = document.getElementById('documento').value.trim();
        const genero = document.getElementById('genero').value;
        const ciudad = document.getElementById('ciudad').value;
        const barrio = document.getElementById('barrio').value;
        const fechaNacimiento = document.getElementById('fecha_nacimiento').value;
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;
        const habeasdata = document.getElementById('habeasdata').checked;

        if (!documento) {
            mostrarAlerta('Por favor, ingresa tu documento', 'warning');
            return false;
        }

        if (!genero) {
            mostrarAlerta('Por favor, selecciona tu género', 'warning');
            return false;
        }

        if (!ciudad) {
            mostrarAlerta('Por favor, selecciona tu ciudad', 'warning');
            return false;
        }

        if (!barrio) {
            mostrarAlerta('Por favor, selecciona tu barrio', 'warning');
            return false;
        }

        if (!fechaNacimiento) {
            mostrarAlerta('Por favor, ingresa tu fecha de nacimiento', 'warning');
            return false;
        }

        if (!password1 || !password2) {
            mostrarAlerta('Por favor, ingresa tu contraseña', 'warning');
            return false;
        }

        if (password1 !== password2) {
            mostrarAlerta('Las contraseñas no coinciden', 'danger');
            return false;
        }

        if (password1.length <= 4) {
            mostrarAlerta('La contraseña debe tener más de 5 caracteres', 'danger');
            return false;
        }

        if (password1.includes(' ')) {
            mostrarAlerta('La contraseña no puede contener espacios', 'danger');
            return false;
        }

        if (!habeasdata) {
            mostrarAlerta('Debes aceptar recibir información de marketing', 'warning');
            return false;
        }

        return true;
    }

    /**
     * Muestra una alerta temporal
     */
    function mostrarAlerta(mensaje, tipo) {
        // Buscar o crear contenedor de alertas
        let contenedorAlertas = document.querySelector('.flash-messages1');
        if (!contenedorAlertas) {
            contenedorAlertas = document.createElement('div');
            contenedorAlertas.className = 'flash-messages1';
            document.body.insertBefore(contenedorAlertas, document.body.firstChild);
        }

        const alerta = document.createElement('div');
        alerta.className = `flash1 ${tipo}`;
        alerta.innerHTML = `
            <span class="close-btn">&times;</span>
            ${mensaje}
        `;

        contenedorAlertas.appendChild(alerta);

        // Cerrar al hacer click en la X
        alerta.querySelector('.close-btn').addEventListener('click', function() {
            alerta.remove();
        });

        // Auto-cerrar después de 5 segundos
        setTimeout(function() {
            alerta.remove();
        }, 5000);
    }

    /**
     * Muestra un spinner de carga mientras se crea el usuario
     */
    function mostrarSpinnerCarga() {
        // Verificar que no exista ya
        if (document.getElementById('loading-overlay')) {
            return;
        }

        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-3">Creando usuario...</p>
                <small>Por favor espera, esto puede tomar unos segundos</small>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    /**
     * Resalta las enumeraciones (a., b., c., etc.) en el texto del contrato
     */
    function resaltarEnumeraciones() {
        const contenido = document.getElementById('contenidoContrato');
        if (!contenido) return;

        // Obtener todos los párrafos
        const parrafos = contenido.querySelectorAll('p');
        
        parrafos.forEach(function(parrafo) {
            let html = parrafo.innerHTML;
            
            // 1. Buscar letras con punto: a., b., c., etc.
            html = html.replace(/(\s)([a-f])(\.)/g, function(match, space, letter, dot) {
                return space + '<span class="enum-letter">' + letter + dot + '</span>';
            });
            html = html.replace(/^([a-f])(\.)/g, '<span class="enum-letter">$1$2</span>');
            
            // 2. Buscar letras con paréntesis: a), b), c), etc.
            html = html.replace(/(\s)([a-f])(\))/g, function(match, space, letter, paren) {
                return space + '<span class="enum-letter">' + letter + paren + '</span>';
            });
            html = html.replace(/^([a-f])(\))/g, '<span class="enum-letter">$1$2</span>');
            
            // 3. Buscar números con punto: 1., 2., 3., etc.
            html = html.replace(/(\s)([1-9])(\.)/g, function(match, space, num, dot) {
                return space + '<span class="enum-number">' + num + dot + '</span>';
            });
            html = html.replace(/^([1-9])(\.)/g, '<span class="enum-number">$1$2</span>');
            
            parrafo.innerHTML = html;
        });
    }

})();
