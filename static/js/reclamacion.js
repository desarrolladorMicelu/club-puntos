// ============================================
// RECLAMACION.JS - LÓGICA PARA FORMULARIO DE RECLAMACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== ELEMENTOS DEL DOM ==========
    const btnBuscarDocumento = document.getElementById('btnBuscarDocumento');
    const documentoInput = document.getElementById('documentoReclamacion');
    const btnContinuar = document.getElementById('btnContinuar');
    const btnAtras = document.getElementById('btnAtras');
    const btnCancelar = document.getElementById('btnCancelar');
    const btnEnviarReclamacion = document.getElementById('btnEnviarReclamacion');
    const aceptarTerminos = document.getElementById('aceptarTerminos');
    
    // Pasos del formulario
    const paso1 = document.getElementById('paso1');
    const paso2 = document.getElementById('paso2');
    const paso3 = document.getElementById('paso3');
    
    // Campos del formulario
    const emailReclamacion = document.getElementById('emailReclamacion');
    const nombreReclamacion = document.getElementById('nombreReclamacion');
    const telefonoReclamacion = document.getElementById('telefonoReclamacion');
    const imeiReclamacion = document.getElementById('imeiReclamacion');
    const nombreDispositivo = document.getElementById('nombreDispositivo');
    const planCobertura = document.getElementById('planCobertura');
    const tipoCobertura = document.getElementById('tipoCobertura');

    // ========== VARIABLES DE ESTADO ==========
    let datosUsuario = null;
    let pasoActual = 1;

    // ========== BUSCAR USUARIO POR DOCUMENTO ==========
    btnBuscarDocumento.addEventListener('click', async function() {
        const documento = documentoInput.value.trim();

        if (!documento) {
            Swal.fire({
                icon: 'warning',
                title: 'Campo vacío',
                text: 'Por favor ingrese su número de documento',
                confirmButtonColor: '#31C0CA'
            });
            return;
        }

        // Mostrar loading
        const btn = this;
        const textoOriginal = btn.innerHTML;
        btn.disabled = true;
        btn.classList.add('loading');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/buscar_usuario_reclamacion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ documento: documento })
            });

            const data = await response.json();

            if (response.ok && data.exito) {
                datosUsuario = data.datos;
                
                // Llenar los campos del formulario
                emailReclamacion.value = datosUsuario.email || '';
                nombreReclamacion.value = datosUsuario.nombre || '';
                telefonoReclamacion.value = datosUsuario.telefono || '';
                imeiReclamacion.value = datosUsuario.imei || '';
                nombreDispositivo.value = datosUsuario.referencia || '';
                // Deshabilitar el IMEI ya que viene de la BD y darle estilo de éxito
                imeiReclamacion.disabled = true;
                imeiReclamacion.style.borderColor = '#43e97b';

                Swal.fire({
                    icon: 'success',
                    title: '¡Información encontrada!',
                    text: `Usuario encontrado: ${datosUsuario.nombre}`,
                    confirmButtonColor: '#31C0CA',
                    timer: 2000,
                    showConfirmButton: false
                });

                // Deshabilitar el input de documento
                documentoInput.disabled = true;
                btn.innerHTML = '<i class="fas fa-check"></i>';
                btn.classList.remove('loading');
                
                // Enfocar en el campo de nombre del dispositivo
                nombreDispositivo.focus();

            } else {
                throw new Error(data.mensaje || 'No se encontró información');
            }

        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'No encontrado',
                text: error.message || 'No se encontró una cobertura activa con este documento',
                confirmButtonColor: '#dc3545'
            });
            
            // Restaurar botón
            btn.disabled = false;
            btn.classList.remove('loading');
            btn.innerHTML = textoOriginal;
        }
    });

    // ========== VALIDAR NOMBRE DEL DISPOSITIVO ==========
    nombreDispositivo.addEventListener('input', function() {
        validarPaso1();
    });

    // ========== VALIDAR IMEI EN TIEMPO REAL ==========
    imeiReclamacion.addEventListener('input', function() {
        // Solo permitir números
        this.value = this.value.replace(/[^0-9]/g, '');
        
        // Limitar a 15 caracteres
        if (this.value.length > 15) {
            this.value = this.value.substring(0, 15);
        }

        // Validar paso 1
        validarPaso1();
    });

    imeiReclamacion.addEventListener('blur', function() {
        if (this.value.length > 0 && this.value.length !== 15) {
            this.style.borderColor = '#dc3545';
            Swal.fire({
                icon: 'warning',
                title: 'IMEI incorrecto',
                text: 'El IMEI debe tener exactamente 15 dígitos',
                confirmButtonColor: '#31C0CA',
                timer: 2000
            });
        } else if (this.value.length === 15) {
            this.style.borderColor = '#43e97b';
        }
    });

    // ========== VALIDAR TÉRMINOS ==========
    aceptarTerminos.addEventListener('change', function() {
        validarPaso1();
    });

    // ========== FUNCIÓN PARA VALIDAR PASO 1 ==========
    function validarPaso1() {
        const imeiValido = imeiReclamacion.value.length === 15;
        const nombreDispositivoValido = nombreDispositivo.value.trim() !== '';
        const terminosAceptados = aceptarTerminos.checked;
        const usuarioEncontrado = datosUsuario !== null;

        if (imeiValido && nombreDispositivoValido && terminosAceptados && usuarioEncontrado) {
            btnContinuar.disabled = false;
        } else {
            btnContinuar.disabled = true;
        }
    }

    // ========== FUNCIÓN PARA VALIDAR PASO 2 ==========
    function validarPaso2() {
        const planSeleccionado = planCobertura.value !== '';
        const tipoSeleccionado = tipoCobertura.value !== '';

        if (planSeleccionado && tipoSeleccionado) {
            btnContinuar.disabled = false;
        } else {
            btnContinuar.disabled = true;
        }
    }

    // Validar cuando cambian los selects
    planCobertura.addEventListener('change', validarPaso2);
    tipoCobertura.addEventListener('change', validarPaso2);

    // ========== FUNCIÓN PARA VALIDAR PASO 3 ==========
    function validarPaso3() {
        const formatoReclamacion = document.getElementById('formatoReclamacion').files.length > 0;
        const fotocopiaCedula = document.getElementById('fotocopiaCedula').files.length > 0;
        const fotografiasEquipo = document.getElementById('fotografiasEquipo').files.length > 0;
        const fotografiaSerial = document.getElementById('fotografiaSerial').files.length > 0;

        // Validar tamaño de archivos (máximo 4MB)
        const archivos = [
            document.getElementById('formatoReclamacion'),
            document.getElementById('fotocopiaCedula'),
            document.getElementById('facturaCompra'),
            document.getElementById('fotografiasEquipo'),
            document.getElementById('fotografiaSerial')
        ];

        for (let input of archivos) {
            if (input.files.length > 0) {
                for (let file of input.files) {
                    if (file.size > 4 * 1024 * 1024) { // 4MB
                        Swal.fire({
                            icon: 'error',
                            title: 'Archivo muy grande',
                            text: `El archivo ${file.name} supera el tamaño máximo de 4MB`,
                            confirmButtonColor: '#dc3545'
                        });
                        input.value = '';
                        return false;
                    }
                }
            }
        }

        return formatoReclamacion && fotocopiaCedula && fotografiasEquipo && fotografiaSerial;
    }

    // Validar cuando se cargan archivos
    document.querySelectorAll('.reclamacion-input-file').forEach(input => {
        input.addEventListener('change', function() {
            if (pasoActual === 3) {
                if (validarPaso3()) {
                    btnEnviarReclamacion.disabled = false;
                } else {
                    btnEnviarReclamacion.disabled = true;
                }
            }
        });
    });

    // ========== NAVEGACIÓN ENTRE PASOS ==========
    btnContinuar.addEventListener('click', function() {
        if (pasoActual === 1) {
            // Validar paso 1
            if (!aceptarTerminos.checked) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Términos y condiciones',
                    text: 'Debe aceptar los términos y condiciones para continuar',
                    confirmButtonColor: '#31C0CA'
                });
                return;
            }

            if (!datosUsuario) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Información incompleta',
                    text: 'Por favor busque primero su información de usuario',
                    confirmButtonColor: '#31C0CA'
                });
                return;
            }

            if (imeiReclamacion.value.length !== 15) {
                Swal.fire({
                    icon: 'warning',
                    title: 'IMEI incorrecto',
                    text: 'El IMEI debe tener exactamente 15 dígitos',
                    confirmButtonColor: '#31C0CA'
                });
                imeiReclamacion.focus();
                return;
            }

            if (nombreDispositivo.value.trim() === '') {
                Swal.fire({
                    icon: 'warning',
                    title: 'Nombre del dispositivo',
                    text: 'Debe ingresar el nombre del dispositivo',
                    confirmButtonColor: '#31C0CA'
                });
                nombreDispositivo.focus();
                return;
            }

            // Ir al paso 2
            cambiarPaso(2);

        } else if (pasoActual === 2) {
            // Validar paso 2
            if (!planCobertura.value) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Selecciona un plan',
                    text: 'Debe seleccionar un plan de cobertura',
                    confirmButtonColor: '#31C0CA'
                });
                return;
            }

            if (!tipoCobertura.value) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Selecciona tipo de cobertura',
                    text: 'Debe seleccionar el tipo de cobertura',
                    confirmButtonColor: '#31C0CA'
                });
                return;
            }

            // Ir al paso 3
            cambiarPaso(3);
        }
    });

    // ========== BOTÓN ATRÁS ==========
    btnAtras.addEventListener('click', function() {
        if (pasoActual > 1) {
            cambiarPaso(pasoActual - 1);
        }
    });

    // ========== FUNCIÓN PARA CAMBIAR DE PASO ==========
    function cambiarPaso(nuevoPaso) {
        // Ocultar todos los pasos
        paso1.style.display = 'none';
        paso2.style.display = 'none';
        paso3.style.display = 'none';

        // Mostrar el paso actual
        if (nuevoPaso === 1) {
            paso1.style.display = 'block';
            btnAtras.style.display = 'none';
            btnContinuar.style.display = 'inline-flex';
            btnEnviarReclamacion.style.display = 'none';
            validarPaso1();
        } else if (nuevoPaso === 2) {
            paso2.style.display = 'block';
            btnAtras.style.display = 'inline-flex';
            btnContinuar.style.display = 'inline-flex';
            btnEnviarReclamacion.style.display = 'none';
            btnContinuar.disabled = true;
            validarPaso2();
        } else if (nuevoPaso === 3) {
            paso3.style.display = 'block';
            btnAtras.style.display = 'inline-flex';
            btnContinuar.style.display = 'none';
            btnEnviarReclamacion.style.display = 'inline-flex';
            btnEnviarReclamacion.disabled = true;
        }

        pasoActual = nuevoPaso;

        // Scroll al inicio del formulario
        document.querySelector('.reclamacion-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ========== CANCELAR FORMULARIO ==========
    btnCancelar.addEventListener('click', function() {
        Swal.fire({
            title: '¿Cancelar reclamación?',
            text: 'Se perderán todos los datos ingresados',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, cancelar',
            cancelButtonText: 'No, continuar'
        }).then((result) => {
            if (result.isConfirmed) {
                reiniciarFormulario();
                Swal.fire({
                    icon: 'info',
                    title: 'Formulario cancelado',
                    text: 'Los datos han sido limpiados',
                    confirmButtonColor: '#31C0CA',
                    timer: 2000,
                    showConfirmButton: false
                });
            }
        });
    });

    // ========== ENVIAR RECLAMACIÓN ==========
    document.getElementById('reclamacionForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validar archivos requeridos
        if (!validarPaso3()) {
            Swal.fire({
                icon: 'warning',
                title: 'Documentos incompletos',
                text: 'Por favor suba todos los documentos requeridos',
                confirmButtonColor: '#31C0CA'
            });
            return;
        }

        // Preparar datos para enviar
        const formData = new FormData();
        formData.append('documento', documentoInput.value.trim());
        formData.append('email', emailReclamacion.value);
        formData.append('nombre', nombreReclamacion.value);
        formData.append('telefono', telefonoReclamacion.value);
        formData.append('imei', imeiReclamacion.value);
        formData.append('nombre_dispositivo', nombreDispositivo.value);
        formData.append('plan', planCobertura.value);
        formData.append('tipo_cobertura', tipoCobertura.value);

        // Agregar archivos
        formData.append('formato_reclamacion', document.getElementById('formatoReclamacion').files[0]);
        formData.append('fotocopia_cedula', document.getElementById('fotocopiaCedula').files[0]);
        
        if (document.getElementById('facturaCompra').files[0]) {
            formData.append('factura_compra', document.getElementById('facturaCompra').files[0]);
        }

        // Agregar múltiples fotos del equipo
        const fotografiasEquipo = document.getElementById('fotografiasEquipo').files;
        for (let i = 0; i < fotografiasEquipo.length; i++) {
            formData.append('fotografias_equipo', fotografiasEquipo[i]);
        }

        formData.append('fotografia_serial', document.getElementById('fotografiaSerial').files[0]);

        // Mostrar confirmación
        Swal.fire({
            title: '¿Enviar reclamación?',
            html: `
                <div class="text-start">
                    <p><strong>Cliente:</strong> ${nombreReclamacion.value}</p>
                    <p><strong>Documento:</strong> ${documentoInput.value}</p>
                    <p><strong>Dispositivo:</strong> ${nombreDispositivo.value}</p>
                    <p><strong>IMEI:</strong> ${imeiReclamacion.value}</p>
                    <p><strong>Plan:</strong> ${planCobertura.options[planCobertura.selectedIndex].text}</p>
                    <p><strong>Cobertura:</strong> ${tipoCobertura.options[tipoCobertura.selectedIndex].text}</p>
                </div>
            `,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#43e97b',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Revisar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                
                btnEnviarReclamacion.disabled = true;
                btnEnviarReclamacion.classList.add('loading');
                btnEnviarReclamacion.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';

                try {
                    // TODO: Implementar llamada real al backend
                    // const response = await fetch('/procesar_reclamacion', {
                    //     method: 'POST',
                    //     body: formData
                    // });

                    // Simulación de envío exitoso
                    await new Promise(resolve => setTimeout(resolve, 2000));

                    Swal.fire({
                        icon: 'success',
                        title: '¡Reclamación enviada!',
                        html: `
                            <p>Tu reclamación ha sido enviada exitosamente.</p>
                            <p>Recibirás una respuesta en tu correo: <strong>${emailReclamacion.value}</strong></p>
                            <p class="mt-3"><small>Número de referencia: REC-${Date.now()}</small></p>
                        `,
                        confirmButtonColor: '#43e97b'
                    }).then(() => {
                        reiniciarFormulario();
                        // Volver al tab de activar cobertura
                        document.getElementById('activar-tab').click();
                    });

                } catch (error) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error al enviar',
                        text: 'Ocurrió un error al enviar la reclamación. Por favor intente nuevamente.',
                        confirmButtonColor: '#dc3545'
                    });

                    btnEnviarReclamacion.disabled = false;
                    btnEnviarReclamacion.classList.remove('loading');
                    btnEnviarReclamacion.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Enviar Reclamación';
                }
            }
        });
    });

    // ========== FUNCIÓN PARA REINICIAR FORMULARIO ==========
    function reiniciarFormulario() {
        // Limpiar campos
        document.getElementById('reclamacionForm').reset();
        documentoInput.disabled = false;
        documentoInput.value = '';
        emailReclamacion.value = '';
        nombreReclamacion.value = '';
        telefonoReclamacion.value = '';
        imeiReclamacion.value = '';
        nombreDispositivo.value = '';
        imeiReclamacion.disabled = true;
        imeiReclamacion.style.borderColor = '#e0e0e0';
        
        aceptarTerminos.checked = false;
        
        // Restaurar botón de búsqueda
        btnBuscarDocumento.disabled = false;
        btnBuscarDocumento.classList.remove('loading');
        btnBuscarDocumento.innerHTML = '<i class="fas fa-search me-2"></i>Buscar';
        
        // Limpiar datos
        datosUsuario = null;
        
        // Volver al paso 1
        cambiarPaso(1);
    }

    // ========== PERMITIR BUSCAR CON ENTER ==========
    documentoInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            btnBuscarDocumento.click();
        }
    });

    // Inicialmente el IMEI está deshabilitado hasta buscar usuario
    imeiReclamacion.disabled = true;

    console.log('✅ Módulo de reclamación inicializado correctamente');
});