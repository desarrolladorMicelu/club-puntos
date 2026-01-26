-- ============================================================================
-- MIGRACIÓN COMPLETA DESDE BASE DE DATOS
-- Ejecutar este script UNA SOLA VEZ para migrar todos los clientes
-- ============================================================================

-- PASO 1: Migrar puntos de compras (ACUMULACION)
-- ============================================================================
INSERT INTO plan_beneficios.transacciones_puntos (
    id,
    documento,
    tipo_transaccion,
    puntos,
    puntos_disponibles_antes,
    puntos_disponibles_despues,
    fecha_transaccion,
    fecha_vencimiento,
    referencia_compra,
    descripcion,
    estado,
    creado_en
)
SELECT 
    gen_random_uuid()::text as id,
    documento,
    'ACUMULACION' as tipo_transaccion,
    total_puntos as puntos,
    0 as puntos_disponibles_antes,
    total_puntos as puntos_disponibles_despues,
    COALESCE(fecha_registro, CURRENT_TIMESTAMP) as fecha_transaccion,
    COALESCE(fecha_registro, CURRENT_TIMESTAMP) + INTERVAL '365 days' as fecha_vencimiento,
    'MIGRACION_COMPRAS' as referencia_compra,
    'Migración: Puntos históricos de compras' as descripcion,
    'ACTIVO' as estado,
    CURRENT_TIMESTAMP as creado_en
FROM plan_beneficios."Puntos_Clientes"
WHERE total_puntos > 0
  AND NOT EXISTS (
      SELECT 1 FROM plan_beneficios.transacciones_puntos t 
      WHERE t.documento = "Puntos_Clientes".documento 
        AND t.tipo_transaccion = 'ACUMULACION'
        AND t.referencia_compra = 'MIGRACION_COMPRAS'
  );

-- Ver cuántos se migraron
SELECT COUNT(*) as "Compras migradas" 
FROM plan_beneficios.transacciones_puntos 
WHERE tipo_transaccion = 'ACUMULACION' 
  AND referencia_compra = 'MIGRACION_COMPRAS';

-- PASO 2: Migrar redenciones (REDENCION)
-- ============================================================================
INSERT INTO plan_beneficios.transacciones_puntos (
    id,
    documento,
    tipo_transaccion,
    puntos,
    puntos_disponibles_antes,
    puntos_disponibles_despues,
    fecha_transaccion,
    fecha_vencimiento,
    referencia_redencion,
    descripcion,
    estado,
    creado_en
)
SELECT 
    gen_random_uuid()::text as id,
    documento,
    'REDENCION' as tipo_transaccion,
    -puntos_utilizados as puntos,  -- Negativo porque se gastaron
    0 as puntos_disponibles_antes,
    0 as puntos_disponibles_despues,
    fecha_canjeo as fecha_transaccion,
    NULL as fecha_vencimiento,
    id::text as referencia_redencion,
    'Migración: Cupón ' || cupon as descripcion,
    'ACTIVO' as estado,
    CURRENT_TIMESTAMP as creado_en
FROM plan_beneficios.historial_beneficio
WHERE puntos_utilizados > 0
  AND NOT EXISTS (
      SELECT 1 FROM plan_beneficios.transacciones_puntos t 
      WHERE t.referencia_redencion = historial_beneficio.id::text
  );

-- Ver cuántos se migraron
SELECT COUNT(*) as "Redenciones migradas" 
FROM plan_beneficios.transacciones_puntos 
WHERE tipo_transaccion = 'REDENCION';

-- PASO 3: Migrar referidos (REFERIDO)
-- ============================================================================
INSERT INTO plan_beneficios.transacciones_puntos (
    id,
    documento,
    tipo_transaccion,
    puntos,
    puntos_disponibles_antes,
    puntos_disponibles_despues,
    fecha_transaccion,
    fecha_vencimiento,
    referencia_referido,
    descripcion,
    estado,
    creado_en
)
SELECT 
    gen_random_uuid()::text as id,
    documento_cliente as documento,
    'REFERIDO' as tipo_transaccion,
    puntos_obtenidos as puntos,
    0 as puntos_disponibles_antes,
    puntos_obtenidos as puntos_disponibles_despues,
    fecha_referido as fecha_transaccion,
    fecha_referido + INTERVAL '365 days' as fecha_vencimiento,
    id::text as referencia_referido,
    'Migración: Referido ' || nombre_referido as descripcion,
    'ACTIVO' as estado,
    CURRENT_TIMESTAMP as creado_en
FROM plan_beneficios.referidos
WHERE puntos_obtenidos > 0
  AND NOT EXISTS (
      SELECT 1 FROM plan_beneficios.transacciones_puntos t 
      WHERE t.referencia_referido = referidos.id::text
  );

-- Ver cuántos se migraron
SELECT COUNT(*) as "Referidos migrados" 
FROM plan_beneficios.transacciones_puntos 
WHERE tipo_transaccion = 'REFERIDO';

