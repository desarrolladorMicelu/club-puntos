"""
Servicio para generar PDFs de consentimiento digital con firma SHA-256
Utiliza ReportLab para la generación de PDFs
"""
import hashlib
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame


def generar_hash_firma(documento, nombre, email, telefono, fecha, ip, user_agent, version='2026'):
    """
    Genera un hash SHA-256 único para la firma digital del consentimiento
    
    Args:
        documento: Cédula o NIT del usuario
        nombre: Nombre completo
        email: Correo electrónico
        telefono: Número de teléfono
        fecha: Fecha y hora de aceptación (ISO format)
        ip: Dirección IP del usuario
        user_agent: Navegador del usuario
        version: Versión del contrato
        
    Returns:
        str: Hash SHA-256 de 64 caracteres hexadecimales
    """
    # Concatenar todos los datos con separador |
    datos = f"{documento}|{nombre}|{email}|{telefono}|{fecha}|{ip}|{user_agent}|{version}"
    
    # Generar hash SHA-256
    hash_obj = hashlib.sha256(datos.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    return hash_hex


def generar_pdf_consentimiento(datos_usuario, hash_firma):
    """
    Genera un PDF del contrato de servicio cloud computing con firma digital
    
    Args:
        datos_usuario: Dict con datos del usuario (documento, nombre, email, telefono, ciudad, fecha, ip, user_agent)
        hash_firma: Hash SHA-256 de la firma digital
        
    Returns:
        bytes: Contenido del PDF en bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuración de márgenes
    margin_left = 0.75 * inch
    margin_right = width - 0.75 * inch
    y = height - 0.75 * inch
    
    # ========== ENCABEZADO ==========
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "CONTRATO DE SERVICIO DE CLOUD COMPUTING")
    y -= 0.25 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "Entre el Usuario y MICELU.CO S.A.S.")
    y -= 0.2 * inch
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "Versión 2026")
    y -= 0.4 * inch
    
    # ========== INTRODUCCIÓN ==========
    c.setFont("Helvetica", 9)
    intro_text = [
        "Este contrato regula el acceso, uso y condiciones del Servicio de Cloud Computing prestado por MICELU.CO S.A.S.",
        '("MiCelu") a los usuarios que adquieren un dispositivo y activan el servicio mediante registro digital a partir de',
        "un mes de la adquisición del dispositivo. La aceptación se perfecciona mediante clic en la plataforma."
    ]
    for line in intro_text:
        c.drawString(margin_left, y, line)
        y -= 0.18 * inch
    
    y -= 0.15 * inch
    
    # ========== CLÁUSULAS (VERSIÓN COMPACTA) ==========
    c.setFont("Helvetica-Bold", 9)
    
    clausulas = [
        ("CLÁUSULA PRIMERA. DEFINICIONES:", [
            "a) Servicio Cloud: Plataforma tecnológica en modalidad PaaS alojada en nube privada de acceso restringido.",
            "b) Información Confidencial: Toda información técnica, documental, de trazabilidad, código, arquitectura y derivados.",
            "c) Proveedores Tecnológicos Integrados: Servicios de terceros integrados por MiCelu sin sublicencia al usuario.",
            "d) IMEI Asociado: Identificador del dispositivo registrado.",
            "e) Fuerza Mayor Tecnológica: Evento imprevisible, irresistible y externo que afecte la prestación del servicio."
        ]),
        ("CLÁUSULA SEGUNDA. OBJETO:", [
            "MiCelu presta al usuario un Servicio de Cloud Computing en modalidad PaaS que permite acceder a trazabilidad del",
            "dispositivo, historial, documentos asociados, facturas electrónicas y sistema de puntos. El servicio aplica únicamente",
            "a dispositivos registrados por el usuario."
        ]),
        ("CLÁUSULA TERCERA. NATURALEZA DEL SERVICIO:", [
            "El servicio es un entorno de nube privada de acceso restringido. MiCelu actúa como integrador, no como revendedor",
            "de servicios de terceros. El usuario reconoce que no existe acceso al software interno ni sublicencias sobre",
            "componentes tecnológicos."
        ]),
        ("CLÁUSULA CUARTA. CONDICIÓN SUSPENSIVA DE ACTIVACIÓN:", [
            "El servicio solo nace cuando el usuario: a) Registra el dispositivo, b) Proporciona su información personal,",
            "c) Acepta este contrato por clic, d) Valida el IMEI, e) Completa la activación."
        ]),
        ("CLÁUSULA QUINTA. ASOCIATIVIDAD AL DISPOSITIVO:", [
            "El servicio se vincula exclusivamente al IMEI. No es transferible. Venta del dispositivo implica terminación inmediata.",
            "Manipulación del IMEI implica terminación sin reembolso. La cuenta es personal e intransferible."
        ]),
        ("CLÁUSULA SEXTA. ALCANCE FUNCIONAL:", [
            "Durante la vigencia el usuario podrá acceder a: a) Trazabilidad y Testeo Digital, b) Facturación Electrónica en la Nube,",
            "c) Fidelización y Puntos, d) Consulta y Gestión Digital, e) Información registrada en la activación, f) Cobertura de",
            "pantalla opcional (sujeta a términos del proveedor A5/ACINCO S.A.S.)."
        ]),
        ("CLÁUSULA SÉPTIMA. OBLIGACIONES DEL USUARIO:", [
            "1. Registrar información veraz, 2. No manipular el dispositivo, 3. No alterar el IMEI, 4. No vulnerar la plataforma,",
            "5. No usar el servicio para fines ilícitos, 6. Mantener confidencialidad de claves."
        ]),
        ("CLÁUSULA OCTAVA. PROHIBICIONES:", [
            "1. Acceder al software interno, 2. Realizar ingeniería inversa o copias, 3. Divulgar información técnica,",
            "4. Sublicenciar o transferir el servicio, 5. Manipular identidad o IMEI."
        ]),
        ("CLÁUSULA NOVENA. DURACIÓN:", [
            "El servicio dura doce (12) meses desde la activación. Finalizado el periodo, se deshabilita automáticamente.",
            "MiCelu eliminará la información al cierre del servicio."
        ]),
        ("CLÁUSULA DÉCIMA. RESPONSABILIDAD DE MICELU:", [
            "MiCelu responde únicamente por la plataforma y su funcionamiento básico. No responde por: a) Fallas de terceros,",
            "b) Problemas de conectividad externa, c) Manipulación del dispositivo, d) Cambios de IMEI, e) Daños indirectos."
        ])
    ]
    
    c.setFont("Helvetica", 8)
    
    for titulo, contenido in clausulas:
        # Verificar si necesitamos nueva página
        if y < 2 * inch:
            c.showPage()
            y = height - 0.75 * inch
            c.setFont("Helvetica", 8)
        
        # Título de la cláusula
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin_left, y, titulo)
        y -= 0.15 * inch
        
        # Contenido
        c.setFont("Helvetica", 8)
        for line in contenido:
            if y < 1.5 * inch:
                c.showPage()
                y = height - 0.75 * inch
                c.setFont("Helvetica", 8)
            c.drawString(margin_left, y, line)
            y -= 0.13 * inch
        
        y -= 0.1 * inch
    
    # Nueva página para datos del usuario
    c.showPage()
    y = height - 0.75 * inch
    
    # ========== DATOS DEL USUARIO ==========
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "DATOS DEL TITULAR QUE ACEPTA EL CONTRATO:")
    y -= 0.3 * inch
    
    c.setFont("Helvetica", 9)
    datos = [
        f"Documento: {datos_usuario.get('documento', 'N/A')}",
        f"Nombre: {datos_usuario.get('nombre', 'N/A')}",
        f"Email: {datos_usuario.get('email', 'N/A')}",
        f"Teléfono: {datos_usuario.get('telefono', 'N/A')}",
        f"Ciudad: {datos_usuario.get('ciudad', 'N/A')}",
        f"Fecha de aceptación: {datos_usuario.get('fecha', 'N/A')}",
        f"Dirección IP: {datos_usuario.get('ip', 'N/A')}"
    ]
    
    for dato in datos:
        c.drawString(margin_left, y, dato)
        y -= 0.2 * inch
    
    y -= 0.2 * inch
    
    # ========== FIRMA DIGITAL ==========
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "FIRMA DIGITAL (HASH SHA-256):")
    y -= 0.25 * inch
    
    c.setFont("Courier", 7)
    # Dividir el hash en líneas de 64 caracteres
    hash_line1 = hash_firma[:64]
    c.drawString(margin_left, y, hash_line1)
    y -= 0.3 * inch
    
    # ========== PIE DE PÁGINA ==========
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin_left, y, "DECLARACIÓN DE ACEPTACIÓN:")
    y -= 0.2 * inch
    
    c.setFont("Helvetica", 8)
    declaracion = [
        "El usuario declara que ha leído íntegramente el presente contrato, comprende sus términos y condiciones,",
        "y manifiesta su aceptación expresa mediante clic en la plataforma digital de MICELU.CO S.A.S.",
        "Esta firma digital constituye prueba plena del perfeccionamiento del contrato conforme a la Ley 527 de 1999."
    ]
    
    for line in declaracion:
        c.drawString(margin_left, y, line)
        y -= 0.15 * inch
    
    y -= 0.2 * inch
    c.setFont("Helvetica", 7)
    c.drawString(margin_left, y, f"Documento generado automáticamente el {datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')}")
    y -= 0.12 * inch
    c.drawString(margin_left, y, "Este documento tiene validez legal como firma electrónica según la legislación colombiana.")
    
    # Finalizar PDF
    c.save()
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    return pdf_content
