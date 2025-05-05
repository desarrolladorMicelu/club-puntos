import base64
from functools import wraps
import io
import os
import random
import secrets
import string
import msal
from time import timezone
from flask import Flask, flash, json, jsonify, logging, redirect, render_template, request, session, url_for
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
import schedule
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from io import BytesIO
import traceback
from apscheduler.triggers.cron import CronTrigger
import pytz

 
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
    #'db3':'postgresql://postgres:123@localhost:5432/cobertura_local'
}

CLIENTE_ID = os.getenv('CLIENTE_ID')
CLIENTE_SECRETO = os.getenv('CLIENTE_SECRETO')
TENANT_ID = os.getenv('TENANT_ID')
SHAREPOINT_URL = os.getenv('SHAREPOINT_URL') 
SITE_ID = os.getenv('SITE_ID')
ARCHIVO_EXCEL = os.getenv('ARCHIVO_EXCEL')

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
scheduler = BackgroundScheduler()

#Modelos Coberturas
class cobertura_inactiva(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'cobertura_inactiva'
    __table_args__ = {'schema': 'plan_beneficios'}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    imei = db.Column(db.String(50))
    nit = db.Column(db.BigInteger)
    correo_cliente = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    fecha_compra = db.Column(db.Date)
    referencia_celular = db.Column(db.String(50))
    status = db.Column(db.Integer)
    nombre_cliente = db.Column(db.String(50))
    
class fecha_correo(db.Model):
    __bind_key__ = 'db3'
    __tablename__ = 'fecha_correo'
    __table_args__ = {'schema': 'plan_beneficios'}

    imei = db.Column(db.String(50), primary_key=True)
    fecha_envio = db.Column(db.Date)
 
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
 
    documento = db.Column(db.String(50), nullable=False)
    imei = db.Column(db.String(50), nullable=False, unique=True)
    nombreCliente = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100))
    fecha = db.Column(db.DateTime, nullable=False)
    valor = db.Column(db.String(50), nullable=False)
    referencia = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    id = db.Column(db.String(150), primary_key=True)
    fecha_activacion = db.Column(db.DateTime, nullable=False)
 
    @staticmethod
    def before_insert(mapper, connection, target):
        target.id = f"{target.documento}-{target.imei}"
 
