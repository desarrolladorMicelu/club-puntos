document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el modal
    var modal = new bootstrap.Modal(document.getElementById('cobModal'), {
        backdrop: 'static',
        keyboard: false
    });

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

    // Mostrar el modal automáticamente
    modal.show();

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
    }
    
    async function buscarDatosImei(imei) {
        try {
            // Mostrar spinner de página completa
            fullPageSpinner.classList.remove('d-none');
            fullPageSpinner.querySelector('.fw-bold').textContent = 'Buscando información del IMEI...';
            
            // Deshabilitar campos
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
            
            // Ocultar spinner antes de mostrar cualquier alerta
            fullPageSpinner.classList.add('d-none');
            imeiInput.disabled = false;
            
            if (data.exito && data.datos) {
                // Guardar datos completos
                datosCobertura = data.datos;
                
                // Actualizar campos del formulario
                nombreClienteInput.value = data.datos.nombre || '';
                fechaInput.value = data.datos.fecha || '';
                valorInput.value = data.datos.valor || '';
                nitInput.value = data.datos.nit || ''; 
                referenciaInput.value = data.datos.referencia || '';
                telefonoInput.value = data.datos.telefono || '';
                
                // Habilitar botón de confirmar
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
            // Ocultar spinner antes de mostrar el error
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
            // Validar campos vacíos primero
            if (!nombreClienteInput.value.trim() || !fechaInput.value || !valorInput.value || !nitInput.value.trim() || !referenciaInput.value.trim() || !telefonoInput.value.trim()) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'Campos incompletos',
                    text: 'Por favor complete todos los campos requeridos.',
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
            let nitValue = nitInput.value.trim();
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

            // Limpiar y validar el documento
            nitValue = nitValue.split('-')[0];
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
            if (diferenciaDias > 10) {
                await Swal.fire({
                    icon: 'error',
                    title: 'Fuera de tiempo',
                    html: `
                        <div class="alert alert-danger" role="alert">
                            <strong>¡Atención!</strong> Han pasado más de 10 días desde la fecha de compra.
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
                    correo: datosCobertura.correo || '',
                }),
            });

            const policyData = await responsePolicies.json();
            
            if (!policyData.exito) {
                throw new Error(policyData.mensaje || 'Error al crear la póliza');
            }

            // Procesar cobertura
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
                        correo: datosCobertura.correo || '',
                    },
                    referencia: referenciaValue,
                    fecha: fechaInput.value,
                    valor: valorInput.value,
                    telefono: telefonoInput.value,
                }),
            });
    
            const data = await response.json();
    
            // Ocultar spinner antes de mostrar resultados
            fullPageSpinner.classList.add('d-none');
    
            if (data.exito) {
                // Calcular fecha de finalización
                const fechaFinalizacion = new Date(fechaCompra);
                fechaFinalizacion.setMonth(fechaFinalizacion.getMonth() + 6);
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
                                <strong>¡Éxito!</strong> La cobertura y póliza han sido activadas exitosamente por 6 meses.
                            </div>
                            <ul>
                                <li><strong>IMEI:</strong> ${imei}</li>
                                <li><strong>Correo de notificación enviado a:</strong> ${datosCobertura.correo || 'No proporcionado'}</li>
                                <li><strong>Fecha Compra:</strong> ${fechaInput.value}</li>
                                <li><strong>Fecha de Finalización:</strong> ${fechaFinalizacionStr}</li>
                            </ul>
                        `,
                        confirmButtonText: 'Aceptar',
                    });
                    cobForm.reset();
                    datosCobertura = null;
                    modal.hide();
                }
            } else {
                throw new Error(data.mensaje || 'Error al confirmar la cobertura');
            }
        } catch (error) {
            console.error('Error al procesar:', error);
            // Asegurar que el spinner se oculte antes de mostrar el error
            fullPageSpinner.classList.add('d-none');
            
            await Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Error al procesar la solicitud. Inténtelo nuevamente.',
            });
        } finally {
            // Asegurar que el spinner se oculte y el botón se restaure
            fullPageSpinner.classList.add('d-none');
            cobBtnConf.disabled = false;
            cobBtnConf.textContent = 'Confirmar Cobertura';
        }
    });
});