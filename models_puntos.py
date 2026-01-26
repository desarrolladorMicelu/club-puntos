# ============================================================================
# NUEVOS MODELOS PARA SISTEMA DE PUNTOS CON AUDITORÍA
# ============================================================================
from datetime import datetime
import uuid
from app import db

class Transacciones_Puntos(db.Model):
    """
    Tabla de auditoría completa de TODAS las transacciones de puntos.
    Cada movimiento de puntos (acumulación, redención, vencimiento) queda registrado aquí.
    """
    __bind_key__ = 'db3'
    __tablename__ = 'transacciones_puntos'
    __table_args__ = {'schema': 'plan_beneficios'}
    
    # Identificación
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    documento = db.Column(db.String(50), nullable=False, index=True)
    
    # Tipo de transacción
    tipo_transaccion = db.Column(db.String(20), nullable=False)  # 'ACUMULACION', 'REDENCION', 'VENCIMIENTO', 'REGALO', 'REFERIDO'
    
    # Puntos (positivo para acumulación, negativo para redención/vencimiento)
    puntos = db.Column(db.Integer, nullable=False)
    
    # Saldos (para auditoría)
    puntos_disponibles_antes = db.Column(db.Integer, nullable=False, default=0)
    puntos_disponibles_despues = db.Column(db.Integer, nullable=False, default=0)
    
    # Fechas
    fecha_transaccion = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)  # Solo para ACUMULACION (1 año después)
    
    # Referencias para trazabilidad
    referencia_compra = db.Column(db.String(100), nullable=True)  # TIPODCTO-NRODCTO para compras
    referencia_redencion = db.Column(db.String(36), nullable=True)  # UUID del historial_beneficio
    referencia_referido = db.Column(db.String(36), nullable=True)  # UUID del referido
    
    # Descripción legible
    descripcion = db.Column(db.String(500), nullable=True)
    
    # Estado de la transacción
    estado = db.Column(db.String(20), nullable=False, default='ACTIVO')  # 'ACTIVO', 'VENCIDO', 'USADO'
    
    # Metadata
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.now)
    actualizado_en = db.Column(db.DateTime, nullable=True, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Transaccion {self.tipo_transaccion} {self.puntos}pts Doc:{self.documento}>'