db.event.listen(cobertura_clientes, 'before_insert', cobertura_clientes.before_insert)
    
    
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
    SELECT DISTINCT TOP 1
        v.Tipo_Documento,
        v.Documento,
        v.Tipo_Documento + v.Documento AS Factura,
        LEFT(v.Serie, 15) AS IMEI,
        v.Referencia AS Producto,
        v.Valor,
        v.Fecha_Inicial AS Fecha,
        v.NIT,
        m.codgrupo,
        c.EMAIL AS Correo,
        c.TEL1 AS Telefono,
        c.Nombre AS Nombre_Cliente
    FROM 
        VSeriesUtilidad v WITH (NOLOCK)
    JOIN
        MTMercia m ON v.Producto = m.CODIGO
    JOIN
        MTPROCLI c ON v.nit = c.NIT
    WHERE 
        v.Tipo_Documento IN ('FB', 'FM')
        AND v.Valor > 0
        AND m.CODLINEA = 'CEL'
        AND m.CODGRUPO = 'SEMI'
        AND v.NIT NOT IN ('1152718000', '1053817613', '1000644140', '01')
        AND LEFT(v.Serie, 15) = ?
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
            <body style="font-family: Poppins, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
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
            
            # Verificar si ya existe cobertura para este IMEI
            cobertura_existente = cobertura_clientes.query.filter_by(imei=imei).first()
            if cobertura_existente:
                return jsonify({
                    'exito': False,
                    'mensaje': 'Ya existe una cobertura activa para este IMEI',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400
            
            return jsonify({
                'exito': True,
                'datos': datos_cobertura,
                'usuario': usuario.nombre if usuario else None,
                'usuario_documento': documento_sesion,
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
                
            # Validar que el IMEI exista en la base de datos
            datos_cobertura = buscar_por_imei(imei)
            if not datos_cobertura:
                return jsonify({
                    'exito': False,
                    'mensaje': 'No se encontró información para el IMEI ingresado',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 404
                
            # Validar que el NIT de la cobertura coincida con el del usuario
            nit_cobertura = str(datos_cobertura.get('nit', ''))
            if '-' in nit_cobertura:
                nit_cobertura = nit_cobertura.split('-')[0]
            nit_cobertura = nit_cobertura.strip()
            
            if nit_cobertura != nit_limpio:
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para activar la cobertura de este IMEI',
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
                
            # Preparar datos para guardar
            datos_guardar = {
                'documento': nit_limpio,
                'imei': imei,
                'nombreCliente': datos.get('datos', {}).get('nombre', '').strip(),
                'correo': correo,
                'fecha': datetime.strptime(datos.get('fecha'), '%Y-%m-%d'),
                'valor': float(datos.get('valor', 0)),
                'referencia': datos.get('referencia', '').strip(),
                'telefono': datos.get('telefono', '').strip(),
                'fecha_activacion': datetime.now()
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

                # Guardar la cobertura
                nueva_cobertura = cobertura_clientes(**datos_guardar)
                db.session.add(nueva_cobertura)
                db.session.commit()
                
                # Calcular fecha de fin de cobertura (1 año)
                fecha_fin = (datos_guardar['fecha'] + timedelta(days=365)).strftime('%d/%m/%Y')
                
                # Enviar correo de confirmación
                exito, error = cobertura_email_service.enviar_confirmacion_cobertura(
                    datos_guardar, 
                    fecha_fin
                )
                
                if not exito:
                    app.logger.warning(f"La cobertura se guardó pero hubo un error al enviar el correo: {error}")
                
                return jsonify({
                    'exito': True,
                    'mensaje': 'La cobertura ha sido activada exitosamente por 1 año',
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

# Configuración de logging (solo consola)
#logging.basicConfig(
    #level=logging.INFO,
    #format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #handlers=[
        #logging.StreamHandler()  # Solo mantener el handler para consola
    #]
#)

#logger = logging.getLogger(__name__)

# Ruta para visualizar coberturas inactivas
@app.route("/coberturas_inactivas", methods=['GET', 'POST'])
@login_required
def coberturas_inactivas():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
    
    if request.method == 'GET':
        return render_template("coberturas_inactivas.html", usuario=usuario)
    
    datos = request.json
    fecha_inicio = datos.get('fecha_inicio', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    fecha_fin = datos.get('fecha_fin', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        resultados_consulta = obtener_datos_consulta(fecha_inicio, fecha_fin)
        
        if not resultados_consulta:
            return jsonify({
                'exito': False,
                'mensaje': 'No se encontraron resultados en el período especificado',
                'usuario': usuario.nombre if usuario else None
            }), 404
        
        coberturas_inactivas, imeis_con_cobertura = filtrar_coberturas_inactivas(resultados_consulta)
        
        if not coberturas_inactivas:
            return jsonify({
                'exito': False,
                'mensaje': 'No se encontraron coberturas inactivas en el período especificado',
                'imeis_con_cobertura': imeis_con_cobertura,
                'usuario': usuario.nombre if usuario else None
            }), 404
            
        return jsonify({
            'exito': True,
            'coberturas_inactivas': coberturas_inactivas,
            'imeis_con_cobertura': imeis_con_cobertura,
            'cantidad_con_cobertura': len(imeis_con_cobertura),
            'usuario': usuario.nombre if usuario else None
        })
            
    except Exception as e:
        #logger.error(f"Error al buscar coberturas inactivas: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': f'Error en el servidor: {str(e)}',
            'usuario': usuario.nombre if usuario else None
        }), 500

def obtener_datos_consulta(fecha_inicio, fecha_fin):
    #logger.info(f"Consultando datos desde {fecha_inicio} hasta {fecha_fin}")
    
    conn = obtener_conexion_bd()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        v.Tipo_Documento,
        v.Documento,
        v.Tipo_Documento + v.Documento AS Factura,
        LEFT(v.Serie, 15) AS IMEI,
        v.Referencia AS Producto,
        v.Valor,
        v.Fecha_Inicial AS Fecha_Compra,
        v.NIT,
        m.codgrupo,
        c.EMAIL AS Correo,
        c.TEL1 AS Telefono,
        c.Nombre
    FROM 
        VSeriesUtilidad v WITH (NOLOCK)
    JOIN
        MTMercia m ON v.Producto = m.CODIGO
    JOIN
        MTPROCLI c ON v.nit = c.NIT
    WHERE 
        v.Tipo_Documento IN ('FB', 'FM')
        AND v.Valor > 0
        AND v.Fecha_Inicial BETWEEN ? AND ?
        AND m.CODLINEA = 'CEL'
        AND m.CODGRUPO = 'SEMI'
        AND v.NIT NOT IN ('1152718000', '1053817613', '1000644140', '01')  
    ORDER BY 
        v.Fecha_Inicial DESC
    """                                                                                                         
    
    cursor.execute(query, (fecha_inicio, fecha_fin))
    resultados = cursor.fetchall()
    
    datos_consulta = []
    for row in resultados:
        datos_consulta.append({
            'tipo_documento': row.Tipo_Documento,
            'documento': row.Documento,
            'factura': row.Factura,
            'imei': row.IMEI,
            'producto': row.Producto,
            'valor': float(row.Valor),
            'fecha_compra': row.Fecha_Compra.strftime('%Y-%m-%d'),
            'nit': row.NIT,
            'codgrupo': row.codgrupo,
            'correo': row.Correo if hasattr(row, 'Correo') else "",
            'telefono': row.Telefono if hasattr(row, 'Telefono') else "",
            'nombre': row.Nombre if hasattr(row, 'Nombre') else ""
        })
    
    cursor.close()
    conn.close()
    
    #logger.info(f"Se encontraron {len(datos_consulta)} registros")
    return datos_consulta

def filtrar_coberturas_inactivas(datos_consulta):
    coberturas_inactivas = []
    imeis_con_cobertura = []
    nuevas_registradas = 0
    
    for dato in datos_consulta:
        imei_original = dato['imei']
        dato['imei'] = ''.join(c for c in imei_original if c.isdigit())
        
        if not dato['imei']:
            #logger.warning(f"IMEI vacío después de limpieza. Saltando registro.")
            continue
        
        dato['nit'] = dato['nit'].split('-')[0] if '-' in dato['nit'] else dato['nit']
        dato['nit'] = ''.join(c for c in dato['nit'] if c.isdigit())
        
        try:
            cobertura_activa = cobertura_clientes.query.filter_by(imei=dato['imei']).first()
            
            if cobertura_activa:
                imeis_con_cobertura.append({
                    'imei': dato['imei'],
                    'imei_original': imei_original,
                    'producto': dato['producto'],
                    'fecha_compra': dato['fecha_compra'],
                    'valor': dato['valor'],
                    'factura': dato['factura'],
                    'nit': dato['nit'],
                    'cliente': getattr(cobertura_activa, 'nombre_cliente', 'N/A')
                })
                continue
            
            cobertura_inactiva_existente = cobertura_inactiva.query.filter_by(imei=dato['imei']).first()
            
            if not cobertura_inactiva_existente:
                try:
                    nueva_cobertura = cobertura_inactiva(
                        imei=dato['imei'],
                        nit=dato['nit'],
                        correo_cliente=dato.get('correo', ""),
                        telefono=dato.get('telefono', ""),
                        fecha_compra=datetime.strptime(dato['fecha_compra'], '%Y-%m-%d'),
                        referencia_celular=dato['producto'],
                        nombre_cliente=dato.get('nombre', ""),
                        status=0
                    )
                    
                    db.session.add(nueva_cobertura)
                    db.session.commit()
                    nuevas_registradas += 1
                
                except Exception as e:
                    #logger.error(f"Error al registrar cobertura inactiva: {str(e)}")
                    db.session.rollback()
            
            coberturas_inactivas.append(dato)
        
        except Exception as e:
            #logger.error(f"Error al verificar cobertura: {str(e)}")
            db.session.rollback()
    
    #logger.info(f"Se encontraron {len(coberturas_inactivas)} coberturas inactivas ({nuevas_registradas} nuevas)")
    return coberturas_inactivas, imeis_con_cobertura



@app.route("/exportar_coberturas_inactivas", methods=['GET', 'POST'])
def exportar_coberturas_inactivas():
    if request.method == 'GET':
        return render_template("exportar_coberturas_inactivas.html")
    
    try:
        coberturas = obtener_coberturas_inactivas()
        
        if not coberturas:
            return jsonify({
                'exito': False,
                'mensaje': 'No se encontraron coberturas inactivas para exportar',
            }), 404
        
        # Usar la nueva función de exportación a Excel en SharePoint
        resultado_exportacion = exportar_a_excel_sharepoint(coberturas)
        
        if resultado_exportacion['exito']:
            return jsonify({
                'exito': True,
                'mensaje': f'Se exportaron {resultado_exportacion["cantidad"]} registros a Excel en SharePoint',
                'url_hoja': resultado_exportacion.get('url_hoja', ''),
            })
        else:
            return jsonify({
                'exito': False,
                'mensaje': f'Error al exportar: {resultado_exportacion["error"]}',
            }), 500
            
    except Exception as e:
        #logger.error(f"Error al exportar coberturas inactivas: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': f'Error en el servidor: {str(e)}',
        }), 500

def obtener_coberturas_inactivas():
    try:
        # Calcular la fecha de 7 días atrás
        fecha_limite = (datetime.now() - timedelta(days=7)).date()
        
        # Consultar solo los registros de los últimos 7 días
        coberturas = cobertura_inactiva.query.filter(
            cobertura_inactiva.fecha_compra >= fecha_limite
        ).all()
        
        resultado = []
        for c in coberturas:
            resultado.append({
                'imei': c.imei,
                'nit': c.nit,
                'correo_cliente': c.correo_cliente,
                'telefono': c.telefono,
                'fecha_compra': c.fecha_compra.strftime('%Y-%m-%d') if c.fecha_compra else None,
                'referencia_celular': c.referencia_celular,
                'nombre_cliente': getattr(c, 'nombre_cliente', ""),
                'status': c.status
            })
        
        return resultado
        
    except Exception as e:
        #logger.error(f"Error al obtener coberturas inactivas: {str(e)}")
        #logger.error(traceback.format_exc())
        return []

def exportar_a_excel_sharepoint(coberturas):
    """
    Exporta los datos de coberturas inactivas a un archivo Excel en SharePoint 
    usando Microsoft Graph API.
    """
    try:
        #logger.info("Iniciando exportación a Excel con Microsoft Graph API")
        
        # 1. Autenticación con MSAL para obtener token para Microsoft Graph
        app = msal.ConfidentialClientApplication(
            CLIENTE_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENTE_SECRETO
        )
        
        # Obtener token para Graph API
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" not in result:
            #logger.error(f"Error de autenticación: {result.get('error_description', result.get('error'))}")
            return {'exito': False, 'error': f"Error de autenticación: {result.get('error_description')}"}
        
        access_token = result["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 2. Preparar datos para Excel
        excel_headers = ["IMEI", "NIT", "Nombre Cliente", "Correo Cliente", "Teléfono", 
                         "Fecha Compra", "Referencia Celular", "Estado"]
        
        data = []
        for c in coberturas:
            data.append([ 
                c['imei'], 
                c['nit'], 
                c['nombre_cliente'], 
                c['correo_cliente'], 
                c['telefono'], 
                c['fecha_compra'], 
                c['referencia_celular'], 
                "Inactivo" if c['status'] == 0 else "Activo"
            ])
        
        # Crear DataFrame y Excel en memoria
        df = pd.DataFrame(data, columns=excel_headers)
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H-%M')
        sheet_name = f"Exportacion {fecha_actual}"[:31]  # Limitar a 31 caracteres
        
        # Crear Excel en memoria
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Formato básico
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_length
        
        buffer.seek(0)
        file_content = buffer.read()
        
        # 3. Determinar la ubicación correcta en SharePoint usando Graph API
        site_name = "ProyectosMICELU"  
        
        # Obtener el ID del sitio primero
        #logger.info(f"Obteniendo detalles del sitio: {site_name}")
        site_response = requests.get(
            f"https://graph.microsoft.com/v1.0/sites/micelu.sharepoint.com:/sites/{site_name}",
            headers=headers
        )
        
        if not site_response.ok:
            #logger.error(f"Error al obtener el sitio: {site_response.text}")
            return {'exito': False, 'error': f"Error al acceder al sitio: {site_response.text}"}
        
        site_id = site_response.json().get("id")
        #logger.info(f"ID del sitio obtenido: {site_id}")
        
        # 4. Obtener la drive de documentos compartidos
        drive_response = requests.get(
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives",
            headers=headers
        )
        
        if not drive_response.ok:
            #logger.error(f"Error al obtener drives: {drive_response.text}")
            return {'exito': False, 'error': f"Error al acceder a los drives: {drive_response.text}"}
        
        drives = drive_response.json().get("value", [])
        document_drive = None
        
        for drive in drives:
            if drive.get("name") == "Documentos" or "document" in drive.get("name", "").lower():
                document_drive = drive
                break
        
        if not document_drive:
            if drives:
                document_drive = drives[0]  # Usar el primer drive disponible
            else:
                #logger.error("No se encontraron drives disponibles")
                return {'exito': False, 'error': "No se encontraron bibliotecas de documentos"}
        
        drive_id = document_drive.get("id")
        #logger.info(f"Drive ID para subir archivo: {drive_id}")
        
        # 5. Subir el archivo Excel
        file_name = "Coberturas inactivas MICELU.xlsx"
        
        # Verificar si el archivo existe
        file_check_response = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}",
            headers=headers
        )
        
        if file_check_response.status_code == 200:
            # Archivo existe, actualizarlo
            #logger.info(f"Archivo {file_name} existe, actualizando...")
            upload_response = requests.put(
                f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content",
                headers={"Authorization": f"Bearer {access_token}"},
                data=file_content
            )
        else:
            # Archivo no existe, crearlo
            #logger.info(f"Archivo {file_name} no existe, creando...")
            upload_response = requests.put(
                f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content",
                headers={"Authorization": f"Bearer {access_token}"},
                data=file_content
            )
        
        if not upload_response.ok:
            #logger.error(f"Error al subir archivo: {upload_response.text}")
            return {'exito': False, 'error': f"Error al subir archivo: {upload_response.text}"}
        
        file_data = upload_response.json()
        file_url = file_data.get("webUrl")
        
        #logger.info(f"Archivo Excel subido exitosamente: {file_url}")
        return {
            'exito': True,
            'cantidad': len(coberturas),
            'url_hoja': file_url
        }
        
    except Exception as e:
        #logger.error(f"Error al exportar a Excel: {str(e)}")
        #logger.error(traceback.format_exc())
        return {'exito': False, 'error': str(e)}
def ensure_folder_exists(ctx, folder_path):
    """
    Asegura que una carpeta existe en SharePoint.
    Si no existe, la crea junto con todas las carpetas padre necesarias.
    """
    try:
        # Separar el path en sus componentes
        parts = [p for p in folder_path.split('/') if p]
        current_path = ''
        
        for part in parts:
            current_path += f"/{part}"
            try:
                folder = ctx.web.get_folder_by_server_relative_url(current_path)
                ctx.load(folder)
                ctx.execute_query()
                #logger.info(f"Carpeta existente: {current_path}")
            except Exception:
                # Si la carpeta no existe, la creamos
                parent_path = current_path[:current_path.rfind('/')]
                if not parent_path:
                    parent_path = "/"
                    
                parent_folder = ctx.web.get_folder_by_server_relative_url(parent_path)
                parent_folder.folders.add(part)
                ctx.execute_query()
                #logger.info(f"Carpeta creada: {current_path}")
    except Exception as e:
        #logger.error(f"Error al verificar/crear carpetas: {str(e)}")
        raise
# Definir la función que quieres ejecutar
def exportar_coberturas_automaticamente():
    with app.app_context():
        try:
            # Obtener fechas (domingo actual y 7 días atrás)
            fecha_fin = datetime.now().strftime('%Y-%m-%d')
            fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Obtener datos de coberturas inactivas
            resultados_consulta = obtener_datos_consulta(fecha_inicio, fecha_fin)
            
            if not resultados_consulta:
                return
            
            # Filtrar coberturas inactivas
            coberturas_inactivas, _ = filtrar_coberturas_inactivas(resultados_consulta)
            
            if not coberturas_inactivas:
                return
            
            # Obtener todas las coberturas inactivas de la base de datos
            coberturas_db = obtener_coberturas_inactivas()
            
            # Exportar a Excel en SharePoint
            exportar_a_excel_sharepoint(coberturas_db)
            
        except Exception as e:
            import traceback
            traceback.format_exc()

# Definir la función para actualizar coberturas inactivas diariamente
def actualizar_coberturas_inactivas_diario():
    with app.app_context():
        try:
            # Usar pytz para obtener la fecha actual en Colombia
            ahora = datetime.now(bogota_tz)
            
            # Verificar si hoy es domingo (día 6), en cuyo caso no ejecutamos esta función
            if ahora.weekday() == 6:  # 6 = domingo
                return
            
            # Consultar solo el día actual con la zona horaria correcta
            fecha = ahora.strftime('%Y-%m-%d')
            
            # Obtener datos de consulta solo para la fecha actual
            resultados_consulta = obtener_datos_consulta(fecha, fecha)
            
            if not resultados_consulta:
                return
            
            # (Esta función ya verifica si el registro existe antes de crearlo)
            coberturas_inactivas, _ = filtrar_coberturas_inactivas(resultados_consulta)
            
            if not coberturas_inactivas:
                return
                
        except Exception as e:
            #logger.error(f"❌ ERROR CRÍTICO EN LA ACTUALIZACIÓN DIARIA: {str(e)}")
            import traceback
            #logger.error(traceback.format_exc())

# Nueva función para enviar reporte semanal de coberturas activadas
def enviar_reporte_coberturas_activadas():
    with app.app_context():
        try:
            #logger.info("===== INICIANDO REPORTE SEMANAL DE COBERTURAS ACTIVADAS =====")
            
            # Calcular rango de fechas: última semana (de lunes a domingo)
            hoy = datetime.now(bogota_tz)
            # Obtener el número de días desde el lunes de la semana actual
            dia_semana = hoy.weekday()  # 0=Lunes, 6=Domingo
            
            # Calcular fecha de inicio (lunes de la semana actual)
            fecha_inicio = (hoy - timedelta(days=dia_semana)).replace(hour=0, minute=0, second=0)
            # Calcular fecha de fin (domingo de la semana actual)
            fecha_fin = hoy.replace(hour=23, minute=59, second=59)
            
            rango_fechas = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
            
            # Consultar la base de datos para obtener coberturas activadas en el rango de fechas
            coberturas_activadas = cobertura_clientes.query.filter(
                cobertura_clientes.fecha_activacion.between(fecha_inicio, fecha_fin)
            ).all()
            
            if not coberturas_activadas:
                #logger.warning("No se encontraron coberturas activadas en el período especificado")
                return
            
            #logger.info(f"Se encontraron {len(coberturas_activadas)} coberturas activadas en el período")
            
            # Preparar datos para Excel
            data = []
            for c in coberturas_activadas:
                data.append([
                    c.imei,
                    c.documento,
                    c.nombreCliente,
                    c.correo,
                    c.telefono,
                    c.fecha.strftime('%Y-%m-%d') if c.fecha else '',
                    c.fecha_activacion.strftime('%Y-%m-%d') if c.fecha_activacion else '',
                    c.referencia,
                    c.valor
                ])
            
            # Crear DataFrame y Excel en memoria
            excel_headers = ["IMEI", "NIT/Documento", "Nombre Cliente", "Correo Cliente", 
                             "Teléfono", "Fecha Compra", "Fecha Activación", 
                             "Referencia Celular", "Valor"]
            
            df = pd.DataFrame(data, columns=excel_headers)
            
            # Crear Excel en memoria
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Coberturas Activadas", index=False)
                
                # Formato básico
                worksheet = writer.sheets["Coberturas Activadas"]
                for idx, col in enumerate(df.columns):
                    max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_length
            
            buffer.seek(0)
            file_content = buffer.getvalue()
            
            # Enviar correo con el reporte
            email_client = EmailClient.from_connection_string(
                "endpoint=https://email-sender-communication-micelu.unitedstates.communication.azure.com/;accesskey=VmkxyJLEb9bzf+23ve1gMPSCHC9jluovcOIJoSyrWrKPhBflOywY6HRWFj9u6pAULH+qsr6UGrlgBeCjuNcpMA=="
            )
            sender_address = "DoNotReply@baca2159-db63-4c5c-87b8-a2fcdcec0539.azurecomm.net"
            
            # Lista de destinatarios del reporte
            destinatarios = [
                "agonzalez@acinco.com.co",
                "leslyvalderrama@acinco.com.co",
                "juangarcia@micelu.co",
                'higuitaa891@gmail.com',
                "coordinadormed@micelu.co",
                "karen.vargas@micelu.co"
            ]
            
            # Formato del asunto
            asunto = f"Coberturas activas {rango_fechas} MICELU"
            
            # Contenido del correo
            contenido_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: green;">Reporte de Coberturas Activadas </h2>
                <p style="color: black; font-size: 16px;">Estimados,</p>
                <p style="color: black; font-size: 16px;">Adjunto encontrarán el reporte de las coberturas activadas durante el período del <strong>{rango_fechas}</strong>.</p>
                <p style="color: black; font-size: 16px;">Se reportan un total de <strong>{len(coberturas_activadas)}</strong> coberturas activadas durante este período.</p>
                <p style="color: black; font-size: 16px;">Para más detalles, por favor revisen el archivo adjunto.</p>
                <p style="color: black; font-size: 16px;">Atentamente,<br>Equipo Micelu.co</p>
            </body>
            </html>
            """
            
            # Preparar mensaje con archivo adjunto
            mensaje = {
                "senderAddress": sender_address,
                "recipients": {
                    "to": [{"address": email} for email in destinatarios]
                },
                "content": {
                    "subject": asunto,
                    "html": contenido_html,
                    "attachments": [
                        {
                            "name": f"Coberturas_Activadas_{fecha_inicio.strftime('%Y%m%d')}_al_{fecha_fin.strftime('%Y%m%d')}.xlsx",
                            "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "contentInBase64": base64.b64encode(file_content).decode('utf-8')
                        }
                    ]
                }
            }
            
            # Enviar correo
            poller = email_client.begin_send(mensaje)
            result = poller.result()
            
        except Exception as e:
            
            import traceback
            #logger.error(traceback.format_exc())

# Definir zona horaria de Bogotá
bogota_tz = pytz.timezone('America/Bogota')
def configurar_tareas_programadas():
    """
    Configura todas las tareas programadas del sistema
    """
    try:
        # Crear scheduler con zona horaria
        scheduler = BackgroundScheduler(timezone=bogota_tz)
        
        # 1. Exportación de coberturas inactivas cada domingo a las 23:59
        scheduler.add_job(
            exportar_coberturas_automaticamente, 'cron', 
            day_of_week='sun', hour='23', minute='59', 
            timezone=bogota_tz,
            id='exportar_coberturas',
            replace_existing=True
        )

        # 2. Actualización diaria de coberturas inactivas a las 23:00
        scheduler.add_job(
            actualizar_coberturas_inactivas_diario, 'cron', 
            hour='23', minute='00', 
            timezone=bogota_tz,
            id='actualizar_coberturas_inactivas',
            replace_existing=True
        )

        # 3. Reporte semanal de coberturas activadas cada domingo a las 21:00
        scheduler.add_job(
            enviar_reporte_coberturas_activadas, 'cron',
            day_of_week='sun', hour='21', minute='00',
            timezone=bogota_tz,
            id='reporte_coberturas_activadas',
            replace_existing=True
        )

        # 4. Procesamiento diario de coberturas inactivas a las 9:00 AM
        scheduler.add_job(
            procesar_coberturas_inactivas_programado, 'cron',
            hour='8', minute='55',
            timezone=bogota_tz,
            id='procesar_coberturas_inactivas',
            replace_existing=True
        )
        
        # Iniciar el planificador
        scheduler.start()
        app.logger.info("Tareas programadas configuradas correctamente con zona horaria de Bogotá")
        
    except Exception as e:
        app.logger.error(f"Error al configurar tareas programadas: {str(e)}")
        
# Clase para el servicio de correo para coberturas inactivas
class CoberturaInactivaEmailService:
    def __init__(self):
        # Configuración de conexión de Azure Communication Services
        self.connection_string = "endpoint=https://email-sender-communication-micelu.unitedstates.communication.azure.com/;accesskey=VmkxyJLEb9bzf+23ve1gMPSCHC9jluovcOIJoSyrWrKPhBflOywY6HRWFj9u6pAULH+qsr6UGrlgBeCjuNcpMA=="
        self.sender_address = "DoNotReply@baca2159-db63-4c5c-87b8-a2fcdcec0539.azurecomm.net"

    def enviar_correo_cobertura_inactiva(self, datos_cobertura, tipo_correo):
        """
        Envía un correo al cliente informando sobre la cobertura pendiente de activar
        
        Args:
            datos_cobertura: diccionario con datos de la cobertura inactiva
            tipo_correo: 1 para primer correo (día 1), 3 para segundo correo (día 3)
        """
        try:
            email_client = EmailClient.from_connection_string(self.connection_string)

            # URL de la imagen y dirección de activación
            url_imagen = "https://i.ibb.co/1DsGPLQ/imagen.jpg"
            url_activacion = "https://club-puntos-micelu.azurewebsites.net/"  # URL donde el cliente puede activar la cobertura

            # Configuramos el asunto y contenido según el tipo de correo
            if tipo_correo == 1:
                asunto = "¡Activa tu cobertura de Pantalla!"
                mensaje_principal = f"""
                <p>Estimado(a) {datos_cobertura['nombre_cliente']},</p>
                <p style="color: red; font-size: 16px;">Notamos que aún no has activado la cobertura de pantalla para tu dispositivo adquirido recientemente.</p>
                <p style="color: red; font-size: 16px;">Recuerda que puedes activar tu cobertura <strong>gratis</strong> y disfrutar de los beneficios por todo un año:</p>
                """
            else:  # tipo_correo == 3
                asunto = "¡Recordatorio urgente: Activa tu cobertura de Pantalla!"
                mensaje_principal = f"""
                <p style="color: red; font-size: 16px;">Estimado(a) {datos_cobertura['nombre_cliente']},</p>
                <p style="color: red; font-size: 16px;">Han pasado tres días desde tu compra y notamos que aún no has activado la cobertura de Pantalla para tu dispositivo.</p>
                <p style="color: red; font-size: 16px;">No pierdas esta oportunidad de proteger tu Equipo <strong>sin costo adicional</strong>:</p>
                """

            contenido_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="{url_imagen}" alt="Logo Micelu" style="max-width:600px; display: block; margin: 0 auto;">
                </div>
                <h2 style="color: #333;">Cobertura de Pantalla</h2>
                {mensaje_principal}
                <ul>
                    <li><strong>IMEI:</strong> {datos_cobertura['imei']}</li>
                    <li><strong>Dispositivo:</strong> {datos_cobertura['referencia_celular']}</li>
                    <li><strong>Fecha de compra:</strong> {datos_cobertura['fecha_compra']}</li>
                </ul>
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{url_activacion}" style="background-color: #4CAF50; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">ACTIVAR MI COBERTURA</a>
                </div>
                <p>Para activar tu cobertura solo necesitas:</p>
                <ul>
                    <li>Tu número de documento</li>
                    <li>El IMEI de tu dispositivo</li>
                    <li>Un correo electrónico activo</li>
                    <li>Registrarse en club puntos </li>
                </ul>
                <p>Si tienes dudas, puedes contactarnos a través de servicio al cliente.</p>
                <p>Atentamente,<br>Equipo Micelu.co</p>
            </body>
            </html>
            """

            # Preparar destinatarios
            destinatarios = [
                {
                    "address": datos_cobertura['correo_cliente'],
                    "displayName": datos_cobertura['nombre_cliente']
                }
            ]
            
            # Mensaje de correo
            mensaje = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": dest["address"], "displayName": dest["displayName"]} for dest in destinatarios]
                },
                "content": {
                    "subject": asunto,
                    "html": contenido_html
                }
            }

            # Enviar correo
            poller = email_client.begin_send(mensaje)
            result = poller.result()

            return True, None

        except Exception as e:
            mensaje_error = f"Error al enviar correo de cobertura inactiva: {str(e)}"
            app.logger.error(mensaje_error)
            return False, mensaje_error

# Crear instancia del servicio de correo
cobertura_inactiva_email_service = CoberturaInactivaEmailService()

@app.route("/procesar_coberturas_inactivas", methods=['GET'])
@login_required
def procesar_coberturas_inactivas():
    """
    Endpoint para procesar coberturas inactivas y enviar correos automáticamente
    """
    try:
        resultados = {
            'correos_dia1_enviados': 0,
            'correos_dia3_enviados': 0,
            'coberturas_activadas': 0,
            'errores': []
        }
        
        # Procesamos las coberturas inactivas
        procesar_envio_correos_inactivas(resultados)
        
        return jsonify({
            'exito': True,
            'mensaje': f"Procesamiento completo: {resultados['correos_dia1_enviados']} correos día 1, {resultados['correos_dia3_enviados']} correos día 3, {resultados['coberturas_activadas']} coberturas activadas verificadas",
            'detalles': resultados
        })
    
    except Exception as e:
        app.logger.error(f"Error al procesar coberturas inactivas: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': f'Error en el servidor: {str(e)}'
        }), 500

def procesar_envio_correos_inactivas(resultados):
    """
    Procesa las coberturas inactivas para enviar correos automáticos
    y actualizar estados.
    """
    hoy = datetime.now().date()
    
    try:
        # 1. Verificar y eliminar coberturas que ya fueron activadas
        eliminar_coberturas_activadas(resultados)
        
        # 2. Enviar correos a clientes con cobertura inactiva de 1 día
        enviar_correos_dia1(hoy, resultados)
        
        # 3. Enviar correos a clientes con cobertura inactiva de 3 días
        enviar_correos_dia3(hoy, resultados)
        
        # 4. Confirmar cambios en la base de datos
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al procesar coberturas inactivas: {str(e)}")
        resultados['errores'].append(str(e))

def eliminar_coberturas_activadas(resultados):
    """
    Elimina de la tabla cobertura_inactiva aquellas que ya fueron activadas
    """
    try:
        # Obtenemos todas las coberturas inactivas
        coberturas_inactivas = cobertura_inactiva.query.all()
        
        # Obtener todos los IMEIs de coberturas activas de una sola vez
        coberturas_activas_imeis = set(
            item.imei.strip() for item in cobertura_clientes.query.with_entities(cobertura_clientes.imei).all()
            if item.imei is not None
        )
        
        app.logger.info(f"Verificando {len(coberturas_inactivas)} coberturas inactivas contra {len(coberturas_activas_imeis)} coberturas activas")
        
        for cobertura in coberturas_inactivas:
            # Asegurarnos que el IMEI no sea None y eliminar espacios
            imei_normalizado = cobertura.imei.strip() if cobertura.imei else ""
            
            # Verificamos si la cobertura ya fue activada usando nuestro conjunto
            if imei_normalizado and imei_normalizado in coberturas_activas_imeis:
                # La cobertura ya fue activada, la eliminamos de inactivas
                app.logger.info(f"Eliminando cobertura inactiva con IMEI {imei_normalizado} porque ya está activada")
                db.session.delete(cobertura)
                resultados['coberturas_activadas'] += 1
        
        # Confirmar explícitamente los cambios
        db.session.commit()
        app.logger.info(f"Se eliminaron {resultados['coberturas_activadas']} coberturas inactivas que ya estaban activadas")
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar coberturas activadas: {str(e)}")
        resultados['errores'].append(f"Error al eliminar coberturas activadas: {str(e)}")

def enviar_correos_dia1(hoy, resultados):
    """
    Envía correos a clientes que compraron hace 1 día y aún no han activado la cobertura
    """
    try:
        # Fecha de compra de hace 1 día
        fecha_objetivo = hoy - timedelta(days=1)
        
        # Obtener coberturas inactivas compradas hace 1 día y con status 0 (sin correo enviado)
        coberturas_dia1 = cobertura_inactiva.query.filter(
            cobertura_inactiva.fecha_compra == fecha_objetivo,
            cobertura_inactiva.status == 0
        ).all()
        
        for cobertura in coberturas_dia1:
            # Verificar si el correo es válido
            if not cobertura.correo_cliente or '@' not in cobertura.correo_cliente:
                app.logger.warning(f"Cobertura IMEI {cobertura.imei} sin correo válido")
                continue
                
            # Verificar si ya fue activada (doble verificación)
            cobertura_activa = cobertura_clientes.query.filter_by(imei=cobertura.imei).first()
            if cobertura_activa:
                db.session.delete(cobertura)
                resultados['coberturas_activadas'] += 1
                continue
                
            # Preparar datos para el correo
            datos_cobertura = {
                'imei': cobertura.imei,
                'nombre_cliente': cobertura.nombre_cliente if cobertura.nombre_cliente else "Cliente",
                'correo_cliente': cobertura.correo_cliente,
                'fecha_compra': cobertura.fecha_compra.strftime('%d/%m/%Y') if cobertura.fecha_compra else "No disponible",
                'referencia_celular': cobertura.referencia_celular if cobertura.referencia_celular else "Dispositivo"
            }
            
            # Enviar correo día 1
            exito, error = cobertura_inactiva_email_service.enviar_correo_cobertura_inactiva(
                datos_cobertura, 
                tipo_correo=1
            )
            
            if exito:
                # Actualizar status a 1 (correo día 1 enviado)
                cobertura.status = 1
                
                # Registrar fecha de envío del correo
                nueva_fecha_correo = fecha_correo(
                    imei=cobertura.imei,
                    fecha_envio=hoy
                )
                db.session.add(nueva_fecha_correo)
                
                resultados['correos_dia1_enviados'] += 1
                app.logger.info(f"Correo día 1 enviado para IMEI {cobertura.imei}")
            else:
                app.logger.error(f"Error al enviar correo día 1 para IMEI {cobertura.imei}: {error}")
                resultados['errores'].append(f"Error al enviar correo día 1 para IMEI {cobertura.imei}: {error}")
        
    except Exception as e:
        app.logger.error(f"Error al enviar correos día 1: {str(e)}")
        resultados['errores'].append(f"Error al enviar correos día 1: {str(e)}")

def enviar_correos_dia3(hoy, resultados):
    """
    Envía correos a clientes que compraron hace 3 días, ya tienen status 1 (primer correo enviado)
    y aún no han activado la cobertura
    """
    try:
        # Fecha de compra de hace 3 días
        fecha_objetivo = hoy - timedelta(days=3)
        
        # Obtener coberturas inactivas compradas hace 3 días y con status 1 (ya recibieron el primer correo)
        coberturas_dia3 = cobertura_inactiva.query.filter(
            cobertura_inactiva.fecha_compra == fecha_objetivo,
            cobertura_inactiva.status == 1
        ).all()
        
        for cobertura in coberturas_dia3:
            # Verificar si el correo es válido
            if not cobertura.correo_cliente or '@' not in cobertura.correo_cliente:
                app.logger.warning(f"Cobertura IMEI {cobertura.imei} sin correo válido")
                continue
                
            # Verificar si ya fue activada (doble verificación)
            cobertura_activa = cobertura_clientes.query.filter_by(imei=cobertura.imei).first()
            if cobertura_activa:
                db.session.delete(cobertura)
                resultados['coberturas_activadas'] += 1
                continue
                
            # Preparar datos para el correo
            datos_cobertura = {
                'imei': cobertura.imei,
                'nombre_cliente': cobertura.nombre_cliente if cobertura.nombre_cliente else "Cliente",
                'correo_cliente': cobertura.correo_cliente,
                'fecha_compra': cobertura.fecha_compra.strftime('%d/%m/%Y') if cobertura.fecha_compra else "No disponible",
                'referencia_celular': cobertura.referencia_celular if cobertura.referencia_celular else "Dispositivo"
            }
            
            # Enviar correo día 3
            exito, error = cobertura_inactiva_email_service.enviar_correo_cobertura_inactiva(
                datos_cobertura, 
                tipo_correo=3
            )
            
            if exito:
                # Actualizar status a 3 (correo día 3 enviado)
                cobertura.status = 3
                
                # Registrar fecha de envío del correo
                nueva_fecha_correo = fecha_correo(
                    imei=cobertura.imei,
                    fecha_envio=hoy
                )
                db.session.add(nueva_fecha_correo)
                
                resultados['correos_dia3_enviados'] += 1
                app.logger.info(f"Correo día 3 enviado para IMEI {cobertura.imei}")
            else:
                app.logger.error(f"Error al enviar correo día 3 para IMEI {cobertura.imei}: {error}")
                resultados['errores'].append(f"Error al enviar correo día 3 para IMEI {cobertura.imei}: {error}")
        
    except Exception as e:
        app.logger.error(f"Error al enviar correos día 3: {str(e)}")
        resultados['errores'].append(f"Error al enviar correos día 3: {str(e)}")

# Función para programar el procesamiento automático de coberturas inactivas

def configurar_tareas_programadas():
    """
    Configura las tareas programadas para el procesamiento automático de coberturas inactivas
    """
    try:
        scheduler = BackgroundScheduler(timezone=bogota_tz)
        
        # Programar tarea para ejecutarse todos los días a las 9:00 AM hora de Bogotá
        scheduler.add_job(
            func=procesar_coberturas_inactivas_programado,
            trigger=CronTrigger(hour=8, minute=55, timezone=bogota_tz),
            id='procesar_coberturas_inactivas',
            replace_existing=True
        )
        
        # Iniciar el planificador
        scheduler.start()
        app.logger.info("Tareas programadas configuradas correctamente con zona horaria de Bogotá")
        
    except Exception as e:
        app.logger.error(f"Error al configurar tareas programadas: {str(e)}")
def procesar_coberturas_inactivas_programado():
    """
    Función que se ejecuta automáticamente por el planificador
    """
    app.logger.info("Iniciando procesamiento programado de coberturas inactivas")
    resultados = {
        'correos_dia1_enviados': 0,
        'correos_dia3_enviados': 0,
        'coberturas_activadas': 0,
        'errores': []
    }
    
    try:
        # Procesar coberturas inactivas
        procesar_envio_correos_inactivas(resultados)
        
        app.logger.info(f"Procesamiento programado completado: {resultados['correos_dia1_enviados']} correos día 1, "
                      f"{resultados['correos_dia3_enviados']} correos día 3, "
                      f"{resultados['coberturas_activadas']} coberturas activadas")
        
        if resultados['errores']:
            app.logger.error(f"Errores durante el procesamiento programado: {resultados['errores']}")
            
    except Exception as e:
        app.logger.error(f"Error en procesamiento programado: {str(e)}")


if __name__ == '__app__':
    app.run(port=os.getenv("PORT", default=5000))