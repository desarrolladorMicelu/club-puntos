# ============================================================================
# MÓDULO BLACKLIST DE VENDEDORES
# Sistema para inhabilitar puntos a vendedores de OFIMA
# ============================================================================

import pyodbc
import psycopg2
from datetime import datetime, timedelta
import logging
from typing import List, Set, Tuple, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlacklistVendedores:
    """
    Clase para manejar la blacklist de vendedores que no pueden acumular puntos.
    Los vendedores se obtienen de la tabla vmaestrodevendedores en OFIMA (SQL Server).
    """
    
    def __init__(self):
        self.vendedores_blacklist: Set[str] = set()
        self.ultima_actualizacion: Optional[datetime] = None
        
    def obtener_conexion_ofima(self) -> pyodbc.Connection:
        """
        Obtiene conexión a la base de datos OFIMA (SQL Server)
        Usa la misma configuración que la función existente obtener_conexion_bd()
        """
        try:
            conn = pyodbc.connect(
                '''DRIVER={ODBC Driver 18 for SQL Server};'''
                '''SERVER=172.200.231.95;'''
                '''DATABASE=MICELU1;'''
                '''UID=db_read;'''
                '''PWD=mHRL_<='(],#aZ)T"A3QeD;'''
                '''TrustServerCertificate=yes'''
            )
            logger.info("✅ Conexión exitosa a OFIMA (SQL Server)")
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a OFIMA: {e}")
            raise
    
    def consultar_vendedores_ofima(self) -> List[str]:
        """
        Consulta la tabla vmaestrodevendedores en OFIMA para obtener 
        las cédulas de todos los vendedores activos.
        
        Returns:
            List[str]: Lista de cédulas de vendedores
        """
        vendedores = []
        
        try:
            conn = self.obtener_conexion_ofima()
            cursor = conn.cursor()
            
            # Consulta para obtener vendedores activos
            # Asumiendo que la tabla tiene campos como cedula, nombre, estado
            query = """
            SELECT DISTINCT 
                LTRIM(RTRIM(CAST(cedula AS VARCHAR(50)))) as cedula_limpia
            FROM vmaestrodevendedores 
            WHERE cedula IS NOT NULL 
                AND cedula != '' 
                AND cedula != '0'
                AND (estado IS NULL OR estado = 1 OR estado = 'A' OR estado = 'ACTIVO')
            """
            
            cursor.execute(query)
            resultados = cursor.fetchall()
            
            for row in resultados:
                cedula = str(row[0]).strip()
                if cedula and cedula != '0':
                    vendedores.append(cedula)
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Consultados {len(vendedores)} vendedores desde OFIMA")
            
        except Exception as e:
            logger.error(f"❌ Error consultando vendedores en OFIMA: {e}")
            # En caso de error, devolver lista vacía para no bloquear el sistema
            return []
        
        return vendedores
    
    def actualizar_blacklist(self) -> bool:
        """
        Actualiza la blacklist consultando la tabla de vendedores en OFIMA.
        
        Returns:
            bool: True si la actualización fue exitosa
        """
        try:
            logger.info("🔄 Actualizando blacklist de vendedores...")
            
            vendedores = self.consultar_vendedores_ofima()
            
            if vendedores:
                self.vendedores_blacklist = set(vendedores)
                self.ultima_actualizacion = datetime.now()
                
                logger.info(f"✅ Blacklist actualizada: {len(self.vendedores_blacklist)} vendedores")
                logger.info(f"📋 Primeros 5 vendedores: {list(self.vendedores_blacklist)[:5]}")
                
                return True
            else:
                logger.warning("⚠️ No se obtuvieron vendedores, manteniendo blacklist anterior")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando blacklist: {e}")
            return False
    
    def es_vendedor_blacklisted(self, cedula: str) -> bool:
        """
        Verifica si una cédula está en la blacklist de vendedores.
        
        Args:
            cedula (str): Cédula a verificar
            
        Returns:
            bool: True si está en blacklist (no puede acumular puntos)
        """
        if not cedula:
            return False
            
        cedula_limpia = str(cedula).strip()
        
        # Si no hay blacklist cargada, intentar cargarla
        if not self.vendedores_blacklist and not self.ultima_actualizacion:
            logger.info("🔄 Blacklist vacía, cargando por primera vez...")
            self.actualizar_blacklist()
        
        es_vendedor = cedula_limpia in self.vendedores_blacklist
        
        if es_vendedor:
            logger.info(f"🚫 Cédula {cedula_limpia} está en blacklist de vendedores")
        
        return es_vendedor
    
    def necesita_actualizacion(self, horas_maximas: int = 24) -> bool:
        """
        Verifica si la blacklist necesita ser actualizada.
        
        Args:
            horas_maximas (int): Horas máximas sin actualizar
            
        Returns:
            bool: True si necesita actualización
        """
        if not self.ultima_actualizacion:
            return True
            
        tiempo_transcurrido = datetime.now() - self.ultima_actualizacion
        return tiempo_transcurrido > timedelta(hours=horas_maximas)
    
    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas de la blacklist.
        
        Returns:
            dict: Estadísticas de la blacklist
        """
        return {
            'total_vendedores': len(self.vendedores_blacklist),
            'ultima_actualizacion': self.ultima_actualizacion.isoformat() if self.ultima_actualizacion else None,
            'necesita_actualizacion': self.necesita_actualizacion(),
            'primeros_5_vendedores': list(self.vendedores_blacklist)[:5] if self.vendedores_blacklist else []
        }
    
    def limpiar_puntos_vendedores(self, db_session) -> Tuple[int, List[str]]:
        """
        Limpia los puntos acumulados de todos los vendedores en blacklist.
        Esta función debe ejecutarse después de actualizar la blacklist.
        
        Args:
            db_session: Sesión de SQLAlchemy
            
        Returns:
            Tuple[int, List[str]]: (cantidad_limpiados, lista_cedulas_limpiadas)
        """
        if not self.vendedores_blacklist:
            logger.warning("⚠️ No hay vendedores en blacklist para limpiar")
            return 0, []
        
        try:
            # Importar aquí para evitar dependencias circulares
            from app import Puntos_Clientes
            
            cedulas_limpiadas = []
            
            for cedula in self.vendedores_blacklist:
                # Buscar el registro de puntos del vendedor
                puntos_vendedor = db_session.query(Puntos_Clientes).filter_by(documento=cedula).first()
                
                if puntos_vendedor:
                    # Guardar los puntos que tenía antes de limpiar
                    puntos_anteriores = puntos_vendedor.total_puntos
                    puntos_regalo_anteriores = puntos_vendedor.puntos_regalo or 0
                    
                    # Limpiar todos los puntos
                    puntos_vendedor.total_puntos = 0
                    puntos_vendedor.puntos_regalo = 0
                    puntos_vendedor.puntos_redimidos = str(puntos_anteriores + puntos_regalo_anteriores)
                    
                    cedulas_limpiadas.append(cedula)
                    
                    logger.info(f"🧹 Limpiados puntos de vendedor {cedula}: "
                              f"{puntos_anteriores + puntos_regalo_anteriores} puntos removidos")
            
            # Confirmar cambios
            db_session.commit()
            
            logger.info(f"✅ Limpieza completada: {len(cedulas_limpiadas)} vendedores procesados")
            
            return len(cedulas_limpiadas), cedulas_limpiadas
            
        except Exception as e:
            logger.error(f"❌ Error limpiando puntos de vendedores: {e}")
            db_session.rollback()
            return 0, []


# Instancia global de la blacklist
blacklist_vendedores = BlacklistVendedores()


def verificar_blacklist_vendedor(cedula: str) -> bool:
    """
    Función de conveniencia para verificar si una cédula está en blacklist.
    
    Args:
        cedula (str): Cédula a verificar
        
    Returns:
        bool: True si está en blacklist (no puede acumular puntos)
    """
    return blacklist_vendedores.es_vendedor_blacklisted(cedula)


def actualizar_blacklist_periodica() -> bool:
    """
    Función para actualizar la blacklist periódicamente.
    Debe ser llamada por el scheduler.
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    return blacklist_vendedores.actualizar_blacklist()


def limpiar_puntos_vendedores_blacklist(db_session) -> Tuple[int, List[str]]:
    """
    Función para limpiar puntos de vendedores en blacklist.
    
    Args:
        db_session: Sesión de SQLAlchemy
        
    Returns:
        Tuple[int, List[str]]: (cantidad_limpiados, lista_cedulas_limpiadas)
    """
    return blacklist_vendedores.limpiar_puntos_vendedores(db_session)