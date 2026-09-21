-- Script de referencia para la tabla de la ruleta.
-- No se ejecuta automáticamente ni se toca desde la app.

CREATE TABLE IF NOT EXISTS plan_beneficios.ruleta (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(10) NOT NULL UNIQUE,
    premio TEXT NOT NULL,
    fecha_canjeo TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE plan_beneficios.ruleta IS 'Registro de participaciones en la ruleta de premios';
COMMENT ON COLUMN plan_beneficios.ruleta.documento IS 'Documento del participante';
COMMENT ON COLUMN plan_beneficios.ruleta.premio IS 'Premio asignado';
COMMENT ON COLUMN plan_beneficios.ruleta.fecha_canjeo IS 'Fecha y hora del giro';
