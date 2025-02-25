document.addEventListener('DOMContentLoaded', function() {
    // Agregar el HTML del overlay spinner al body
    const spinnerHTML = `
        <div id="fullPageSpinner" class="position-fixed top-0 start-0 w-100 h-100 d-none" style="background: rgba(0, 0, 0, 0.5); z-index: 9999;">
            <div class="position-absolute top-50 start-50 translate-middle text-center">
                <div class="spinner-border text-light" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <div class="text-light mt-3 fw-bold">Buscando información del IMEI...</div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', spinnerHTML);
    const fullPageSpinner = document.getElementById('fullPageSpinner');

    // Obtener referencias a los elementos del formulario
    const cobForm = document.getElementById('cobForm');
    const cobBtnConf = document.getElementById('cobBtnConf');
    const imeiInput = document.getElementById('imei');
    const nombreClienteInput = document.getElementById('nombreCliente');
    const fechaInput = document.getElementById('fecha');
    const valorInput = document.getElementById("valor");
    const nitInput = document.getElementById('nit');
    const referenciaInput = document.getElementById('referencia');
    const telefonoInput = document.getElementById('telefono');
    let datosCobertura = null;
    
    // Función para limpiar un NIT/documento
    function limpiarDocumento(documento) {
        return documento ? documento.split('-')[0].trim() : '';
    }
    
    // Validación en tiempo real para el campo NIT
    nitInput.addEventListener('input', function(e) {
        let value = e.target.value;
        value = value.replace(/[^\d-]/g, '');
        if (value.includes('-')) {
            value = value.split('-')[0];
        }
        value = value.slice(0, 10);
        e.target.value = value;
    });

    // Buscar datos cuando se ingresa el IMEI
    imeiInput.addEventListener('blur', async function() {
        const imei = this.value.trim();
        if (imei) {
            if (!/^\d{15}$/.test(imei)) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'IMEI Inválido',
                    text: 'El IMEI debe tener exactamente 15 dígitos numéricos'
                });
                limpiarCampos();
                return;
            }
            await buscarDatosImei(imei);
        }
    });
    
    function limpiarCampos() {
        nombreClienteInput.value = '';
        fechaInput.value = '';
        valorInput.value = '';
        nitInput.value = ''; 
        referenciaInput.value = '';
        telefonoInput.value = '';
        datosCobertura = null;
        cobBtnConf.disabled = true;
        nitInput.disabled = false;
    }
    
    async function buscarDatosImei(imei) {
        try {
            fullPageSpinner.classList.remove('d-none');
            fullPageSpinner.querySelector('.fw-bold').textContent = 'Buscando información del IMEI...';
            
            imeiInput.disabled = true;
            cobBtnConf.disabled = true;
            
            const response = await fetch('/cobertura', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imei: imei,
                    accion: 'buscar'
                })
            });
            
            const data = await response.json();
            
            fullPageSpinner.classList.add('d-none');
            imeiInput.disabled = false;
            
            if (data.exito && data.datos) {
                // Limpiar y comparar documentos
                const nitLimpio = limpiarDocumento(data.datos.nit);
                const documentoLimpio = limpiarDocumento(data.usuario_documento);
                
                if (nitLimpio !== documentoLimpio) {
                    await Swal.fire({
                        icon: 'error',
                        title: 'Acceso Denegado',
                        text: 'Solo el propietario del dispositivo puede activar la cobertura.'
                    });
                    limpiarCampos();
                    return;
                }
                
                // Verificar si tenemos correo electrónico
                if (!data.datos.correo || !data.datos.correo.trim()) {
                    await Swal.fire({
                        icon: 'warning',
                        title: 'Correo electrónico faltante',
                        text: 'El correo electrónico es obligatorio para activar la cobertura. Por favor actualice su información de perfil.',
                        footer: '<a href="/perfil">Ir a Mi Perfil</a>'
                    });
                    // No bloqueamos el proceso aquí, solo alertamos
                }
                
                datosCobertura = {
                    ...data.datos,
                    nit: nitLimpio
                };
                
                nombreClienteInput.value = data.datos.nombre?.trim() || '';
                fechaInput.value = data.datos.fecha || '';
                valorInput.value = data.datos.valor || '';
                nitInput.value = nitLimpio;
                referenciaInput.value = data.datos.referencia?.trim() || '';
                telefonoInput.value = data.datos.telefono?.trim() || '';
                
                nitInput.disabled = true;
                cobBtnConf.disabled = false;
            } else {
                await Swal.fire({
                    icon: 'warning',
                    title: 'No encontrado',
                    text: data.mensaje || 'No se encontró información para este IMEI'
                });
                limpiarCampos();
            }
        } catch (error) {
            fullPageSpinner.classList.add('d-none');
            imeiInput.disabled = false;
            
            console.error('Error completo:', error);
            await Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error al buscar la información del IMEI'
            });
            limpiarCampos();
        }
    }
    
    cobBtnConf.addEventListener('click', async function (e) {
        e.preventDefault();

        try {
            // Verificar si tenemos datos de cobertura
            if (!datosCobertura) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Datos incompletos',
                    text: 'Por favor busque primero la información del IMEI.',
                });
                return;
            }

            // Verificar explícitamente que tengamos un correo electrónico
            if (!datosCobertura.correo || !datosCobertura.correo.trim()) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Correo electrónico faltante',
                    text: 'El correo electrónico es obligatorio para activar la cobertura. Por favor actualice su información de perfil.',
                    footer: '<a href="/perfil">Ir a Mi Perfil</a>'
                });
                return;
            }

            // Validar campos vacíos primero
            if (!nombreClienteInput.value.trim() || !fechaInput.value || !valorInput.value || 
                !nitInput.value.trim() || !referenciaInput.value.trim() || !telefonoInput.value.trim()) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Campos incompletos',
                    text: 'Por favor complete todos los campos requeridos.',
                });
                return;
            }

            // Validación adicional de seguridad
            if (datosCobertura && datosCobertura.nit !== nitInput.value.trim()) {
                await Swal.fire({
                    icon: 'error',
                    title: 'Error de Validación',
                    text: 'Los datos no coinciden con el propietario del dispositivo.'
                });
                return;
            }

            // Mostrar confirmación antes de proceder
            const confirmResult = await Swal.fire({
                title: '¿Confirmar Cobertura?',
                text: '¿Está seguro de que desea confirmar la cobertura?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Sí, confirmar',
                cancelButtonText: 'Cancelar'
            });

            if (!confirmResult.isConfirmed) {
                return;
            }
        
            const imei = imeiInput.value.trim();
            const nitValue = nitInput.value.trim();
            const referenciaValue = referenciaInput.value.trim();
            const fechaCompra = new Date(fechaInput.value);
            const fechaActual = new Date();

            // Validaciones iniciales
            if (!imei || !datosCobertura) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Datos incompletos',
                    text: 'Por favor ingrese un IMEI válido.',
                });
                return;
            }
        
            // Validación del documento
            if (!nitValue) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Falta información',
                    text: 'El documento es obligatorio.',
                });
                return;
            }

            // Validar formato del documento
            if (!/^\d{1,10}$/.test(nitValue)) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Documento inválido',
                    text: 'El documento debe contener entre 1 y 10 dígitos numéricos.',
                });
                return;
            }

            // Calcular la diferencia en días
            const diferenciaDias = Math.floor((fechaActual - fechaCompra) / (1000 * 60 * 60 * 24));

            // Validar que no hayan pasado más de 10 días desde la compra
            if (diferenciaDias > 30) {
                await Swal.fire({
                    icon: 'error',
                    title: 'Fuera de tiempo',
                    html: `
                        <div class="alert alert-danger" role="alert">
                            <strong>¡Atención!</strong> Han pasado más de 30 días desde la fecha de compra.
                            No es posible activar la cobertura.
                            <br>
                            Fecha de compra: ${fechaInput.value}
                            <br>
                            Días transcurridos: ${diferenciaDias}
                        </div>
                    `,
                    confirmButtonText: 'Aceptar',
                });
                return;
            }

            // Mostrar spinner con mensaje de confirmación
            fullPageSpinner.classList.remove('d-none');
            fullPageSpinner.querySelector('.fw-bold').textContent = 'Confirmando cobertura...';
            
            cobBtnConf.disabled = true;
            cobBtnConf.textContent = 'Procesando...';
    
            // Crear la póliza
            const responsePolicies = await fetch('/create_policy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imei: imei,
                    nombre: nombreClienteInput.value.trim(),
                    nit: nitValue,
                    correo: datosCobertura.correo?.trim() || '',
                }),
            });

            const policyData = await responsePolicies.json();
            
            // Modificar esta parte para continuar incluso si la póliza ya existe
            if (!policyData.exito && !policyData.poliza_existente) {
                throw new Error(policyData.mensaje || 'Error al crear la póliza');
            }

            // Procesar cobertura independientemente del resultado de la póliza
            const response = await fetch('/cobertura', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nit: nitValue,
                    imei: imei,
                    accion: 'guardar',
                    datos: {
                        nombre: nombreClienteInput.value.trim(),
                        correo: datosCobertura.correo?.trim() || '',
                    },
                    referencia: referenciaValue,
                    fecha: fechaInput.value,
                    valor: valorInput.value,
                    telefono: telefonoInput.value.trim(),
                }),
            });
    
            const data = await response.json();
    
            fullPageSpinner.classList.add('d-none');
    
            if (data.exito) {
                // Calcular fecha de finalización
                const fechaFinalizacion = new Date(fechaCompra);
                fechaFinalizacion.setFullYear(fechaFinalizacion.getFullYear() + 1);
                const fechaFinalizacionStr = fechaFinalizacion.toISOString().split('T')[0];
    
                if (fechaActual > fechaFinalizacion) {
                    await Swal.fire({
                        icon: 'error',
                        title: 'Cobertura Caducada',
                        html: `
                            <div class="alert alert-danger" role="alert">
                                <strong>¡Atención!</strong> La cobertura ha caducado. La fecha de finalización fue ${fechaFinalizacionStr}.
                            </div>
                        `,
                        confirmButtonText: 'Aceptar',
                    });
                } else {
                    await Swal.fire({
                        icon: 'success',
                        title: 'Cobertura y Póliza Confirmadas',
                        html: `
                            <div class="alert alert-success" role="alert">
                                <strong>¡Éxito!</strong> La cobertura y póliza han sido activadas exitosamente por 1 año.
                            </div>
                            <ul>
                                <li><strong>IMEI:</strong> ${imei}</li>
                                <li><strong>Correo de notificación enviado a:</strong> ${datosCobertura.correo?.trim() || 'No proporcionado'}</li>
                                <li><strong>Fecha Compra:</strong> ${fechaInput.value}</li>
                                <li><strong>Fecha de Finalización:</strong> ${fechaFinalizacionStr}</li>
                            </ul>
                        `,
                        confirmButtonText: 'Aceptar',
                    });
                    cobForm.reset();
                    datosCobertura = null;
                }
            } else {
                throw new Error(data.mensaje || 'Error al confirmar la cobertura');
            }
        } catch (error) {
            console.error('Error al procesar:', error);
            fullPageSpinner.classList.add('d-none');
            
            await Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Error al procesar la solicitud. Inténtelo nuevamente.',
            });
        } finally {
            fullPageSpinner.classList.add('d-none');
            cobBtnConf.disabled = false;
            cobBtnConf.textContent = 'Confirmar Cobertura';
        }
    });
});

/* js para info imei*/ 
document.querySelector('.question-icon').addEventListener('click', function(e) {
    const modal = document.getElementById('imeiInfoModal');
    const iconRect = this.getBoundingClientRect();
    
    modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    modal.style.left = `${iconRect.left}px`;
    modal.style.top = `${iconRect.top - 120}px`; // Ajusta este valor para posicionar sobre el ícono
  });
  
  // Cerrar modal al hacer clic fuera
  document.addEventListener('click', function(e) {
    const modal = document.getElementById('imeiInfoModal');
    const icon = document.querySelector('.question-icon');
    
    if (modal.style.display === 'block' && 
        !icon.contains(e.target) && 
        !modal.contains(e.target)) {
      modal.style.display = 'none';
    }
  });