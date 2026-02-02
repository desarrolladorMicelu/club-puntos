import base64
from functools import wraps
import io
import os
import random
import secrets
import string
import msal
from time import timezone
from flask import Flask, flash, json, jsonify, logging, redirect, render_template, request, session, url_for, Response
import csv
import os
from flask_sqlalchemy import SQLAlchemy
import pyodbc
import psycopg2
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
    #'db3':'postgresql://postgres:123@localhost:5432/Puntos'
}

CLIENTE_ID = os.getenv('CLIENTE_ID')
CLIENTE_SECRETO = os.getenv('CLIENTE_SECRETO')
TENANT_ID = os.getenv('TENANT_ID')
SHAREPOINT_URL = os.getenv('SHAREPOINT_URL') 
SITE_ID = os.getenv('SITE_ID')
ARCHIVO_EXCEL = os.getenv('ARCHIVO_EXCEL')
app.config['POLICY_ENVIRONMENT'] = 'prod'  # o 'qa'

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
    ultima_actualizacion = db.Column(db.DateTime, nullable=True)  # NUEVO CAMPO
   
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
    fecha_uso_real = db.Column(db.DateTime, nullable=True)  # NUEVO CAMPO
    estado_cupon = db.Column(db.String(20), default='GENERADO')  # NUEVO CAMPO
   
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

