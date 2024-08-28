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
bcrypt = Bcrypt(app)  

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
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_documento' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/recuperar_pass')
def recuperar_pass():
    return render_template('recuperar_pass.html')

@app.route('/miperfil')
def miperfil():
    return render_template('miperfil.html')
#---------------------------------------------------LOGIN-------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        documento = str(request.form.get('documento'))
        contraseña = str(request.form.get('contraseña'))
        user = Usuario.query.filter_by(documento=documento).first()
        # Verifica las credenciales del usuario
        if user and user.contraseña and contraseña:
            try:
                if bcrypt.check_password_hash(user.contraseña, contraseña):
                    session['user_documento'] = user.documento
                    flash(f'Bienvenido, {user.nombre}. Has iniciado sesión correctamente.', 'success')
                    return render_template('login.html', redirect_url=url_for('mhistorialcompras'))
                else:
                    flash('Contraseña incorrecta. Por favor, intenta de nuevo.', 'error')
            except ValueError as e:
                print(f"Error al verificar la contraseña: {str(e)}")
                flash('Error al verificar la contraseña. Por favor, contacta al administrador.', 'error')
        else:
            flash('Documento o Contraseña Incorrectos. Por favor, intenta de nuevo.', 'error')
    return render_template('login.html')

@app.route('/mhistorialcompras')
@login_required
def mhistorialcompras():
    documento = session.get('user_documento')
    
    if not documento:
        return redirect(url_for('login'))
    
    try:
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

        # Verificar si el cliente existe
        check_query = """
        SELECT COUNT(*) as count
        FROM Clientes c
        WHERE c.HABILITADO = 'S' AND c.NIT = ?
        """
        cursor.execute(check_query, documento)
        count = cursor.fetchone().count
        # Consulta principal
        query = """
        SELECT
            m.NOMBRE AS PRODUCTO_NOMBRE,
            m.VLRVENTA,
            m.FHCOMPRA
        FROM
            Clientes c
        JOIN
            V_CLIENTES_FAC vc ON c.NOMBRE = vc.NOMBRE
        JOIN
            Mvtrade m ON vc.tipoDcto = m.Tipodcto AND vc.nroDcto = m.NRODCTO
        WHERE
            c.HABILITADO = 'S'
            AND c.NIT = ?
        ORDER BY
            m.FHCOMPRA DESC;
        """
 
        cursor.execute(query, documento)
        results = cursor.fetchall()
        historial = []
        for row in results:
            historial.append({
                "PRODUCTO_NOMBRE": row.PRODUCTO_NOMBRE,
                "VLRVENTA": float(row.VLRVENTA),
                "FHCOMPRA": row.FHCOMPRA.strftime('%Y-%m-%d')
            })
 
        cursor.close()
        conn.close()
 
        if not historial:
            flash('No se encontró historial de compras para este usuario.', 'info')
        
        return render_template('mhistorialcompras.html', historial=historial)
 
    except pyodbc.Error as e:
        print("Error al conectarse a la base de datos:", e)
        flash('Error al obtener el historial de compras. Por favor, intente más tarde.', 'error')
        return render_template('mhistorialcompras.html', historial=[])

@app.route('/mpuntosprincipal')
@login_required
def mpuntosprincipal():
    return render_template('mpuntosprincipal.html')

@app.route('/quesonpuntos')
@login_required
def quesonpuntos():
    return render_template('puntos.html')

@app.route('/homepuntos')
@login_required
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
    
#------------------funciones para traer informacion del carrusel------------------------------------------------

def get_product_info(product_id):
    products = {
        1: {
            'nombre': 'Iphone 12',
            'precio': 1450000,
            'puntos': 500,
            'descripcion': 'El Apple iPhone 15 conserva el diseño de la generación anterior pero incorpora el Dynamic Island ',
            'image': 'images/iphone12.png'
        },
        2: {
            'nombre': 'Diadema -Smartpods',
            'precio': 999000,
            'puntos': 800 ,
            'descripcion': 'Diadema bluetooth SmartPods Pro A+  con diseño ergonómico, con la posibilidad de adaptarse a la cabeza',
            'image': 'images/diadema.png'
        },
        3: {
            'nombre': 'Airpods Pro 2 Alta Calidad (Genéricos 1.1)',
            'precio': 675000,
            'puntos': 350 ,
            'descripcion': '',
            'image': 'images/airpods.jpg'
        },
        4: {
            'nombre': 'Smartwatch',
            'precio': 210000,
            'puntos': 150 ,
            'descripcion': '',
            'image': 'images/smartwatch.png'
        }
        # Añade más productos aquí
    }
    return products.get(product_id)
    #----------------------------------- mpuntosprincipal-----------------------------
@app.route('/infobeneficios/<int:product_id>')
def infobeneficios(product_id):
    # Aquí deberías tener una función que obtenga la información del producto
    # basándose en el product_id. Por ejemplo:
    product = get_product_info(product_id)

    
    return render_template("infobeneficios.html", product=product)
    


if __name__ == '__main__':
    app.run(debug=True)