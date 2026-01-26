-- ============================================================================
-- ACTUALIZAR ESTADOS Y TIPOS DE TRANSACCIONES
-- ============================================================================

-- 1. Actualizar restricción de estados para incluir 'ANULADO'
ALTER TABLE plan_beneficios.transacciones_puntos 
DROP CONSTRAINT IF EXISTS transacciones_puntos_estado_check;

ALTER TABLE plan_beneficios.transacciones_puntos 
ADD CONSTRAINT transacciones_puntos_estado_check 
CHECK (estado IN ('ACTIVO', 'VENCIDO', 'USADO', 'ANULADO'));

-- 2. Actualizar restricción de tipos para incluir 'CORRECCION'
ALTER TABLE plan_beneficios.transacciones_puntos 
DROP CONSTRAINT IF EXISTS transacciones_puntos_tipo_transaccion_check;

ALTER TABLE plan_beneficios.transacciones_puntos 
ADD CONSTRAINT transacciones_puntos_tipo_transaccion_check 
CHECK (tipo_transaccion IN ('ACUMULACION', 'REDENCION', 'VENCIMIENTO', 'REGALO', 'REFERIDO', 'CORRECCION'));

-- 3. Verificar que se aplicaron correctamente
SELECT constraint_name, check_clause 
FROM information_schema.check_constraints 
WHERE constraint_name IN ('transacciones_puntos_estado_check', 'transacciones_puntos_tipo_transaccion_check');