# ============================================================================
# NUEVO MODELO: TRANSACCIONES DE PUNTOS (Sistema de Auditoría)
# ============================================================================
class Transacciones_Puntos(db.Model):
    """
    Tabla de auditoría completa de TODAS las transacciones de puntos.
    Cada movimiento (acumulación, redención, vencimiento) queda registrado aquí.
    """
    __bind_key__ = 'db3'
    __tablename__ = 'transacciones_puntos'
    __table_args__ = {'schema': 'plan_beneficios'}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    documento = db.Column(db.String(50), nullable=False, index=True)
    tipo_transaccion = db.Column(db.String(20), nullable=False)  # 'ACUMULACION', 'REDENCION', 'VENCIMIENTO', 'REGALO', 'REFERIDO'
    puntos = db.Column(db.Integer, nullable=False)
    puntos_disponibles_antes = db.Column(db.Integer, nullable=False, default=0)
    puntos_disponibles_despues = db.Column(db.Integer, nullable=False, default=0)
    fecha_transaccion = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    referencia_compra = db.Column(db.String(100), nullable=True)
    referencia_redencion = db.Column(db.String(36), nullable=True)
    referencia_referido = db.Column(db.String(36), nullable=True)
    descripcion = db.Column(db.String(500), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')  # 'ACTIVO', 'VENCIDO', 'USADO'
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)
    actualizado_en = db.Column(db.DateTime, nullable=True, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Transaccion {self.tipo_transaccion} {self.puntos}pts Doc:{self.documento}>'

# ============================================================================
# FUNCIONES DEL NUEVO SISTEMA DE PUNTOS
# ============================================================================

def cliente_esta_migrado(documento):
    """Verifica si un cliente ya está en el nuevo sistema"""
    try:
        resultado = Transacciones_Puntos.query.filter_by(documento=documento).first() is not None
        return resultado
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False

def calcular_puntos_nuevo_sistema(documento):
    """Calcula puntos disponibles usando el nuevo sistema de transacciones"""
    try:
        hoy = datetime.now()
        
        # Usar ORM en lugar de SQL raw
        puntos_activos = db.session.query(
            db.func.coalesce(db.func.sum(Transacciones_Puntos.puntos), 0)
        ).filter(
            Transacciones_Puntos.documento == documento,
            Transacciones_Puntos.estado == 'ACTIVO',
            db.or_(
                Transacciones_Puntos.fecha_vencimiento.is_(None),
                Transacciones_Puntos.fecha_vencimiento >= hoy
            )
        ).scalar()
        
        return int(puntos_activos or 0)
    except Exception as e:
        print(f"❌ Error en calcular_puntos_nuevo_sistema: {e}")
        # Limpiar la sesión en caso de error
        try:
            db.session.rollback()
        except:
            pass
        return 0

def calcular_puntos_sistema_viejo(documento):
    """Calcula puntos usando el sistema viejo (tu código actual)"""
    puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
    if puntos_usuario:
        puntos_redimidos = int(puntos_usuario.puntos_redimidos or '0')
        puntos_regalo = int(puntos_usuario.puntos_regalo or 0)
        return max(0, puntos_usuario.total_puntos + puntos_regalo - puntos_redimidos)
    return 0

def calcular_puntos_con_fallback(documento):
    """
    Calcula puntos usando SOLO el sistema nuevo.
    Si el cliente no está migrado, retorna 0 (debe migrarse primero).
    """
    try:
        if cliente_esta_migrado(documento):
            return calcular_puntos_nuevo_sistema(documento)
        else:
            print(f"⚠️ Cliente {documento} NO está migrado - Retornando 0 puntos")
            return 0
    except Exception as e:
        print(f"❌ Error calculando puntos para {documento}: {e}")
        import traceback
        traceback.print_exc()
        # Hacer rollback y limpiar sesión
        try:
            db.session.rollback()
        except Exception as rollback_error:
            print(f"❌ Error en rollback: {rollback_error}")
        # NO usar sistema viejo - retornar 0 para forzar migración
        print(f"❌ Error crítico - Cliente {documento} debe ser migrado manualmente")
        return 0

def crear_transaccion_manual(documento, tipo, puntos, descripcion, referencia=None, fecha_compra=None):
    """Crea una transacción manualmente en el nuevo sistema"""
    if fecha_compra is None:
        fecha_compra = datetime.now()
    
    # Calcular saldo antes
    saldo_antes = calcular_puntos_con_fallback(documento)
    
    # Calcular fecha de vencimiento (1 año para ACUMULACION y REFERIDO)
    fecha_vencimiento = None
    if tipo in ['ACUMULACION', 'REFERIDO']:
        fecha_vencimiento = fecha_compra + timedelta(days=365)
    
    # Crear transacción
    transaccion = Transacciones_Puntos(
        id=str(uuid.uuid4()),
        documento=documento,
        tipo_transaccion=tipo,
        puntos=puntos,
        puntos_disponibles_antes=saldo_antes,
        puntos_disponibles_despues=saldo_antes + puntos,
        fecha_transaccion=fecha_compra,
        fecha_vencimiento=fecha_vencimiento,
        referencia_compra=referencia if tipo in ['ACUMULACION', 'CORRECCION'] else None,
        referencia_redencion=referencia if tipo == 'REDENCION' else None,
        referencia_referido=referencia if tipo == 'REFERIDO' else None,
        descripcion=descripcion,
        estado='ACTIVO'
    )
    
    db.session.add(transaccion)
    return transaccion

def migrar_cliente_individual(documento):
    """Migra un cliente específico al nuevo sistema"""
    print(f"🔄 Migrando cliente {documento}...")
    
    # 1. Migrar puntos de compras
    puntos_cliente = Puntos_Clientes.query.filter_by(documento=documento).first()
    if puntos_cliente and puntos_cliente.total_puntos > 0:
        crear_transaccion_manual(
            documento=documento,
            tipo='ACUMULACION',
            puntos=puntos_cliente.total_puntos,
            descripcion='Migración: Puntos históricos de compras',
            referencia='MIGRACION_COMPRAS',
            fecha_compra=puntos_cliente.fecha_registro or datetime.now()
        )
        print(f"  ✅ Compras: {puntos_cliente.total_puntos} puntos")
    
    # 2. Migrar redenciones
    redenciones = historial_beneficio.query.filter_by(documento=documento).all()
    total_redimido = 0
    for redencion in redenciones:
        crear_transaccion_manual(
            documento=documento,
            tipo='REDENCION',
            puntos=-redencion.puntos_utilizados,  # Negativo
            descripcion=f'Migración: Cupón {redencion.cupon}',
            referencia=str(redencion.id),
            fecha_compra=redencion.fecha_canjeo
        )
        total_redimido += redencion.puntos_utilizados
    if total_redimido > 0:
        print(f"  ✅ Redenciones: {total_redimido} puntos")
    
    # 3. Migrar referidos
    referidos = Referidos.query.filter_by(documento_cliente=documento).all()
    total_referidos = 0
    for referido in referidos:
        if referido.puntos_obtenidos:
            crear_transaccion_manual(
                documento=documento,
                tipo='REFERIDO',
                puntos=referido.puntos_obtenidos,
                descripcion=f'Migración: Referido {referido.nombre_referido}',
                referencia=str(referido.id),
                fecha_compra=referido.fecha_referido
            )
            total_referidos += referido.puntos_obtenidos
    if total_referidos > 0:
        print(f"  ✅ Referidos: {total_referidos} puntos")
    
    # 4. Migrar puntos de regalo
    if puntos_cliente and puntos_cliente.puntos_regalo:
        crear_transaccion_manual(
            documento=documento,
            tipo='REGALO',
            puntos=puntos_cliente.puntos_regalo,
            descripcion='Migración: Puntos de regalo históricos',
            referencia='MIGRACION_REGALOS'
        )
        print(f"  ✅ Regalos: {puntos_cliente.puntos_regalo} puntos")
    
    print(f"✅ Cliente {documento} migrado exitosamente")

# ============================================================================
# FUNCIONES DE RETRASO DE 1 DÍA EN PUNTOS
# Los puntos de compras de HOY no están disponibles hasta MAÑANA
# ============================================================================
def obtener_fecha_limite_puntos():
    """
    Retorna la fecha límite para calcular puntos disponibles.
    Los puntos de compras de HOY no están disponibles, solo los de días anteriores.
    """
    # La fecha límite es AYER (las compras de hoy no cuentan)
    fecha_limite = datetime.now().date() - timedelta(days=1)
    return fecha_limite

def es_compra_disponible_para_puntos(fecha_compra):
    """
    Verifica si una compra ya está disponible para acumular puntos.
    Retorna True si la compra es de un día anterior a HOY.
    """
    if not fecha_compra:
        return False
    
    # Convertir a date si es datetime
    if isinstance(fecha_compra, datetime):
        fecha_compra = fecha_compra.date()
    
    fecha_limite = obtener_fecha_limite_puntos()
    return fecha_compra <= fecha_limite

def calcular_puntos_con_retraso(facturas_dict, documento):
    """
    Calcula los puntos aplicando el retraso de 1 día.
    Solo cuenta puntos de compras anteriores a HOY.
    Retorna: (total_puntos_disponibles, total_puntos_pendientes, historial)
    """
    total_puntos_disponibles = 0
    total_puntos_pendientes = 0
    historial = []
    
    # Obtener el valor base para el cálculo de puntos
    obtener_puntos_valor = maestros.query.with_entities(maestros.obtener_puntos).first()[0]
    
    for factura_key, factura_info in facturas_dict.items():
        lineas = factura_info['lineas']
        mediopag = factura_info['mediopag']
        es_individual = len(factura_info['items']) == 1
        fecha_compra = factura_info['fecha_compra']
        total_venta_factura = factura_info['total_venta']
        
        # Verificar si esta compra ya está disponible para puntos
        compra_disponible = es_compra_disponible_para_puntos(fecha_compra)
        
        # Condiciones de cálculo (lógica original sin cambios)
        tiene_cel_cyt = any('CEL' in l or 'CYT' in l for l in lineas)
        tiene_gdgt_acce = any('GDGT' in l or 'ACCE' in l for l in lineas)
        solo_gdgt_acce = all('GDGT' in l or 'ACCE' in l for l in lineas) if lineas else False
        medio_pago_valido = mediopag in ['01', '02']
        aplicar_multiplicador = False
        puntos_factura = 0
        
        # Cálculo de puntos según el año (lógica original sin cambios)
        if fecha_compra.year == 2024:
            puntos_factura = int((total_venta_factura // obtener_puntos_valor) / 2)
            if fecha_compra >= datetime(2024, 11, 25):
                if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                    aplicar_multiplicador = True
                if medio_pago_valido and es_individual:
                    aplicar_multiplicador = True
                if aplicar_multiplicador:
                    puntos_factura *= 2
        elif fecha_compra.year >= 2025:
            puntos_factura = int(total_venta_factura // obtener_puntos_valor)
            if (tiene_cel_cyt and tiene_gdgt_acce) or (tiene_gdgt_acce and solo_gdgt_acce):
                aplicar_multiplicador = True
            if medio_pago_valido and es_individual:
                aplicar_multiplicador = True
            if aplicar_multiplicador:
                puntos_factura *= 2
        
        # Separar puntos disponibles de pendientes
        if compra_disponible:
            total_puntos_disponibles += puntos_factura
        else:
            total_puntos_pendientes += puntos_factura
        
        # Procesar cada item de la factura para el historial
        for producto_key, row in factura_info['items'].items():
            venta_item = float(row[1])
            proporcion = venta_item / total_venta_factura if total_venta_factura > 0 else 0
            puntos_item = int(puntos_factura * proporcion)
            tipo_documento = "Factura Medellín" if row[3] == "FM" else "Factura Bogotá" if row[3] == "FB" else row[3]
            
            historial.append({
                "PRODUCTO_NOMBRE": row[0],
                "VLRVENTA": venta_item,
                "FHCOMPRA": fecha_compra.strftime('%Y-%m-%d'),
                "PUNTOS_GANADOS": puntos_item if compra_disponible else 0,
                "PUNTOS_PENDIENTES": puntos_item if not compra_disponible else 0,
                "TIPODCTO": tipo_documento,
                "NRODCTO": row[4],
                "LINEA": row[5],
                "MEDIOPAG": row[6],
                "TIPO_REGISTRO": "COMPRA",
                "DISPONIBLE": compra_disponible
            })
    
    return total_puntos_disponibles, total_puntos_pendientes, historial

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
                email_client = EmailClient.from_connection_string("endpoint=https://email-sender-miceluaz.unitedstates.communication.azure.com/;accesskey=BQXdsHbbOrCCgNlhAjruR1TEKGQMImCDnrz0InjuvKnRw4vfUqulJQQJ99BJACULyCp6Z5KHAAAAAZCS35sJ")
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
                    "senderAddress": "DoNotReply@micelu.co"
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
        # Usar sistema híbrido para calcular puntos
        total_puntos = calcular_puntos_con_fallback(documento_usuario)
       
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
@app.route('/factura/<int:factura_id>/pdf')
@login_required
def ver_factura_pdf(factura_id):
    """Ruta para servir PDFs de facturas"""
    try:
        # Aquí deberías implementar la lógica para obtener el PDF de la factura
        # Por ahora, devolvemos un PDF de ejemplo o un error
        documento = session.get('user_documento')
        if not documento:
            return redirect(url_for('login'))
        
        # TODO: Implementar lógica para obtener el PDF real de la factura
        
        # Ejemplo de respuesta (reemplazar con lógica real)
        return jsonify({
            'error': 'PDF no disponible',
            'message': 'Esta funcionalidad está en desarrollo'
        }), 404
        
    except Exception as e:
        return jsonify({
            'error': 'Error al cargar la factura',
            'message': str(e)
        }), 500

@app.route('/certificado/<int:certificado_id>/pdf')
@login_required
def ver_certificado_pdf(certificado_id):
    """Ruta para servir PDFs de certificados"""
    try:
        # Aquí deberías implementar la lógica para obtener el PDF del certificado
        # Por ahora, devolvemos un PDF de ejemplo o un error
        documento = session.get('user_documento')
        if not documento:
            return redirect(url_for('login'))
        
        # TODO: Implementar lógica para obtener el PDF real del certificado
        
        # Ejemplo de respuesta (reemplazar con lógica real)
        return jsonify({
            'error': 'PDF no disponible',
            'message': 'Esta funcionalidad está en desarrollo'
        }), 404
        
    except Exception as e:
        return jsonify({
            'error': 'Error al cargar el certificado',
            'message': str(e)
        }), 500

@app.route('/api/facturas')
def api_facturas():
    """API para obtener facturas del usuario a partir de factuiras.csv (filtradas por Receptor)."""
    try:
        documento = session.get('user_documento')
        if not documento:
            return jsonify({'error': 'No autorizado', 'message': 'Debes iniciar sesión'}), 401
        print("documento",documento)
        csv_path = os.path.join(os.getcwd(), 'factuiras.csv')
        if not os.path.exists(csv_path):
            return jsonify({'facturas': []})

        facturas = []
        # usar utf-8-sig para eliminar BOM en la primera cabecera
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # cubrir posible cabecera con BOM
                factura = (row.get('Factura') or row.get('\ufeffFactura') or '').strip()
                print(factura)
                receptor = (row.get('Receptor') or '').strip()
                print(receptor)
                if not factura or not receptor:
                    continue
                if str(receptor) != str(documento):
                    continue
                facturas.append({
                    'id': factura,  # usamos el número como id
                    'numero': factura,
                    'fecha': '',
                    'total': 0
                })
                print("facturas",facturas)

        return jsonify({'facturas': facturas})
    except Exception as e:
        print(f"Error en api_facturas: {e}")
        return jsonify({'error': str(e), 'message': 'Error interno del servidor'}), 500

@app.route('/api/test')
def api_test():
    """Ruta de prueba para verificar que las APIs funcionan"""
    return jsonify({
        'status': 'success',
        'message': 'API funcionando correctamente',
        'timestamp': str(datetime.now())
    })

@app.route('/api/facturas/<string:numero>/pdf')
def api_factura_pdf(numero: str):
    """Obtiene el pdf_url de Dataico para una factura por número y lo retorna como JSON."""
    try:
        # Endpoint externo Dataico
        external_url = 'https://api.dataico.com/direct/dataico_api/v2/invoices'
        headers = {
            'Auth-Token': '22f4608a83bad3c2438b8877a3ff12b5',
            'Content-Type': 'application/json'
        }
        params = { 'number': numero }

        resp = requests.get(external_url, headers=headers, params=params, timeout=20)
        if resp.status_code != 200:
            return jsonify({'error': 'Error consultando Dataico', 'status': resp.status_code, 'detail': resp.text}), 502

        data = resp.json() if resp.content else {}
        pdf_url = None
        if isinstance(data, dict):
            invoice = data.get('invoice') or {}
            pdf_url = invoice.get('pdf_url')

        if not pdf_url:
            return jsonify({'error': 'pdf_url no encontrado en la respuesta de Dataico'}), 404

        return jsonify({'pdf_url': pdf_url, 'numero': numero})
    except Exception as e:
        return jsonify({'error': 'Fallo al obtener el PDF', 'message': str(e)}), 500

def _dataico_pdf_url(numero: str) -> str | None:
    external_url = 'https://api.dataico.com/direct/dataico_api/v2/invoices'
    headers = {
        'Auth-Token': '22f4608a83bad3c2438b8877a3ff12b5',
        'Content-Type': 'application/json'
    }
    params = { 'number': numero }
    resp = requests.get(external_url, headers=headers, params=params, timeout=20)
    if resp.status_code != 200:
        return None
    data = resp.json() if resp.content else {}
    invoice = data.get('invoice') or {}
    return invoice.get('pdf_url')

@app.route('/api/facturas/<string:numero>/pdf/stream')
def api_factura_pdf_stream(numero: str):
    """Descarga el PDF de Dataico y lo sirve desde nuestro dominio para poder embeber en iframe."""
    try:
        pdf_url = _dataico_pdf_url(numero)
        if not pdf_url:
            return jsonify({'error': 'pdf_url no encontrado'}), 404

        upstream = requests.get(pdf_url, timeout=30)
        if upstream.status_code != 200:
            return jsonify({'error': 'No se pudo descargar el PDF', 'status': upstream.status_code}), 502

        response = Response(upstream.content, mimetype='application/pdf')
        # Opcional: permitir que se embeber desde nuestro dominio
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Cache-Control'] = 'private, max-age=300'
        if request.args.get('download') == '1':
            response.headers['Content-Disposition'] = f'attachment; filename="factura-{numero}.pdf"'
        return response
    except Exception as e:
        return jsonify({'error': 'Fallo al servir el PDF', 'message': str(e)}), 500

@app.route('/api/certificados')
def api_certificados():
    """API para obtener certificados del usuario a partir de factuiras.csv (filtradas por Receptor).
    Sólo se listan filas con enlace NSYS no vacío.
    """
    try:
        documento = session.get('user_documento')
        if not documento:
            return jsonify({'error': 'No autorizado', 'message': 'Debes iniciar sesión'}), 401

        csv_path = os.path.join(os.getcwd(), 'factuiras.csv')
        if not os.path.exists(csv_path):
            return jsonify({'certificados': []})

        certificados = []
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                factura = (row.get('Factura') or row.get('\ufeffFactura') or '').strip()
                receptor = (row.get('Receptor') or '').strip()
                nsys = (row.get('NSYS') or '').strip()
                if not factura or not receptor:
                    continue
                if str(receptor) != str(documento):
                    continue
                if not nsys:
                    continue
                certificados.append({
                    'id': factura,
                    'numero': factura,
                    'fecha': '',
                    'tipo': 'Certificado de diagnóstico',
                    'link': nsys
                })
                print("certificados",certificados)

        return jsonify({'certificados': certificados})
    except Exception as e:
        print(f"Error en api_certificados: {e}")
        return jsonify({'error': str(e), 'message': 'Error interno del servidor'}), 500

@app.route('/api/certificados/<string:numero>/pdf')
def api_certificado_pdf(numero: str):
    """Obtiene el pdf_url (vía Dataico) para un certificado por número y lo retorna como JSON.
    Nota: Si certificados usan la misma numeración que facturas en Dataico, este método funciona tal cual.
    """
    try:
        pdf_url = _dataico_pdf_url(numero)
        if not pdf_url:
            return jsonify({'error': 'pdf_url no encontrado para el certificado'}), 404
        return jsonify({'pdf_url': pdf_url, 'numero': numero})
    except Exception as e:
        return jsonify({'error': 'Fallo al obtener el PDF de certificado', 'message': str(e)}), 500

@app.route('/api/certificados/<string:numero>/pdf/stream')
def api_certificado_pdf_stream(numero: str):
    """Descarga el PDF del certificado desde Dataico y lo sirve desde nuestro dominio."""
    try:
        # Permite forzar un link específico (ej. NSYS) desde el frontend
        forced_url = request.args.get('url')
        # Intentar primero con NSYS si existe en CSV para este usuario cuando no viene forzado
        nsys_url = forced_url if forced_url else None
        documento = session.get('user_documento')
        csv_path = os.path.join(os.getcwd(), 'factuiras.csv')
        if not nsys_url and documento and os.path.exists(csv_path):
            with open(csv_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    fac = (row.get('Factura') or row.get('\ufeffFactura') or '').strip()
                    rec = (row.get('Receptor') or '').strip()
                    if fac == numero and str(rec) == str(documento):
                        nsys_url = (row.get('NSYS') or '').strip()
                        break

        if not nsys_url:
            return jsonify({'error': 'No hay enlace de certificado (NSYS) para este número'}), 404
        upstream = requests.get(nsys_url, timeout=30)
        if upstream.status_code != 200:
            return jsonify({'error': 'No se pudo descargar el PDF del certificado', 'status': upstream.status_code}), 502
        response = Response(upstream.content, mimetype='application/pdf')
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Cache-Control'] = 'private, max-age=300'
        if request.args.get('download') == '1':
            response.headers['Content-Disposition'] = f'attachment; filename="certificado-{numero}.pdf"'
        return response
    except Exception as e:
        return jsonify({'error': 'Fallo al servir el PDF de certificado', 'message': str(e)}), 500

@app.route('/mhistorialcompras')
@login_required
def mhistorialcompras():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
    if not documento:
        return redirect(url_for('login'))
    
    try:
        print(f"🔍 DEBUG: Consultando historial para documento: {documento}")
        
        # ============================================================================
        # CONSULTAR AMBAS FUENTES: SQL SERVER (2026+) + POSTGRESQL (2025-)
        # ============================================================================
        
        results_combinados = []
        
        # 1. Consultar SQL Server (Ofima) - Compras 2026+
        try:
            print("🔄 Consultando SQL Server (2026+)...")
            query_sql_server = """
            SELECT DISTINCT
             m.PRODUCTO_NOMBRE AS PRODUCTO_NOMBRE,
             CAST(m.VLRVENTA AS DECIMAL(15,2)) AS VLRVENTA,
             m.FHCOMPRA AS FHCOMPRA,
             m.TIPODCTO AS TIPODCTO,
             m.NRODCTO AS NRODCTO,
             m.LINEA AS LINEA,
             '' AS MEDIOPAG,
             m.PRODUCTO AS PRODUCTO
            FROM MVTRADE m
            WHERE m.IDENTIFICACION = ?
                AND CAST(m.VLRVENTA AS DECIMAL(15,2)) > 0
                AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
            ORDER BY m.FHCOMPRA DESC
            """
            
            results_sql = ejecutar_query_sql_server(query_sql_server, (documento,))
            if results_sql:
                print(f"✅ SQL Server: {len(results_sql)} registros")
                results_combinados.extend(results_sql)
            else:
                print("⚠️ SQL Server: Sin resultados")
        except Exception as e:
            print(f"⚠️ Error en SQL Server: {e}")
        
        # 2. Consultar PostgreSQL - Compras 2025-
        try:
            print("🔄 Consultando PostgreSQL (2025-)...")
            query_postgres = """
            SELECT DISTINCT
             m.nombre AS PRODUCTO_NOMBRE,
             CAST(m.vlrventa AS DECIMAL(15,2)) AS VLRVENTA,
             m.fhcompra AS FHCOMPRA,
             m.tipodcto AS TIPODCTO,
             m.nrodcto AS NRODCTO,
             'CEL' AS LINEA,
             '' AS MEDIOPAG,
             m.producto AS PRODUCTO
            FROM micelu_backup.mvtrade m
            WHERE m.nit = %s
                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
            ORDER BY m.fhcompra DESC;
            """
            
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            cursor_pg.execute(query_postgres, (documento,))
            results_pg = cursor_pg.fetchall()
            cursor_pg.close()
            conn_pg.close()
            
            print(f"✅ PostgreSQL: {len(results_pg)} registros")
            results_combinados.extend(results_pg)
        except Exception as e:
            print(f"⚠️ Error en PostgreSQL: {e}")
        
        print(f"📊 Total combinado: {len(results_combinados)} registros")
        
        # ============================================================================
        # PROCESAR RESULTADOS COMBINADOS
        # ============================================================================
        facturas_dict = {}
        for row in results_combinados:
            key = f"{row[3]}-{row[4]}"  # TIPODCTO-NRODCTO
            producto_key = f"{key}-{row[7]}"  # key-PRODUCTO
            
            # Convertir fecha
            fecha_str = row[2]  # FHCOMPRA
            try:
                if isinstance(fecha_str, str) and '/' in fecha_str:
                    fecha_compra = datetime.strptime(fecha_str, '%d/%m/%Y')
                elif isinstance(fecha_str, datetime):
                    fecha_compra = fecha_str
                else:
                    fecha_compra = datetime.now()
            except:
                fecha_compra = datetime.now()
            
            if key not in facturas_dict:
                facturas_dict[key] = {
                    'items': {},
                    'lineas': set(),
                    'mediopag': row[6].strip() if row[6] else '',
                    'total_venta': 0,
                    'fecha_compra': fecha_compra
                }
            
            if producto_key not in facturas_dict[key]['items']:
                facturas_dict[key]['items'][producto_key] = row
                facturas_dict[key]['total_venta'] += float(row[1])
                if row[5]:
                    facturas_dict[key]['lineas'].add(str(row[5]).upper())
        
        # ============================================================================
        # USAR FUNCIÓN DE CÁLCULO CON RETRASO DE 1 DÍA
        # Los puntos de compras de HOY no están disponibles hasta MAÑANA
        # ============================================================================
        total_puntos_disponibles, total_puntos_pendientes, historial = calcular_puntos_con_retraso(facturas_dict, documento)
        
        # Agregar referidos (lógica original - los referidos son inmediatos)
        referidos = Referidos.query.filter_by(
            documento_referido=documento).all()
        total_referidos_puntos = sum(
            referido.puntos_obtenidos for referido in referidos)
        total_puntos_disponibles += total_referidos_puntos
        
        for referido in referidos:
            historial.append({
                "FHCOMPRA": referido.fecha_referido.strftime('%Y-%m-%d'),
                "PRODUCTO_NOMBRE": f"Referido: {referido.nombre_cliente}",
                "VLRVENTA": referido.puntos_obtenidos * 100,
                "TIPODCTO": "Referido",
                "NRODCTO": str(referido.id),
                "PUNTOS_GANADOS": referido.puntos_obtenidos,
                "PUNTOS_PENDIENTES": 0,
                "LINEA": "REFERIDO",
                "MEDIOPAG": "",
                "DISPONIBLE": True
            })
        
        # ============================================================================
        # ACTUALIZAR PUNTOS: Sistema híbrido inteligente
        # ============================================================================
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        
        # Verificar si es usuario nuevo (ya está en sistema nuevo)
        if cliente_esta_migrado(documento):
            print(f"🆕 Usuario {documento} ya está en sistema nuevo - Creando transacción de compra")
            
            # Calcular puntos actuales antes de agregar nuevos
            puntos_actuales = calcular_puntos_con_fallback(documento)
            puntos_nuevos = total_puntos_disponibles - puntos_actuales
            
            # Solo crear transacción si hay puntos nuevos
            if puntos_nuevos > 0:
                try:
                    crear_transaccion_manual(
                        documento=documento,
                        tipo='ACUMULACION',
                        puntos=puntos_nuevos,
                        descripcion=f'Compras recientes - {len(facturas_dict)} facturas',
                        referencia='COMPRAS_RECIENTES'
                    )
                    print(f"✅ Transacción creada para usuario nuevo: +{puntos_nuevos} puntos")
                except Exception as e:
                    print(f"⚠️ Error creando transacción para usuario nuevo: {e}")
                    db.session.rollback()
            
            # Actualizar sistema viejo para compatibilidad
            if puntos_usuario:
                puntos_usuario.total_puntos = total_puntos_disponibles
                puntos_usuario.ultima_actualizacion = datetime.now()
            else:
                nuevo_usuario = Puntos_Clientes(
                    documento=documento,
                    total_puntos=total_puntos_disponibles,
                    puntos_redimidos='0',
                    puntos_regalo=0
                )
                db.session.add(nuevo_usuario)
            
            db.session.commit()
        else:
            # Usuario viejo - usar sistema viejo (se migrará automáticamente después)
            if puntos_usuario:
                puntos_usuario.total_puntos = total_puntos_disponibles
                puntos_usuario.ultima_actualizacion = datetime.now()
                db.session.commit()
            else:
                nuevo_usuario = Puntos_Clientes(
                    documento=documento,
                    total_puntos=total_puntos_disponibles,
                    puntos_redimidos='0',
                    puntos_regalo=0
                )
                db.session.add(nuevo_usuario)
                db.session.commit()
        
        # ============================================================================
        # USAR SISTEMA HÍBRIDO PARA CALCULAR PUNTOS FINALES
        # ============================================================================
        total_puntos = calcular_puntos_con_fallback(documento)
        
        historial.sort(key=lambda x: x['FHCOMPRA'], reverse=True)
        
        print(f"📊 Puntos disponibles: {total_puntos_disponibles}, Puntos pendientes: {total_puntos_pendientes}")
        
        return render_template(
            'mhistorialcompras.html',
            historial=historial,
            total_puntos=total_puntos,
            puntos_pendientes=total_puntos_pendientes,
            usuario=usuario,
            puntos_regalo=puntos_usuario.puntos_regalo if puntos_usuario else 0
        )
        
    except Exception as e:
        print(f"❌ Error en mhistorialcompras: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login'))

@app.route('/mpuntosprincipal')
@login_required
def mpuntosprincipal():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()
   
    # Usar sistema híbrido para calcular puntos
    total_puntos = calcular_puntos_con_fallback(documento)
   
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
 
        # ============================================================================
        # USAR SISTEMA HÍBRIDO PARA VERIFICAR PUNTOS DISPONIBLES
        # ============================================================================
        puntos_disponibles = calcular_puntos_con_fallback(documento)
        
        if puntos_a_redimir > puntos_disponibles:
            return jsonify({
                'success': False, 
                'message': f'No tienes suficientes puntos. Disponibles: {puntos_disponibles}'
            }), 400
 
        valor_del_punto = maestros.query.with_entities(maestros.valordelpunto).first()[0]
        descuento = puntos_a_redimir * valor_del_punto
        tiempo_expiracion = datetime.now() + timedelta(hours=horas_expiracion)
 
        woo_coupon = create_woo_coupon(codigo, descuento, tiempo_expiracion)
        if not woo_coupon:
            return jsonify({'success': False, 'message': 'Error al crear el cupón en WooCommerce'}), 500
 
        # ============================================================================
        # CREAR TRANSACCIÓN EN EL SISTEMA NUEVO
        # ============================================================================
        nuevo_historial = historial_beneficio(
            id=uuid.uuid4(),
            documento=documento,
            valor_descuento=descuento,
            puntos_utilizados=puntos_a_redimir,
            fecha_canjeo=datetime.now(),
            cupon=codigo,
            tiempo_expiracion=tiempo_expiracion,
            estado_cupon='GENERADO'
        )
        db.session.add(nuevo_historial)
        
        # Crear transacción de redención en el sistema nuevo
        if cliente_esta_migrado(documento):
            crear_transaccion_manual(
                documento=documento,
                tipo='REDENCION',
                puntos=-puntos_a_redimir,  # Negativo porque se están gastando
                descripcion=f'Redención cupón {codigo} - ${descuento:,.0f}',
                referencia=str(nuevo_historial.id)
            )
        
        # Actualizar sistema viejo para mantener compatibilidad
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_usuario:
            puntos_redimidos_actual = int(puntos_usuario.puntos_redimidos or '0')
            puntos_usuario.puntos_redimidos = str(puntos_redimidos_actual + puntos_a_redimir)
            puntos_usuario.ultima_actualizacion = datetime.now()
        
        db.session.commit()
        
        # Recalcular puntos disponibles después de la redención
        nuevos_puntos = calcular_puntos_con_fallback(documento)
 
        return jsonify({
            'success': True,
            'new_total': nuevos_puntos,
            'codigo': codigo,
            'descuento': descuento,
            'tiempo_expiracion': tiempo_expiracion.isoformat()
        }), 200
 
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': f'Error al redimir puntos: {str(e)}'}), 500
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
    if not documento:
        return redirect(url_for('login'))
    
    try:
        print(f"🔍 DEBUG quesonpuntos: Consultando puntos para documento: {documento}")
        
        # ============================================================================
        # CONSULTAR AMBAS FUENTES: SQL SERVER (2026+) + POSTGRESQL (2025-)
        # ============================================================================
        
        results_combinados = []
        
        # 1. Consultar SQL Server (Ofima) - Compras 2026+
        try:
            query_sql_server = """
            SELECT DISTINCT
             m.PRODUCTO_NOMBRE AS PRODUCTO_NOMBRE,
             CAST(m.VLRVENTA AS DECIMAL(15,2)) AS VLRVENTA,
             m.FHCOMPRA AS FHCOMPRA,
             m.TIPODCTO AS TIPODCTO,
             m.NRODCTO AS NRODCTO,
             m.LINEA AS LINEA,
             '' AS MEDIOPAG,
             m.PRODUCTO AS PRODUCTO
            FROM MVTRADE m
            WHERE m.IDENTIFICACION = ?
                AND CAST(m.VLRVENTA AS DECIMAL(15,2)) > 0
                AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
            ORDER BY m.FHCOMPRA DESC
            """
            
            results_sql = ejecutar_query_sql_server(query_sql_server, (documento,))
            if results_sql:
                results_combinados.extend(results_sql)
        except Exception as e:
            print(f"⚠️ Error en SQL Server: {e}")
        
        # 2. Consultar PostgreSQL - Compras 2025-
        try:
            query_postgres = """
            SELECT DISTINCT
             m.nombre AS PRODUCTO_NOMBRE,
             CAST(m.vlrventa AS DECIMAL(15,2)) AS VLRVENTA,
             m.fhcompra AS FHCOMPRA,
             m.tipodcto AS TIPODCTO,
             m.nrodcto AS NRODCTO,
             'CEL' AS LINEA,
             '' AS MEDIOPAG,
             m.producto AS PRODUCTO
            FROM micelu_backup.mvtrade m
            WHERE m.nit = %s
                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
            ORDER BY m.fhcompra DESC;
            """
            
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            cursor_pg.execute(query_postgres, (documento,))
            results_pg = cursor_pg.fetchall()
            cursor_pg.close()
            conn_pg.close()
            results_combinados.extend(results_pg)
        except Exception as e:
            print(f"⚠️ Error en PostgreSQL: {e}")
        
        # Agrupar por factura
        facturas_dict = {}
        for row in results_combinados:
            key = f"{row[3]}-{row[4]}"  # TIPODCTO-NRODCTO
            producto_key = f"{key}-{row[7]}"  # key-PRODUCTO
            
            # Convertir fecha
            fecha_str = row[2]
            try:
                if isinstance(fecha_str, str) and '/' in fecha_str:
                    fecha_compra = datetime.strptime(fecha_str, '%d/%m/%Y')
                elif isinstance(fecha_str, datetime):
                    fecha_compra = fecha_str
                else:
                    fecha_compra = datetime.now()
            except:
                fecha_compra = datetime.now()
            
            if key not in facturas_dict:
                facturas_dict[key] = {
                    'items': {},
                    'lineas': set(),
                    'mediopag': row[6].strip() if row[6] else '',
                    'total_venta': 0,
                    'fecha_compra': fecha_compra
                }
            
            if producto_key not in facturas_dict[key]['items']:
                facturas_dict[key]['items'][producto_key] = row
                facturas_dict[key]['total_venta'] += float(row[1])
                if row[5]:
                    facturas_dict[key]['lineas'].add(str(row[5]).upper())
        
        # Calcular puntos con retraso
        total_puntos_disponibles, total_puntos_pendientes, historial = calcular_puntos_con_retraso(facturas_dict, documento)
        
        # Agregar referidos
        referidos = Referidos.query.filter_by(documento_referido=documento).all()
        total_referidos_puntos = sum(referido.puntos_obtenidos for referido in referidos)
        total_puntos_disponibles += total_referidos_puntos
        
        # Actualizar base de datos
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        
        if cliente_esta_migrado(documento):
            # Usuario ya migrado - actualizar sistema viejo para compatibilidad
            if puntos_usuario:
                puntos_usuario.total_puntos = total_puntos_disponibles
                puntos_usuario.ultima_actualizacion = datetime.now()
            else:
                nuevo_usuario = Puntos_Clientes(
                    documento=documento,
                    total_puntos=total_puntos_disponibles,
                    puntos_redimidos='0',
                    puntos_regalo=0
                )
                db.session.add(nuevo_usuario)
            db.session.commit()
        else:
            # Usuario no migrado - actualizar sistema viejo
            if puntos_usuario:
                puntos_usuario.total_puntos = total_puntos_disponibles
                puntos_usuario.ultima_actualizacion = datetime.now()
                db.session.commit()
            else:
                nuevo_usuario = Puntos_Clientes(
                    documento=documento,
                    total_puntos=total_puntos_disponibles,
                    puntos_redimidos='0',
                    puntos_regalo=0
                )
                db.session.add(nuevo_usuario)
                db.session.commit()
        
        # Calcular puntos finales usando sistema híbrido
        total_puntos = calcular_puntos_con_fallback(documento)
        
        print(f"🔍 DEBUG quesonpuntos: Total puntos finales: {total_puntos}")
        
        # Obtener usuario
        usuario = Usuario.query.filter_by(documento=documento).first()
        puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
        
        return render_template('puntos.html', 
                               total_puntos=total_puntos, 
                               puntos_pendientes=total_puntos_pendientes,
                               usuario=usuario,
                               puntos_regalo=puntos_usuario.puntos_regalo if puntos_usuario else 0)
    
    except Exception as e:
        print(f"❌ Error en quesonpuntos: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        
        # Intentar mostrar al menos los puntos guardados
        try:
            usuario = Usuario.query.filter_by(documento=documento).first()
            puntos_usuario = Puntos_Clientes.query.filter_by(documento=documento).first()
            total_puntos = calcular_puntos_con_fallback(documento)
            
            return render_template('puntos.html', 
                                   total_puntos=total_puntos, 
                                   puntos_pendientes=0,
                                   usuario=usuario,
                                   puntos_regalo=puntos_usuario.puntos_regalo if puntos_usuario else 0)
        except:
            flash('Error al cargar puntos. Por favor intenta de nuevo.', 'error')
            return render_template('puntos.html', 
                                   total_puntos=0, 
                                   puntos_pendientes=0,
                                   usuario=Usuario.query.filter_by(documento=documento).first(),
                                   puntos_regalo=0)

@app.route('/test_imei_samples')
@login_required
def test_imei_samples():
    """Ver ejemplos de IMEIs en la base de datos"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Ver algunos ejemplos de series
        cursor_pg.execute("""
            SELECT serie, tipo_documento, documento, referencia, valor, nit
            FROM micelu_backup.vseries_utilidad 
            WHERE serie IS NOT NULL AND serie != ''
            ORDER BY fecha_inicial DESC
            LIMIT 10
        """)
        
        ejemplos = cursor_pg.fetchall()
        
        # Ver si hay algún IMEI que contenga parte del que buscamos
        imei_parcial = "355843800846903"
        cursor_pg.execute("""
            SELECT serie, tipo_documento, documento, referencia, valor, nit
            FROM micelu_backup.vseries_utilidad 
            WHERE serie LIKE %s OR serie LIKE %s OR serie LIKE %s
            LIMIT 5
        """, (f"%{imei_parcial[:10]}%", f"%{imei_parcial[:8]}%", f"%{imei_parcial[:6]}%"))
        
        similares = cursor_pg.fetchall()
        
        # Ver estadísticas de longitud de series
        cursor_pg.execute("""
            SELECT 
                LENGTH(serie) as longitud,
                COUNT(*) as cantidad,
                MIN(serie) as ejemplo_min,
                MAX(serie) as ejemplo_max
            FROM micelu_backup.vseries_utilidad 
            WHERE serie IS NOT NULL AND serie != ''
            GROUP BY LENGTH(serie)
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        
        estadisticas = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'ejemplos_recientes': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1],
                    'documento': row[2],
                    'referencia': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'nit': row[5]
                } for row in ejemplos
            ],
            'similares_al_buscado': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1],
                    'documento': row[2],
                    'referencia': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'nit': row[5]
                } for row in similares
            ],
            'estadisticas_longitud': [
                {
                    'longitud': row[0],
                    'cantidad': row[1],
                    'ejemplo_min': row[2],
                    'ejemplo_max': row[3]
                } for row in estadisticas
            ]
        })
        
    except Exception as e:
        print(f"❌ ERROR test_imei_samples: {e}")
        return jsonify({'error': str(e)})

