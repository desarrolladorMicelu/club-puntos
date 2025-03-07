import base64
from functools import wraps
import io
import os
import random
import secrets
import string
from time import timezone
from flask import Flask, flash, jsonify, logging, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
import pyodbc
from flask_bcrypt import Bcrypt  
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import uuid
import requests
from sqlalchemy.dialects.postgresql import UUID
from pytz import UTC
import sqlalchemy
from woocommerce import API
from sqlalchemy import Float
from azure.communication.email import EmailClient


 
app = Flask(__name__)
# Configurar el tiempo de la sesión a 30 minutos
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
#Envio correo recuperar contraseña
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'my_session'
app.config['SECRET_KEY'] = 'yLxqdG0BGUft0Ep'
app.config['SQLALCHEMY_BINDS'] = {
    #'db2':'postgresql://postgres:WeLZnkiKBsfVFvkaRHWqfWtGzvmSnOUn@viaduct.proxy.rlwy.net:35149/railway',
    'db3':'postgresql://postgres:vWUiwzFrdvcyroebskuHXMlBoAiTfgzP@junction.proxy.rlwy.net:47834/railway'
}
 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  
mail = Mail(app)
 
recovery_codes = {}
 
wcapi = API(
    url="http://example.com",
    consumer_key="ck_24e1d02972506069aec3b589f727cc58636491df",
    consumer_secret="cs_8bd38a861efefc56403c7899d5303c3351c9e028",
    version="wc/v3"
)
 
 
#Modelos base de datos Plan de Beneficios
class Usuario(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'Usuarios'
    __table_args__ = {'schema': 'plan_beneficios'}
    
    documento = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(50))
    telefono= db.Column(db.String(50), nullable=False)
    contraseña = db.Column(db.String(100))
    habeasdata = db.Column(db.Boolean)
    ciudad = db.Column(db.String(40))
    nombre = db.Column(db.String(50))
    rango = db.Column(db.String(50))
    estado = db.Column(db.Boolean, default=True)
    genero = db.Column(db.String(20))
    fecha_nacimiento = db.Column(db.Date)
    barrio = db.Column(db.String(100))
 
class Puntos_Clientes(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'Puntos_Clientes'
    __table_args__ = {'schema': 'plan_beneficios'}
    documento = db.Column(db.String(50), primary_key=True)
    total_puntos = db.Column(db.Integer)
    puntos_redimidos = db.Column(db.String(50))
    fecha_registro = db.Column(db.TIMESTAMP(timezone=True))
    puntos_disponibles = db.Column(db.Integer)
    puntos_regalo = db.Column(db.Integer)
   
class historial_beneficio(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'historial_beneficio'
    __table_args__ = {'schema': 'plan_beneficios'}
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento = db.Column(db.String(50), primary_key=True)
    valor_descuento = db.Column(db.Integer)
    puntos_utilizados = db.Column(db.Integer)
    fecha_canjeo = db.Column(db.TIMESTAMP(timezone=True))
    cupon = db.Column(db.String(70))
    tiempo_expiracion = db.Column(db.TIMESTAMP(timezone=True))
    cupon_fisico = db.Column(db.String(70))
    estado = db.Column(db.Boolean, default=False)
   
class maestros(db.Model):
    __bind_key__= 'db3'
    __tablename__= 'maestros'
    __table_args__ = {'schema': 'plan_beneficios'}
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    valordelpunto = db.Column(db.Float)
    obtener_puntos = db.Column(db.Float)

class Referidos(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'referidos'
    __table_args__ = {'schema': 'plan_beneficios'}
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_cliente = db.Column(db.String, nullable=False)
    puntos_obtenidos = db.Column(db.Integer)
    fecha_referido = db.Column(db.DateTime, default=datetime.now)
    documento_referido = db.Column(db.String, nullable=False)
    nombre_referido = db.Column(db.String, nullable=False)
    nombre_cliente = db.Column(db.String, nullable = False)
    estado = db.Column(db.Boolean)
    fecha_actualizacion = db.Column(db.DateTime)

class cobertura_clientes(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'cobertura_clientes'
    __table_args__ = {'schema': 'plan_beneficios'}

    documento = db.Column(db.String(50), primary_key=True, nullable=False)
    imei = db.Column(db.String(50), nullable=False, unique=True)
    nombreCliente = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, nullable=False)
    valor = db.Column(db.String(50), nullable=False)
    referencia = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_documento' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
 
@app.route('/recuperar_pass', methods=['GET', 'POST'])
def recuperar_pass():
    if request.method == 'POST':
        documento = request.form.get('documento')
        email = request.form.get('email')
              
        usuario = Usuario.query.filter_by(documento=documento, email=email).first()
        if usuario:
            caracteres = string.ascii_uppercase + string.digits
            codigo = ''.join(secrets.choice(caracteres) for _ in range(6))
           
            # Establecer tiempo de expiración
            expiracion = datetime.now() + timedelta(minutes=15)
           
            # Guardar código con tiempo de expiración
            recovery_codes[email] = {'codigo': codigo, 'expiracion': expiracion}
           
            # Enviar correo
            try:
                email_client = EmailClient.from_connection_string("endpoint=https://email-sender-communication-micelu.unitedstates.communication.azure.com/;accesskey=VmkxyJLEb9bzf+23ve1gMPSCHC9jluovcOIJoSyrWrKPhBflOywY6HRWFj9u6pAULH+qsr6UGrlgBeCjuNcpMA==")
                message = {
                    "content": {
                        "subject": "Código de recuperación de contraseña micelu.co",
                        "plainText": f"Tu código de recuperación es: {codigo}. Este código expirará en 15 minutos."
                    },
                    "recipients": {
                        "to": [
                            {
                                "address": email,
                                "displayName": "Customer Name"
                            }
                        ]
                    },
                    "senderAddress": "DoNotReply@baca2159-db63-4c5c-87b8-a2fcdcec0539.azurecomm.net"
                }
                poller = email_client.begin_send(message)
                return jsonify({
                    'success': True,
                    'message': 'Se ha enviado un código de recuperación a tu email. El código expirará en 15 minutos.'
                })
            except Exception as e:
                app.logger.error(f"Error al enviar email: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Hubo un error al enviar el código. Por favor, intenta de nuevo más tarde.'
                })
        else:
            app.logger.warning(f"No se encontró usuario para documento: {documento}, email: {email}")
            return jsonify({
                'success': False,
                'message': 'No se encontró un usuario con esos datos. Por favor, verifica la información.'
            })
    return render_template('recuperar_pass.html')
 
@app.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    email = request.form.get('email')
    codigo_ingresado = request.form.get('codigo')
   
    if email in recovery_codes and recovery_codes[email]['codigo'] == codigo_ingresado:
        # Código válido, proceder con la recuperación de contraseña
        del recovery_codes[email]  # Eliminar el código usado
        return jsonify({'success': True, 'message': 'Código válido. Puedes proceder a cambiar tu contraseña.'})
    else:
        return jsonify({'success': False, 'message': 'Su codigo ha expirado o es incorrecto, Porfavor solicitar otro.'})
   
@app.route('/cambiar_contrasena', methods=['POST'])
def cambiar_contrasena():
    email = request.form.get('email')
    nueva_contrasena = request.form.get('nueva_contrasena')
   
    if len(nueva_contrasena) < 5:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 5 caracteres.'})
   
    if ' ' in (nueva_contrasena):
        return jsonify(({'success': False, 'message': 'La contraseña no puede contener espacios.'}))
   
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario:
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        usuario.contraseña = hashed_password
        db.session.commit()
        return jsonify({'success': True, 'message': 'Contraseña cambiada exitosamente.'})
    else:
        return jsonify({'success': False, 'message': 'Usuario no encontrado.'})
    
@app.route('/miperfil')
@login_required
def miperfil():
    documento_usuario = session.get('user_documento')
   
    usuario = Usuario.query.filter_by(documento=documento_usuario).first()
   
    if usuario:
        # Consultar los puntos del usuario
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento_usuario).first()
        if puntos_usuario:
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            puntos_regalo = int(puntos_usuario.puntos_regalo or '0')  # Aseguramos que puntos_regalo esté presente
            total_puntos = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos
        else:
            total_puntos = 0
       
        # Consultar el último registro de historial_beneficio
        ultimo_historial = Puntos_Clientes.query.filter_by(documento=documento_usuario).order_by(Puntos_Clientes.fecha_registro.desc()).first()
       
       
        # Pasar los datos a la plantilla
        return render_template('miperfil.html', usuario=usuario, total_puntos=total_puntos, ultimo_historial=ultimo_historial)
    else:
        flash('No se encontró el usuario en la base de datos.', 'error')
        return redirect(url_for('login'))
#---------------------------------------------------LOGIN-------------------------------------------------
@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    data = request.json
    field = data.get('field')
    value = data.get('value')
    documento_usuario = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento_usuario).first()
   
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
   
    if field == 'email':
        usuario.email = value
    elif field == 'telefono':
        usuario.telefono = value
    else:
        return jsonify({'success': False, 'message': 'Campo no válido'}), 400
   
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Perfil actualizado correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
 
