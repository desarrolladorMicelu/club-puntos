from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
import pyodbc
from flask_bcrypt import Bcrypt  # Change this import

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'my_session'
app.config['SECRET_KEY'] = 'yLxqdG0BGUft0Ep'
app.config['SQLALCHEMY_BINDS'] = {
    'db2':'postgresql://postgres:WeLZnkiKBsfVFvkaRHWqfWtGzvmSnOUn@viaduct.proxy.rlwy.net:35149/railway'
}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # Initialize Bcrypt with the app

class Usuario(db.Model):
    __bind_key__ = 'db2'
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

@app.route('/recuperar_pass')
def recuperar_pass():
    return render_template('recuperar_pass.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        documento = str(request.form.get('documento'))
        contraseña = str(request.form.get('contraseña'))
        
        # Debugging: Print received values
        print(f"Documento: {documento}")
        print(f"Contraseña recibida: {contraseña}")
        
        # Buscar al usuario por su documento
        user = Usuario.query.filter_by(documento=documento).first()
        
        if user:
            print(f"Usuario encontrado: {user.nombre}")
            print(f"Contraseña almacenada: {user.contraseña}")
        else:
            print("Usuario no encontrado")
        
        # Verifica las credenciales del usuario
        if user and user.contraseña and contraseña:
            try:
                if bcrypt.check_password_hash(user.contraseña, contraseña):
                    session['user_documento'] = user.documento
                    flash(f'Bienvenido, @{user.nombre}. Has iniciado sesión correctamente.', 'success')
                    return redirect(url_for('mhistorialcompras'))
                else:
                    flash('Contraseña incorrecta. Por favor, intenta de nuevo.', 'error')
            except ValueError as e:
                print(f"Error al verificar la contraseña: {str(e)}")
                flash('Error al verificar la contraseña. Por favor, contacta al administrador.', 'error')
        else:
            flash('Credenciales inválidas o incompletas. Por favor, intenta de nuevo.', 'error')
    
    return render_template('login.html')

@app.route('/crear_pass', methods=['GET', 'POST'])
def crear_pass():
    if request.method == 'POST':
        documento = request.form['documento']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']
        habeasdata = 'habeasdata' in request.form

        # Verificar si las contraseñas coinciden
        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('crear_pass'))
        
        # Verificar si la contraseña tiene más de 4 caracteres
        if len(contraseña) <= 4:
            flash('La contraseña debe tener más de 5 caracteres', 'danger')
            return redirect(url_for('crear_pass'))

        # Verificar si la contraseña contiene espacios
        if ' ' in contraseña:
            flash('La contraseña no puede contener espacios', 'danger')
            return redirect(url_for('crear_pass'))

        # Verificar si el documento ya está registrado
        usuario_existente = Usuario.query.filter_by(documento=documento).first()
        if usuario_existente:
            flash('Este documento ya ha sido registrado', 'danger')
            return redirect(url_for('crear_pass'))
        
        try:
            # Intentar crear el usuario
            usuario_creado = crear_usuario(documento, contraseña, habeasdata)
            if usuario_creado:
                flash('Usuario creado exitosamente. <a href="/" class="alert-link">Inicia sesión aquí</a>', 'success')
            else:
                flash('Cédula no registrada. Por favor, registre una compra', 'warning')
            return redirect(url_for('crear_pass'))
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                flash('Este documento ya ha sido registrado', 'danger')
            else:
                flash('Error al crear el usuario: {}'.format(str(e)), 'danger')
            return redirect(url_for('crear_pass'))
    return render_template('crear_pass.html')

def crear_usuario(cedula, contraseña, habeasdata):
    try:
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

        # Consulta SQL con parámetro
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
            AND c.CIUDAD IN ('05001', '11001')
            AND (m.TIPODCTO='FM' OR m.TIPODCTO='FB')
            AND m.VLRVENTA>0
            AND c.NIT = ?
        ORDER BY
            c.NOMBRE;
        """

        # Ejecutar la consulta con el parámetro de cédula
        cursor.execute(query, (cedula,))

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
                    if row.CIUDAD == '05001':
                        ciudad = 'Medellin'
                    elif row.CIUDAD == '11001':
                        ciudad = 'Bogota'
                    else:
                        ciudad = 'No identificado'

                    clave=bcrypt.generate_password_hash(contraseña).decode('utf-8')
                    
                    

                    nuevo_usuario = Usuario(
                        documento=row.NIT.strip() if row.NIT else None,
                        email=row.EMAIL.strip() if row.EMAIL else None,
                        telefono=row.telefono.strip() if row.telefono else None,
                        contraseña=clave,
                        habeasdata=habeasdata,
                        ciudad=ciudad,
                        nombre=row.CLIENTE_NOMBRE.strip() if row.CLIENTE_NOMBRE else None,
                        rango=row.DescripTipoCli.strip() if row.DescripTipoCli else None,
                        estado=True
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
    
@app.route('/mhistorialcompras')
def mhistorialcompras():
    return render_template('mhistorialcompras.html')

@app.route('/mpuntosprincipal')
def mpuntosprincipal():
    return render_template('mpuntosprincipal.html')


if __name__ == '__main__':
    app.run(debug=True)