@app.route('/test_simple_imei/<imei>')
@login_required
def test_simple_imei(imei):
    """Función de prueba simple para debuggear búsqueda de IMEI"""
    try:
        print(f"🔍 TEST SIMPLE: Probando IMEI: {imei}")
        
        # Probar consulta directa en PostgreSQL
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Consulta muy simple usando vseries_utilidad
        query_simple = """
        SELECT serie, tipo_documento, documento, referencia, valor, nit, fecha_inicial
        FROM micelu_backup.vseries_utilidad 
        WHERE serie = %s OR LEFT(serie, 15) = %s
        LIMIT 1
        """
        
        cursor_pg.execute(query_simple, (imei, imei[:15]))
        result = cursor_pg.fetchone()
        
        if result:
            print(f"✅ TEST SIMPLE: Encontrado: {result}")
            return jsonify({
                'encontrado': True,
                'serie': result[0],
                'tipo_documento': result[1],
                'documento': result[2],
                'referencia': result[3],
                'valor': float(result[4]) if result[4] else 0,
                'nit': result[5],
                'fecha_inicial': str(result[6]) if result[6] else None
            })
        else:
            print(f"❌ TEST SIMPLE: No encontrado")
            # Buscar similares
            cursor_pg.execute("SELECT serie FROM micelu_backup.vseries_utilidad WHERE serie LIKE %s LIMIT 5", (f"%{imei[:10]}%",))
            similares = cursor_pg.fetchall()
            
            # También contar total de registros
            cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.vseries_utilidad")
            total = cursor_pg.fetchone()[0]
            
            return jsonify({
                'encontrado': False,
                'imei_buscado': imei,
                'similares': [row[0] for row in similares],
                'total_registros_en_tabla': total
            })
        
        cursor_pg.close()
        conn_pg.close()
        
    except Exception as e:
        print(f"❌ ERROR test_simple_imei: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/mis_productos/<nit>')
@login_required
def mis_productos(nit):
    """Ver qué productos/códigos tiene un usuario específico"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Buscar productos en mvtrade
        cursor_pg.execute("""
            SELECT DISTINCT
                producto,
                nombre,
                tipodcto,
                nrodcto,
                vlrventa,
                fhcompra
            FROM micelu_backup.mvtrade 
            WHERE nit = %s
            ORDER BY fhcompra DESC
            LIMIT 10
        """, (nit,))
        
        productos = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'nit': nit,
            'productos_disponibles': [
                {
                    'codigo_producto': row[0],
                    'nombre': row[1],
                    'tipo_documento': row[2],
                    'numero_documento': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'fecha': str(row[5]) if row[5] else None
                } for row in productos
            ],
            'total': len(productos)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/test_vseries_status')
@login_required
def test_vseries_status():
    """Verificar el estado de la tabla vseries_utilidad después de la reimportación"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Contar total de registros
        cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.vseries_utilidad")
        total_registros = cursor_pg.fetchone()[0]
        
        # Ver algunos ejemplos de series
        cursor_pg.execute("""
            SELECT serie, tipo_documento, documento, referencia, valor, fecha_inicial, nit
            FROM micelu_backup.vseries_utilidad 
            WHERE serie IS NOT NULL AND serie != ''
            ORDER BY fecha_inicial DESC
            LIMIT 10
        """)
        ejemplos = cursor_pg.fetchall()
        
        # Ver qué NITs únicos hay
        cursor_pg.execute("""
            SELECT nit, COUNT(*) as cantidad
            FROM micelu_backup.vseries_utilidad 
            GROUP BY nit
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        nits_frecuentes = cursor_pg.fetchall()
        
        # Buscar NITs similares al tuyo
        cursor_pg.execute("""
            SELECT DISTINCT nit
            FROM micelu_backup.vseries_utilidad 
            WHERE nit LIKE %s OR nit LIKE %s
            LIMIT 5
        """, ('%1036689216%', '%103668%'))
        nits_similares = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'total_registros': total_registros,
            'ejemplos_series': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1],
                    'documento': row[2],
                    'referencia': row[3][:50] + '...' if row[3] and len(row[3]) > 50 else row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'fecha_inicial': str(row[5]) if row[5] else None,
                    'nit': row[6]
                } for row in ejemplos
            ],
            'nits_mas_frecuentes': [
                {
                    'nit': row[0],
                    'cantidad': row[1]
                } for row in nits_frecuentes
            ],
            'nits_similares_al_tuyo': [row[0] for row in nits_similares]
        })
        
    except Exception as e:
        print(f"❌ ERROR test_vseries_status: {e}")
        return jsonify({'error': str(e)})

@app.route('/test_real_imeis/<nit>')
@login_required
def test_real_imeis(nit):
    """Ver los IMEIs reales después de la reimportación"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Ver IMEIs reales del usuario
        cursor_pg.execute("""
            SELECT 
                serie,
                tipo_documento, 
                documento, 
                referencia, 
                valor, 
                fecha_inicial
            FROM micelu_backup.vseries_utilidad 
            WHERE nit = %s OR nit LIKE %s
            ORDER BY fecha_inicial DESC
            LIMIT 5
        """, (nit, f"{nit}%"))
        
        resultados = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'nit_buscado': nit,
            'imeis_reales': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1],
                    'documento': row[2],
                    'referencia': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'fecha_inicial': str(row[5]) if row[5] else None
                } for row in resultados
            ],
            'total_encontrados': len(resultados)
        })
        
    except Exception as e:
        print(f"❌ ERROR test_real_imeis: {e}")
        return jsonify({'error': str(e)})

