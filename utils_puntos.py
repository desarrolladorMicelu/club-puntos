# ============================================================================
# UTILIDADES PARA SISTEMA DE PUNTOS CON AUDITORÍA
# ============================================================================
from datetime import datetime, timedelta
from app import db
from models_puntos import Transacciones_Puntos

def calcular_puntos_disponibles(documento):
    """
    Calcula los puntos disponibles de un cliente en tiempo real.
    Excluye automáticamente puntos vencidos (más de 1 año).
    
    Returns:
        dict: {
            'puntos_disponibles': int,
            'puntos_vencidos': int,
            'puntos_por_vencer_30dias': int
        }
    """
    hoy = datetime.now()
    fecha_30_dias = hoy + timedelta(days=30)
    
    # Puntos activos (no vencidos)
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
    
    # Puntos vencidos (para reportes)
    puntos_vencidos = db.session.query(
        db.func.coalesce(db.func.sum(Transacciones_Puntos.puntos), 0)
    ).filter(
        Transacciones_Puntos.documento == documento,
        Transacciones_Puntos.estado == 'ACTIVO',
        Transacciones_Puntos.fecha_vencimiento < hoy,
        Transacciones_Puntos.fecha_vencimiento.isnot(None)
    ).scalar()
    
    # Puntos por vencer en 30 días
    puntos_por_vencer = db.session.query(
        db.func.coalesce(db.func.sum(Transacciones_Puntos.puntos), 0)
    ).filter(
        Transacciones_Puntos.documento == documento,
        Transacciones_Puntos.estado == 'ACTIVO',
        Transacciones_Puntos.fecha_vencimiento.between(hoy, fecha_30_dias)
    ).scalar()
    
    return {
        'puntos_disponibles': int(puntos_activos or 0),
        'puntos_vencidos': int(puntos_vencidos or 0),
        'puntos_por_vencer_30dias': int(puntos_por_vencer or 0)
    }


def crear_transaccion_acumulacion(documento, puntos, referencia_compra, descripcion, fecha_compra=None):
    """
    Crea una transacción de acumulación de puntos por compra.
    
    Args:
        documento: Cédula del cliente
        puntos: Cantidad de puntos a acumular
        referencia_compra: Identificador de la compra (TIPODCTO-NRODCTO)
        descripcion: Descripción legible de la transacción
        fecha_compra: Fecha de la compra (para calcular vencimiento)
    
    Returns:
        Transacciones_Puntos: La transacción creada
    """
    if fecha_compra is None:
        fecha_compra = datetime.now()
    
    # Calcular saldo antes
    saldo_antes = calcular_puntos_disponibles(documento)['puntos_disponibles']
    
    # Fecha de vencimiento: 1 año después de la compra
    fecha_vencimiento = fecha_compra + timedelta(days=365)
    
    # Crear transacción
    transaccion = Transacciones_Puntos(
        documento=documento,
        tipo_transaccion='ACUMULACION',
        puntos=puntos,
        puntos_disponibles_antes=saldo_antes,
        puntos_disponibles_despues=saldo_antes + puntos,
        fecha_transaccion=fecha_compra,
        fecha_vencimiento=fecha_vencimiento,
        referencia_compra=referencia_compra,
        descripcion=descripcion,
        estado='ACTIVO'
    )
    
    db.session.add(transaccion)
    return transaccion


def crear_transaccion_redencion(documento, puntos, referencia_redencion, descripcion):
    """
    Crea una transacción de redención de puntos.
    Usa FIFO (First In First Out) para marcar qué puntos se están usando.
    
    Args:
        documento: Cédula del cliente
        puntos: Cantidad de puntos a redimir (positivo)
        referencia_redencion: UUID del historial_beneficio
        descripcion: Descripción legible
    
    Returns:
        Transacciones_Puntos: La transacción creada
    """
    # Calcular saldo antes
    saldo_antes = calcular_puntos_disponibles(documento)['puntos_disponibles']
    
    # Verificar que tenga suficientes puntos
    if puntos > saldo_antes:
        raise ValueError(f"Puntos insuficientes. Disponibles: {saldo_antes}, Solicitados: {puntos}")
    
    # Crear transacción de redención (puntos negativos)
    transaccion = Transacciones_Puntos(
        documento=documento,
        tipo_transaccion='REDENCION',
        puntos=-puntos,  # Negativo porque se están gastando
        puntos_disponibles_antes=saldo_antes,
        puntos_disponibles_despues=saldo_antes - puntos,
        fecha_transaccion=datetime.now(),
        referencia_redencion=referencia_redencion,
        descripcion=descripcion,
        estado='ACTIVO'
    )
    
    db.session.add(transaccion)
    
    # FIFO: Marcar los puntos más antiguos como USADO
    marcar_puntos_usados_fifo(documento, puntos)
    
    return transaccion