#---------------------------------------------------LOGIN-------------------------------------------------



@app.route('/iniciosesion', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Comentamos la generación del captcha
        # captcha_text, captcha_image = generate_captcha_image()
        # session['captcha'] = captcha_text
        # return render_template('login.html', captcha_image=captcha_image)
        return render_template('login.html')
    elif request.method == 'POST':
        documento = str(request.form.get('documento'))
        contraseña = str(request.form.get('contraseña'))
        # Comentamos la verificación del captcha
        # user_captcha = request.form.get('captcha')
       
        # Eliminamos la verificación del captcha
        # if user_captcha != session.get('captcha'):
        #     return jsonify({'status': 'error', 'message': 'Captcha incorrecto. Por favor, intenta de nuevo.'})
       
        user = Usuario.query.filter_by(documento=documento).first()
        if user and user.contraseña and contraseña:
            # Verificar el estado del usuario
            if not user.estado:
                return jsonify({'status': 'error', 'message': 'Usuario inactivo. No fue posible iniciar sesión. Por favor acércate a las oficinas para cambiar tu estado.'})
           
            try:
                if bcrypt.check_password_hash(user.contraseña, contraseña):
                    session['user_documento'] = user.documento
                    # Hacer la sesión permanente pero con tiempo de vida limitado
                    session.permanent = True
                    return jsonify({'status': 'success', 'message': f'Bienvenido, {user.nombre}. Has iniciado sesión correctamente.', 'redirect_url': url_for('quesonpuntos')})
                else:
                    return jsonify({'status': 'error', 'message': 'Contraseña incorrecta. Por favor, intenta de nuevo.'})
            except ValueError as e:
                print(f"Error al verificar la contraseña: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Error al verificar la contraseña. Por favor, contacta al administrador.'})
        else:
            return jsonify({'status': 'error', 'message': 'Documento o Contraseña Incorrectos. Por favor, intenta de nuevo.'})

#@app.route('/refresh_captcha', methods=['GET'])
#def refresh_captcha():
 #   captcha_text, captcha_image = generate_captcha_image()
  #  session['captcha'] = captcha_text
   # return jsonify({'captcha_image': captcha_image})


@app.route('/login', methods=["GET", "POST"])
def loginn():
    return render_template('login.html')

#--------------------RUTA HISTORIAL --------------------------------------------------
@app.route('/mhistorialcompras')
@login_required
def mhistorialcompras():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
    if not documento:
        return redirect(url_for('login'))
    try:
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=20.109.21.246;"
            "DATABASE=MICELU;"
            "UID=db_read;"
            "PWD=mHRL_<='(],#aZ)T\"A3QeD;"
            "TrustServerCertificate=yes"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        # Verificar si el cliente existe
        check_query = """
        SELECT COUNT(*) as count
        FROM Clientes c
        WHERE c.HABILITADO = 'S' AND c.NIT = ?
        """
        cursor.execute(check_query, documento)
        # Consulta de facturas modificada para evitar duplicados
        query = """
        SELECT DISTINCT
         m.NOMBRE AS PRODUCTO_NOMBRE,
         m.VLRVENTA,
         m.FHCOMPRA,
         m.TIPODCTO,
         m.NRODCTO,
         mt.CODLINEA AS LINEA,
         vv.MEDIOPAG,
         m.PRODUCTO
        FROM
            Clientes c
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        JOIN
            MtMercia mt ON mt.CODIGO = m.PRODUCTO
        LEFT JOIN
            v_ventas vv ON vv.TipoDcto = m.Tipodcto AND vv.nrodcto = m.NRODCTO
        WHERE
            c.HABILITADO = 'S'
            AND (c.NIT = ? OR c.NIT LIKE ?)
            AND m.VLRVENTA > 0
            AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
        ORDER BY
            m.FHCOMPRA DESC;
        """
        cursor.execute(query, (documento, f"{documento}%"))
        results = cursor.fetchall()
        historial = []
        total_puntos_nuevos = 0
        # Agrupamos por factura usando un identificador único para cada producto
        facturas_dict = {}
        for row in results:
            key = f"{row.TIPODCTO}-{row.NRODCTO}"
            # Identificador único por producto
            producto_key = f"{key}-{row.PRODUCTO}"
            if key not in facturas_dict:
                facturas_dict[key] = {
                    'items': {},  # Cambiado a diccionario para evitar duplicados
                    'lineas': set(),
                    'mediopag': row.MEDIOPAG.strip() if row.MEDIOPAG else '',
                    'total_venta': 0,
                    'fecha_compra': row.FHCOMPRA
                }
            # Solo agregar el producto si no existe
            if producto_key not in facturas_dict[key]['items']:
                facturas_dict[key]['items'][producto_key] = row
                facturas_dict[key]['total_venta'] += float(row.VLRVENTA)
                if row.LINEA:
                    facturas_dict[key]['lineas'].add(row.LINEA.upper())
        # Procesamos cada factura
        for factura_key, factura_info in facturas_dict.items():
            lineas = factura_info['lineas']
            mediopag = factura_info['mediopag']
            es_individual = len(factura_info['items']) == 1
            fecha_compra = factura_info['fecha_compra']
            total_venta_factura = factura_info['total_venta']
            # Condición 1: Líneas específicas
            tiene_cel_cyt = any('CEL' in l or 'CYT' in l for l in lineas)
            tiene_gdgt_acce = any('GDGT' in l or 'ACCE' in l for l in lineas)
            solo_gdgt_acce = all(
                'GDGT' in l or 'ACCE' in l for l in lineas) if lineas else False
            # Condición 2: Medio de pago y factura individual
            medio_pago_valido = mediopag in ['01', '02']
            # Determinar si aplicar multiplicador
            aplicar_multiplicador = False
            # Calcular puntos para toda la factura
            puntos_factura = 0
            # Obtener el valor base para el cálculo de puntos
            obtener_puntos = maestros.query.with_entities(
                maestros.obtener_puntos).first()[0]
            # Diferentes cálculos según el año
            if fecha_compra.year == 2024:
                # Para 2024, dividir los puntos entre 2
                puntos_factura = int(
                    (total_venta_factura // obtener_puntos) / 2)
                # Aplicar multiplicador x2 si cumple las condiciones después del 25 de noviembre
                if fecha_compra >= datetime(2024, 11, 25):
                    if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                        aplicar_multiplicador = True
                    if medio_pago_valido and es_individual:
                        aplicar_multiplicador = True
                    if aplicar_multiplicador:
                        puntos_factura *= 2
            elif fecha_compra.year == 2025:
                # Para 2025, cálculo normal sin división
                puntos_factura = int(total_venta_factura // obtener_puntos)
                # Aplicar multiplicador x2 si cumple las condiciones
                if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                    aplicar_multiplicador = True
                if medio_pago_valido and es_individual:
                    aplicar_multiplicador = True
                if aplicar_multiplicador:
                    puntos_factura *= 2
            total_puntos_nuevos += puntos_factura
            # Procesar cada item único de la factura
            for producto_key, row in factura_info['items'].items():
                venta_item = float(row.VLRVENTA)
                proporcion = venta_item / total_venta_factura if total_venta_factura > 0 else 0
                puntos_item = int(puntos_factura * proporcion)
                tipo_documento = "Factura Medellín" if row.TIPODCTO == "FM" else "Factura Bogotá" if row.TIPODCTO == "FB" else row.TIPODCTO
                historial.append({
                    "PRODUCTO_NOMBRE": row.PRODUCTO_NOMBRE,
                    "VLRVENTA": venta_item,
                    "FHCOMPRA": fecha_compra.strftime('%Y-%m-%d'),
                    "PUNTOS_GANADOS": puntos_item,
                    "TIPODCTO": tipo_documento,
                    "NRODCTO": row.NRODCTO,
                    "LINEA": row.LINEA,
                    "MEDIOPAG": row.MEDIOPAG,
                    "TIPO_REGISTRO": "COMPRA"
                })
        cursor.close()
        conn.close()
        referidos = Referidos.query.filter_by(
            documento_referido=documento).all()
        total_referidos_puntos = sum(
            referido.puntos_obtenidos for referido in referidos)
        total_puntos_nuevos += total_referidos_puntos
        for referido in referidos:
            historial.append({
                "FHCOMPRA": referido.fecha_referido.strftime('%Y-%m-%d'),
                "PRODUCTO_NOMBRE": f"Referido: {referido.nombre_cliente}",
                "VLRVENTA": referido.puntos_obtenidos * 100,
                "TIPODCTO": "Referido",
                "NRODCTO": str(referido.id),
                "PUNTOS_GANADOS": referido.puntos_obtenidos,
                "LINEA": "REFERIDO",
                "MEDIOPAG": ""
            })
        puntos_usuario = Puntos_Clientes.query.filter_by(
            documento=documento).first()
        if puntos_usuario:
            puntos_regalo = puntos_usuario.puntos_regalo or 0
            puntos_usuario.total_puntos = total_puntos_nuevos
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            puntos_regalo = int(puntos_usuario.puntos_regalo or '0')
            total_puntos = max(0, (puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos))
            db.session.commit()
        else:
            nuevo_usuario = Puntos_Clientes(
                documento=documento,
                total_puntos=total_puntos_nuevos,
                puntos_redimidos='0',
                puntos_regalo=0
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            total_puntos = total_puntos_nuevos
        historial.sort(key=lambda x: x['FHCOMPRA'], reverse=True)
        return render_template(
            'mhistorialcompras.html',
            historial=historial,
            total_puntos=total_puntos,
            usuario=usuario,
            puntos_regalo=puntos_usuario.puntos_regalo if puntos_usuario else 0
        )
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('error_page'))
    
@app.route('/mpuntosprincipal')
@login_required
def mpuntosprincipal():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
   
    total_puntos = 0
   
    if documento:
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
            puntos_regalo = int(puntos_usuario.puntos_regalo or 0)
            total_puntos = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos
   
    try:
        wcapi = API(
            url="https://micelu.co",
            consumer_key="ck_24e1d02972506069aec3b589f727cc58636491df",
            consumer_secret="cs_8bd38a861efefc56403c7899d5303c3351c9e028",
            version="wc/v3",
            timeout=30
        )
       
        response = wcapi.get("products", params={
            "per_page": 12,  
            "orderby": "date",
            "order": "desc",
            "status": "publish"  
        })
       
        if response.status_code == 200:
            wc_products = response.json()
           
            products = []
            for wc_product in wc_products:
                try:
                    product = {
                        'id': wc_product.get('id', ''),
                        'name': wc_product.get('name', 'Sin Nombre').title(),
                        'price': wc_product.get('price', '0'),
                        'description': wc_product.get('description', ''),
                        'short_description': wc_product.get('short_description', ''),
                        'image_url': wc_product.get('images', [{'src': url_for('static', filename='images/placeholder.png')}])[0]['src'],
                        'slug': wc_product.get('slug', '')
                    }
                    products.append(product)
                except Exception as product_error:
                    print(f"Error processing product: {product_error}")
        else:
            products = []
   
    except Exception as e:
        print(f"Error fetching products: {e}")
        products = []
   
    return render_template('mpuntosprincipal.html', total_puntos=total_puntos, products=products, usuario=usuario)
 
wcapi = API(
    url="https://micelu.co",
    consumer_key="ck_4a0a6ac32a9cbfe9d5f0dd4a029312e0893e22a7",
    consumer_secret="cs_e7d06f5199b3982b3e02234cc305a8f2d0b71dd0",
    version="wc/v3"
)



@app.route('/redimir_puntos', methods=['POST'])
@login_required
def redimir_puntos():
    try:
        documento = session.get('user_documento')
        puntos_a_redimir = int(request.json.get('points'))
        codigo = request.json.get('code')
        horas_expiracion = int(request.json.get('expiration_hours', 12))
 
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if not puntos_usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
 
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
        puntos_regalo= int(puntos_usuario.puntos_regalo or "0")
        puntos_disponibles = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos
 
        if puntos_a_redimir > puntos_disponibles:
            return jsonify({'success': False, 'message': 'No tienes suficientes puntos'}), 400
 
        valor_del_punto = maestros.query.with_entities(maestros.valordelpunto).first()[0]
        descuento = puntos_a_redimir * valor_del_punto
        tiempo_expiracion = datetime.now() + timedelta(hours=horas_expiracion)
 
        woo_coupon = create_woo_coupon(codigo, descuento, tiempo_expiracion)
        if not woo_coupon:
            return jsonify({'success': False, 'message': 'Error al crear el cupón en WooCommerce'}), 500
 
        puntos_usuario.puntos_redimidos = str(puntos_redimidos + puntos_a_redimir)
        puntos_usuario.puntos_disponibles = puntos_usuario.total_puntos - int(puntos_usuario.puntos_redimidos)
 
        nuevo_historial = historial_beneficio(
            id=uuid.uuid4(),
            documento=documento,
            valor_descuento=descuento,
            puntos_utilizados=puntos_a_redimir,
            fecha_canjeo=datetime.now(),
            cupon=codigo,
            tiempo_expiracion=tiempo_expiracion
        )
 
        db.session.add(nuevo_historial)
        db.session.commit()
 
        return jsonify({
            'success': True,
            'new_total': puntos_usuario.puntos_disponibles,
            'codigo': codigo,
            'descuento': descuento,
            'tiempo_expiracion': tiempo_expiracion.isoformat()
        }), 200
 
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': f'Error al redimir puntos: {str(e)}'}), 500
    
 # crear cupones a redimir 
def create_woo_coupon(code, amount, expiration_time):
    try:
        data = {
            "code": code,
            "discount_type": "fixed_cart",
            "amount": str(amount),
            "individual_use": True,
            "exclude_sale_items": True,
            "usage_limit": 1,
            "date_expires": expiration_time.strftime("%Y-%m-%dT%H:%M:%S")
        }
 
        response = wcapi.post("coupons", data)
        response.raise_for_status()  
        coupon_data = response.json()
 
        if 'id' in coupon_data:
            return coupon_data
        else:
            print(f"Error al crear cupón: {coupon_data}")
            return None
 
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a WooCommerce API: {e}")
        return None
    except ValueError as e:
        print(f"Error al procesar la respuesta JSON: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al crear cupón en WooCommerce: {e}")
        return None
    

@app.route('/ver_ultimo_coupon', methods=['GET'])
@login_required
def ultimo_coupon():
    try:
        documento = session.get('user_documento')
        ultimo_historial = historial_beneficio.query.filter_by(documento=documento).order_by(historial_beneficio.fecha_canjeo.desc()).first()
 
        if ultimo_historial:
            return jsonify({
                'success': True,
                'codigo': ultimo_historial.cupon,
                'descuento': ultimo_historial.valor_descuento,
                'tiempo_expiracion': ultimo_historial.tiempo_expiracion
            })
        else:
            return jsonify({'success': False, 'message': 'No se encontró ningún cupón'}), 404
 
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener el último cupón'}), 500  


#Ruta para manejar el descuento de los puntos



@app.route('/quesonpuntos')
@login_required
def quesonpuntos():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
    if not documento:
        return redirect(url_for('login'))
    
    try:
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=20.109.21.246;"
            "DATABASE=MICELU;"
            "UID=db_read;"
            "PWD=mHRL_<='(],#aZ)T\"A3QeD;"
            "TrustServerCertificate=yes"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Consulta de facturas
        query = """
        SELECT DISTINCT
         m.NOMBRE AS PRODUCTO_NOMBRE,
         m.VLRVENTA,
         m.FHCOMPRA,
         m.TIPODCTO,
         m.NRODCTO,
         mt.CODLINEA AS LINEA,
         vv.MEDIOPAG,
         m.PRODUCTO
        FROM
            Clientes c
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        JOIN
            MtMercia mt ON mt.CODIGO = m.PRODUCTO
        LEFT JOIN
            v_ventas vv ON vv.TipoDcto = m.Tipodcto AND vv.nrodcto = m.NRODCTO
        WHERE
            c.HABILITADO = 'S'
            AND (c.NIT = ? OR c.NIT LIKE ?)
            AND m.VLRVENTA > 0
            AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
        ORDER BY
            m.FHCOMPRA DESC;
        """
        cursor.execute(query, (documento, f"{documento}%"))
        results = cursor.fetchall()
        historial = []
        total_puntos_nuevos = 0
        
        # Agrupamos por factura usando un identificador único para cada producto
        facturas_dict = {}
        for row in results:
            key = f"{row.TIPODCTO}-{row.NRODCTO}"
            producto_key = f"{key}-{row.PRODUCTO}"
            if key not in facturas_dict:
                facturas_dict[key] = {
                    'items': {},
                    'lineas': set(),
                    'mediopag': row.MEDIOPAG.strip() if row.MEDIOPAG else '',
                    'total_venta': 0,
                    'fecha_compra': row.FHCOMPRA
                }
            
            if producto_key not in facturas_dict[key]['items']:
                facturas_dict[key]['items'][producto_key] = row
                facturas_dict[key]['total_venta'] += float(row.VLRVENTA)
                if row.LINEA:
                    facturas_dict[key]['lineas'].add(row.LINEA.upper())
        
        # Procesamos cada factura (mismo código que en mhistorialcompras)
        for factura_key, factura_info in facturas_dict.items():
            lineas = factura_info['lineas']
            mediopag = factura_info['mediopag']
            es_individual = len(factura_info['items']) == 1
            fecha_compra = factura_info['fecha_compra']
            total_venta_factura = factura_info['total_venta']
            
            # Condiciones de cálculo de puntos (igual que en mhistorialcompras)
            tiene_cel_cyt = any('CEL' in l or 'CYT' in l for l in lineas)
            tiene_gdgt_acce = any('GDGT' in l or 'ACCE' in l for l in lineas)
            solo_gdgt_acce = all(
                'GDGT' in l or 'ACCE' in l for l in lineas) if lineas else False
            medio_pago_valido = mediopag in ['01', '02']
            aplicar_multiplicador = False
            puntos_factura = 0
            
            # Obtener el valor base para el cálculo de puntos
            obtener_puntos = maestros.query.with_entities(
                maestros.obtener_puntos).first()[0]
            
            # Cálculo de puntos (igual que en mhistorialcompras)
            if fecha_compra.year == 2024:
                puntos_factura = int(
                    (total_venta_factura // obtener_puntos) / 2)
                if fecha_compra >= datetime(2024, 11, 25):
                    if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                        aplicar_multiplicador = True
                    if medio_pago_valido and es_individual:
                        aplicar_multiplicador = True
                    if aplicar_multiplicador:
                        puntos_factura *= 2
            elif fecha_compra.year == 2025:
                puntos_factura = int(total_venta_factura // obtener_puntos)
                if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                    aplicar_multiplicador = True
                if medio_pago_valido and es_individual:
                    aplicar_multiplicador = True
                if aplicar_multiplicador:
                    puntos_factura *= 2
            
            total_puntos_nuevos += puntos_factura
        
        cursor.close()
        conn.close()
        
        # Agregar puntos de referidos
        referidos = Referidos.query.filter_by(
            documento_referido=documento).all()
        total_referidos_puntos = sum(
            referido.puntos_obtenidos for referido in referidos)
        total_puntos_nuevos += total_referidos_puntos
        
        # Buscar o crear registro de puntos para el usuario
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        
        if not puntos_usuario:
            # Crear nuevo registro de puntos si no existe
            puntos_usuario = Puntos_Clientes(
                documento=documento,
                total_puntos=total_puntos_nuevos,
                puntos_redimidos='0',
                puntos_regalo=0
            )
            db.session.add(puntos_usuario)
        else:
            # Actualizar puntos si ya existe
            puntos_usuario.total_puntos = total_puntos_nuevos
        
        db.session.commit()
        
        # Calcular puntos totales con manejo seguro de valores nulos
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or 0)
        puntos_regalo = int(puntos_usuario.puntos_regalo or 0)
        total_puntos = max(0, (puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos))
        
        return render_template('puntos.html', 
                               total_puntos=total_puntos, 
                               usuario=usuario)
    
    except Exception as e:
        print(f"Error en quesonpuntos: {e}")
        # Registrar el error en un log si es posible
        return redirect(url_for('login'))  # Redirigir al login en caso de error

@app.route('/homepuntos')
def homepuntos():
    return render_template('home.html')



@app.route('/logout')
@login_required
def logout():
    session.pop('user_documento', None)
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

#----------------------------------CREAR CONTRASEÑA----------------------------------
@app.route('/crear_pass', methods=['GET', 'POST'])
def crear_pass():
    if request.method == 'POST':
        documento = request.form['documento']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']
        habeasdata = 'habeasdata' in request.form
        genero = request.form['genero'] 
        ciudad = request.form['ciudad']
        barrio = request.form['barrio']
        fecha_nacimiento = datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date()
       
        # Verificaciones existentes (sin cambios)
        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('crear_pass'))
       
        if len(contraseña) <= 4:
            flash('La contraseña debe tener más de 5 caracteres', 'danger')
            return redirect(url_for('crear_pass'))
       
        if ' ' in contraseña:
            flash('La contraseña no puede contener espacios', 'danger')
            return redirect(url_for('crear_pass'))
       
        usuario_existente = Usuario.query.filter_by(documento=documento).first()
        if usuario_existente:
            flash('Este documento ya ha sido registrado', 'danger')
            return redirect(url_for('crear_pass'))
       
        try:
            # Crear el usuario en la tabla original
            usuario_creado = crear_usuario(documento, contraseña, habeasdata, genero, ciudad, barrio, fecha_nacimiento)
           
            if usuario_creado:
                # Crear el registro en la tabla Puntos_Clientes
                nuevo_punto_cliente = Puntos_Clientes(
                    documento=documento,
                    total_puntos='0',
                    fecha_registro=datetime.now(UTC),
                    puntos_redimidos='0'
                )
                db.session.add(nuevo_punto_cliente)
                db.session.commit()
               
                flash('Usuario creado exitosamente. <a href="/" class="alert-link">Inicia sesión aquí</a>', 'success')
            else:
                flash('Cédula no registrada. Por favor, registre una compra', 'warning')
           
            return redirect(url_for('crear_pass'))
       
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash('Este documento ya ha sido registrado', 'danger')
        except sqlalchemy.exc.DataError as e:
            db.session.rollback()
            flash('Error en el formato de los datos. Por favor, revise la información ingresada.', 'danger')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error al crear el usuario: {str(e)}')
            flash('Ocurrió un error al crear el usuario. Por favor, inténtelo de nuevo.', 'danger')
       
        return redirect(url_for('crear_pass'))
   
    return render_template('crear_pass.html')
 
 
def crear_usuario(cedula, contraseña, habeasdata, genero, ciudad, barrio, fecha_nacimiento):
    try:
        # Extraer solo los primeros dígitos antes del guion o espacios
        documento = cedula.split('-')[0].split()[0]
 
        # Conexión a la base de datos
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=20.109.21.246;"
            "DATABASE=MICELU;"
            "UID=db_read;"
            "PWD=mHRL_<='(],#aZ)T\"A3QeD;"
            "TrustServerCertificate=yes"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
 
        # Consulta SQL modificada para usar los primeros dígitos
        query = """
        SELECT DISTINCT
            c.NOMBRE AS CLIENTE_NOMBRE,
            c.NIT,
            c.TEL1 AS telefono,
            c.EMAIL,
            c.CIUDAD,
            c.DescripTipoCli
        FROM
            Clientes c
        JOIN
            Canal cn ON c.CANAL = cn.CODCANAL
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        JOIN
            MtMercia mt ON m.PRODUCTO=mt.CODIGO
        WHERE
            c.HABILITADO = 'S'
            AND (m.TIPODCTO='FM' OR m.TIPODCTO='FB')
            AND m.VLRVENTA>0
            AND (c.NIT = ? OR c.NIT LIKE ?)
        ORDER BY
            c.NOMBRE;
        """
 
        # Ejecutar la consulta con el parámetro de cédula limpia
        cursor.execute(query, (documento, f"{documento}%"))
 
 
        # Obtener todos los resultados
        results = cursor.fetchall()
 
        # Cerrar la conexión
        cursor.close()
        conn.close()
 
        # Si no hay resultados, la cédula no está registrada
        if not results:
            return False
 
        with app.app_context():
            with db.session.begin():
                for row in results:
                    
                    ciudad= 'Medellin' if ciudad == 'Medellín' else 'Bogota' if ciudad == 'Bogotá' else ciudad
 
                    clave = bcrypt.generate_password_hash(contraseña).decode('utf-8')
                   
                    nuevo_usuario = Usuario(
                        documento=documento,  
                        email=row.EMAIL.strip() if row.EMAIL else None,
                        telefono=row.telefono.strip() if row.telefono else None,
                        contraseña=clave,
                        habeasdata=habeasdata,
                        ciudad=ciudad,
                        nombre=row.CLIENTE_NOMBRE.strip() if row.CLIENTE_NOMBRE else None,
                        rango=row.DescripTipoCli.strip() if row.DescripTipoCli else None,
                        estado=True,
                        genero=genero,
                        barrio=barrio,
                        fecha_nacimiento=fecha_nacimiento
                    )
                    db.session.add(nuevo_usuario)
                    db.session.commit()
 
        return True
 
    except pyodbc.Error as e:
        print("Error al conectarse a la base de datos:", e)
        raise e
    except Exception as e:
        print("Error al crear el usuario:", e)
        raise e
    
#------------------funciones para traer informacion del carrusel------------------------------------------------

def get_product_info(product_id):
    try:
        wcapi = API(
            url="https://micelu.co",
            consumer_key="ck_24e1d02972506069aec3b589f727cc58636491df",
            consumer_secret="cs_8bd38a861efefc56403c7899d5303c3351c9e028",
            version="wc/v3",
            timeout=30
        )
        
        response = wcapi.get(f"products/{product_id}")
        if response.status_code == 200:
            wc_product = response.json()
            product = {
                'id': wc_product['id'],
                'name': wc_product['name'],
                'price': wc_product['price'],
                'description': wc_product['description'],
                'short_description': wc_product['short_description'],
                'color': wc_product['attributes'][0]['options'][0] if wc_product['attributes'] else 'N/A',
                'image_url': wc_product['images'][0]['src'] if wc_product['images'] else url_for('static', filename='images/placeholder.png'),
                'points': int(float(wc_product['price']) * 0.01),  # Asumiendo que 1 punto = 1% del precio
                'attributes': wc_product['attributes']
            }
            return product
        else:
            print(f"Error al obtener el producto {product_id}: {response.text}")
            return None
    except Exception as e:
        print(f"Error al obtener producto de WooCommerce: {str(e)}")
        return None
    #----------------------------------- mpuntosprincipal-----------------------------
@app.route('/infobeneficios/<int:product_id>')
@login_required
def infobeneficios(product_id):
    product = get_product_info(product_id)
        # Asumimos que el documento del usuario está en la sesión
    documento = session.get('user_documento')
  
    total_puntos = 0
    if documento:
        # Consulta a la base de datos para obtener los puntos del usuario
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            total_puntos = puntos_usuario.total_puntos
    
    return render_template("infobeneficios.html", product=product, total_puntos=total_puntos)

@app.route('/redime_ahora')
def redime_ahora():
    documento_usuario = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento_usuario).first()
    total_puntos = 0
    if documento_usuario:
        usuario = Usuario.query.filter_by(documento=documento_usuario).first()
       
        if usuario:
   
            puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento_usuario).first()
            if puntos_usuario:
                puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
                puntos_regalo = int(puntos_usuario.puntos_regalo or 0) 
                total_puntos = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos
    return render_template("redime_ahora.html",total_puntos=total_puntos, usuario=usuario)

@app.route('/acumulapuntos')
def acumulapuntos():
    return render_template("acumulapuntos.html")

@app.route('/admin')
@login_required
def administrar():
    return render_template("admin.html")

@app.route('/')
def inicio():
    return render_template("home.html")

@app.route('/redimir')
def redimiendo():
    documento_usuario = session.get('user_documento')
    total_puntos = 0
    if documento_usuario:
        usuario = Usuario.query.filter_by(documento=documento_usuario).first()
       
        if usuario:
            puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento_usuario).first()
            if puntos_usuario:
                puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
                total_puntos = puntos_usuario.total_puntos - puntos_redimidos
   
    return render_template("redimir.html",total_puntos=total_puntos)
    
#--------------------------------- Cupon Tienda fisica------------------------------------

@app.route('/redimir_puntos_fisicos', methods=['POST'])
@login_required
def redimir_puntos_fisicos():
    try:
        documento = session.get('user_documento')
        puntos_a_redimir = int(request.json.get('points'))
        codigo = request.json.get('code')
        
        tiempo_expiracion = datetime.now() + timedelta(hours=12)
        
        # Verificar si el cupón ya existe y no ha expirado
        cupon_existente = historial_beneficio.query.filter_by(
            cupon_fisico=codigo, 
            documento=documento, 
            estado=False
        ).first()
        
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if not puntos_usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
        puntos_regalo = int(puntos_usuario.puntos_regalo or "0")
        puntos_disponibles = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos
        
        if puntos_a_redimir > puntos_disponibles:
            return jsonify({'success': False, 'message': 'No tienes suficientes puntos'}), 400
        
        valor_del_punto = maestros.query.with_entities(maestros.valordelpunto).first()[0]
        descuento = puntos_a_redimir * valor_del_punto
        
        if cupon_existente:
            # Verificar si el cupón ha expirado
            if datetime.now() > cupon_existente.tiempo_expiracion:
                cupon_existente.estado = True
                db.session.commit()
                return jsonify({
                    'success': False, 
                    'message': 'El cupón ha expirado'
                }), 400
            
            puntos_usuario.puntos_redimidos = str(puntos_redimidos + puntos_a_redimir)
            # Actualizar puntos_disponibles directamente
            puntos_usuario.puntos_disponibles = max(0, (puntos_usuario.total_puntos + puntos_regalo - int(puntos_usuario.puntos_redimidos)))
            
            cupon_existente.estado = True
            cupon_existente.valor_descuento = descuento
            cupon_existente.puntos_utilizados = puntos_a_redimir
            cupon_existente.fecha_canjeo = datetime.now()
            
        else:
            # Si no existe un cupón previo, crear uno nuevo
            puntos_usuario.puntos_redimidos = str(puntos_redimidos + puntos_a_redimir)
            # Actualizar puntos_disponibles directamente
            puntos_usuario.puntos_disponibles = max(0, (puntos_usuario.total_puntos + puntos_regalo - int(puntos_usuario.puntos_redimidos)))
            
            nuevo_historial = historial_beneficio(
                id=uuid.uuid4(),
                documento=documento,
                valor_descuento=descuento,
                puntos_utilizados=puntos_a_redimir,
                fecha_canjeo=datetime.now(),
                cupon='',
                cupon_fisico=codigo,
                tiempo_expiracion=tiempo_expiracion,
                estado=False
            )
            db.session.add(nuevo_historial)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_total': puntos_usuario.puntos_disponibles,  # Return the updated points
            'codigo': codigo,
            'descuento': descuento,
            'tiempo_expiracion': tiempo_expiracion.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': f'Error al redimir puntos: {str(e)}'}), 500
    
@app.route('/check_coupon_status', methods=['POST'])
@login_required
def check_coupon_status():
    try:
        documento = session.get('user_documento')
        codigo = request.json.get('code')
        
        cupon = historial_beneficio.query.filter_by(cupon_fisico=codigo,documento=documento).first()
        
        if not cupon:
            return jsonify({'valid': False, 'message': 'Cupón no encontrado'}), 404
        
        current_time = datetime.now().replace(tzinfo=None)
        expiration_time = cupon.tiempo_expiracion.replace(tzinfo=None)
        
        is_expired = current_time > expiration_time
        
        if is_expired:
            cupon.estado = True
            db.session.commit()
            return jsonify({'valid': False, 'message': 'Cupón expirado'}), 200
        
        return jsonify({
            'valid': not cupon.estado,
            'codigo': cupon.cupon_fisico,
            'descuento': cupon.valor_descuento,
            'expiracion': cupon.tiempo_expiracion.isoformat()
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({'valid': False, 'message': str(e)}), 500

#inicio de la cobertura
    
def obtener_conexion_bd():

    conn = pyodbc.connect('''DRIVER={ODBC Driver 18 for SQL Server};SERVER=20.109.21.246;DATABASE=MICELU;UID=db_read;PWD=mHRL_<='(],#aZ)T"A3QeD;TrustServerCertificate=yes''')

    return conn

def buscar_por_imei(imei):
    """
    Busca información asociada a un IMEI específico
    """
    conn = obtener_conexion_bd()
    cursor = conn.cursor()
    
    consulta = """
    WITH VSeriesUtilidadConcatenada AS (
        SELECT *, 
               Tipo_Documento + Documento AS Clave_Documento,
               LEFT(Serie, 15) AS Serie_Truncada
        FROM VSeriesUtilidad WITH (NOLOCK)
        WHERE Tipo_Documento IN ('FB', 'FM')
          AND Valor > 0
          AND LEFT(Serie, 15) = ?
    ),
    VreporteMVtradeConcatenada AS (
        SELECT *, 
               T_Dcto + Documento AS Clave_Documento
        FROM VreporteMVtrade WITH (NOLOCK)
        WHERE Vendedor NOT IN ('1000644140', '0', '1026258734')
    ),
    MtMerciaFiltrada AS (
        SELECT *
        FROM MtMercia WITH (NOLOCK)
        WHERE CODLINEA = 'CEL'
          AND CODGRUPO = 'SEMI'
    ),
    SeriesUnicas AS (
        SELECT DISTINCT TOP 1
            VS.Serie_Truncada AS IMEI,
            VS.Referencia AS Producto, 
            VS.Valor AS Valor,
            VS.Fecha_Inicial AS Fecha, 
            VS.NIT, 
            C.NOMBRE AS Nombre_Cliente, 
            C.EMAIL AS Correo, 
            C.TEL1 AS Telefono
        FROM 
            Clientes C WITH (NOLOCK)
        JOIN 
            VSeriesUtilidadConcatenada VS ON C.NIT = VS.NIT
        JOIN 
            VreporteMVtradeConcatenada VR ON VS.Clave_Documento = VR.Clave_Documento
        JOIN 
            MtMerciaFiltrada MM ON VS.Producto = MM.CODIGO
    )
    SELECT * FROM SeriesUnicas;
    """
    
    try:
        cursor.execute(consulta, (imei,))
        resultado = cursor.fetchone()
        
        if resultado:
            return {
                'imei': resultado.IMEI,
                'referencia': resultado.Producto,
                'valor': float(resultado.Valor),
                'fecha': resultado.Fecha.strftime('%Y-%m-%d') if resultado.Fecha else None,
                'nit': resultado.NIT,
                'nombre': resultado.Nombre_Cliente,
                'correo': resultado.Correo,
                'telefono': resultado.Telefono
            }
        return None
        
    except Exception as e:
        app.logger.error(f"Error en la consulta: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()
        
def obtener_token_auth():
    url = 'https://ms.proteccionmovil.co/api/v1/auth/token'
    params = {
        'clientId': 'Q7bMfHwO6f2l4uWGV5B9',
        'clientSecret': '6jfbwulaBbQ165xmblQxmgQZHsbyM1hoSjpjzA4m'
    }
    
    respuesta = requests.get(url, params=params)
    datos_respuesta = respuesta.json()
    
    return datos_respuesta['data']['token'], datos_respuesta['data']['type']
def list_policy_options(imei, token, token_type):
    """
    Obtiene las opciones de póliza disponibles para un IMEI específico.
    
    Args:
        imei (str): IMEI del dispositivo
        token (str): Token de autenticación
        token_type (str): Tipo de token
    
    Returns:
        tuple: (plan_id, price_option_id) si es exitoso
        dict: Diccionario con error si falla
    """
    try:
        url = 'https://ms.proteccionmovil.co/api/v1/policies/options'
        headers = {
            'Authorization': f'{token_type} {token}',
            'Content-Type': 'application/json'
        }
        params = {
            'imei': imei,
            'sponsorId': 'MICELU'
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if response.status_code != 200 or 'data' not in data:
            return {
                'error': {
                    'message': data.get('message', 'Error al obtener opciones de póliza'),
                    'status': response.status_code
                }
            }
            
        # Obtener el primer plan y su primera opción de precio
        plans = data['data'].get('plans', [])
        if not plans:
            return {
                'error': {
                    'message': 'No hay planes disponibles para este IMEI'
                }
            }
            
        first_plan = plans[0]
        price_options = first_plan.get('priceOptions', [])
        if not price_options:
            return {
                'error': {
                    'message': 'No hay opciones de precio disponibles para este plan'
                }
            }
            
        return first_plan['id'], price_options[0]['id']
        
    except Exception as e:
        return {
            'error': {
                'message': f'Error al obtener opciones de póliza: {str(e)}'
            }
        }

class CoberturaEmailService:
    def __init__(self):
        # Configuración de conexión de Azure Communication Services
        self.connection_string = "endpoint=https://email-sender-communication-micelu.unitedstates.communication.azure.com/;accesskey=VmkxyJLEb9bzf+23ve1gMPSCHC9jluovcOIJoSyrWrKPhBflOywY6HRWFj9u6pAULH+qsr6UGrlgBeCjuNcpMA=="
        self.sender_address = "DoNotReply@baca2159-db63-4c5c-87b8-a2fcdcec0539.azurecomm.net"

    def enviar_confirmacion_cobertura(self, datos_cobertura, fecha_fin):
        try:
            email_client = EmailClient.from_connection_string(self.connection_string)

            # URL de la imagen
            url_imagen = "https://i.ibb.co/1DsGPLQ/imagen.jpg"

            contenido_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="{url_imagen}" alt="Logo Micelu" style="max-width:600px; display: block; margin: 0 auto;">
                </div>
                <h2 style="color: #333;">Confirmación de Cobertura</h2>
                <p>Estimado(a) {datos_cobertura['nombreCliente']},</p>
                <p>Su cobertura ha sido activada exitosamente por 1 año con los siguientes detalles:</p>
                <ul>
                    <li><strong>IMEI:</strong> {datos_cobertura['imei']}</li>
                    <li><strong>Fecha de compra:</strong> {datos_cobertura['fecha'].strftime('%d/%m/%Y')}</li>
                    <li><strong>Valor:</strong> ${datos_cobertura['valor']}</li>
                    <li><strong>Vigencia hasta:</strong> {fecha_fin}</li>
                </ul>
                <p>Gracias por confiar en nosotros.</p>
                <p>Atentamente,<br>Equipo Micelu.co</p>
            </body>
            </html>
            """

            # Preparar destinatarios
            destinatarios = [
                {
                    "address": datos_cobertura['correo'],
                    "displayName": datos_cobertura['nombreCliente']
                }
            ]
            # Mensaje de correo
            mensaje = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": dest["address"], "displayName": dest["displayName"]} for dest in destinatarios]
                },
                "content": {
                    "subject": "Confirmación de Cobertura micelu.co",
                    "html": contenido_html
                }
            }

            # Enviar correo
            poller = email_client.begin_send(mensaje)
            result = poller.result()

            return True, None

        except Exception as e:
            mensaje_error = f"Error al enviar correo de cobertura: {str(e)}"
            app.logger.error(mensaje_error)
            return False, mensaje_error
# Crear una instancia del servicio de correo para coberturas
cobertura_email_service = CoberturaEmailService()

def clean_text(value):
    if isinstance(value, str):
        return ' '.join(value.split())
    return value



@app.route("/create_policy", methods=['POST'])
def create_policy():
    try:
        datos = request.json
        imei = datos.get('imei')
        nombre = datos.get('nombre', '').strip()
        nit = datos.get('nit', '').strip()
        correo = datos.get('correo', '').strip()

        if not all([imei, nombre, nit, correo]):
            return jsonify({
                'exito': False,
                'mensaje': 'Todos los campos son requeridos Completa la informacion en mi perfil'
            }), 400

        # Obtener token de autenticación
        token, token_type = obtener_token_auth()

        # Verificar si existe la póliza
        url = f'https://ms.proteccionmovil.co/api/v1/policy/imei/{imei}?sponsorId=MICELU'
        headers = {
            'Authorization': f'{token_type} {token}'
        }
        
        response = requests.get(url, headers=headers)
        policy_data = response.json()
        
        # Si encuentra una póliza existente, retornar éxito
        if 'data' in policy_data and policy_data['data'].get('policies'):
            return jsonify({
                'exito': True,
                'mensaje': 'El IMEI ya cuenta con una póliza',
                'poliza_existente': True
            })

        # Si no existe póliza, obtener opciones de póliza
        url = f'https://ms.proteccionmovil.co/api/v1/policies/options'
        params = {
            'imei': imei,
            'sponsorId': 'MICELU'
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if response.status_code != 200 or 'data' not in data:
            return jsonify({
                'exito': False,
                'mensaje': data.get('message', 'Error al obtener opciones de póliza'),
                'status': response.status_code
            }), 400
            
        # Obtener el primer plan y su primera opción de precio
        plans = data['data'].get('plans', [])
        if not plans:
            return jsonify({
                'exito': False,
                'mensaje': 'No hay planes disponibles para este IMEI'
            }), 400
            
        first_plan = plans[0]
        price_options = first_plan.get('priceOptions', [])
        if not price_options:
            return jsonify({
                'exito': False,
                'mensaje': 'No hay opciones de precio disponibles para este plan'
            }), 400

        # Preparar payload para la póliza
        nombre_completo = nombre.split(' ')
        first_name = nombre_completo[0]
        last_name = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''

        payload = {
            "sponsorId": "MICELU",
            "planId": first_plan['id'],
            "priceOptionId": price_options[0]['id'],
            "device": {
                "imei": imei,
                "line": 'POR_ACTUALIZAR'
            },
            "client": {
                "genderId": "POR_ACTUALIZAR",
                "email": correo,
                "firstName": first_name,
                "lastName": last_name,
                "identification": {
                    "type": "CEDULA_CIUDADANIA",
                    "number": nit
                }
            }
        }

        # Pre-generar póliza
        url_pre = 'https://ms.proteccionmovil.co/api/v1/policy/pregeneration'
        headers['Content-Type'] = 'application/json'
        
        pre_response = requests.post(url_pre, headers=headers, json=payload)
        pre_data = pre_response.json()
        
        if 'error' in pre_data or ('data' in pre_data and pre_data['data']['message'] != 'Pregeneración exitosa'):
            error_msg = pre_data.get('error', {}).get('message', 'Error en la pregeneración de la póliza')
            return jsonify({
                'exito': False,
                'mensaje': error_msg
            }), 400

        # Generar póliza final
        url_generate = 'https://ms.proteccionmovil.co/api/v1/policy'
        final_response = requests.post(url_generate, headers=headers, json=payload)
        final_data = final_response.json()
        
        if 'error' in final_data:
            return jsonify({
                'exito': False,
                'mensaje': final_data['error'].get('message', 'Error al generar la póliza final')
            }), 400

        return jsonify({
            'exito': True,
            'mensaje': 'Póliza creada exitosamente',
            'policy_id': final_data['data'].get('id')
        })

    except Exception as e:
        app.logger.error(f"Error al crear póliza: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': f'Error en el servidor: {str(e)}'
        }), 500

@app.route("/cobertura", methods=['GET', 'POST'])
@login_required
def cobertura():
    documento = session.get('user_documento')
    
    usuario = Usuario.query.filter_by(documento=documento).first()
    
    # Obtener los puntos del usuario
    puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
    total_puntos = 0
    
    if puntos_usuario:
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
        puntos_regalo = int(puntos_usuario.puntos_regalo or '0')
        total_puntos = puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos

    if request.method == 'GET':
        return render_template(
            "cobertura.html",
            usuario=usuario,
            total_puntos=total_puntos
        )
    
    datos = request.json
    
    imei = datos.get('imei')
    accion = datos.get('accion', 'buscar')

    if not imei:
        return jsonify({
            'exito': False,
            'mensaje': 'El IMEI es obligatorio para continuar',
            'usuario': usuario.nombre if usuario else None,
            'total_puntos': total_puntos
        }), 400

    try:
        if accion == 'buscar':
            datos_cobertura = buscar_por_imei(imei)
            
            if not datos_cobertura:
                return jsonify({
                    'exito': False,
                    'mensaje': 'No se encontró información para el IMEI ingresado',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 404
            
            # Obtener y limpiar el NIT de cobertura
            nit_cobertura = str(datos_cobertura.get('nit', ''))
            if '-' in nit_cobertura:
                nit_cobertura = nit_cobertura.split('-')[0]
            nit_cobertura = nit_cobertura.strip()
            
            # Limpiar el documento de sesión
            documento_sesion = str(documento).strip()
        
            
            # Validación más detallada
            if nit_cobertura != documento_sesion:
                
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para acceder a la información de este IMEI',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 403
            
            return jsonify({
                'exito': True,
                'datos': datos_cobertura,
                'usuario': usuario.nombre if usuario else None,
                'usuario_documento': documento_sesion,  # Enviamos el documento limpio
                'total_puntos': total_puntos
            })
            
        elif accion == 'guardar':
            nit = datos.get('nit')
            if not nit:
                return jsonify({
                    'exito': False,
                    'mensaje': 'El documento (NIT) es un campo obligatorio',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400
                
            try:
                # Limpiamos el NIT recibido para comparar
                nit_limpio = str(nit).replace('-', '').strip()
            except ValueError:
                return jsonify({
                    'exito': False,
                    'mensaje': 'El documento debe ser un número válido sin puntos ni espacios',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400
            
            # Validar que el NIT proporcionado coincida con el usuario logueado
            if nit_limpio != str(documento):
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para activar la cobertura con este documento',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 403
            # Obtener y validar el correo
            correo = datos.get('datos', {}).get('correo', '').strip()
            if not correo:
                return jsonify({
                    'exito': False,
                    'mensaje': 'El correo electrónico es obligatorio para activar la cobertura',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400

                
            datos_guardar = {
                'documento': nit_limpio,
                'imei': imei,
                'nombreCliente': datos.get('datos', {}).get('nombre', '').strip(),
                'correo': datos.get('datos', {}).get('correo', '').strip(),
                'fecha': datetime.strptime(datos.get('fecha'), '%Y-%m-%d'),
                'valor': float(datos.get('valor', 0)),
                'referencia': datos.get('referencia', '').strip(),
                'telefono': datos.get('telefono', '').strip()
            }
                
            try:
                # Verificar si ya existe una cobertura activa para este IMEI
                cobertura_existente = cobertura_clientes.query.filter_by(imei=imei).first()
                if cobertura_existente:
                    return jsonify({
                        'exito': False,
                        'mensaje': 'Ya existe una cobertura activa para este IMEI',
                        'usuario': usuario.nombre if usuario else None,
                        'total_puntos': total_puntos
                    }), 400

                nueva_cobertura = cobertura_clientes(**datos_guardar)
                db.session.add(nueva_cobertura)
                db.session.commit()
                
                fecha_fin = (datetime.now() + timedelta(days=180)).strftime('%d/%m/%Y')
                
                exito, error = cobertura_email_service.enviar_confirmacion_cobertura(
                    datos_guardar, 
                    fecha_fin
                )
                
                if not exito:
                    app.logger.warning(f"La cobertura se guardó pero hubo un error al enviar el correo: {error}")
                
                return jsonify({
                    'exito': True,
                    'mensaje': 'La cobertura ha sido activada exitosamente por 6 meses',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                })
                
            except Exception as e:
                app.logger.error(f"Error al procesar la cobertura: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'exito': False,
                    'mensaje': 'Ha ocurrido un error al procesar la solicitud. Por favor, inténtelo nuevamente.',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                })
            
    except Exception as e:
        app.logger.error(f"Error en el servidor: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': f'Error en el servidor: {str(e)}',
            'usuario': usuario.nombre if usuario else None,
            'total_puntos': total_puntos
        }), 500
        
@app.route('/cobertura', methods=['GET'])
def cobertura1():
    return render_template("cobertura.html")
    
if __name__ == '__app__':
    app.run(port=os.getenv("PORT", default=5000))