@app.route('/test_other_tables')
@login_required
def test_other_tables():
    """Ver qué datos hay en otras tablas que podrían tener IMEIs"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        resultados = {}
        
        # Revisar tabla mvtrade (que sabemos que funciona para puntos)
        try:
            cursor_pg.execute("""
                SELECT COUNT(*) FROM micelu_backup.mvtrade
                WHERE nit = %s
            """, ('1036689216',))
            count_mvtrade = cursor_pg.fetchone()[0]
            
            if count_mvtrade > 0:
                cursor_pg.execute("""
                    SELECT tipodcto, nrodcto, producto, nombre, vlrventa, fhcompra, nit
                    FROM micelu_backup.mvtrade
                    WHERE nit = %s
                    LIMIT 3
                """, ('1036689216',))
                ejemplos_mvtrade = cursor_pg.fetchall()
                resultados['mvtrade'] = {
                    'count': count_mvtrade,
                    'ejemplos': [list(row) for row in ejemplos_mvtrade]
                }
        except Exception as e:
            resultados['mvtrade'] = {'error': str(e)}
        
        # Revisar otras tablas
        tablas_a_revisar = ['clientes', 'v_clientes_fac', 'v_ventas']
        
        for tabla in tablas_a_revisar:
            try:
                cursor_pg.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'micelu_backup' 
                    AND table_name = '{tabla}'
                    ORDER BY ordinal_position
                """)
                columnas = cursor_pg.fetchall()
                
                cursor_pg.execute(f"SELECT COUNT(*) FROM micelu_backup.{tabla}")
                count = cursor_pg.fetchone()[0]
                
                resultados[tabla] = {
                    'count': count,
                    'columnas': [{'nombre': col[0], 'tipo': col[1]} for col in columnas]
                }
                
            except Exception as e:
                resultados[tabla] = {'error': str(e)}
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/test_convert_imei/<nit>')
@login_required
def test_convert_imei(nit):
    """Convertir los IMEIs de notación científica a formato normal"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Convertir series de notación científica a formato normal
        cursor_pg.execute("""
            SELECT 
                serie as serie_original,
                CASE 
                    WHEN serie ~ '^[0-9.E+-]+$' THEN 
                        LPAD(CAST(CAST(serie AS DECIMAL(20,0)) AS TEXT), 15, '0')
                    ELSE serie
                END AS serie_convertida,
                tipo_documento, 
                documento, 
                referencia, 
                valor, 
                fecha_inicial
            FROM micelu_backup.vseries_utilidad 
            WHERE nit = %s OR nit LIKE %s
            ORDER BY fecha_inicial DESC
            LIMIT 5
        """, (nit, f"{nit}%"))
        
        resultados = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'nit_buscado': nit,
            'imeis_convertidos': [
                {
                    'serie_original': row[0],
                    'serie_convertida': row[1],
                    'tipo_documento': row[2],
                    'documento': row[3],
                    'referencia': row[4],
                    'valor': float(row[5]) if row[5] else 0,
                    'fecha_inicial': str(row[6]) if row[6] else None
                } for row in resultados
            ],
            'total_encontrados': len(resultados)
        })
        
    except Exception as e:
        print(f"❌ ERROR test_convert_imei: {e}")
        return jsonify({'error': str(e)})

@app.route('/test_imei_by_nit/<nit>')
@login_required
def test_imei_by_nit(nit):
    """Ver qué IMEIs tiene un NIT específico"""
    try:
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Buscar IMEIs por NIT
        cursor_pg.execute("""
            SELECT serie, tipo_documento, documento, referencia, valor, fecha_inicial
            FROM micelu_backup.vseries_utilidad 
            WHERE nit = %s OR nit LIKE %s
            ORDER BY fecha_inicial DESC
            LIMIT 10
        """, (nit, f"{nit}%"))
        
        imeis_del_nit = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        return jsonify({
            'nit_buscado': nit,
            'imeis_encontrados': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1],
                    'documento': row[2],
                    'referencia': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'fecha_inicial': str(row[5]) if row[5] else None
                } for row in imeis_del_nit
            ],
            'total_encontrados': len(imeis_del_nit)
        })
        
    except Exception as e:
        print(f"❌ ERROR test_imei_by_nit: {e}")
        return jsonify({'error': str(e)})

@app.route('/test_imei/<imei>')
@login_required
def test_imei(imei):
    """Función de prueba para debuggear búsqueda de IMEI"""
    try:
        print(f"🔍 TEST: Probando IMEI: {imei}")
        
        # Probar consulta directa en PostgreSQL
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        
        # Consulta simple para ver qué hay en la tabla series
        query_test = """
        SELECT COUNT(*) FROM micelu_backup.series 
        WHERE serie LIKE %s OR LEFT(serie, 15) LIKE %s
        """
        
        cursor_pg.execute(query_test, (f"%{imei}%", f"%{imei}%"))
        count = cursor_pg.fetchone()[0]
        print(f"🔍 TEST: Encontrados {count} registros con IMEI similar")
        
        # Buscar algunos ejemplos
        query_examples = """
        SELECT serie, tipo_documento, documento, referencia, valor, nit
        FROM micelu_backup.series 
        WHERE serie LIKE %s OR LEFT(serie, 15) LIKE %s
        LIMIT 5
        """
        
        cursor_pg.execute(query_examples, (f"%{imei}%", f"%{imei}%"))
        examples = cursor_pg.fetchall()
        
        cursor_pg.close()
        conn_pg.close()
        
        # Probar la función buscar_por_imei
        resultado_busqueda = buscar_por_imei(imei)
        
        return jsonify({
            'imei_buscado': imei,
            'registros_encontrados': count,
            'ejemplos': [
                {
                    'serie': row[0],
                    'tipo_documento': row[1], 
                    'documento': row[2],
                    'referencia': row[3],
                    'valor': float(row[4]) if row[4] else 0,
                    'nit': row[5]
                } for row in examples
            ],
            'resultado_buscar_por_imei': resultado_busqueda
        })
        
    except Exception as e:
        print(f"❌ ERROR test_imei: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

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
                # Crear el registro en la tabla Puntos_Clientes (para compatibilidad)
                nuevo_punto_cliente = Puntos_Clientes(
                    documento=documento,
                    total_puntos='0',
                    fecha_registro=datetime.now(UTC),
                    puntos_redimidos='0'
                )
                db.session.add(nuevo_punto_cliente)
                
                # ============================================================================
                # USUARIOS NUEVOS: Crear transacción inicial en sistema nuevo
                # ============================================================================
                print(f"🆕 Usuario nuevo {documento}: Creando en sistema nuevo desde día 1")
                transaccion_inicial = Transacciones_Puntos(
                    id=str(uuid.uuid4()),
                    documento=documento,
                    tipo_transaccion='REGALO',
                    puntos=0,  # 0 puntos iniciales
                    puntos_disponibles_antes=0,
                    puntos_disponibles_despues=0,
                    fecha_transaccion=datetime.now(),
                    fecha_vencimiento=None,  # Los regalos no vencen
                    descripcion='Usuario nuevo - Registro inicial en sistema nuevo',
                    estado='ACTIVO'
                )
                db.session.add(transaccion_inicial)
                
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
        print(f"🔍 DEBUG crear_usuario: Documento limpio: {documento}")
 
        # Consulta SQL Server (MICELU1)
        query_sql_server = """
        SELECT DISTINCT
            c.NOMBRE AS CLIENTE_NOMBRE,
            c.NIT,
            CASE 
                WHEN c.TEL1 IS NOT NULL AND c.TEL1 != '' THEN c.TEL1 
                ELSE c.TEL2 
            END AS telefono,
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
            AND (m.TIPODCTO='FM' OR m.TIPODCTO='FB' OR m.TIPODCTO='FC')
            AND m.VLRVENTA>0
            AND (c.NIT = ? OR c.NIT LIKE ?)
        ORDER BY
            c.NOMBRE;
        """
        
        # Consulta PostgreSQL (backup histórico)
        query_postgres = """
        SELECT DISTINCT
            c.nombre AS CLIENTE_NOMBRE,
            c.nit AS NIT,
            CASE 
                WHEN c.tel1 IS NOT NULL AND c.tel1 != '' THEN c.tel1 
                ELSE c.tel2 
            END AS telefono,
            c.email AS EMAIL,
            c.ciudad AS CIUDAD,
            c.descrip_tipo_cli AS DescripTipoCli
        FROM
            micelu_backup.clientes c
        JOIN
            micelu_backup.v_clientes_fac vc ON c.nombre = vc.nombre
        JOIN
            micelu_backup.mvtrade m ON vc.tipodcto = m.tipodcto AND vc.nrodcto = m.nrodcto
        WHERE
            c.habilitado = 'S'
            AND (m.tipodcto='FM' OR m.tipodcto='FB' OR m.tipodcto='FC')
            AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            AND (c.nit = %s OR c.nit LIKE %s)
        ORDER BY
            c.nombre;
        """
 
        print(f"🔍 DEBUG crear_usuario: Ejecutando consulta con parámetros: {documento}, {documento}%")
        
        # DIAGNÓSTICO: Vamos a probar consultas más simples primero
        try:
            print("🔍 DIAGNÓSTICO: Probando conexión directa a SQL Server...")
            conn_sql = obtener_conexion_bd()
            cursor_sql = conn_sql.cursor()
            
            # Consulta 1: ¿Existe la cédula en Clientes?
            cursor_sql.execute("SELECT COUNT(*) FROM Clientes WHERE NIT = ? OR NIT LIKE ?", (documento, f"{documento}%"))
            count_clientes = cursor_sql.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO: Cédulas encontradas en Clientes: {count_clientes}")
            
            # Consulta 2: ¿Está habilitada?
            cursor_sql.execute("SELECT COUNT(*) FROM Clientes WHERE (NIT = ? OR NIT LIKE ?) AND HABILITADO = 'S'", (documento, f"{documento}%"))
            count_habilitados = cursor_sql.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO: Cédulas habilitadas: {count_habilitados}")
            
            # Consulta 3: ¿Tiene compras?
            cursor_sql.execute("""
                SELECT COUNT(*) FROM Clientes c
                JOIN V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
                JOIN Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
                WHERE (c.NIT = ? OR c.NIT LIKE ?) 
                AND c.HABILITADO = 'S'
                AND (m.TIPODCTO='FM' OR m.TIPODCTO='FB' OR m.TIPODCTO='FC')
                AND m.VLRVENTA>0
            """, (documento, f"{documento}%"))
            count_compras = cursor_sql.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO: Compras válidas encontradas: {count_compras}")
            
            # Consulta 4: Ver datos específicos del cliente
            cursor_sql.execute("SELECT TOP 3 NOMBRE, NIT, HABILITADO, CIUDAD FROM Clientes WHERE NIT = ? OR NIT LIKE ?", (documento, f"{documento}%"))
            clientes_info = cursor_sql.fetchall()
            print(f"🔍 DIAGNÓSTICO: Información de clientes:")
            for cliente in clientes_info:
                print(f"   - Nombre: {cliente[0]}, NIT: {cliente[1]}, Habilitado: {cliente[2]}, Ciudad: {cliente[3]}")
            
            cursor_sql.close()
            conn_sql.close()
            
        except Exception as e:
            print(f"❌ DIAGNÓSTICO falló: {e}")
        
        # DIAGNÓSTICO POSTGRESQL: Vamos a probar consultas más simples
        try:
            print("🔍 DIAGNÓSTICO POSTGRESQL: Probando conexión...")
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            
            # Consulta 1: ¿Existe la cédula en clientes?
            cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.clientes WHERE nit = %s OR nit LIKE %s", (documento, f"{documento}%"))
            count_clientes_pg = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: Cédulas encontradas en clientes: {count_clientes_pg}")
            
            # Consulta 2: ¿Está habilitada?
            cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.clientes WHERE (nit = %s OR nit LIKE %s) AND habilitado = 'S'", (documento, f"{documento}%"))
            count_habilitados_pg = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: Cédulas habilitadas: {count_habilitados_pg}")
            
            # Consulta 3: ¿Tiene compras en mvtrade?
            cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.mvtrade WHERE nit = %s AND CAST(vlrventa AS DECIMAL(15,2)) > 0", (documento,))
            count_mvtrade = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: Compras en mvtrade: {count_mvtrade}")
            
            # Consulta 4: ¿Existe en v_clientes_fac?
            cursor_pg.execute("SELECT COUNT(*) FROM micelu_backup.v_clientes_fac vc JOIN micelu_backup.clientes c ON c.nombre = vc.nombre WHERE c.nit = %s", (documento,))
            count_v_clientes_fac = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: Registros en v_clientes_fac: {count_v_clientes_fac}")
            
            # Consulta 5: Ver datos específicos del cliente
            cursor_pg.execute("SELECT nombre, nit, habilitado, ciudad FROM micelu_backup.clientes WHERE nit = %s OR nit LIKE %s LIMIT 3", (documento, f"{documento}%"))
            clientes_info_pg = cursor_pg.fetchall()
            print(f"🔍 DIAGNÓSTICO PG: Información de clientes:")
            for cliente in clientes_info_pg:
                print(f"   - Nombre: {cliente[0]}, NIT: {cliente[1]}, Habilitado: {cliente[2]}, Ciudad: {cliente[3]}")
            
            # Consulta 6: Probar el JOIN completo paso a paso
            cursor_pg.execute("""
                SELECT COUNT(*) FROM micelu_backup.clientes c
                JOIN micelu_backup.v_clientes_fac vc ON c.nombre = vc.nombre
                WHERE c.nit = %s AND c.habilitado = 'S'
            """, (documento,))
            count_join1 = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: JOIN clientes + v_clientes_fac: {count_join1}")
            
            cursor_pg.execute("""
                SELECT COUNT(*) FROM micelu_backup.clientes c
                JOIN micelu_backup.v_clientes_fac vc ON c.nombre = vc.nombre
                JOIN micelu_backup.mvtrade m ON vc.tipodcto = m.tipodcto AND vc.nrodcto = m.nrodcto
                WHERE c.nit = %s AND c.habilitado = 'S'
                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            """, (documento,))
            count_join2 = cursor_pg.fetchone()[0]
            print(f"🔍 DIAGNÓSTICO PG: JOIN completo sin filtro tipo documento: {count_join2}")
            
            cursor_pg.close()
            conn_pg.close()
            
        except Exception as e:
            print(f"❌ DIAGNÓSTICO POSTGRESQL falló: {e}")
            import traceback
            traceback.print_exc()
        
        # Ejecutar consulta con fallback
        results, fuente = ejecutar_consulta_con_fallback(
            query_sql_server, 
            query_postgres, 
            (documento, f"{documento}%"),
            tipo_consulta='usuario'
        )
        
        print(f"🔍 DEBUG crear_usuario: Fuente: {fuente}, Resultados: {len(results)}")
 
        # Si no hay resultados, la cédula no está registrada
        if not results:
            print(f"❌ DEBUG crear_usuario: No se encontraron resultados para documento {documento}")
            return False
 
        print(f"✅ DEBUG crear_usuario: Procesando {len(results)} resultados")
        
        with app.app_context():
            with db.session.begin():
                for i, row in enumerate(results):
                    print(f"🔍 DEBUG crear_usuario: Procesando resultado {i+1}: {row.CLIENTE_NOMBRE if hasattr(row, 'CLIENTE_NOMBRE') else 'Sin nombre'}")
                    
                    ciudad= 'Medellin' if ciudad == 'Medellín' else 'Bogota' if ciudad == 'Bogotá' else 'Cali' if ciudad == 'Cali' else ciudad
 
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
                    print(f"✅ DEBUG crear_usuario: Usuario creado exitosamente")
                    
                    # ============================================================================
                    # CREAR TRANSACCIONES INICIALES DE PUNTOS
                    # Calcular puntos desde AMBAS fuentes (SQL Server + PostgreSQL)
                    # ============================================================================
                    try:
                        print(f"🔄 Calculando puntos iniciales para {documento}...")
                        
                        # Consultar compras de AMBAS fuentes
                        results_compras = []
                        
                        # SQL Server (2026+)
                        try:
                            conn_sql = obtener_conexion_bd()
                            cursor_sql = conn_sql.cursor()
                            query_compras_sql = """
                            SELECT DISTINCT
                             m.PRODUCTO_NOMBRE, CAST(m.VLRVENTA AS DECIMAL(15,2)), m.FHCOMPRA,
                             m.TIPODCTO, m.NRODCTO, m.LINEA, '', m.PRODUCTO
                            FROM MVTRADE m
                            WHERE m.IDENTIFICACION = ?
                                AND CAST(m.VLRVENTA AS DECIMAL(15,2)) > 0
                                AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
                            """
                            cursor_sql.execute(query_compras_sql, (documento,))
                            results_compras.extend(cursor_sql.fetchall())
                            cursor_sql.close()
                            conn_sql.close()
                        except Exception as e_sql:
                            print(f"⚠️ Error consultando SQL Server: {e_sql}")
                            pass
                        
                        # PostgreSQL (2025-)
                        try:
                            conn_pg = obtener_conexion_bd_backup()
                            cursor_pg = conn_pg.cursor()
                            query_compras_pg = """
                            SELECT DISTINCT
                             m.nombre, CAST(m.vlrventa AS DECIMAL(15,2)), m.fhcompra,
                             m.tipodcto, m.nrodcto, 'CEL', '', m.producto
                            FROM micelu_backup.mvtrade m
                            WHERE m.nit = %s
                                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                                AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
                            """
                            cursor_pg.execute(query_compras_pg, (documento,))
                            results_compras.extend(cursor_pg.fetchall())
                            cursor_pg.close()
                            conn_pg.close()
                        except Exception as e_pg:
                            print(f"⚠️ Error consultando PostgreSQL: {e_pg}")
                            pass
                        
                        if results_compras:
                            # Agrupar por factura y calcular puntos
                            facturas_dict = {}
                            for row in results_compras:
                                key = f"{row[3]}-{row[4]}"
                                producto_key = f"{key}-{row[7]}"
                                
                                fecha_str = row[2]
                                try:
                                    if isinstance(fecha_str, str) and '/' in fecha_str:
                                        fecha_compra = datetime.strptime(fecha_str, '%d/%m/%Y')
                                    elif isinstance(fecha_str, datetime):
                                        fecha_compra = fecha_str
                                    else:
                                        fecha_compra = datetime.now()
                                except:
                                    fecha_compra = datetime.now()
                                
                                if key not in facturas_dict:
                                    facturas_dict[key] = {
                                        'items': {},
                                        'lineas': set(),
                                        'mediopag': '',
                                        'total_venta': 0,
                                        'fecha_compra': fecha_compra
                                    }
                                
                                if producto_key not in facturas_dict[key]['items']:
                                    facturas_dict[key]['items'][producto_key] = row
                                    facturas_dict[key]['total_venta'] += float(row[1])
                                    if row[5]:
                                        facturas_dict[key]['lineas'].add(str(row[5]).upper())
                            
                            # Calcular puntos con retraso
                            total_puntos_disponibles, _, _ = calcular_puntos_con_retraso(facturas_dict, documento)
                            
                            # Crear registro en Puntos_Clientes
                            nuevo_puntos = Puntos_Clientes(
                                documento=documento,
                                total_puntos=total_puntos_disponibles,
                                puntos_redimidos='0',
                                puntos_regalo=0,
                                fecha_registro=datetime.now(),
                                puntos_disponibles=total_puntos_disponibles
                            )
                            db.session.add(nuevo_puntos)
                            
                            # Crear transacción inicial en el sistema nuevo
                            crear_transaccion_manual(
                                documento=documento,
                                tipo='ACUMULACION',
                                puntos=total_puntos_disponibles,
                                descripcion=f'Puntos iniciales al registrarse - {len(facturas_dict)} facturas',
                                referencia='REGISTRO_INICIAL'
                            )
                            
                            db.session.commit()
                            print(f"✅ Puntos iniciales creados: {total_puntos_disponibles} puntos")
                        else:
                            # Sin compras, crear registro con 0 puntos
                            nuevo_puntos = Puntos_Clientes(
                                documento=documento,
                                total_puntos=0,
                                puntos_redimidos='0',
                                puntos_regalo=0,
                                fecha_registro=datetime.now(),
                                puntos_disponibles=0
                            )
                            db.session.add(nuevo_puntos)
                            db.session.commit()
                            print(f"✅ Usuario sin compras, registro creado con 0 puntos")
                            
                    except Exception as e:
                        print(f"⚠️ Error calculando puntos iniciales: {e}")
                        db.session.rollback()
 
        return True
 
    except pyodbc.Error as e:
        print(f"❌ Error de base de datos en crear_usuario: {e}")
        raise e
    except Exception as e:
        print(f"❌ Error general en crear_usuario: {e}")
        import traceback
        traceback.print_exc()
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
    documento = session.get('user_documento')
  
    # Usar sistema híbrido para calcular puntos
    total_puntos = calcular_puntos_con_fallback(documento)
    
    return render_template("infobeneficios.html", product=product, total_puntos=total_puntos)

@app.route('/redime_ahora')
def redime_ahora():
    documento_usuario = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento_usuario).first()
    
    # Usar sistema híbrido para calcular puntos
    total_puntos = calcular_puntos_con_fallback(documento_usuario)
    
    return render_template("redime_ahora.html", total_puntos=total_puntos, usuario=usuario)

@app.route('/acumulapuntos')
def acumulapuntos():
    return render_template("acumulapuntos.html")

@app.route('/debug_documento/<documento>')
def debug_documento(documento):
    """Función de debug para verificar si un documento existe en las bases de datos"""
    try:
        print(f"🔍 DEBUG: Buscando documento {documento}")
        
        # 1. Probar SQL Server
        try:
            print("🔄 Probando SQL Server...")
            conn_sql = obtener_conexion_bd()
            cursor_sql = conn_sql.cursor()
            
            # Consulta simple para ver si el cliente existe
            query_simple_sql = "SELECT TOP 5 NIT, NOMBRE FROM Clientes WHERE NIT = ? OR NIT LIKE ?"
            cursor_sql.execute(query_simple_sql, (documento, f"{documento}%"))
            resultados_sql = cursor_sql.fetchall()
            cursor_sql.close()
            conn_sql.close()
            
            print(f"✅ SQL Server encontró {len(resultados_sql)} clientes")
            
        except Exception as e:
            print(f"❌ SQL Server falló: {e}")
            resultados_sql = []
        
        # 2. Probar PostgreSQL
        try:
            print("🔄 Probando PostgreSQL...")
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            
            # Consulta simple para ver si el cliente existe
            query_simple_pg = "SELECT nit, nombre FROM micelu_backup.clientes WHERE nit = %s OR nit LIKE %s LIMIT 5"
            cursor_pg.execute(query_simple_pg, (documento, f"{documento}%"))
            resultados_pg = cursor_pg.fetchall()
            cursor_pg.close()
            conn_pg.close()
            
            print(f"✅ PostgreSQL encontró {len(resultados_pg)} clientes")
            
        except Exception as e:
            print(f"❌ PostgreSQL falló: {e}")
            resultados_pg = []
        
        # 3. Probar si tiene compras
        try:
            print("🔄 Probando compras en PostgreSQL...")
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            
            query_compras = """
            SELECT COUNT(*) as total_compras, 
                   MIN(fhcompra) as primera_compra, 
                   MAX(fhcompra) as ultima_compra,
                   SUM(CAST(vlrventa AS DECIMAL(15,2))) as total_ventas
            FROM micelu_backup.mvtrade 
            WHERE nit = %s 
                AND CAST(vlrventa AS DECIMAL(15,2)) > 0
                AND (tipodcto = 'FM' OR tipodcto = 'FB' OR tipodcto = 'FC')
            """
            cursor_pg.execute(query_compras, (documento,))
            compras_info = cursor_pg.fetchone()
            cursor_pg.close()
            conn_pg.close()
            
        except Exception as e:
            print(f"❌ Error consultando compras: {e}")
            compras_info = (0, None, None, 0)
        
        # Crear respuesta HTML
        html = f"""
        <h2>🔍 Debug Documento: {documento}</h2>
        
        <h3>📊 SQL Server (MICELU1)</h3>
        <p>Clientes encontrados: {len(resultados_sql)}</p>
        <ul>
        """
        
        for row in resultados_sql:
            html += f"<li>NIT: {row[0]}, Nombre: {row[1]}</li>"
        
        html += f"""
        </ul>
        
        <h3>📊 PostgreSQL (Backup)</h3>
        <p>Clientes encontrados: {len(resultados_pg)}</p>
        <ul>
        """
        
        for row in resultados_pg:
            html += f"<li>NIT: {row[0]}, Nombre: {row[1]}</li>"
        
        html += f"""
        </ul>
        
        <h3>🛒 Información de Compras (PostgreSQL)</h3>
        <p>Total compras: {compras_info[0] if compras_info else 0}</p>
        <p>Primera compra: {compras_info[1] if compras_info and compras_info[1] else 'N/A'}</p>
        <p>Última compra: {compras_info[2] if compras_info and compras_info[2] else 'N/A'}</p>
        <p>Total ventas: ${compras_info[3] if compras_info else 0:,.2f}</p>
        
        <h3>🔧 Consulta Completa de Registro</h3>
        """
        
        # Probar la consulta completa de registro
        try:
            query_registro_pg = """
            SELECT DISTINCT
                c.nombre AS CLIENTE_NOMBRE,
                c.nit AS NIT,
                CASE 
                    WHEN c.tel1 IS NOT NULL AND c.tel1 != '' THEN c.tel1 
                    ELSE c.tel2 
                END AS telefono,
                c.email AS EMAIL,
                c.ciudad AS CIUDAD,
                c.descrip_tipo_cli AS DescripTipoCli
            FROM
                micelu_backup.clientes c
            JOIN
                micelu_backup.v_clientes_fac vc ON c.nombre = vc.nombre
            JOIN
                micelu_backup.mvtrade m ON vc.tipodcto = m.tipodcto AND vc.nrodcto = m.nrodcto
            WHERE
                c.habilitado = 'S'
                AND (m.tipodcto='FM' OR m.tipodcto='FB' OR m.tipodcto='FC')
                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                AND (c.nit = %s OR c.nit LIKE %s)
            ORDER BY
                c.nombre;
            """
            
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            cursor_pg.execute(query_registro_pg, (documento, f"{documento}%"))
            registro_resultados = cursor_pg.fetchall()
            cursor_pg.close()
            conn_pg.close()
            
            html += f"<p>✅ Consulta de registro encontró: {len(registro_resultados)} resultados</p>"
            
            for i, row in enumerate(registro_resultados):
                html += f"<p>Resultado {i+1}: {row[0]} - {row[1]} - {row[3]}</p>"
                
        except Exception as e:
            html += f"<p>❌ Error en consulta de registro: {e}</p>"
        
        html += """
        <br><br>
        <a href="/crear_pass">← Volver al registro</a>
        """
        
        return html
        
    except Exception as e:
        return f"<h2>❌ Error en debug</h2><p>{str(e)}</p>"

@app.route('/test_historial_postgres')
def test_historial_postgres():
    """Probar la consulta de historial en PostgreSQL"""
    try:
        documento = session.get('user_documento', '1036689216')
        
        # Consulta simple que sabemos que funciona
        query_simple = """
        SELECT DISTINCT
         m.nombre AS PRODUCTO_NOMBRE,
         CAST(m.vlrventa AS DECIMAL(15,2)) AS VLRVENTA,
         '2025-01-01'::DATE AS FHCOMPRA,
         m.tipodcto AS TIPODCTO,
         m.nrodcto AS NRODCTO,
         'CEL' AS LINEA,
         '' AS MEDIOPAG,
         m.producto AS PRODUCTO
        FROM micelu_backup.mvtrade m
        WHERE m.nit = %s
            AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
        ORDER BY m.tipodcto, m.nrodcto;
        """
        
        conn = obtener_conexion_bd_backup()
        cursor = conn.cursor()
        cursor.execute(query_simple, (documento,))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        html = f"<h2>Test Historial PostgreSQL</h2>"
        html += f"<p>Documento: {documento}</p>"
        html += f"<p>Resultados: {len(resultados)}</p>"
        
        for i, row in enumerate(resultados):
            html += f"<p>Registro {i+1}: {row}</p>"
            
        return html
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/test_postgres_simple')
def test_postgres_simple():
    """Prueba simple de PostgreSQL"""
    try:
        documento = session.get('user_documento', '1000644140')
        
        # Consulta simple sin JOINs complejos
        query_simple = """
        SELECT m.tipodcto, m.nrodcto, m.nombre, m.vlrventa, m.fhcompra, m.nit
        FROM micelu_backup.mvtrade m
        WHERE m.nit = %s
        LIMIT 10
        """
        
        conn = obtener_conexion_bd_backup()
        cursor = conn.cursor()
        cursor.execute(query_simple, (documento,))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        
        html = f"<h2>Prueba PostgreSQL Simple</h2>"
        html += f"<p>Documento: {documento}</p>"
        html += f"<p>Resultados encontrados: {len(resultados)}</p>"
        
        for i, row in enumerate(resultados[:5]):
            html += f"<p>Registro {i+1}: {row}</p>"
            
        return html
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error</h2><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/actualizar_fechas_postgres')
@login_required
def actualizar_fechas_postgres():
    """Función para actualizar las fechas en PostgreSQL desde el CSV"""
    try:
        import csv
        actualizaciones = 0
        errores = 0
        
        # Leer el CSV con las fechas correctas
        with open('series (1).csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            
            for row in reader:
                try:
                    # Limpiar datos del CSV
                    tipo_doc = row['Tipo_Documento'].strip()
                    documento = row['Documento'].strip().replace('"', '').strip()
                    nit = row['NIT'].strip().replace('"', '').strip()
                    fecha_str = row['Fecha_Inicial'].strip()
                    
                    # Parsear fecha
                    if ' ' in fecha_str:
                        fecha_real = fecha_str.split(' ')[0]  # Solo la parte de fecha
                    else:
                        fecha_real = fecha_str
                    
                    # Actualizar PostgreSQL
                    update_query = """
                    UPDATE micelu_backup.mvtrade 
                    SET fhcompra = %s 
                    WHERE tipodcto = %s AND nrodcto = %s AND nit = %s
                    """
                    
                    cursor_pg.execute(update_query, (fecha_real, tipo_doc, documento, nit))
                    
                    if cursor_pg.rowcount > 0:
                        actualizaciones += cursor_pg.rowcount
                    
                except Exception as e:
                    errores += 1
                    print(f"Error procesando fila: {e}")
            
            conn_pg.commit()
            cursor_pg.close()
            conn_pg.close()
        
        return jsonify({
            'success': True,
            'actualizaciones': actualizaciones,
            'errores': errores,
            'message': f'Actualizadas {actualizaciones} fechas en PostgreSQL. Errores: {errores}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error al actualizar fechas en PostgreSQL'
        })

@app.route('/test_postgres')
def test_postgres():
    """Ruta de prueba para verificar PostgreSQL"""
    try:
        conn = obtener_conexion_bd_backup()
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT COUNT(*) FROM micelu_backup.mvtrade")
        count_mvtrade = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM micelu_backup.clientes")
        count_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM micelu_backup.v_clientes_fac")
        count_v_clientes_fac = cursor.fetchone()[0]
        
        # Probar consulta específica con tu documento
        documento = session.get('user_documento', '1000644140')  # Usar tu documento o uno de prueba
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM micelu_backup.clientes c
            JOIN micelu_backup.v_clientes_fac vc ON c.nombre = vc.nombre
            JOIN micelu_backup.mvtrade m ON vc.tipodcto = m.tipodcto AND vc.nrodcto = m.nrodcto
            WHERE c.nit = %s OR c.nit LIKE %s
        """, (documento, f"{documento}%"))
        
        count_user_data = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return f"""
        <h2>Test PostgreSQL Backup</h2>
        <p>✅ Conexión exitosa</p>
        <p>📊 Registros en mvtrade: {count_mvtrade}</p>
        <p>👥 Registros en clientes: {count_clientes}</p>
        <p>🔗 Registros en v_clientes_fac: {count_v_clientes_fac}</p>
        <p>🎯 Datos para documento {documento}: {count_user_data}</p>
        """
        
    except Exception as e:
        import traceback
        return f"""
        <h2>❌ Error PostgreSQL</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """

@app.route('/')
def inicio():
    return render_template("home.html")

@app.route('/redimir')
def redimiendo():
    documento_usuario = session.get('user_documento')
    
    # Usar sistema híbrido para calcular puntos
    total_puntos = calcular_puntos_con_fallback(documento_usuario)
   
    return render_template("redimir.html", total_puntos=total_puntos)
    
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
        
        # Usar sistema híbrido para calcular puntos disponibles
        puntos_disponibles = calcular_puntos_con_fallback(documento)
        
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
            
            # Actualizar puntos usando sistema híbrido
            puntos_redimidos_actual = int(puntos_usuario.puntos_redimidos or '0')
            puntos_usuario.puntos_redimidos = str(puntos_redimidos_actual + puntos_a_redimir)
            
            cupon_existente.estado = True
            cupon_existente.valor_descuento = descuento
            cupon_existente.puntos_utilizados = puntos_a_redimir
            cupon_existente.fecha_canjeo = datetime.now()
            
        else:
            # Si no existe un cupón previo, crear uno nuevo
            puntos_redimidos_actual = int(puntos_usuario.puntos_redimidos or '0')
            puntos_usuario.puntos_redimidos = str(puntos_redimidos_actual + puntos_a_redimir)
            
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
    """
    Crea una nueva conexión a SQL Server con autocommit habilitado.
    IMPORTANTE: Siempre cerrar la conexión después de usarla.
    """
    conn = pyodbc.connect(
        '''DRIVER={ODBC Driver 18 for SQL Server};SERVER=172.200.231.95;DATABASE=MICELU1;UID=db_read;PWD=mHRL_<='(],#aZ)T"A3QeD;TrustServerCertificate=yes''',
        autocommit=True  # Evita problemas de transacciones cerradas
    )
    return conn

def ejecutar_query_sql_server(query, params=None):
    """
    Ejecuta una query en SQL Server de forma segura usando context manager.
    Retorna los resultados o None si hay error.
    """
    conn = None
    cursor = None
    try:
        conn = obtener_conexion_bd()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"❌ Error ejecutando query SQL Server: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def obtener_conexion_bd_backup():
    """Conexión a PostgreSQL con datos históricos"""
    try:
        conn = psycopg2.connect(
            host="junction.proxy.rlwy.net",
            port=47834,
            database="railway", 
            user="postgres",
            password="vWUiwzFrdvcyroebskuHXMlBoAiTfgzP"
        )
        print("✅ Conexión PostgreSQL exitosa")
        return conn
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        raise

def obtener_datos_sharepoint():
    """
    Obtiene todos los datos de compras desde PostgreSQL y los retorna como DataFrame.
    Esta función reemplaza la lectura de SharePoint para el dashboard de auditoría.
    """
    try:
        query_postgres = """
        SELECT DISTINCT
         m.nit AS IDENTIFICACION,
         m.nombre AS PRODUCTO,
         CAST(m.vlrventa AS DECIMAL(15,2)) AS VLRVENTA,
         m.fhcompra AS FHCOMPRA,
         m.tipodcto AS TIPODCTO,
         m.nrodcto AS NRODCTO,
         'CEL' AS LINEA,
         '' AS MEDIOPAG
        FROM micelu_backup.mvtrade m
        WHERE CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
        ORDER BY m.fhcompra DESC;
        """
        
        conn_pg = obtener_conexion_bd_backup()
        
        # Usar pandas para leer directamente a DataFrame
        df = pd.read_sql_query(query_postgres, conn_pg)
        conn_pg.close()
        
        # Debug: ver qué columnas se obtuvieron
        print(f"📋 Columnas obtenidas: {df.columns.tolist()}")
        
        # Normalizar nombres de columnas a mayúsculas
        df.columns = df.columns.str.upper()
        
        # Convertir fechas de texto DD/MM/YYYY a datetime
        def convertir_fecha(fecha_str):
            try:
                if isinstance(fecha_str, str) and '/' in fecha_str:
                    return datetime.strptime(fecha_str, '%d/%m/%Y')
                elif isinstance(fecha_str, datetime):
                    return fecha_str
                else:
                    return datetime.now()
            except:
                return datetime.now()
        
        if 'FHCOMPRA' in df.columns:
            df['FHCOMPRA'] = df['FHCOMPRA'].apply(convertir_fecha)
        
        print(f"✅ Datos obtenidos: {len(df)} registros de compras")
        return df
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        import traceback
        traceback.print_exc()
        return None