def marcar_puntos_usados_fifo(documento, puntos_a_usar):
    """
    Marca los puntos más antiguos como USADO siguiendo FIFO.
    
    Args:
        documento: Cédula del cliente
        puntos_a_usar: Cantidad de puntos que se están usando
    """
    hoy = datetime.now()
    
    # Obtener transacciones de acumulación activas, ordenadas por fecha (FIFO)
    transacciones_disponibles = Transacciones_Puntos.query.filter(
        Transacciones_Puntos.documento == documento,
        Transacciones_Puntos.tipo_transaccion.in_(['ACUMULACION', 'REGALO', 'REFERIDO']),
        Transacciones_Puntos.estado == 'ACTIVO',
        db.or_(
            Transacciones_Puntos.fecha_vencimiento.is_(None),
            Transacciones_Puntos.fecha_vencimiento >= hoy
        )
    ).order_by(Transacciones_Puntos.fecha_transaccion.asc()).all()
    
    puntos_restantes = puntos_a_usar
    
    for transaccion in transacciones_disponibles:
        if puntos_restantes <= 0:
            break
        
        if transaccion.puntos <= puntos_restantes:
            # Usar todos los puntos de esta transacción
            transaccion.estado = 'USADO'
            puntos_restantes -= transaccion.puntos
        else:
            # Dividir la transacción (crear una nueva con el resto)
            puntos_usados = puntos_restantes
            puntos_sobrantes = transaccion.puntos - puntos_usados
            
            # Marcar la transacción original como USADO
            transaccion.estado = 'USADO'
            transaccion.puntos = puntos_usados
            
            # Crear nueva transacción con los puntos sobrantes
            nueva_transaccion = Transacciones_Puntos(
                documento=documento,
                tipo_transaccion=transaccion.tipo_transaccion,
                puntos=puntos_sobrantes,
                puntos_disponibles_antes=0,  # No aplica para splits
                puntos_disponibles_despues=0,
                fecha_transaccion=transaccion.fecha_transaccion,
                fecha_vencimiento=transaccion.fecha_vencimiento,
                referencia_compra=transaccion.referencia_compra,
                descripcion=f"Split de {transaccion.id}",
                estado='ACTIVO'
            )
            db.session.add(nueva_transaccion)
            
            puntos_restantes = 0


def crear_transaccion_regalo(documento, puntos, descripcion):
    """
    Crea una transacción de puntos de regalo (no vencen).
    
    Args:
        documento: Cédula del cliente
        puntos: Cantidad de puntos de regalo
        descripcion: Descripción del regalo
    
    Returns:
        Transacciones_Puntos: La transacción creada
    """
    saldo_antes = calcular_puntos_disponibles(documento)['puntos_disponibles']
    
    transaccion = Transacciones_Puntos(
        documento=documento,
        tipo_transaccion='REGALO',
        puntos=puntos,
        puntos_disponibles_antes=saldo_antes,
        puntos_disponibles_despues=saldo_antes + puntos,
        fecha_transaccion=datetime.now(),
        fecha_vencimiento=None,  # Los regalos NO vencen
        descripcion=descripcion,
        estado='ACTIVO'
    )
    
    db.session.add(transaccion)
    return transaccion


def crear_transaccion_referido(documento, puntos, referencia_referido, descripcion):
    """
    Crea una transacción de puntos por referido.
    
    Args:
        documento: Cédula del cliente que refirió
        puntos: Cantidad de puntos por el referido
        referencia_referido: UUID del referido
        descripcion: Descripción del referido
    
    Returns:
        Transacciones_Puntos: La transacción creada
    """
    saldo_antes = calcular_puntos_disponibles(documento)['puntos_disponibles']
    
    # Los puntos de referidos vencen 1 año después
    fecha_vencimiento = datetime.now() + timedelta(days=365)
    
    transaccion = Transacciones_Puntos(
        documento=documento,
        tipo_transaccion='REFERIDO',
        puntos=puntos,
        puntos_disponibles_antes=saldo_antes,
        puntos_disponibles_despues=saldo_antes + puntos,
        fecha_transaccion=datetime.now(),
        fecha_vencimiento=fecha_vencimiento,
        referencia_referido=referencia_referido,
        descripcion=descripcion,
        estado='ACTIVO'
    )
    
    db.session.add(transaccion)
    return transaccion


def obtener_historial_transacciones(documento, limite=50):
    """
    Obtiene el historial de transacciones de un cliente.
    
    Args:
        documento: Cédula del cliente
        limite: Número máximo de transacciones a retornar
    
    Returns:
        list: Lista de transacciones ordenadas por fecha descendente
    """
    transacciones = Transacciones_Puntos.query.filter(
        Transacciones_Puntos.documento == documento
    ).order_by(
        Transacciones_Puntos.fecha_transaccion.desc()
    ).limit(limite).all()
    
    return transacciones


