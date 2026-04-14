-- Ejecutar una vez en la misma base PostgreSQL que usa db3 (Railway / plan_beneficios).
-- Equivale a visitar (como admin): GET /admin/init_productos_carrusel

CREATE SCHEMA IF NOT EXISTS plan_beneficios;

CREATE TABLE IF NOT EXISTS plan_beneficios.productos_carrusel (
    id UUID PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    imagen_url VARCHAR(500),
    precio_original INTEGER NOT NULL,
    puntos_requeridos INTEGER NOT NULL,
    codigo_producto VARCHAR(100),
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITHOUT TIME ZONE
);