def ejecutar_consulta_con_fallback(query_sql_server, query_postgres, parametros, tipo_consulta='historial'):
    """
    Ejecuta consulta en SQL Server primero, si no hay resultados consulta PostgreSQL
    Devuelve resultados en formato consistente
    """
    # Manejar diferentes tipos de parámetros
    if isinstance(parametros, tuple) and len(parametros) == 2 and isinstance(parametros[0], list):
        # Caso especial para buscar_por_imei con parámetros diferentes
        params_sql, params_pg = parametros
    else:
        # Caso normal con los mismos parámetros para ambas consultas
        params_sql = parametros
        params_pg = parametros  # Usar los mismos parámetros para PostgreSQL
    
    # 1. Intentar primero en SQL Server (MICELU1)
    try:
        print("🔄 Consultando SQL Server (MICELU1)...")
        resultados = ejecutar_query_sql_server(query_sql_server, params_sql)
        
        if resultados:
            print(f"✅ SQL Server devolvió {len(resultados)} registros")
            return resultados, 'sql_server'
        else:
            print("⚠️ SQL Server no devolvió resultados")
            
    except Exception as e:
        print(f"❌ SQL Server falló: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Si no hay resultados, consultar PostgreSQL backup
    try:
        print("🔄 Consultando PostgreSQL backup...")
        conn_pg = obtener_conexion_bd_backup()
        cursor_pg = conn_pg.cursor()
        cursor_pg.execute(query_postgres, params_pg)
        resultados_pg = cursor_pg.fetchall()
        cursor_pg.close()
        conn_pg.close()
        
        print(f"✅ PostgreSQL devolvió {len(resultados_pg)} registros")
        
        if not resultados_pg:
            return [], 'no_results'
        
        # Convertir tuplas de PostgreSQL a objetos con atributos para compatibilidad
        if tipo_consulta == 'historial':
            # Para consultas de historial de compras (8 campos)
            class ResultRowHistorial:
                def __init__(self, row):
                    self.PRODUCTO_NOMBRE = row[0]
                    self.VLRVENTA = row[1]
                    self.FHCOMPRA = row[2]
                    self.TIPODCTO = row[3]
                    self.NRODCTO = row[4]
                    self.LINEA = row[5]
                    self.MEDIOPAG = row[6]
                    self.PRODUCTO = row[7]
            
            resultados_convertidos = [ResultRowHistorial(row) for row in resultados_pg]
        
        elif tipo_consulta == 'usuario':
            # Para consultas de registro de usuarios (6 campos)
            class ResultRowUsuario:
                def __init__(self, row):
                    self.CLIENTE_NOMBRE = row[0]
                    self.NIT = row[1]
                    self.telefono = row[2]
                    self.EMAIL = row[3]
                    self.CIUDAD = row[4]
                    self.DescripTipoCli = row[5]
            
            resultados_convertidos = [ResultRowUsuario(row) for row in resultados_pg]
        
        elif tipo_consulta == 'cobertura':
            # Para consultas de cobertura (12 campos)
            class ResultRowCobertura:
                def __init__(self, row):
                    self.Tipo_Documento = row[0]
                    self.Documento = row[1]
                    self.Factura = row[2]
                    self.IMEI = row[3]
                    self.Producto = row[4]
                    self.Valor = row[5]
                    self.Fecha_Compra = row[6]
                    self.NIT = row[7]
                    self.codgrupo = row[8]
                    self.Correo = row[9] if len(row) > 9 else ""
                    self.Telefono = row[10] if len(row) > 10 else ""
                    self.Nombre = row[11] if len(row) > 11 else ""
            
            resultados_convertidos = [ResultRowCobertura(row) for row in resultados_pg]
        
        else:
            # Devolver tuplas sin conversión para otros tipos
            resultados_convertidos = resultados_pg
        
        return resultados_convertidos, 'postgres'
        
    except Exception as e:
        print(f"❌ PostgreSQL también falló: {e}")
        import traceback
        traceback.print_exc()
        return [], 'error'

def buscar_por_imei(imei):
    """
    Busca información asociada a un IMEI específico con fallback a PostgreSQL
    Usa múltiples tablas para encontrar el IMEI
    """
    imei_limpio = imei.strip()
    print(f"🔍 DEBUG buscar_por_imei: Buscando IMEI: {imei_limpio}")
    
    # Preparar variantes del IMEI
    imei_variantes = [imei_limpio]
    if imei_limpio.endswith('A'):
        imei_variantes.append(imei_limpio[:-1])
    else:
        imei_variantes.append(imei_limpio + 'A')
    
    print(f"🔍 DEBUG buscar_por_imei: Variantes: {imei_variantes}")
    
    try:
        for variante in imei_variantes:
            print(f"🔍 DEBUG buscar_por_imei: Probando variante: {variante}")
            
            # Intentar SQL Server primero
            try:
                print("🔍 Intentando SQL Server...")
                
                query_sql_server = """
                SELECT DISTINCT TOP 1
                    v.Tipo_Documento, v.Documento, v.Tipo_Documento + v.Documento AS Factura,
                    v.Serie AS Serie_Completa, LEFT(v.Serie, 15) AS IMEI, v.Referencia AS Producto,
                    v.Valor, v.Fecha_Inicial AS Fecha, v.NIT, m.codgrupo, c.EMAIL AS Correo,
                    CASE WHEN c.TEL1 IS NOT NULL AND c.TEL1 != '' THEN c.TEL1 ELSE c.TEL2 END AS Telefono,
                    c.Nombre AS Nombre_Cliente
                FROM VSeriesUtilidad v WITH (NOLOCK)
                JOIN MTMercia m ON v.Producto = m.CODIGO
                JOIN MTPROCLI c ON v.nit = c.NIT
                WHERE v.Tipo_Documento IN ('FB', 'FM', 'FC') AND v.Valor > 0
                    AND m.CODLINEA = 'CEL' AND m.CODGRUPO = 'SEMI'
                    AND v.NIT NOT IN ('1152718000', '1053817613', '1000644140', '01')
                    AND (v.Serie = ? OR LEFT(v.Serie, 15) = ?)
                ORDER BY v.Fecha_Inicial DESC
                """
                
                resultados = ejecutar_query_sql_server(query_sql_server, (variante, variante[:15]))
                
                if resultados:
                    print(f"✅ SQL Server encontró resultado")
                    resultado = resultados[0]
                    return {
                        'imei': resultado[3],  # Serie_Completa
                        'imei_limpio': resultado[4],  # IMEI
                        'referencia': resultado[5],  # Producto
                        'valor': float(resultado[6]),  # Valor
                        'fecha': resultado[7].strftime('%Y-%m-%d') if resultado[7] else None,
                        'nit': resultado[8],  # NIT
                        'nombre': resultado[12] if len(resultado) > 12 else '',
                        'correo': resultado[10] if len(resultado) > 10 else '',
                        'telefono': resultado[11] if len(resultado) > 11 else ''
                    }
                    
            except Exception as e:
                print(f"⚠️ SQL Server falló: {e}")
            
            # Intentar PostgreSQL
            try:
                print("🔄 Consultando PostgreSQL backup...")
                conn_pg = obtener_conexion_bd_backup()
                cursor_pg = conn_pg.cursor()
                
                # Buscar en vseries_utilidad primero
                query_vseries = """
                SELECT 
                    v.tipo_documento, v.documento, v.tipo_documento || v.documento AS factura,
                    v.serie, LEFT(v.serie, 15) AS imei, v.referencia,
                    CAST(v.valor AS DECIMAL(15,2)) AS valor,
                    CASE 
                        WHEN v.fecha_inicial ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}' THEN TO_DATE(v.fecha_inicial, 'DD/MM/YYYY')
                        ELSE '2025-01-01'::DATE
                    END AS fecha,
                    v.nit, 'SEMI' AS codgrupo,
                    COALESCE(c.email, '') AS correo, COALESCE(c.tel1, c.tel2, '') AS telefono,
                    COALESCE(c.nombre, '') AS nombre_cliente
                FROM micelu_backup.vseries_utilidad v
                LEFT JOIN micelu_backup.clientes c ON TRIM(v.nit) = TRIM(c.nit)
                WHERE v.tipo_documento IN ('FB', 'FM', 'FC')
                    AND CAST(v.valor AS DECIMAL(15,2)) > 0
                    AND v.nit NOT IN ('1152718000', '1053817613', '1000644140', '01')
                    AND (v.serie = %s OR LEFT(v.serie, 15) = %s)
                ORDER BY fecha DESC
                LIMIT 1
                """
                
                cursor_pg.execute(query_vseries, (variante, variante[:15]))
                resultado = cursor_pg.fetchone()
                
                if resultado:
                    print(f"✅ PostgreSQL vseries_utilidad encontró resultado")
                    cursor_pg.close()
                    conn_pg.close()
                    return {
                        'imei': resultado[3],  # serie
                        'imei_limpio': resultado[4],  # imei
                        'referencia': resultado[5],  # referencia
                        'valor': float(resultado[6]),  # valor
                        'fecha': resultado[7].strftime('%Y-%m-%d') if resultado[7] else None,
                        'nit': resultado[8],  # nit
                        'nombre': resultado[12] if len(resultado) > 12 else '',
                        'correo': resultado[10] if len(resultado) > 10 else '',
                        'telefono': resultado[11] if len(resultado) > 11 else ''
                    }
                
                # Si no encuentra en vseries_utilidad, buscar en mvtrade
                print("🔍 Buscando en mvtrade...")
                query_mvtrade = """
                SELECT 
                    m.tipodcto, m.nrodcto, m.tipodcto || m.nrodcto AS factura,
                    m.producto, LEFT(TRIM(m.producto), 15) AS imei, m.nombre,
                    CAST(m.vlrventa AS DECIMAL(15,2)) AS valor,
                    CASE 
                        WHEN m.fhcompra ~ '^[0-9]{2}/[0-9]{2}/[0-9]{4}' THEN TO_DATE(m.fhcompra, 'DD/MM/YYYY')
                        ELSE '2025-01-01'::DATE
                    END AS fecha,
                    m.nit, 'CEL' AS codgrupo,
                    COALESCE(c.email, '') AS correo, COALESCE(c.tel1, c.tel2, '') AS telefono,
                    COALESCE(c.nombre, '') AS nombre_cliente
                FROM micelu_backup.mvtrade m
                LEFT JOIN micelu_backup.clientes c ON TRIM(m.nit) = TRIM(c.nit)
                WHERE m.tipodcto IN ('FB', 'FM', 'FC')
                    AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                    AND m.nit NOT IN ('1152718000', '1053817613', '1000644140', '01')
                    AND (TRIM(m.producto) = %s OR LEFT(TRIM(m.producto), 15) = %s OR m.producto = %s)
                ORDER BY fecha DESC
                LIMIT 1
                """
                
                cursor_pg.execute(query_mvtrade, (variante.strip(), variante[:15].strip(), variante))
                resultado = cursor_pg.fetchone()
                
                cursor_pg.close()
                conn_pg.close()
                
                if resultado:
                    print(f"✅ PostgreSQL mvtrade encontró resultado")
                    return {
                        'imei': resultado[3],  # producto
                        'imei_limpio': resultado[4],  # imei
                        'referencia': resultado[5],  # nombre
                        'valor': float(resultado[6]),  # valor
                        'fecha': resultado[7].strftime('%Y-%m-%d') if resultado[7] else None,
                        'nit': resultado[8],  # nit
                        'nombre': resultado[12] if len(resultado) > 12 else '',
                        'correo': resultado[10] if len(resultado) > 10 else '',
                        'telefono': resultado[11] if len(resultado) > 11 else ''
                    }
                
            except Exception as e:
                print(f"❌ PostgreSQL falló: {e}")
        
        print(f"❌ DEBUG buscar_por_imei: No se encontraron resultados para el IMEI: {imei_limpio}")
        return None
        
    except Exception as e:
        print(f"❌ ERROR buscar_por_imei: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

class CoberturaEmailService:
    def __init__(self):
        # Configuración de conexión de Azure Communication Services
        self.connection_string = "endpoint=https://email-sender-miceluaz.unitedstates.communication.azure.com/;accesskey=BQXdsHbbOrCCgNlhAjruR1TEKGQMImCDnrz0InjuvKnRw4vfUqulJQQJ99BJACULyCp6Z5KHAAAAAZCS35sJ"
        self.sender_address = "DoNotReply@micelu.co"

    def enviar_confirmacion_cobertura(self, datos_cobertura, fecha_fin):
        try:
            email_client = EmailClient.from_connection_string(self.connection_string)

            # URL de la imagen
            url_imagen = "https://i.postimg.cc/zXqYFxZf/Cobertura.jpg"

            contenido_html = f"""
            <html>
                <body style="font-family: Poppins, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; font-size: 14px; line-height: 1.6;">
                    <div style="text-align: center; margin-bottom: 20px;">
                    <img src="{url_imagen}" alt="Logo Micelu" style="max-width: 600px; display: block; margin: 0 auto;">
                    </div>
                    <h2 style="color: #333; font-size: 20px;">Confirmación de Cobertura</h2>
                    <p style="font-size: 16px;">Estimado(a) <strong>{datos_cobertura['nombreCliente']}</strong>,</p>
                    <p style="font-size: 16px;">Su cobertura ha sido activada exitosamente por 1 año con los siguientes detalles:</p>
                    <ul style="font-size: 16px; padding-left: 20px;">
                    <li><strong>IMEI:</strong> {datos_cobertura['imei']}</li>
                    <li><strong>Fecha de compra:</strong> {datos_cobertura['fecha'].strftime('%d/%m/%Y')}</li>
                    <li><strong>Valor:</strong> ${datos_cobertura['valor']}</li>
                    <li><strong>Vigencia hasta:</strong> {fecha_fin}</li>
                    </ul>
                    <p style="font-size: 16px;">Gracias por confiar en nosotros.</p>
                    <p style="font-size: 16px;">Atentamente,<br><strong>Equipo Micelu.co</strong></p>
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

class PolicyIntegrationService:
    """
    Servicio de integración para generar pólizas en API externa
    
    """
    
    # Configuración de la API - Producción
    API_CONFIG_PROD = {
        'AUTH_URL': 'https://ms.proteccionmovil.co/api/v1/auth/token',
        'CLIENT_ID': 'Q7bMfHwO6f2l4uWGV5B9',
        'CLIENT_SECRET': '6jfbwulaBbQ165xmblQxmgQZHsbyM1hoSjpjzA4m',
        'BASE_URL': 'https://ms.proteccionmovil.co/api/v1'
    }

    # Configuración de la API - Pruebas (QA)
    API_CONFIG_QA = {
        'AUTH_URL': 'https://qamicroservice.proteccionmovil.co/api/v1/auth/token',
        'CLIENT_ID': 'mS8DJ3GFOBW3d8AIZsSy',
        'CLIENT_SECRET': 'Y2stnRwVvPWJhJvt4KRA0Js1LWtnijp4ls6s05Qz',
        'BASE_URL': 'https://qamicroservice.proteccionmovil.co/api/v1'
    }
    # Configuración de planes específicos
    PLANES_ESPECIFICOS = {
        'qa': {
            'ASISTENCIA_FRACTURA_PANTALLA': {
                'plan_id': 107,
                'price_id': 324,
                'nombre': 'Plan Asistencia Fractura de pantalla'
            }
        },
        'prod': {
            'ASISTENCIA_FRACTURA_PANTALLA': {
                'plan_id': 70,
                'price_id': 199,
                'nombre': 'Plan Asistencia Fractura de pantalla'
            }
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_config(self, environment='prod'):
        """Obtiene la configuración según el ambiente -"""
        
        return self.API_CONFIG_PROD if environment == 'prod' else self.API_CONFIG_QA
    
    def get_auth_token(self, environment='prod'):
        """
        Obtiene token de autenticación según el ambiente
        Returns: (token, token_type)
        """
        try:
            config = self.get_config(environment)
            url = config['AUTH_URL']
            params = {
                'clientId': config['CLIENT_ID'],
                'clientSecret': config['CLIENT_SECRET']
            }
            
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Error al obtener token: {response.status_code} - {response.text}")
                return None, None
            
            response_data = response.json()
            
            if 'data' not in response_data:
                
                return None, None
            
            token = response_data['data']['token']
            token_type = response_data['data']['type']
            
            
            return token, token_type
            
        except requests.exceptions.RequestException as e:
            
            return None, None
        except Exception as e:
            self.logger.error(f"Error inesperado al obtener token: {str(e)}")
            return None, None
    
    def list_policy_options(self, imei, token, token_type, sponsor_id="MICELU", environment='prod'):
        """
        Lista opciones de póliza según el ambiente
        Returns: (plan_id, price_option_id)
        """
        try:
            config = self.get_config(environment)
            url = f"{config['BASE_URL']}/policy/imei/{imei}?sponsorId={sponsor_id}"
            headers = {
                'Authorization': f'{token_type} {token}'
            }
            
            self.logger.debug(f"Consultando opciones de póliza para IMEI: {imei}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Error al consultar póliza: {response.status_code} - {response.text}")
                return None, None
            
            response_data = response.json()
            
            if 'error' in response_data:
                self.logger.error(f"Error en respuesta de póliza: {response_data['error']}")
                return None, None
            
            if 'data' not in response_data or 'policies' not in response_data['data']:
                self.logger.error(f"Estructura de respuesta inesperada: {response_data}")
                return None, None
            
            policies = response_data['data']['policies']
            if not policies or not policies[0].get('pricingOptions'):
                self.logger.error("No se encontraron pólizas o opciones de precio")
                return None, None
            
            plan_id = policies[0]['id']
            price_option_id = policies[0]['pricingOptions'][0]['id']
            
            self.logger.debug(f"Opciones obtenidas - Plan ID: {plan_id}, Price Option ID: {price_option_id}")
            return plan_id, price_option_id
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de conexión al consultar póliza: {str(e)}")
            return None, None
        except Exception as e:
            self.logger.error(f"Error inesperado al consultar póliza: {str(e)}")
            return None, None
    
    def get_specific_plan_ids(self, environment='prod', plan_type='ASISTENCIA_FRACTURA_PANTALLA'):
        """
        Obtiene los IDs específicos del plan solicitado según el ambiente
        Returns: (plan_id, price_option_id) para el plan específico
        """
        if environment in self.PLANES_ESPECIFICOS and plan_type in self.PLANES_ESPECIFICOS[environment]:
            plan_config = self.PLANES_ESPECIFICOS[environment][plan_type]
            plan_id = plan_config['plan_id']
            price_id = plan_config['price_id']
            
    
            return plan_id, price_id
        else:
            self.logger.warning(f"Plan específico '{plan_type}' no encontrado para ambiente '{environment}', usando método estándar")
            return None, None
    
    def pre_generate_policy(self, payload, token, token_type, environment='prod'):
        """Pregenera póliza según el ambiente"""
        try:
            config = self.get_config(environment)
            url = f"{config['BASE_URL']}/policy/pregeneration"
            headers = {
                'Authorization': f'{token_type} {token}',
                'Content-Type': 'application/json'
            }
            
            #self.logger.debug(f"Pregenerando póliza para IMEI: {payload.get('device', {}).get('imei', 'N/A')}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                #self.logger.error(f"Error en pregeneración: {response.status_code} - {response.text}")
                return None
            
            response_data = response.json()
            #self.logger.debug(f"Pregeneración completada: {response_data}")
            return response_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de conexión en pregeneración: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error inesperado en pregeneración: {str(e)}")
            return None
    
    def generate_policy(self, payload, token, token_type, environment='prod'):
        """Genera póliza según el ambiente"""
        try:
            config = self.get_config(environment)
            url = f"{config['BASE_URL']}/policy"
            headers = {
                'Authorization': f'{token_type} {token}',
                'Content-Type': 'application/json'
            }

            self.logger.debug(f"Generando póliza final para IMEI: {payload.get('device', {}).get('imei', 'N/A')}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Error en generación final: {response.status_code} - {response.text}")
                return None
            
            response_data = response.json()
            self.logger.debug(f"Generación final completada: {response_data}")
            return response_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de conexión en generación final: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error inesperado en generación final: {str(e)}")
            return None
    
    def procesar_cobertura_completa(self, datos_cobertura, environment='prod', usar_plan_especifico=True, tipo_plan='ASISTENCIA_FRACTURA_PANTALLA'):
        """
        Procesa la cobertura completa: busca datos, genera póliza
        
        Parámetros:
        - datos_cobertura: datos del cliente y dispositivo
        - environment: ambiente (qa/prod)
        - usar_plan_especifico: si True, usa los IDs específicos configurados
        - tipo_plan: tipo de plan específico a usar
        """
        try:
            imei = datos_cobertura.get('imei', '').strip()
            if not imei:
                return False, "IMEI no proporcionado", None

            # 1. Buscar información del cliente en la base de datos
            self.logger.info(f"Procesando cobertura para IMEI: {imei} en ambiente: {environment}")
            
            db_results = buscar_por_imei(imei)
            if not db_results:
                return False, "No se encontró información del IMEI en la base de datos", None

            client_info = db_results[0] if isinstance(db_results, list) else db_results
            
            # 2. Obtener token de autenticación
            token, token_type = self.get_auth_token(environment)
            if not token:
                return False, "No se pudo obtener token de autenticación", None

            # 3. Obtener opciones de póliza (método específico o estándar)
            plan_id = None
            price_option_id = None
            
            if usar_plan_especifico:
                # Usar plan específico configurado
                plan_id, price_option_id = self.get_specific_plan_ids(environment, tipo_plan)
                #self.logger.info(f"Usando plan específico: {tipo_plan} - Plan ID: {plan_id}, Price ID: {price_option_id}")
            
            # Si no se pudo obtener el plan específico, usar método estándar como fallback
            if not plan_id or not price_option_id:
                #self.logger.info("Usando método estándar para obtener plan (fallback)")
                plan_id, price_option_id = self.list_policy_options(imei, token, token_type, environment=environment)
                
            if not plan_id or not price_option_id:
                return False, "No se pudieron obtener opciones de póliza para este IMEI", None

            # Primero intentar obtener el nombre de los datos pasados directamente
            nombre_completo = str(datos_cobertura.get('nombre_cliente', '')).strip()
            
            # Si no está en datos_cobertura, buscar en client_info de la BD
            if not nombre_completo:
                nombre_completo = str(client_info.get('nombre_cliente', client_info.get('Nombre_Cliente', ''))).strip()
            
            # Si aún no tenemos nombre, intentar construirlo de otras fuentes
            if not nombre_completo:
                # Intentar otras posibles claves
                nombre_completo = str(client_info.get('nombre', client_info.get('Nombre', ''))).strip()
            
            # Validación final del nombre
            if not nombre_completo:
                return False, "No se pudo obtener el nombre del cliente", None
            
            # Separar nombre y apellido
            if ' ' in nombre_completo:
                partes_nombre = nombre_completo.split(' ')
                first_name = partes_nombre[0]
                last_name = ' '.join(partes_nombre[1:])
            else:
                first_name = nombre_completo
                last_name = ''
            
            # Validación adicional
            if not first_name.strip():
                return False, "El nombre del cliente no puede estar vacío", None
            telefono = str(datos_cobertura.get('telefono', 'POR_ACTUALIZAR')).strip()

            # 5. Construir payload con validaciones adicionales
            correo = str(datos_cobertura.get('correo', client_info.get('correo', client_info.get('Correo', '')))).strip()
            nit = str(datos_cobertura.get('nit', client_info.get('nit', client_info.get('NIT', '')))).strip()
            valor = float(datos_cobertura.get('valor', client_info.get('valor', client_info.get('Valor', 0))))
            
            payload = {
                "sponsorId": "MICELU",
                "planId": plan_id,
                "priceOptionId": price_option_id,
                "insuredValue": valor,
                "device": {
                    "imei": imei,
                    "line": telefono,
                    "referenceTac": imei[:8]
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
            
            # Log para debugging - INCLUIR INFO DEL PLAN
            plan_info = ""
            if usar_plan_especifico and tipo_plan in self.PLANES_ESPECIFICOS:
                plan_info = f", plan específico: {self.PLANES_ESPECIFICOS[tipo_plan]['nombre']}"
            
            self.logger.debug(f"Payload construido: nombre_completo='{nombre_completo}', firstName='{first_name}', lastName='{last_name}', planId={plan_id}, priceOptionId={price_option_id}{plan_info}")
            
            # 6. Pregeneración
            pre_response = self.pre_generate_policy(payload, token, token_type, environment)
            if not pre_response:
                return False, "Error en la pregeneración de póliza", None

            if not (pre_response.get('data', {}).get('message') == 'Pregeneración exitosa'):
                error_msg = pre_response.get('error', {}).get('message', 'Error desconocido en pregeneración')
                return False, f"Pregeneración falló: {error_msg}", pre_response

            # 7. Generación final (solo en producción)
            final_response = None
            if environment == 'prod':
                final_response = self.generate_policy(payload, token, token_type, environment)
                if not final_response:
                    return False, "Error en la generación final de póliza", pre_response

            self.logger.info(f"Póliza procesada exitosamente para IMEI: {imei}{plan_info}")
            
            return True, None, {
                'pre_generation': pre_response,
                'final_generation': final_response,
                'environment': environment,
                'payload_used': payload,
                'plan_info': {
                    'plan_id': plan_id,
                    'price_option_id': price_option_id,
                    'tipo_plan': tipo_plan if usar_plan_especifico else 'estandar',
                    'nombre_plan': self.PLANES_ESPECIFICOS[tipo_plan]['nombre'] if usar_plan_especifico and tipo_plan in self.PLANES_ESPECIFICOS else 'Plan estándar'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error inesperado en procesamiento completo: {str(e)}")
            return False, f"Error inesperado: {str(e)}", None

@app.route("/cobertura", methods=['GET', 'POST'])
@login_required
def cobertura():
    documento = session.get('user_documento')
    usuario = Usuario.query.filter_by(documento=documento).first()

    # Usar sistema híbrido para calcular puntos
    total_puntos = calcular_puntos_con_fallback(documento)

    if request.method == 'GET':
        return render_template(
            "cobertura.html",
            usuario=usuario,
            total_puntos=total_puntos
        )

    try:
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

        if accion == 'buscar':
            print(f"🔍 DEBUG cobertura: Buscando cobertura para IMEI: {imei}, Usuario: {documento}")
            app.logger.debug(f"Buscando cobertura para IMEI: {imei}, Usuario: {documento}")
            datos_cobertura = buscar_por_imei(imei)
            print(f"🔍 DEBUG cobertura: Resultado buscar_por_imei: {datos_cobertura}")

            if not datos_cobertura:
                print(f"❌ DEBUG cobertura: No se encontró información para el IMEI: {imei}")
                return jsonify({
                    'exito': False,
                    'mensaje': 'No se encontró información para el IMEI ingresado',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 404

            nit_cobertura = str(datos_cobertura.get('nit', '')).split('-')[0].strip()
            documento_sesion = str(documento).strip()
            print(f"🔍 DEBUG cobertura: NIT cobertura: {nit_cobertura}, Documento sesión: {documento_sesion}")

            imei_limpio = datos_cobertura.get('imei', imei)[:15]
            cobertura_existente = cobertura_clientes.query.filter_by(imei=imei_limpio).first()

            if cobertura_existente:
                print(f"❌ DEBUG cobertura: Ya existe cobertura para IMEI: {imei_limpio}")
                return jsonify({
                    'exito': False,
                    'mensaje': 'Ya existe una cobertura activa para este IMEI',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400

            es_recompra = imei.endswith('A')
            print(f"🔍 DEBUG cobertura: Es recompra: {es_recompra}")

            if nit_cobertura != documento_sesion and not es_recompra:
                print(f"❌ DEBUG cobertura: Sin permisos. NIT: {nit_cobertura} != Documento: {documento_sesion}")
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para acceder a la información de este IMEI.',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 403

            datos_cobertura['es_recompra'] = es_recompra
            print(f"✅ DEBUG cobertura: Datos encontrados correctamente: {datos_cobertura}")

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

            nit_limpio = str(nit).replace('-', '').strip()
            if nit_limpio != str(documento):
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para activar la cobertura con este documento',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 403

            datos_cobertura = buscar_por_imei(imei)
            if not datos_cobertura:
                return jsonify({
                    'exito': False,
                    'mensaje': 'No se encontró información para el IMEI ingresado',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 404

            nit_cobertura = str(datos_cobertura.get('nit', '')).split('-')[0].strip()
            es_recompra = imei.endswith('A')

            if nit_cobertura != nit_limpio and not es_recompra:
                return jsonify({
                    'exito': False,
                    'mensaje': 'No tiene permisos para activar la cobertura de este IMEI.',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 403

            correo = datos.get('datos', {}).get('correo', '').strip()
            if not correo:
                return jsonify({
                    'exito': False,
                    'mensaje': 'El correo electrónico es obligatorio para activar la cobertura',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400

            imei_limpio = datos_cobertura.get('imei', imei)[:15]

            # Verificar cobertura existente antes de procesar
            cobertura_existente = cobertura_clientes.query.filter_by(imei=imei_limpio).first()
            if cobertura_existente:
                return jsonify({
                    'exito': False,
                    'mensaje': 'Ya existe una cobertura activa para este IMEI',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 400

            # Preparar datos para guardar
            datos_guardar = {
                'documento': nit_limpio,
                'imei': imei_limpio,
                'nombreCliente': datos.get('datos', {}).get('nombre', '').strip(),
                'correo': correo,
                'fecha': datetime.strptime(datos.get('fecha'), '%Y-%m-%d'),
                'valor': float(datos.get('valor', 0)),
                'referencia': datos.get('referencia', '').strip(),
                'telefono': datos.get('telefono', '').strip(),
                'fecha_activacion': datetime.now()
            }

            # Variables para tracking del proceso
            exito_api = False
            error_api = None
            respuesta_api = None
            environment = app.config.get('POLICY_ENVIRONMENT', 'prod')

            # Procesar API externa con manejo de errores mejorado
            try:
                app.logger.info(f"Iniciando procesamiento de API externa para IMEI: {imei_limpio}")
                
                policy_service = PolicyIntegrationService()
                datos_para_api = {
                    'imei': imei_limpio,
                    'nombre_cliente': datos.get('datos', {}).get('nombre', '').strip() or datos_cobertura.get('Nombre_Cliente', ''),
                    'correo': correo,
                    'nit': nit_limpio,
                    'valor': float(datos.get('valor', 0)),
                    'telefono': datos.get('telefono', '').strip()
                }

                exito_api, error_api, respuesta_api = policy_service.procesar_cobertura_completa(
                    datos_para_api, 
                    environment,
                    usar_plan_especifico=True,  # Usar plan específico
                    tipo_plan='ASISTENCIA_FRACTURA_PANTALLA'  # Plan específico configurado
                )
                
                app.logger.info(f"Proceso de API externa completado - Éxito: {exito_api}, Error: {error_api}")
                
            except Exception as e:
                app.logger.error(f"Error crítico en API externa: {str(e)}")
                exito_api = False
                error_api = f"Error crítico: {str(e)}"

            # Guardar en base de datos local (independientemente del resultado de la API)
            try:
                app.logger.info(f"Guardando cobertura en base de datos local para IMEI: {imei_limpio}")
                
                nueva_cobertura = cobertura_clientes(**datos_guardar)
                db.session.add(nueva_cobertura)
                db.session.commit()
                
                app.logger.info(f"Cobertura guardada exitosamente en base de datos local")
                
            except Exception as e:
                app.logger.error(f"Error crítico al guardar en base de datos: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'exito': False,
                    'mensaje': f'Error al guardar la cobertura: {str(e)}',
                    'usuario': usuario.nombre if usuario else None,
                    'total_puntos': total_puntos
                }), 500

            # Enviar email de confirmación (de forma asíncrona para no bloquear la respuesta)
            try:
                fecha_fin = (datos_guardar['fecha'] + timedelta(days=365)).strftime('%d/%m/%Y')
                exito_email, error_email = cobertura_email_service.enviar_confirmacion_cobertura(
                    datos_guardar, fecha_fin
                )
                
                if not exito_email:
                    app.logger.warning(f"Error al enviar correo de confirmación: {error_email}")
                else:
                    app.logger.info(f"Correo de confirmación enviado exitosamente")
                    
            except Exception as e:
                app.logger.warning(f"Error no crítico al enviar email: {str(e)}")

            # Preparar mensaje de respuesta
            mensaje_base = 'La cobertura ha sido activada exitosamente por 1 año'
            if not exito_api:
                mensaje_base += ' (Nota: Procesamiento externo pendiente - se reintentará automáticamente)'

            # Respuesta final
            respuesta_final = {
                'exito': True,
                'mensaje': mensaje_base,
                'usuario': usuario.nombre if usuario else None,
                'total_puntos': total_puntos,
                'api_externa': {
                    'procesada': exito_api,
                    'error': error_api if not exito_api else None,
                    'ambiente': environment
                }
            }

            app.logger.info(f"Proceso completo finalizado para IMEI: {imei_limpio} - Enviando respuesta al cliente")
            return jsonify(respuesta_final)

        else:
            return jsonify({
                'exito': False,
                'mensaje': 'Acción no reconocida',
                'usuario': usuario.nombre if usuario else None,
                'total_puntos': total_puntos
            }), 400

    except Exception as e:
        app.logger.exception(f"Error crítico en el procesamiento de cobertura: {str(e)}")
        # Asegurar rollback en caso de error
        try:
            db.session.rollback()
        except:
            pass
            
        return jsonify({
            'exito': False,
            'mensaje': 'Ocurrió un error interno al procesar la cobertura',
            'usuario': usuario.nombre if usuario else None,
            'total_puntos': total_puntos,
            'error_detalle': str(e) if app.debug else None
        }), 500
@app.route("/buscar_usuario_reclamacion", methods=['POST'])
@login_required
def buscar_usuario_reclamacion():
    try:
        datos = request.json
        documento = datos.get('documento', '').strip()
        
        if not documento:
            return jsonify({
                'exito': False,
                'mensaje': 'El documento es obligatorio'
            }), 400
        
        # Buscar en la tabla cobertura_clientes
        cobertura = cobertura_clientes.query.filter_by(documento=documento).first()
        
        if not cobertura:
            return jsonify({
                'exito': False,
                'mensaje': 'No se encontró una cobertura activa con este documento'
            }), 404
        
        # Retornar los datos de la cobertura
        return jsonify({
            'exito': True,
            'datos': {
                'documento': cobertura.documento,
                'nombre': cobertura.nombreCliente,
                'email': cobertura.correo,
                'telefono': cobertura.telefono,
                'imei': cobertura.imei,
                'referencia': cobertura.referencia,
                'fecha_activacion': cobertura.fecha_activacion.strftime('%Y-%m-%d') if cobertura.fecha_activacion else None
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error al buscar usuario para reclamación: {str(e)}")
        return jsonify({
            'exito': False,
            'mensaje': 'Error al buscar la información de la cobertura'
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
    
    # Consulta SQL Server
    query_sql_server = """
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
        CASE 
            WHEN c.TEL1 IS NOT NULL AND c.TEL1 != '' THEN c.TEL1 
            ELSE c.TEL2 
        END AS Telefono,
        c.Nombre
    FROM 
        VSeriesUtilidad v WITH (NOLOCK)
    JOIN
        MTMercia m ON v.Producto = m.CODIGO
    JOIN
        MTPROCLI c ON v.nit = c.NIT
    WHERE 
        v.Tipo_Documento IN ('FB', 'FM', 'FC')
        AND v.Valor > 0
        AND v.Fecha_Inicial BETWEEN ? AND ?
        AND m.CODLINEA = 'CEL'
        AND m.CODGRUPO = 'SEMI'
        AND v.NIT NOT IN ('1152718000', '1053817613', '1000644140', '01')
        AND (c.EMAIL IS NULL OR c.EMAIL NOT LIKE '%@exito.com')  -- Excluye todos los correos de exito.com  
    ORDER BY 
        v.Fecha_Inicial DESC
    """
    
    # Consulta PostgreSQL
    query_postgres = """
    SELECT 
        v.tipo_documento AS Tipo_Documento,
        v.documento AS Documento,
        v.tipo_documento || v.documento AS Factura,
        LEFT(v.serie, 15) AS IMEI,
        v.referencia AS Producto,
        CAST(v.valor AS DECIMAL(15,2)) AS Valor,
        CASE 
            WHEN v.fecha_inicial ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN v.fecha_inicial::DATE
            ELSE '2025-01-01'::DATE
        END AS Fecha_Compra,
        v.nit AS NIT,
        'SEMI' AS codgrupo,
        COALESCE(c.email, '') AS Correo,
        COALESCE(c.tel1, c.tel2, '') AS Telefono,
        COALESCE(c.nombre, '') AS Nombre
    FROM 
        micelu_backup.vseries_utilidad v
    LEFT JOIN
        micelu_backup.clientes c ON v.nit = c.nit
    WHERE 
        v.tipo_documento IN ('FB', 'FM', 'FC')
        AND CAST(v.valor AS DECIMAL(15,2)) > 0
        AND CASE 
            WHEN v.fecha_inicial ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN v.fecha_inicial::DATE
            ELSE '2025-01-01'::DATE
        END BETWEEN %s AND %s
        AND v.nit NOT IN ('1152718000', '1053817613', '1000644140', '01')
        AND (c.email IS NULL OR c.email NOT LIKE '%@exito.com')
    ORDER BY 
        CASE 
            WHEN v.fecha_inicial ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' THEN v.fecha_inicial::DATE
            ELSE '2025-01-01'::DATE
        END DESC
    """
    
    try:
        # Ejecutar consulta con fallback
        resultados, fuente = ejecutar_consulta_con_fallback(
            query_sql_server, 
            query_postgres, 
            ((fecha_inicio, fecha_fin), (fecha_inicio, fecha_fin)),
            tipo_consulta='cobertura'
        )
        
        datos_consulta = []
        for row in resultados:
            datos_consulta.append({
                'tipo_documento': row.Tipo_Documento if hasattr(row, 'Tipo_Documento') else row[0],
                'documento': row.Documento if hasattr(row, 'Documento') else row[1],
                'factura': row.Factura if hasattr(row, 'Factura') else row[2],
                'imei': row.IMEI if hasattr(row, 'IMEI') else row[3],
                'producto': row.Producto if hasattr(row, 'Producto') else row[4],
                'valor': float(row.Valor if hasattr(row, 'Valor') else row[5]),
                'fecha_compra': row.Fecha_Compra.strftime('%Y-%m-%d') if hasattr(row, 'Fecha_Compra') and row.Fecha_Compra else (row[6].strftime('%Y-%m-%d') if row[6] else None),
                'nit': row.NIT if hasattr(row, 'NIT') else row[7],
                'codgrupo': row.codgrupo if hasattr(row, 'codgrupo') else row[8],
                'correo': row.Correo if hasattr(row, 'Correo') else (row[9] if len(row) > 9 else ""),
                'telefono': row.Telefono if hasattr(row, 'Telefono') else (row[10] if len(row) > 10 else ""),
                'nombre': row.Nombre if hasattr(row, 'Nombre') else (row[11] if len(row) > 11 else "")
            })
        
        #logger.info(f"Se encontraron {len(datos_consulta)} registros desde {fuente}")
        return datos_consulta
        
    except Exception as e:
        #logger.error(f"Error en obtener_datos_consulta: {str(e)}")
        return []

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
bogota_tz = pytz.timezone('America/Bogota')
scheduler = BackgroundScheduler(timezone=bogota_tz)

def exportar_coberturas_automaticamente():
    with app.app_context():
        print("[EXPORTAR] Iniciando exportación automática a SharePoint")
        try:
            hoy = datetime.now()
            # Calcular el lunes y domingo de la semana anterior
            lunes_anterior = hoy - timedelta(days=hoy.weekday() + 7)
            domingo_anterior = lunes_anterior + timedelta(days=6)
            fecha_inicio = lunes_anterior.strftime('%Y-%m-%d')
            fecha_fin = domingo_anterior.strftime('%Y-%m-%d')
            print(f"[EXPORTAR] Consultando datos desde {fecha_inicio} hasta {fecha_fin}")

            resultados_consulta = obtener_datos_consulta(fecha_inicio, fecha_fin)
            if not resultados_consulta:
                print("No se encontraron datos para el rango de fechas especificado.")
                return

            coberturas_inactivas, _ = filtrar_coberturas_inactivas(resultados_consulta)
            if not coberturas_inactivas:
                print("No se encontraron coberturas inactivas.")
                return

            coberturas_db = obtener_coberturas_inactivas()
            print(f"[EXPORTAR] Exportando {len(coberturas_db)} coberturas a SharePoint...")
            exportar_a_excel_sharepoint(coberturas_db)
            print("[EXPORTAR] Exportación a SharePoint finalizada.")

        except Exception as e:
            import traceback
            print("[EXPORTAR] Error en exportación automática:", traceback.format_exc())

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
                print("No hay resultados de consulta")
                return
            
            # (Esta función ya verifica si el registro existe antes de crearlo)
            coberturas_inactivas, _ = filtrar_coberturas_inactivas(resultados_consulta)
            
            if not coberturas_inactivas:
                return
            print(f"Actualización diaria completada: {datetime.now(bogota_tz)}")
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
            fecha_fin = hoy.replace(hour=23, minute=49, second=59)
            
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
                "endpoint=https://email-sender-miceluaz.unitedstates.communication.azure.com/;accesskey=BQXdsHbbOrCCgNlhAjruR1TEKGQMImCDnrz0InjuvKnRw4vfUqulJQQJ99BJACULyCp6Z5KHAAAAAZCS35sJ"
            )
            sender_address = "DoNotReply@micelu.co"
            
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
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            # Preparar mensaje con archivo adjunto
            mensaje = {
                "senderAddress": sender_address,
                "recipients": {
                    "to": [{"address": email} for email in destinatarios]
                },
                "content": {
                    "subject": asunto,
                    "html": contenido_html
                },
                "attachments": [
                    {
                        "name": f"Coberturas_Activadas_{fecha_inicio.strftime('%Y%m%d')}_al_{fecha_fin.strftime('%Y%m%d')}.xlsx",
                        "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "contentInBase64": encoded_content
                    }
                ]
            }
            
            # Enviar correo
            poller = email_client.begin_send(mensaje)
            result = poller.result()
            
        except Exception as e:
            
            import traceback
            #logger.error(traceback.format_exc())

# Definir zona horaria de Bogotá
# Función para programar el procesamiento automático de coberturas inactivas

def procesar_coberturas_inactivas_programado():
    """
    Función que se ejecuta automáticamente por el planificador
    """
    with app.app_context():
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
            import traceback
            error_msg = traceback.format_exc()
            app.logger.error(f"Error en procesamiento programado: {str(e)}")
            print(f"Error en procesar_coberturas_inactivas_programado: {error_msg}")
# eliminar coberturas con más de 30 dias en la db
def limpiar_coberturas_inactivas_antiguas():
    """
    Elimina coberturas inactivas que tengan más de 30 días desde la fecha_compra
    """
    with app.app_context():  # Crear contexto de aplicación
        try:
            # Calcular fecha límite (30 días atrás)
            fecha_limite = datetime.now().date() - timedelta(days=30)
            
            print(f"[LIMPIEZA COBERTURAS] Iniciando limpieza de coberturas inactivas anteriores a: {fecha_limite}")
        
            
            # Contar registros usando el ORM de SQLAlchemy
            total_registros = cobertura_inactiva.query.filter(
                cobertura_inactiva.fecha_compra < fecha_limite
            ).count()
            
            print(f"[LIMPIEZA COBERTURAS] Registros encontrados para eliminar: {total_registros}")
            
            if total_registros == 0:
                print("[LIMPIEZA COBERTURAS] No hay coberturas inactivas antiguas para eliminar")
                
                return {"success": True, "eliminados": 0, "mensaje": "No hay registros para eliminar"}
            
            # Eliminar registros usando el ORM
            registros_eliminados = cobertura_inactiva.query.filter(
                cobertura_inactiva.fecha_compra < fecha_limite
            ).delete()
            
            db.session.commit()
            
            logging.info(f"Se eliminaron {registros_eliminados} coberturas inactivas con más de 30 días")
            
            return {
                "success": True, 
                "eliminados": registros_eliminados,
                "fecha_limite": str(fecha_limite),
                "mensaje": f"Eliminación exitosa de {registros_eliminados} registros"
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error al limpiar coberturas inactivas: {str(e)}"
            print(f"[LIMPIEZA COBERTURAS] ❌ ERROR: {error_msg}")
            logging.error(error_msg)
            return {"success": False, "error": error_msg}



def configurar_tareas_programadas():
    """
    Configura todas las tareas programadas del sistema
    """
    try:
        # Crear scheduler con zona horaria
        
        # 1. Exportación de coberturas inactivas cada domingo a las 23:59
        scheduler.add_job(
            exportar_coberturas_automaticamente, 'cron',
            day_of_week='0',  # 0 = lunes
            hour='8', minute='15',  
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
            day_of_week='6', hour='21', minute='04',
            timezone=bogota_tz,
            id='reporte_coberturas_activadas',
            replace_existing=True
        )
        
        # 4. Procesamiento diario de coberturas inactivas a las 8:10 AM
        scheduler.add_job(
            procesar_coberturas_inactivas_programado, 'cron',
            hour='13', minute='14',
            timezone=bogota_tz,
            id='procesar_coberturas_inactivas',
            replace_existing=True
        )
        # 5. NUEVO: Limpieza diaria de coberturas inactivas antiguas a las 22:00
        
        scheduler.add_job(
            limpiar_coberturas_inactivas_antiguas, 'cron',
            hour='8', minute='50',
            timezone=bogota_tz,
            id='limpiar_coberturas_antiguas',
            replace_existing=True
        )
        
    except Exception as e:
        app.logger.error(f"Error al configurar tareas programadas: {str(e)}")
try:
    # Configurar tareas
    configurar_tareas_programadas()
    
    # Iniciar el programador
    if not scheduler.running:
        scheduler.start()
        print(f"SCHEDULER INICIADO: {datetime.now(bogota_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("El scheduler ya está en ejecución")
        
except Exception as e:
    import traceback
    error_msg = traceback.format_exc()
    print(f"Error al iniciar el scheduler: {error_msg}")

# Clase para el servicio de correo para coberturas inactivas
class CoberturaInactivaEmailService:
    def __init__(self):
        # Configuración de conexión de Azure Communication Services
        self.connection_string = "endpoint=https://email-sender-miceluaz.unitedstates.communication.azure.com/;accesskey=BQXdsHbbOrCCgNlhAjruR1TEKGQMImCDnrz0InjuvKnRw4vfUqulJQQJ99BJACULyCp6Z5KHAAAAAZCS35sJ"
        self.sender_address = "DoNotReply@micelu.co"

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
            url_imagen = "https://i.postimg.cc/SRpM1Jcc/coberturaina.jpg"
            url_activacion = "https://club-puntos-micelu.azurewebsites.net/"  # URL donde el cliente puede activar la cobertura
            url_servicio_cliente = "https://i.postimg.cc/65JHbxrL/serviciocliente.jpg"
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
                    <a href="{url_activacion}" style="background-color: #2196F3; color: white; padding: 12px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">ACTIVAR MI COBERTURA</a>
                </div>
                <p><strong>Para activar tu cobertura solo necesitas:</p>
                <ul>
                    <li>Tu número de documento</li>
                    <li>El IMEI de tu dispositivo</li>
                    <li>Un correo electrónico activo</li>
                    <li>Registrarse en club puntos </li>
                </ul>
                <div style="text-align: center; margin: 25px 0;">
                    <img src="{url_servicio_cliente}" alt="Servicio al Cliente Micelu" style="max-width: 100%; height: auto; display: block; margin: 0 auto;">
                </div>
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


# ============================================================================
# RUTAS DE UTILIDAD PARA EL NUEVO SISTEMA DE PUNTOS
# ============================================================================

@app.route('/api/test_puntos')
@login_required
def test_puntos():
    """Ruta de prueba para comparar sistema viejo vs nuevo"""
    documento = session.get('user_documento')
    
    puntos_viejo = calcular_puntos_sistema_viejo(documento)
    migrado = cliente_esta_migrado(documento)
    puntos_nuevo = calcular_puntos_nuevo_sistema(documento) if migrado else "No migrado"
    
    return jsonify({
        'documento': documento,
        'migrado': migrado,
        'puntos_sistema_viejo': puntos_viejo,
        'puntos_sistema_nuevo': puntos_nuevo,
        'diferencia': puntos_nuevo - puntos_viejo if migrado else 'N/A'
    })

@app.route('/api/migrar_mi_cuenta')
@login_required
def migrar_mi_cuenta():
    """Permite al usuario migrar su propia cuenta manualmente"""
    documento = session.get('user_documento')
    
    if cliente_esta_migrado(documento):
        return jsonify({
            'success': True,
            'mensaje': 'Tu cuenta ya está migrada al nuevo sistema',
            'puntos_disponibles': calcular_puntos_nuevo_sistema(documento)
        })
    
    try:
        migrar_cliente_individual(documento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Tu cuenta ha sido migrada exitosamente',
            'puntos_disponibles': calcular_puntos_nuevo_sistema(documento)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/historial_transacciones')
@login_required
def ver_historial_transacciones():
    """Ver historial completo de transacciones de puntos"""
    documento = session.get('user_documento')
    
    if not cliente_esta_migrado(documento):
        return jsonify({
            'success': False,
            'mensaje': 'Tu cuenta aún no está migrada al nuevo sistema'
        }), 400
    
    try:
        transacciones = Transacciones_Puntos.query.filter_by(
            documento=documento
        ).order_by(
            Transacciones_Puntos.fecha_transaccion.desc()
        ).limit(100).all()
        
        resultado = []
        for t in transacciones:
            resultado.append({
                'id': t.id,
                'tipo': t.tipo_transaccion,
                'puntos': t.puntos,
                'saldo_antes': t.puntos_disponibles_antes,
                'saldo_despues': t.puntos_disponibles_despues,
                'fecha': t.fecha_transaccion.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_vencimiento': t.fecha_vencimiento.strftime('%Y-%m-%d') if t.fecha_vencimiento else None,
                'descripcion': t.descripcion,
                'estado': t.estado
            })
        
        return jsonify({
            'success': True,
            'transacciones': resultado,
            'total': len(resultado)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/info_puntos')
@login_required
def info_puntos():
    """Información detallada de puntos del usuario"""
    documento = session.get('user_documento')
    
    try:
        puntos_disponibles = calcular_puntos_con_fallback(documento)
        migrado = cliente_esta_migrado(documento)
        
        info = {
            'documento': documento,
            'puntos_disponibles': puntos_disponibles,
            'migrado': migrado,
            'sistema': 'nuevo' if migrado else 'viejo'
        }
        
        if migrado:
            # Calcular puntos por vencer usando ORM
            hoy = datetime.now()
            fecha_30_dias = hoy + timedelta(days=30)
            
            puntos_por_vencer = db.session.query(
                db.func.coalesce(db.func.sum(Transacciones_Puntos.puntos), 0)
            ).filter(
                Transacciones_Puntos.documento == documento,
                Transacciones_Puntos.estado == 'ACTIVO',
                Transacciones_Puntos.fecha_vencimiento.between(hoy, fecha_30_dias)
            ).scalar()
            
            info['puntos_por_vencer_30dias'] = int(puntos_por_vencer or 0)
        
        return jsonify(info)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# RUTA DE DEBUG PARA VERIFICAR PUNTOS
# ============================================================================
@app.route('/debug/puntos')
@login_required
def debug_puntos():
    """Debug para ver exactamente qué está pasando con los puntos"""
    documento = session.get('user_documento')
    
    try:
        # Verificar si está migrado
        migrado = cliente_esta_migrado(documento)
        
        # Calcular con sistema viejo
        puntos_viejo = calcular_puntos_sistema_viejo(documento)
        
        # Calcular con sistema nuevo (si está migrado)
        if migrado:
            puntos_nuevo = calcular_puntos_nuevo_sistema(documento)
        else:
            puntos_nuevo = "No migrado"
        
        # Calcular con fallback
        puntos_fallback = calcular_puntos_con_fallback(documento)
        
        # Ver transacciones
        transacciones = []
        if migrado:
            trans = Transacciones_Puntos.query.filter_by(documento=documento).all()
            for t in trans:
                transacciones.append({
                    'tipo': t.tipo_transaccion,
                    'puntos': t.puntos,
                    'estado': t.estado,
                    'fecha': t.fecha_transaccion.strftime('%Y-%m-%d'),
                    'descripcion': t.descripcion
                })
        
        return jsonify({
            'documento': documento,
            'migrado': migrado,
            'puntos_sistema_viejo': puntos_viejo,
            'puntos_sistema_nuevo': puntos_nuevo,
            'puntos_con_fallback': puntos_fallback,
            'transacciones': transacciones
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ============================================================================
# PANEL DE ADMINISTRACIÓN - AUDITORÍA DE PUNTOS
# ============================================================================

def es_admin(documento):
    """Verifica si un usuario es administrador"""
    # Lista de documentos de administradores
    admins = ['1036689216']  # Agregar más documentos de admin aquí
    return documento in admins

def admin_required(f):
    """Decorador para rutas que requieren permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        documento = session.get('user_documento')
        if not documento or not es_admin(documento):
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/auditoria')
@login_required
def admin_auditoria():
    """Panel principal de auditoría de puntos"""
    return render_template('admin_auditoria.html')

@app.route('/admin/api/cliente/<documento>')
@login_required
def admin_get_cliente(documento):
    """Obtener información de un cliente para auditoría - Busca en todas las fuentes"""
    try:
        # 1. Buscar cliente en tabla Usuario (registrado en sistema de puntos)
        usuario = Usuario.query.filter_by(documento=documento).first()
        
        if usuario:
            # Cliente registrado - calcular puntos desde compras
            print(f"🔍 Cliente {documento} registrado, calculando puntos...")
            
            # Calcular puntos usando el sistema híbrido
            puntos_disponibles = calcular_puntos_con_fallback(documento)
            
            cliente_info = {
                'documento': usuario.documento,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'telefono': usuario.telefono,
                'puntos_disponibles': puntos_disponibles,
                'migrado': cliente_esta_migrado(documento),
                'registrado': True
            }
            
            return jsonify({
                'success': True,
                'cliente': cliente_info
            })
        
        # 2. Cliente NO registrado - Buscar en AMBAS fuentes y calcular puntos
        print(f"🔍 Cliente {documento} no registrado, buscando en compras y calculando puntos...")
        
        nombre_cliente = None
        tiene_compras_sql = False
        tiene_compras_pg = False
        total_compras = 0
        total_ventas = 0
        
        # Buscar en SQL Server (2026+)
        try:
            query_sql = """
            SELECT 
                IDENTIFICACION, 
                NOMBRE_CLIENTE,
                COUNT(*) as total_compras,
                SUM(CAST(VLRVENTA AS DECIMAL(15,2))) as total_ventas
            FROM MVTRADE
            WHERE IDENTIFICACION = ?
                AND CAST(VLRVENTA AS DECIMAL(15,2)) > 0
                AND (TIPODCTO = 'FM' OR TIPODCTO = 'FB')
            GROUP BY IDENTIFICACION, NOMBRE_CLIENTE
            """
            results_sql = ejecutar_query_sql_server(query_sql, (documento,))
            
            if results_sql:
                result_sql = results_sql[0]
                nombre_cliente = result_sql[1]
                tiene_compras_sql = True
                total_compras += result_sql[2] or 0
                total_ventas += float(result_sql[3]) if result_sql[3] else 0
                print(f"✅ SQL Server: {result_sql[2]} compras, ${result_sql[3]}")
        except Exception as e:
            print(f"⚠️ Error buscando en SQL Server: {e}")
        
        # Buscar en PostgreSQL (2025-)
        try:
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            query_pg = """
            SELECT 
                m.nit,
                m.nombrecliente,
                COUNT(*) as total_compras,
                SUM(CAST(m.vlrventa AS DECIMAL(15,2))) as total_ventas
            FROM micelu_backup.mvtrade m
            WHERE m.nit = %s
                AND CAST(m.vlrventa AS DECIMAL(15,2)) > 0
                AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
            GROUP BY m.nit, m.nombrecliente
            """
            cursor_pg.execute(query_pg, (documento,))
            result_pg = cursor_pg.fetchone()
            cursor_pg.close()
            conn_pg.close()
            
            if result_pg:
                if not nombre_cliente:
                    nombre_cliente = result_pg[1]
                tiene_compras_pg = True
                total_compras += result_pg[2] or 0
                total_ventas += float(result_pg[3]) if result_pg[3] else 0
                print(f"✅ PostgreSQL: {result_pg[2]} compras, ${result_pg[3]}")
        except Exception as e:
            print(f"⚠️ Error buscando en PostgreSQL: {e}")
        
        # 3. Si se encontró en alguna fuente, calcular puntos y retornar
        if tiene_compras_sql or tiene_compras_pg:
            # Calcular puntos aproximados
            obtener_puntos_valor = maestros.query.with_entities(maestros.obtener_puntos).first()
            if obtener_puntos_valor:
                puntos_calculados = int(total_ventas // obtener_puntos_valor[0])
            else:
                puntos_calculados = 0
            
            fuentes = []
            if tiene_compras_sql:
                fuentes.append("SQL Server (2026+)")
            if tiene_compras_pg:
                fuentes.append("PostgreSQL (2025-)")
            
            mensaje = f'Cliente encontrado en {" y ".join(fuentes)} con {total_compras} compras'
            
            cliente_info = {
                'documento': documento,
                'nombre': nombre_cliente or 'Nombre no disponible',
                'email': None,
                'telefono': None,
                'puntos_disponibles': puntos_calculados,
                'migrado': False,
                'registrado': False,
                'tiene_compras_sql': tiene_compras_sql,
                'tiene_compras_pg': tiene_compras_pg,
                'total_compras': total_compras,
                'total_ventas': int(total_ventas),
                'mensaje': mensaje
            }
            
            print(f"✅ Cliente no registrado: {total_compras} compras, ${total_ventas}, {puntos_calculados} puntos")
            
            return jsonify({
                'success': True,
                'cliente': cliente_info
            })
        
        # 4. Cliente no encontrado en ninguna parte
        return jsonify({
            'success': False,
            'message': f'Cliente con documento {documento} no encontrado en el sistema ni en compras'
        }), 404
        
    except Exception as e:
        print(f"❌ Error en admin_get_cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/transacciones/<documento>')
@login_required
def admin_get_transacciones(documento):
    """Obtener todas las transacciones de un cliente"""
    try:
        if not cliente_esta_migrado(documento):
            return jsonify({
                'success': False,
                'message': 'Cliente no está migrado al nuevo sistema'
            }), 400
        
        transacciones = Transacciones_Puntos.query.filter_by(
            documento=documento
        ).order_by(
            Transacciones_Puntos.fecha_transaccion.desc()
        ).all()
        
        resultado = []
        for t in transacciones:
            resultado.append({
                'id': t.id,
                'tipo': t.tipo_transaccion,
                'puntos': t.puntos,
                'descripcion': t.descripcion,
                'estado': t.estado,
                'fecha': t.fecha_transaccion.isoformat(),
                'fecha_vencimiento': t.fecha_vencimiento.isoformat() if t.fecha_vencimiento else None,
                'referencia': t.referencia_compra or t.referencia_redencion or t.referencia_referido
            })
        
        return jsonify({
            'success': True,
            'transacciones': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/agregar_transaccion', methods=['POST'])
@login_required
def admin_agregar_transaccion():
    """Agregar una nueva transacción (corrección, regalo, etc.)"""
    try:
        data = request.get_json()
        documento = data.get('documento')
        tipo = data.get('tipo')
        puntos = int(data.get('puntos'))
        descripcion = data.get('descripcion')
        referencia = data.get('referencia', '')
        
        # Validaciones
        if not all([documento, tipo, descripcion]):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos'
            }), 400
        
        if tipo not in ['ACUMULACION', 'REDENCION', 'REGALO', 'CORRECCION']:
            return jsonify({
                'success': False,
                'message': 'Tipo de transacción inválido'
            }), 400
        
        # Verificar que el cliente existe
        usuario = Usuario.query.filter_by(documento=documento).first()
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Cliente no encontrado'
            }), 404
        
        # Obtener información del admin que hace la transacción
        admin_documento = session.get('user_documento')
        admin_usuario = Usuario.query.filter_by(documento=admin_documento).first()
        admin_nombre = admin_usuario.nombre if admin_usuario else 'Admin'
        
        # Crear descripción completa con información del admin
        descripcion_completa = f"[ADMIN: {admin_nombre}] {descripcion}"
        
        # Crear la transacción
        crear_transaccion_manual(
            documento=documento,
            tipo=tipo,
            puntos=puntos,
            descripcion=descripcion_completa,
            referencia=referencia
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transacción agregada exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/anular_transaccion', methods=['POST'])
@login_required
def admin_anular_transaccion():
    """Anular una transacción existente"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        motivo = data.get('motivo')
        
        if not all([transaction_id, motivo]):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos'
            }), 400
        
        # Buscar la transacción
        transaccion = Transacciones_Puntos.query.filter_by(id=transaction_id).first()
        if not transaccion:
            return jsonify({
                'success': False,
                'message': 'Transacción no encontrada'
            }), 404
        
        if transaccion.estado != 'ACTIVO':
            return jsonify({
                'success': False,
                'message': 'Solo se pueden anular transacciones activas'
            }), 400
        
        # Obtener información del admin
        admin_documento = session.get('user_documento')
        admin_usuario = Usuario.query.filter_by(documento=admin_documento).first()
        admin_nombre = admin_usuario.nombre if admin_usuario else 'Admin'
        
        # Marcar la transacción original como anulada
        transaccion.estado = 'ANULADO'
        transaccion.actualizado_en = datetime.now()
        
        # Crear transacción de anulación (puntos opuestos)
        descripcion_anulacion = f"[ADMIN: {admin_nombre}] ANULACIÓN: {motivo} (Ref: {transaccion.descripcion})"
        
        crear_transaccion_manual(
            documento=transaccion.documento,
            tipo='CORRECCION',
            puntos=-transaccion.puntos,  # Puntos opuestos para anular
            descripcion=descripcion_anulacion,
            referencia=f"ANULA_{transaction_id[:8]}"
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transacción anulada exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/ultimos_canjeos')
@login_required
def admin_ultimos_canjeos():
    """Obtener los últimos canjeos de puntos de todos los clientes"""
    try:
        # Obtener parámetros de paginación
        limite = request.args.get('limite', 25, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Consultar redenciones (transacciones de tipo REDENCION)
        redenciones = Transacciones_Puntos.query.filter_by(
            tipo_transaccion='REDENCION'
        ).order_by(
            Transacciones_Puntos.fecha_transaccion.desc()
        ).limit(limite).offset(offset).all()
        
        resultado = []
        for redencion in redenciones:
            # Obtener información del cliente
            usuario = Usuario.query.filter_by(documento=redencion.documento).first()
            
            # Obtener información del cupón si existe
            cupon_info = None
            if redencion.referencia_redencion:
                historial = historial_beneficio.query.filter_by(
                    id=redencion.referencia_redencion
                ).first()
                if historial:
                    cupon_info = {
                        'cupon': historial.cupon,
                        'cupon_fisico': historial.cupon_fisico,
                        'valor_descuento': historial.valor_descuento,
                        'estado_cupon': historial.estado_cupon,
                        'fecha_uso_real': historial.fecha_uso_real.isoformat() if historial.fecha_uso_real else None,
                        'tiempo_expiracion': historial.tiempo_expiracion.isoformat() if historial.tiempo_expiracion else None
                    }
            
            resultado.append({
                'id': redencion.id,
                'documento': redencion.documento,
                'nombre_cliente': usuario.nombre if usuario else 'Desconocido',
                'email_cliente': usuario.email if usuario else None,
                'telefono_cliente': usuario.telefono if usuario else None,
                'puntos_utilizados': abs(redencion.puntos),  # Valor absoluto porque es negativo
                'descripcion': redencion.descripcion,
                'fecha_canjeo': redencion.fecha_transaccion.isoformat(),
                'estado': redencion.estado,
                'cupon_info': cupon_info,
                'puntos_disponibles_antes': redencion.puntos_disponibles_antes,
                'puntos_disponibles_despues': redencion.puntos_disponibles_despues
            })
        
        # Contar total de redenciones para paginación
        total_redenciones = Transacciones_Puntos.query.filter_by(
            tipo_transaccion='REDENCION'
        ).count()
        
        return jsonify({
            'success': True,
            'canjeos': resultado,
            'total': total_redenciones,
            'limite': limite,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/estadisticas_canjeos')
@login_required
def admin_estadisticas_canjeos():
    """Obtener estadísticas de canjeos"""
    try:
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Canjeos del mes actual
        canjeos_mes = Transacciones_Puntos.query.filter(
            Transacciones_Puntos.tipo_transaccion == 'REDENCION',
            Transacciones_Puntos.fecha_transaccion >= inicio_mes
        ).count()
        
        # Puntos canjeados del mes
        puntos_mes = db.session.query(
            db.func.sum(Transacciones_Puntos.puntos)
        ).filter(
            Transacciones_Puntos.tipo_transaccion == 'REDENCION',
            Transacciones_Puntos.fecha_transaccion >= inicio_mes
        ).scalar() or 0
        
        # Canjeos de hoy
        inicio_hoy = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        canjeos_hoy = Transacciones_Puntos.query.filter(
            Transacciones_Puntos.tipo_transaccion == 'REDENCION',
            Transacciones_Puntos.fecha_transaccion >= inicio_hoy
        ).count()
        
        # Total histórico
        total_canjeos = Transacciones_Puntos.query.filter_by(
            tipo_transaccion='REDENCION'
        ).count()
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'canjeos_hoy': canjeos_hoy,
                'canjeos_mes': canjeos_mes,
                'puntos_canjeados_mes': abs(int(puntos_mes)),
                'total_canjeos_historico': total_canjeos
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/puntos_clientes')
@login_required
def admin_puntos_clientes():
    """Obtener lista de clientes con sus puntos disponibles"""
    try:
        # Obtener parámetros de paginación y búsqueda
        limite = request.args.get('limite', 25, type=int)
        offset = request.args.get('offset', 0, type=int)
        busqueda = request.args.get('busqueda', '', type=str).strip()
        
        # Construir query base
        query = Puntos_Clientes.query
        
        # Si hay búsqueda, filtrar
        if busqueda:
            # Buscar en Usuario por nombre, email, teléfono o documento
            usuarios_encontrados = Usuario.query.filter(
                db.or_(
                    Usuario.documento.ilike(f'%{busqueda}%'),
                    Usuario.nombre.ilike(f'%{busqueda}%'),
                    Usuario.email.ilike(f'%{busqueda}%'),
                    Usuario.telefono.ilike(f'%{busqueda}%')
                )
            ).all()
            
            # Obtener documentos de usuarios encontrados
            documentos_encontrados = [u.documento for u in usuarios_encontrados]
            
            if documentos_encontrados:
                query = query.filter(Puntos_Clientes.documento.in_(documentos_encontrados))
            else:
                # Si no se encontró nada, retornar vacío
                return jsonify({
                    'success': True,
                    'clientes': [],
                    'total': 0,
                    'limite': limite,
                    'offset': offset
                })
        
        # Aplicar ordenamiento y paginación
        clientes_query = query.order_by(
            Puntos_Clientes.puntos_disponibles.desc()
        ).limit(limite).offset(offset).all()
        
        resultado = []
        for cliente_puntos in clientes_query:
            # Obtener información del usuario
            usuario = Usuario.query.filter_by(documento=cliente_puntos.documento).first()
            
            # Calcular puntos reales usando el sistema nuevo
            puntos_reales = calcular_puntos_con_fallback(cliente_puntos.documento)
            
            resultado.append({
                'documento': cliente_puntos.documento,
                'nombre': usuario.nombre if usuario else 'Desconocido',
                'email': usuario.email if usuario else None,
                'telefono': usuario.telefono if usuario else None,
                'puntos_disponibles': puntos_reales,
                'ultima_actualizacion': cliente_puntos.ultima_actualizacion.isoformat() if cliente_puntos.ultima_actualizacion else None
            })
        
        # Contar total de clientes (con filtro si aplica)
        if busqueda and documentos_encontrados:
            total_clientes = query.count()
        elif busqueda:
            total_clientes = 0
        else:
            total_clientes = Puntos_Clientes.query.count()
        
        return jsonify({
            'success': True,
            'clientes': resultado,
            'total': total_clientes,
            'limite': limite,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/estadisticas_puntos')
@login_required
def admin_estadisticas_puntos():
    """Obtener estadísticas generales de puntos"""
    try:
        # Total de clientes
        total_clientes = Puntos_Clientes.query.count()
        
        # Total de puntos en circulación (suma de puntos disponibles)
        total_puntos = db.session.query(
            db.func.sum(Puntos_Clientes.puntos_disponibles)
        ).scalar() or 0
        
        # Promedio de puntos por cliente
        promedio = int(total_puntos / total_clientes) if total_clientes > 0 else 0
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_clientes': total_clientes,
                'total_puntos_circulacion': int(total_puntos),
                'promedio_puntos': promedio
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/historial_compras')
@login_required
def admin_historial_compras():
    """Obtener historial de compras combinando SQL Server (2026+) y PostgreSQL (2025-)"""
    try:
        # Obtener parámetros
        limite = request.args.get('limite', 25, type=int)
        offset = request.args.get('offset', 0, type=int)
        cliente_busqueda = request.args.get('cliente', '', type=str).strip()
        fecha_desde = request.args.get('fecha_desde', '', type=str)
        fecha_hasta = request.args.get('fecha_hasta', '', type=str)
        
        # ============================================================================
        # CONSULTA 1: SQL SERVER (OFIMA) - Datos de 2026 en adelante
        # ============================================================================
        query_sql_server = """
        SELECT DISTINCT
         m.IDENTIFICACION,
         m.PRODUCTO_NOMBRE,
         CAST(m.VLRVENTA AS DECIMAL(15,2)) AS VLRVENTA,
         m.FHCOMPRA,
         m.TIPODCTO,
         m.NRODCTO,
         m.LINEA,
         '' AS MEDIOPAG
        FROM MVTRADE m
        WHERE CAST(m.VLRVENTA AS DECIMAL(15,2)) > 0
            AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
            AND YEAR(CAST(m.FHCOMPRA AS DATE)) >= 2026
        """
        
        # ============================================================================
        # CONSULTA 2: POSTGRESQL - Datos de 2025 hacia atrás
        # ============================================================================
        query_postgres = """
        SELECT DISTINCT
         m.nit AS IDENTIFICACION,
         m.nombre AS PRODUCTO_NOMBRE,
         CAST(m.vlrventa AS DECIMAL(15,2)) AS VLRVENTA,
         m.fhcompra AS FHCOMPRA,
         m.tipodcto AS TIPODCTO,
         m.nrodcto AS NRODCTO,
         'CEL' AS LINEA,
         '' AS MEDIOPAG
        FROM micelu_backup.mvtrade m
        WHERE CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
        """
        
        params_sql = []
        params_pg = []
        
        # Filtro por cliente
        if cliente_busqueda:
            usuarios = Usuario.query.filter(
                db.or_(
                    Usuario.documento.ilike(f'%{cliente_busqueda}%'),
                    Usuario.nombre.ilike(f'%{cliente_busqueda}%')
                )
            ).all()
            
            if usuarios:
                documentos = [u.documento for u in usuarios]
                placeholders_sql = ','.join(['?'] * len(documentos))
                placeholders_pg = ','.join(['%s'] * len(documentos))
                query_sql_server += f" AND m.IDENTIFICACION IN ({placeholders_sql})"
                query_postgres += f" AND m.nit IN ({placeholders_pg})"
                params_sql.extend(documentos)
                params_pg.extend(documentos)
            else:
                return jsonify({
                    'success': True,
                    'compras': [],
                    'total': 0,
                    'limite': limite,
                    'offset': offset
                })
        
        # Filtro por fechas
        if fecha_desde:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query_sql_server += " AND CAST(m.FHCOMPRA AS DATE) >= ?"
            params_sql.append(fecha_desde_dt.strftime('%Y-%m-%d'))
            
            fecha_desde_str = fecha_desde_dt.strftime('%d/%m/%Y')
            query_postgres += " AND TO_DATE(m.fhcompra, 'DD/MM/YYYY') >= TO_DATE(%s, 'DD/MM/YYYY')"
            params_pg.append(fecha_desde_str)
        
        if fecha_hasta:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            query_sql_server += " AND CAST(m.FHCOMPRA AS DATE) <= ?"
            params_sql.append(fecha_hasta_dt.strftime('%Y-%m-%d'))
            
            fecha_hasta_str = fecha_hasta_dt.strftime('%d/%m/%Y')
            query_postgres += " AND TO_DATE(m.fhcompra, 'DD/MM/YYYY') <= TO_DATE(%s, 'DD/MM/YYYY')"
            params_pg.append(fecha_hasta_str)
        
        # Agregar ordenamiento
        query_sql_server += " ORDER BY m.FHCOMPRA DESC"
        query_postgres += " ORDER BY m.fhcompra DESC"
        
        # ============================================================================
        # EJECUTAR AMBAS CONSULTAS Y COMBINAR RESULTADOS
        # ============================================================================
        resultados_combinados = []
        
        # Consultar SQL Server (2026+)
        try:
            print("🔄 Consultando SQL Server (2026+)...")
            results_sql = ejecutar_query_sql_server(query_sql_server, params_sql)
            if results_sql:
                print(f"✅ SQL Server: {len(results_sql)} registros")
                resultados_combinados.extend(results_sql)
            else:
                print("⚠️ SQL Server: Sin resultados")
        except Exception as e:
            print(f"⚠️ Error en SQL Server: {e}")
        
        # Consultar PostgreSQL (2025-)
        try:
            print("🔄 Consultando PostgreSQL (2025-)...")
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            cursor_pg.execute(query_postgres, params_pg)
            results_pg = cursor_pg.fetchall()
            cursor_pg.close()
            conn_pg.close()
            print(f"✅ PostgreSQL: {len(results_pg)} registros")
            resultados_combinados.extend(results_pg)
        except Exception as e:
            print(f"⚠️ Error en PostgreSQL: {e}")
        
        # Ordenar resultados combinados por fecha descendente
        resultados_combinados.sort(key=lambda x: x[3] if isinstance(x[3], datetime) else datetime.strptime(x[3], '%d/%m/%Y') if '/' in str(x[3]) else datetime.now(), reverse=True)
        
        # Contar total
        total = len(resultados_combinados)
        
        # Aplicar paginación
        resultados_paginados = resultados_combinados[offset:offset + limite]
        
        # Procesar resultados
        resultado = []
        obtener_puntos_valor = maestros.query.with_entities(maestros.obtener_puntos).first()
        
        for row in resultados_paginados:
            documento = str(row[0])
            
            # Obtener nombre del cliente
            usuario = Usuario.query.filter_by(documento=documento).first()
            nombre_cliente = usuario.nombre if usuario else 'Desconocido'
            
            # Convertir fecha
            fecha_compra = row[3]
            if isinstance(fecha_compra, str) and '/' in fecha_compra:
                fecha_compra = datetime.strptime(fecha_compra, '%d/%m/%Y')
            elif not isinstance(fecha_compra, datetime):
                fecha_compra = datetime.now()
            
            # Calcular puntos
            valor_venta = float(row[2])
            if obtener_puntos_valor:
                puntos = int(valor_venta // obtener_puntos_valor[0])
            else:
                puntos = 0
            
            resultado.append({
                'fecha_compra': fecha_compra.strftime('%Y-%m-%d'),
                'documento': documento,
                'nombre_cliente': nombre_cliente,
                'producto_nombre': row[1],
                'valor_venta': valor_venta,
                'puntos_ganados': puntos,
                'tipo_documento': row[4],
                'nro_documento': row[5],
                'disponible': True
            })
        
        return jsonify({
            'success': True,
            'compras': resultado,
            'total': total,
            'limite': limite,
            'offset': offset
        })
        
    except Exception as e:
        print(f"Error en historial_compras: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/estadisticas_compras')
@login_required
def admin_estadisticas_compras():
    """Obtener estadísticas de compras combinando SQL Server (2026+) y PostgreSQL (2025-)"""
    try:
        # Obtener parámetros de filtro
        cliente_busqueda = request.args.get('cliente', '', type=str).strip()
        fecha_desde = request.args.get('fecha_desde', '', type=str)
        fecha_hasta = request.args.get('fecha_hasta', '', type=str)
        
        # ============================================================================
        # CONSULTA SQL SERVER (2026+)
        # ============================================================================
        query_sql_server = """
        SELECT 
         COUNT(*) as total_compras,
         SUM(CAST(m.VLRVENTA AS DECIMAL(15,2))) as total_ventas,
         COUNT(DISTINCT m.IDENTIFICACION) as clientes_unicos
        FROM MVTRADE m
        WHERE CAST(m.VLRVENTA AS DECIMAL(15,2)) > 0
            AND (m.TIPODCTO = 'FM' OR m.TIPODCTO = 'FB')
            AND YEAR(CAST(m.FHCOMPRA AS DATE)) >= 2026
        """
        
        # ============================================================================
        # CONSULTA POSTGRESQL (2025-)
        # ============================================================================
        query_postgres = """
        SELECT 
         COUNT(*) as total_compras,
         SUM(CAST(m.vlrventa AS DECIMAL(15,2))) as total_ventas,
         COUNT(DISTINCT m.nit) as clientes_unicos
        FROM micelu_backup.mvtrade m
        WHERE CAST(m.vlrventa AS DECIMAL(15,2)) > 0
            AND (m.tipodcto = 'FM' OR m.tipodcto = 'FB')
        """
        
        params_sql = []
        params_pg = []
        
        # Filtro por cliente
        if cliente_busqueda:
            usuarios = Usuario.query.filter(
                db.or_(
                    Usuario.documento.ilike(f'%{cliente_busqueda}%'),
                    Usuario.nombre.ilike(f'%{cliente_busqueda}%')
                )
            ).all()
            
            if usuarios:
                documentos = [u.documento for u in usuarios]
                placeholders_sql = ','.join(['?'] * len(documentos))
                placeholders_pg = ','.join(['%s'] * len(documentos))
                query_sql_server += f" AND m.IDENTIFICACION IN ({placeholders_sql})"
                query_postgres += f" AND m.nit IN ({placeholders_pg})"
                params_sql.extend(documentos)
                params_pg.extend(documentos)
        
        # Filtro por fechas
        if fecha_desde:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query_sql_server += " AND CAST(m.FHCOMPRA AS DATE) >= ?"
            params_sql.append(fecha_desde_dt.strftime('%Y-%m-%d'))
            
            fecha_desde_str = fecha_desde_dt.strftime('%d/%m/%Y')
            query_postgres += " AND TO_DATE(m.fhcompra, 'DD/MM/YYYY') >= TO_DATE(%s, 'DD/MM/YYYY')"
            params_pg.append(fecha_desde_str)
        
        if fecha_hasta:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            query_sql_server += " AND CAST(m.FHCOMPRA AS DATE) <= ?"
            params_sql.append(fecha_hasta_dt.strftime('%Y-%m-%d'))
            
            fecha_hasta_str = fecha_hasta_dt.strftime('%d/%m/%Y')
            query_postgres += " AND TO_DATE(m.fhcompra, 'DD/MM/YYYY') <= TO_DATE(%s, 'DD/MM/YYYY')"
            params_pg.append(fecha_hasta_str)
        
        # Ejecutar ambas consultas
        total_compras = 0
        total_ventas = 0
        clientes_unicos_set = set()
        
        # SQL Server
        try:
            results_sql = ejecutar_query_sql_server(query_sql_server, params_sql)
            
            if results_sql:
                result_sql = results_sql[0]
                total_compras += result_sql[0] or 0
                total_ventas += float(result_sql[1]) if result_sql[1] else 0
                # No podemos combinar clientes únicos fácilmente, lo haremos después
        except Exception as e:
            print(f"⚠️ Error en SQL Server estadísticas: {e}")
        
        # PostgreSQL
        try:
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            cursor_pg.execute(query_postgres, params_pg)
            result_pg = cursor_pg.fetchone()
            cursor_pg.close()
            conn_pg.close()
            
            if result_pg:
                total_compras += result_pg[0] or 0
                total_ventas += float(result_pg[1]) if result_pg[1] else 0
        except Exception as e:
            print(f"⚠️ Error en PostgreSQL estadísticas: {e}")
        
        # Para clientes únicos, hacer una consulta combinada simple
        try:
            # SQL Server
            query_clientes_sql = "SELECT DISTINCT IDENTIFICACION FROM MVTRADE WHERE CAST(VLRVENTA AS DECIMAL(15,2)) > 0 AND (TIPODCTO = 'FM' OR TIPODCTO = 'FB') AND YEAR(CAST(FHCOMPRA AS DATE)) >= 2026"
            results_clientes_sql = ejecutar_query_sql_server(query_clientes_sql)
            if results_clientes_sql:
                for row in results_clientes_sql:
                    clientes_unicos_set.add(str(row[0]))
        except:
            pass
        
        try:
            # PostgreSQL
            conn_pg = obtener_conexion_bd_backup()
            cursor_pg = conn_pg.cursor()
            query_clientes_pg = "SELECT DISTINCT nit FROM micelu_backup.mvtrade WHERE CAST(vlrventa AS DECIMAL(15,2)) > 0 AND (tipodcto = 'FM' OR tipodcto = 'FB')"
            cursor_pg.execute(query_clientes_pg)
            for row in cursor_pg.fetchall():
                clientes_unicos_set.add(str(row[0]))
            cursor_pg.close()
            conn_pg.close()
        except:
            pass
        
        clientes_unicos = len(clientes_unicos_set)
        
        # Calcular puntos totales
        obtener_puntos_valor = maestros.query.with_entities(maestros.obtener_puntos).first()
        if obtener_puntos_valor:
            total_puntos = int(total_ventas // obtener_puntos_valor[0])
        else:
            total_puntos = 0
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_compras': total_compras,
                'total_puntos': total_puntos,
                'clientes_unicos': clientes_unicos
            }
        })
        
    except Exception as e:
        print(f"Error en estadisticas_compras: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_compras': total_compras,
                'total_ventas': int(total_ventas),
                'total_puntos': total_puntos,
                'clientes_unicos': clientes_unicos
            }
        })
        
    except Exception as e:
        print(f"Error en estadisticas_compras: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_compras': total_compras,
                'total_ventas': int(total_ventas),
                'total_puntos': total_puntos,
                'clientes_unicos': clientes_unicos
            }
        })
        
    except Exception as e:
        print(f"Error en estadisticas_compras: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin/api/exportar_compras')
@login_required
def admin_exportar_compras():
    """Exportar historial de compras a Excel"""
    try:
        # Obtener parámetros de filtro
        cliente_busqueda = request.args.get('cliente', '', type=str).strip()
        fecha_desde = request.args.get('fecha_desde', '', type=str)
        fecha_hasta = request.args.get('fecha_hasta', '', type=str)
        
        # Obtener datos de SharePoint
        df = obtener_datos_sharepoint()
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'message': 'No hay datos para exportar'
            }), 400
        
        # Aplicar filtros (misma lógica que historial_compras)
        if cliente_busqueda:
            usuarios = Usuario.query.filter(
                db.or_(
                    Usuario.documento.ilike(f'%{cliente_busqueda}%'),
                    Usuario.nombre.ilike(f'%{cliente_busqueda}%')
                )
            ).all()
            
            if usuarios:
                documentos = [u.documento for u in usuarios]
                df = df[df['IDENTIFICACION'].astype(str).isin(documentos)]
        
        if fecha_desde:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            df = df[pd.to_datetime(df['FHCOMPRA']) >= fecha_desde_dt]
        
        if fecha_hasta:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            df = df[pd.to_datetime(df['FHCOMPRA']) <= fecha_hasta_dt]
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Compras', index=False)
        
        output.seek(0)
        
        # Generar nombre de archivo con fecha
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'historial_compras_{fecha_actual}.xlsx'
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        print(f"Error en exportar_compras: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