-- PASO 4: Migrar puntos de regalo (REGALO)
-- ============================================================================
INSERT INTO plan_beneficios.transacciones_puntos (
    id,
    documento,
    tipo_transaccion,
    puntos,
    puntos_disponibles_antes,
    puntos_disponibles_despues,
    fecha_transaccion,
    fecha_vencimiento,
    referencia_compra,
    descripcion,
    estado,
    creado_en
)
SELECT 
    gen_random_uuid()::text as id,
    documento,
    'REGALO' as tipo_transaccion,
    puntos_regalo as puntos,
    0 as puntos_disponibles_antes,
    puntos_regalo as puntos_disponibles_despues,
    COALESCE(fecha_registro, CURRENT_TIMESTAMP) as fecha_transaccion,
    NULL as fecha_vencimiento,  -- Los regalos NO vencen
    'MIGRACION_REGALOS' as referencia_compra,
    'Migración: Puntos de regalo históricos' as descripcion,
    'ACTIVO' as estado,
    CURRENT_TIMESTAMP as creado_en
FROM plan_beneficios."Puntos_Clientes"
WHERE puntos_regalo > 0
  AND NOT EXISTS (
      SELECT 1 FROM plan_beneficios.transacciones_puntos t 
      WHERE t.documento = "Puntos_Clientes".documento 
        AND t.tipo_transaccion = 'REGALO'
        AND t.referencia_compra = 'MIGRACION_REGALOS'
  );

-- Ver cuántos se migraron
SELECT COUNT(*) as "Regalos migrados" 
FROM plan_beneficios.transacciones_puntos 
WHERE tipo_transaccion = 'REGALO';

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

-- Resumen por tipo de transacción
SELECT 
    tipo_transaccion,
    COUNT(*) as cantidad,
    SUM(puntos) as total_puntos
FROM plan_beneficios.transacciones_puntos
GROUP BY tipo_transaccion
ORDER BY tipo_transaccion;

-- Total de clientes migrados
SELECT COUNT(DISTINCT documento) as "Total clientes migrados"
FROM plan_beneficios.transacciones_puntos;

-- Comparar puntos viejo vs nuevo (primeros 10 clientes)
SELECT 
    pc.documento,
    pc.total_puntos + COALESCE(pc.puntos_regalo, 0) - CAST(COALESCE(pc.puntos_redimidos, '0') AS INTEGER) as puntos_sistema_viejo,
    COALESCE((
        SELECT SUM(puntos) 
        FROM plan_beneficios.transacciones_puntos t 
        WHERE t.documento = pc.documento 
          AND t.estado = 'ACTIVO'
          AND (t.fecha_vencimiento IS NULL OR t.fecha_vencimiento >= CURRENT_DATE)
    ), 0) as puntos_sistema_nuevo,
    COALESCE((
        SELECT SUM(puntos) 
        FROM plan_beneficios.transacciones_puntos t 
        WHERE t.documento = pc.documento 
          AND t.estado = 'ACTIVO'
          AND (t.fecha_vencimiento IS NULL OR t.fecha_vencimiento >= CURRENT_DATE)
    ), 0) - (pc.total_puntos + COALESCE(pc.puntos_regalo, 0) - CAST(COALESCE(pc.puntos_redimidos, '0') AS INTEGER)) as diferencia
FROM plan_beneficios."Puntos_Clientes" pc
WHERE EXISTS (
    SELECT 1 FROM plan_beneficios.transacciones_puntos t 
    WHERE t.documento = pc.documento
)
ORDER BY pc.documento
LIMIT 10;

-- Ver si hay diferencias (NO debería haber ninguna)
SELECT COUNT(*) as "Clientes con diferencias"
FROM plan_beneficios."Puntos_Clientes" pc
WHERE EXISTS (
    SELECT 1 FROM plan_beneficios.transacciones_puntos t 
    WHERE t.documento = pc.documento
)
AND (
    pc.total_puntos + COALESCE(pc.puntos_regalo, 0) - CAST(COALESCE(pc.puntos_redimidos, '0') AS INTEGER)
) != COALESCE((
    SELECT SUM(puntos) 
    FROM plan_beneficios.transacciones_puntos t 
    WHERE t.documento = pc.documento 
      AND t.estado = 'ACTIVO'
      AND (t.fecha_vencimiento IS NULL OR t.fecha_vencimiento >= CURRENT_DATE)
), 0);

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================
-- 
-- 1. Este script es IDEMPOTENTE: Puedes ejecutarlo varias veces sin duplicar datos
-- 2. Usa NOT EXISTS para evitar duplicados
-- 3. Migra TODOS los clientes de una vez
-- 4. Toma aproximadamente 1-5 minutos dependiendo de la cantidad de datos
-- 5. Después de ejecutar, TODOS los clientes estarán migrados
-- 
-- ============================================================================