# ============================================================================
# FUNCIÓN PARA MIGRACIÓN DE DATOS HISTÓRICOS
# ============================================================================
def migrar_datos_historicos(documento):
    """
    Migra los datos históricos de un cliente al nuevo sistema de transacciones.
    Esta función se ejecutará una vez por cliente para poblar la tabla.
    
    Args:
        documento: Cédula del cliente a migrar
    
    Returns:
        dict: Resumen de la migración
    """
    from app import Puntos_Clientes, Referidos, historial_beneficio
    
    resumen = {
        'compras_migradas': 0,
        'redenciones_migradas': 0,
        'referidos_migrados': 0,
        'regalos_migrados': 0,
        'errores': []
    }
    
    try:
        # 1. Migrar puntos de compras (desde Puntos_Clientes.total_puntos)
        puntos_cliente = Puntos_Clientes.query.filter_by(documento=documento).first()
        if puntos_cliente and puntos_cliente.total_puntos > 0:
            # Crear transacción de acumulación histórica
            crear_transaccion_acumulacion(
                documento=documento,
                puntos=puntos_cliente.total_puntos,
                referencia_compra='MIGRACION_HISTORICA',
                descripcion='Migración de puntos históricos de compras',
                fecha_compra=puntos_cliente.fecha_registro or datetime.now()
            )
            resumen['compras_migradas'] = puntos_cliente.total_puntos
        
        # 2. Migrar redenciones (desde historial_beneficio)
        redenciones = historial_beneficio.query.filter_by(documento=documento).all()
        for redencion in redenciones:
            crear_transaccion_redencion(
                documento=documento,
                puntos=redencion.puntos_utilizados,
                referencia_redencion=str(redencion.id),
                descripcion=f'Migración: Cupón {redencion.cupon}'
            )
            resumen['redenciones_migradas'] += redencion.puntos_utilizados
        
        # 3. Migrar referidos
        referidos = Referidos.query.filter_by(documento_cliente=documento).all()
        for referido in referidos:
            if referido.puntos_obtenidos:
                crear_transaccion_referido(
                    documento=documento,
                    puntos=referido.puntos_obtenidos,
                    referencia_referido=str(referido.id),
                    descripcion=f'Migración: Referido {referido.nombre_referido}'
                )
                resumen['referidos_migrados'] += referido.puntos_obtenidos
        
        # 4. Migrar puntos de regalo
        if puntos_cliente and puntos_cliente.puntos_regalo:
            crear_transaccion_regalo(
                documento=documento,
                puntos=puntos_cliente.puntos_regalo,
                descripcion='Migración de puntos de regalo históricos'
            )
            resumen['regalos_migrados'] = puntos_cliente.puntos_regalo
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        resumen['errores'].append(str(e))
    
    return resumen


# ============================================================================
# FUNCIÓN PARA PROCESAR VENCIMIENTOS (PARA EL JOB FUTURO)
# ============================================================================
def procesar_vencimientos_puntos():
    """
    Procesa los puntos vencidos de todos los clientes.
    Esta función se ejecutará diariamente mediante un job (APScheduler).
    
    POR AHORA NO SE USA - Preparada para implementación futura.
    
    Returns:
        dict: Resumen del procesamiento
    """
    hoy = datetime.now()
    
    # Buscar transacciones vencidas que aún están ACTIVAS
    transacciones_vencidas = Transacciones_Puntos.query.filter(
        Transacciones_Puntos.estado == 'ACTIVO',
        Transacciones_Puntos.fecha_vencimiento < hoy,
        Transacciones_Puntos.fecha_vencimiento.isnot(None)
    ).all()
    
    total_puntos_vencidos = 0
    clientes_afectados = set()
    
    for transaccion in transacciones_vencidas:
        # Marcar como vencido
        transaccion.estado = 'VENCIDO'
        
        # Crear transacción de vencimiento (para auditoría)
        saldo_antes = calcular_puntos_disponibles(transaccion.documento)['puntos_disponibles']
        
        transaccion_vencimiento = Transacciones_Puntos(
            documento=transaccion.documento,
            tipo_transaccion='VENCIMIENTO',
            puntos=-transaccion.puntos,  # Negativo porque se pierden
            puntos_disponibles_antes=saldo_antes,
            puntos_disponibles_despues=saldo_antes - transaccion.puntos,
            fecha_transaccion=hoy,
            referencia_compra=transaccion.referencia_compra,
            descripcion=f'Vencimiento de puntos de {transaccion.fecha_transaccion.strftime("%Y-%m-%d")}',
            estado='ACTIVO'
        )
        
        db.session.add(transaccion_vencimiento)
        
        total_puntos_vencidos += transaccion.puntos
        clientes_afectados.add(transaccion.documento)
    
    db.session.commit()
    
    return {
        'total_puntos_vencidos': total_puntos_vencidos,
        'clientes_afectados': len(clientes_afectados),
        'transacciones_procesadas': len(transacciones_vencidas)
    }


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def es_compra_disponible_para_puntos(fecha_compra):
    """
    Verifica si una compra ya está disponible para acumular puntos.
    Retorna True si la compra es de un día anterior a HOY.
    """
    from datetime import datetime, timedelta
    
    if not fecha_compra:
        return False
    
    # Convertir a date si es datetime
    if isinstance(fecha_compra, datetime):
        fecha_compra = fecha_compra.date()
    
    # La fecha límite es AYER (las compras de hoy no cuentan)
    fecha_limite = (datetime.now().date() - timedelta(days=1))
    return fecha_compra <= fecha_limite
