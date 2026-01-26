-- ============================================================================
-- MIGRACIÓN: Sistema de Puntos con Auditoría y Vencimiento
-- ============================================================================
-- Este script crea la nueva tabla y agrega campos a las existentes
-- Ejecutar en PostgreSQL (db3)

-- ============================================================================
-- 1. CREAR TABLA DE TRANSACCIONES DE PUNTOS
-- ============================================================================
CREATE TABLE IF NOT EXISTS plan_beneficios.transacciones_puntos (
    id VARCHAR(36) PRIMARY KEY,
    documento VARCHAR(50) NOT NULL,
    
    -- Tipo de transacción
    tipo_transaccion VARCHAR(20) NOT NULL CHECK (tipo_transaccion IN ('ACUMULACION', 'REDENCION', 'VENCIMIENTO', 'REGALO', 'REFERIDO')),
    
    -- Puntos (positivo para acumulación, negativo para redención/vencimiento)
    puntos INTEGER NOT NULL,
    
    -- Saldos (para auditoría)
    puntos_disponibles_antes INTEGER NOT NULL DEFAULT 0,
    puntos_disponibles_despues INTEGER NOT NULL DEFAULT 0,
    
    -- Fechas
    fecha_transaccion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento TIMESTAMP NULL,
    
    -- Referencias para trazabilidad
    referencia_compra VARCHAR(100) NULL,
    referencia_redencion VARCHAR(36) NULL,
    referencia_referido VARCHAR(36) NULL,
    
    -- Descripción legible
    descripcion VARCHAR(500) NULL,
    
    -- Estado de la transacción
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'VENCIDO', 'USADO')),
    
    -- Metadata
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NULL
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_transacciones_documento ON plan_beneficios.transacciones_puntos(documento);
CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON plan_beneficios.transacciones_puntos(fecha_transaccion);
CREATE INDEX IF NOT EXISTS idx_transacciones_estado ON plan_beneficios.transacciones_puntos(estado);
CREATE INDEX IF NOT EXISTS idx_transacciones_vencimiento ON plan_beneficios.transacciones_puntos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_transacciones_tipo ON plan_beneficios.transacciones_puntos(tipo_transaccion);

-- Índice compuesto para consultas de puntos disponibles
CREATE INDEX IF NOT EXISTS idx_transacciones_disponibles 
ON plan_beneficios.transacciones_puntos(documento, estado, fecha_vencimiento);

-- ============================================================================
-- 2. AGREGAR CAMPOS A TABLA historial_beneficio
-- ============================================================================
-- Agregar campo para fecha de uso real del cupón
ALTER TABLE plan_beneficios.historial_beneficio 
ADD COLUMN IF NOT EXISTS fecha_uso_real TIMESTAMP NULL;

-- Agregar campo para estado del cupón
ALTER TABLE plan_beneficios.historial_beneficio 
ADD COLUMN IF NOT EXISTS estado_cupon VARCHAR(20) DEFAULT 'GENERADO' 
CHECK (estado_cupon IN ('GENERADO', 'USADO', 'EXPIRADO', 'CANCELADO'));

-- Comentarios para documentación
COMMENT ON COLUMN plan_beneficios.historial_beneficio.fecha_uso_real IS 'Fecha en que el cupón fue usado en la tienda (no cuando se generó)';
COMMENT ON COLUMN plan_beneficios.historial_beneficio.estado_cupon IS 'Estado actual del cupón: GENERADO (creado), USADO (aplicado en compra), EXPIRADO (venció), CANCELADO (anulado)';

-- ============================================================================
-- 3. AGREGAR CAMPO A TABLA Puntos_Clientes
-- ============================================================================
-- Agregar campo para timestamp de última actualización
ALTER TABLE plan_beneficios."Puntos_Clientes" 
ADD COLUMN IF NOT EXISTS ultima_actualizacion TIMESTAMP NULL;

COMMENT ON COLUMN plan_beneficios."Puntos_Clientes".ultima_actualizacion IS 'Timestamp del último cálculo de puntos disponibles';

-- ============================================================================
-- 4. COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================================
COMMENT ON TABLE plan_beneficios.transacciones_puntos IS 'Tabla de auditoría completa de todas las transacciones de puntos. Cada movimiento (acumulación, redención, vencimiento) queda registrado aquí.';

COMMENT ON COLUMN plan_beneficios.transacciones_puntos.tipo_transaccion IS 'Tipo de movimiento: ACUMULACION (compra), REDENCION (gasto), VENCIMIENTO (expiración), REGALO (bono), REFERIDO (referencia)';
COMMENT ON COLUMN plan_beneficios.transacciones_puntos.puntos IS 'Cantidad de puntos (positivo para acumulación, negativo para redención/vencimiento)';
COMMENT ON COLUMN plan_beneficios.transacciones_puntos.fecha_vencimiento IS 'Fecha de vencimiento de los puntos (1 año después de acumulación). NULL para puntos que no vencen (regalos)';
COMMENT ON COLUMN plan_beneficios.transacciones_puntos.estado IS 'Estado: ACTIVO (disponible), VENCIDO (expirado), USADO (gastado en redención)';

-- ============================================================================
-- 5. VERIFICACIÓN
-- ============================================================================
-- Verificar que la tabla se creó correctamente
SELECT 
    'transacciones_puntos' as tabla,
    COUNT(*) as registros
FROM plan_beneficios.transacciones_puntos;

-- Verificar que los campos se agregaron
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'plan_beneficios' 
  AND table_name = 'historial_beneficio'
  AND column_name IN ('fecha_uso_real', 'estado_cupon');

SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'plan_beneficios' 
  AND table_name = 'Puntos_Clientes'
  AND column_name = 'ultima_actualizacion';
