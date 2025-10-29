document.addEventListener('DOMContentLoaded', function() {
    let facturasCargadas = false;
    let certificadosCargados = false;
    
    // Función de prueba para verificar conectividad
    function testAPI() {
        console.log('Probando conectividad con API...');
        fetch('/api/test')
        .then(response => response.json())
        .then(data => {
            console.log('Test API exitoso:', data);
        })
        .catch(error => {
            console.error('Error en test API:', error);
        });
    }
    
    // Ejecutar test al cargar la página
    testAPI();
    
    // Alternativa usando jQuery para Bootstrap 4
    $(document).ready(function() {
        console.log('jQuery ready - configurando eventos de desplegables');
        
        // Eventos para facturas usando jQuery
        $('#collapseFacturas').on('show.bs.collapse', function() {
            console.log('jQuery: Evento show.bs.collapse disparado para facturas');
            if (!facturasCargadas) {
                console.log('jQuery: Cargando facturas...');
                cargarFacturas();
            } else {
                console.log('jQuery: Facturas ya cargadas, omitiendo...');
            }
        });
        
        // Eventos para certificados usando jQuery
        $('#collapseCertificados').on('show.bs.collapse', function() {
            console.log('jQuery: Evento show.bs.collapse disparado para certificados');
            if (!certificadosCargados) {
                console.log('jQuery: Cargando certificados...');
                cargarCertificados();
            } else {
                console.log('jQuery: Certificados ya cargados, omitiendo...');
            }
        });
    });
    
    // Manejar apertura del desplegable de facturas
    const collapseFacturas = document.getElementById('collapseFacturas');
    console.log('Elemento collapseFacturas encontrado:', collapseFacturas);
    if (collapseFacturas) {
        // Bootstrap 4 usa 'show.bs.collapse' para cuando se va a mostrar
        collapseFacturas.addEventListener('show.bs.collapse', function() {
            console.log('Evento show.bs.collapse disparado para facturas');
            if (!facturasCargadas) {
                console.log('Cargando facturas...');
                cargarFacturas();
            } else {
                console.log('Facturas ya cargadas, omitiendo...');
            }
        });
        
        // También escuchar cuando se muestra completamente
        collapseFacturas.addEventListener('shown.bs.collapse', function() {
            console.log('Evento shown.bs.collapse disparado para facturas');
        });
    } else {
        console.error('No se encontró el elemento collapseFacturas');
    }
    
    // Manejar apertura del desplegable de certificados
    const collapseCertificados = document.getElementById('collapseCertificados');
    console.log('Elemento collapseCertificados encontrado:', collapseCertificados);
    if (collapseCertificados) {
        // Bootstrap 4 usa 'show.bs.collapse' para cuando se va a mostrar
        collapseCertificados.addEventListener('show.bs.collapse', function() {
            console.log('Evento show.bs.collapse disparado para certificados');
            if (!certificadosCargados) {
                console.log('Cargando certificados...');
                cargarCertificados();
            } else {
                console.log('Certificados ya cargados, omitiendo...');
            }
        });
        
        // También escuchar cuando se muestra completamente
        collapseCertificados.addEventListener('shown.bs.collapse', function() {
            console.log('Evento shown.bs.collapse disparado para certificados');
        });
    } else {
        console.error('No se encontró el elemento collapseCertificados');
    }
    
    // Función para cargar facturas
    function cargarFacturas() {
        console.log('Iniciando carga de facturas...');
        
        fetch('/api/facturas', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            console.log('Respuesta recibida:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            let html = '';
            if (data.facturas && data.facturas.length > 0) {
                data.facturas.forEach(function(factura) {
                    html += `
                        <div class="factura-card" data-factura-id="${factura.id}" data-factura-numero="${factura.numero}">
                            <div class="factura-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div class="factura-info">
                                <span class="factura-numero">Factura #${factura.numero}</span>
                                <span class="factura-fecha">${factura.fecha}</span>
                                <span class="factura-total">$${factura.total.toLocaleString()}</span>
                            </div>
                        </div>
                    `;
                });
            } else {
                html = '<div class="col-12 text-center"><p>No se encontraron facturas.</p></div>';
            }
            document.getElementById('facturasGrid').innerHTML = html;
            facturasCargadas = true;
            
            // Re-enlazar eventos de clic para las nuevas tarjetas
            enlazarEventosFacturas();
        })
        .catch(error => {
            console.error('Error al cargar facturas:', error);
            document.getElementById('facturasGrid').innerHTML = '<div class="col-12 text-center"><p class="text-danger">Error al cargar las facturas: ' + error.message + '</p></div>';
        });
    }
    
    // Función para cargar certificados
    function cargarCertificados() {
        console.log('Iniciando carga de certificados...');
        
        fetch('/api/certificados', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            console.log('Respuesta recibida:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            let html = '';
            if (data.certificados && data.certificados.length > 0) {
                data.certificados.forEach(function(certificado) {
                    html += `
                        <div class="certificado-card" data-certificado-id="${certificado.id}" data-certificado-numero="${certificado.numero}">
                            <div class="certificado-icon">
                                <i class="fas fa-certificate"></i>
                            </div>
                            <div class="certificado-info">
                                <span class="certificado-numero">Certificado #${certificado.numero}</span>
                                <span class="certificado-fecha">${certificado.fecha}</span>
                            </div>
                        </div>
                    `;
                });
            } else {
                html = '<div class="col-12 text-center"><p>No se encontraron certificados.</p></div>';
            }
            document.getElementById('certificadosGrid').innerHTML = html;
            certificadosCargados = true;
            
            // Re-enlazar eventos de clic para las nuevas tarjetas
            enlazarEventosCertificados();
        })
        .catch(error => {
            console.error('Error al cargar certificados:', error);
            document.getElementById('certificadosGrid').innerHTML = '<div class="col-12 text-center"><p class="text-danger">Error al cargar los certificados: ' + error.message + '</p></div>';
        });
    }
    
    // Función para enlazar eventos de facturas
    function enlazarEventosFacturas() {
        const facturaCards = document.querySelectorAll('.factura-card');
        facturaCards.forEach(card => {
            card.addEventListener('click', function() {
                const facturaId = this.getAttribute('data-factura-id');
                const facturaNumero = this.getAttribute('data-factura-numero');
                
                document.getElementById('facturaModalLabel').textContent = 'Factura #' + facturaNumero;
                const pdfUrl = '/factura/' + facturaId + '/pdf';
                document.getElementById('pdfViewer').src = pdfUrl;
                
                // Usar Bootstrap modal con JavaScript vanilla
                const modal = new bootstrap.Modal(document.getElementById('facturaModal'));
                modal.show();
            });
        });
    }
    
    // Función para enlazar eventos de certificados
    function enlazarEventosCertificados() {
        const certificadoCards = document.querySelectorAll('.certificado-card');
        certificadoCards.forEach(card => {
            card.addEventListener('click', function() {
                const certificadoId = this.getAttribute('data-certificado-id');
                const certificadoNumero = this.getAttribute('data-certificado-numero');
                
                document.getElementById('certificadoModalLabel').textContent = 'Certificado #' + certificadoNumero;
                const pdfUrl = '/certificado/' + certificadoId + '/pdf';
                document.getElementById('certificadoViewer').src = pdfUrl;
                
                // Usar Bootstrap modal con JavaScript vanilla
                const modal = new bootstrap.Modal(document.getElementById('certificadoModal'));
                modal.show();
            });
        });
    }
    
    // Manejar descarga de PDF de factura
    const descargarFactura = document.getElementById('descargarFactura');
    if (descargarFactura) {
        descargarFactura.addEventListener('click', function() {
            const pdfUrl = document.getElementById('pdfViewer').src;
            if (pdfUrl) {
                window.open(pdfUrl, '_blank');
            }
        });
    }
    
    // Manejar descarga de PDF de certificado
    const descargarCertificado = document.getElementById('descargarCertificado');
    if (descargarCertificado) {
        descargarCertificado.addEventListener('click', function() {
            const pdfUrl = document.getElementById('certificadoViewer').src;
            if (pdfUrl) {
                window.open(pdfUrl, '_blank');
            }
        });
    }
    
    // Limpiar iframe al cerrar el modal de factura
    const facturaModal = document.getElementById('facturaModal');
    if (facturaModal) {
        facturaModal.addEventListener('hidden.bs.modal', function() {
            document.getElementById('pdfViewer').src = '';
        });
    }
    
    // Limpiar iframe al cerrar el modal de certificado
    const certificadoModal = document.getElementById('certificadoModal');
    if (certificadoModal) {
        certificadoModal.addEventListener('hidden.bs.modal', function() {
            document.getElementById('certificadoViewer').src = '';
        });
    }
});
