document.addEventListener('DOMContentLoaded', function() {
    const redeemButton1 = document.getElementById('redeem-button1');
    const pointsInput1 = document.getElementById('points-input1');
    const redemptionModal1 = new bootstrap.Modal(document.getElementById('redemptionModal1'));
    const redemptionCodeElement1 = document.getElementById('redemptionCode1');
    const redemptionDiscountElement1 = document.getElementById('redemptionDiscount1');
    const redemptionExpirationElement1 = document.getElementById('redemptionExpiration1');
    const closeModalButton1 = document.getElementById('closeModalButton1');
 
    closeModalButton1.addEventListener('click', function() {
        redemptionModal1.hide();
    });
 
    function generateRandomCode() {
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let result = '';
        for (let i = 0; i < 8; i++) {
            result += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return result;
    }
 
    redeemButton1.addEventListener('click', async function() {
        const points = parseInt(pointsInput1.value);
       
        if (!points || points <= 0) {
            alert('Por favor ingrese una cantidad válida de puntos');
            return;
        }
 
        const code = generateRandomCode();
       
        try {
            const response = await fetch('/redimir_puntos_fisicos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    points: points,
                    code: code
                })
            });
           
            const data = await response.json();
           
            if (data.success) {
                localStorage.setItem('lastPhysicalCoupon', JSON.stringify({
                    codigo: data.codigo,
                    descuento: data.descuento,
                    expiracion: data.tiempo_expiracion
                }));
 
                redemptionCodeElement1.textContent = data.codigo;
                redemptionDiscountElement1.textContent = new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    minimumFractionDigits: 0
                }).format(data.descuento);
                redemptionExpirationElement1.textContent = new Date(data.tiempo_expiracion).toLocaleString();
 
                redemptionModal1.show();
                pointsInput1.value = '';
            } else {
                alert(data.message || 'Error al generar el cupón');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al procesar la solicitud');
        }
    });
 
    document.getElementById('ver-cupon1').addEventListener('click', async function() {
        const storedCouponData = localStorage.getItem('lastPhysicalCoupon');
       
        if (!storedCouponData) {
            alert('No hay cupón generado recientemente');
            return;
        }
       
        try {
            const { codigo } = JSON.parse(storedCouponData);
           
            const response = await fetch('/check_coupon_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code: codigo })
            });
           
            const data = await response.json();
           
            if (!data.valid) {
                alert('El cupón ha expirado');
                localStorage.removeItem('lastPhysicalCoupon');
                return;
            }
           
            redemptionCodeElement1.textContent = data.codigo;
            redemptionDiscountElement1.textContent = new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(data.descuento);
            redemptionExpirationElement1.textContent = new Date(data.expiracion).toLocaleString();
           
            redemptionModal1.show();
        } catch (error) {
            console.error('Error:', error);
            alert('Error al verificar el cupón');
        }
    });
 
    // Verificación de expiración al cargar la página
    function checkCouponExpiration() {
        const storedCouponData = localStorage.getItem('lastPhysicalCoupon');
        if (storedCouponData) {
            const { codigo, expiracion } = JSON.parse(storedCouponData);
            const currentTime = new Date();
            const expirationTime = new Date(expiracion);
           
            if (currentTime > expirationTime) {
                fetch('/check_coupon_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: codigo })
                })
                .then(response => response.json())
                .then(data => {
                    // Opcional: Puedes añadir lógica adicional aquí si es necesario
                    localStorage.removeItem('lastPhysicalCoupon');
                    redemptionModal1.hide();
                    alert('El cupón ha expirado');
                })
                .catch(error => console.error('Error:', error));
            }
        }
    }
 
    // Verificar expiración cada 5 minutos
    setInterval(checkCouponExpiration, 60 * 1000);
 
    // Verificar expiración al cargar la página
    checkCouponExpiration();
 
    if (document.getElementById('copyCodeButton1')) {
        document.getElementById('copyCodeButton1').addEventListener('click', function() {
            const code = document.getElementById('redemptionCode1').textContent;
            navigator.clipboard.writeText(code).then(() => {
                alert('¡Código copiado al portapapeles!');
            });
        });
    }
});
 
// para la tabla de puntos
function mostrarTabla(tab) {
    // Ocultar ambas tablas
    document.getElementById('tabla-virtual').style.display = 'none';
    document.getElementById('tabla-fisica').style.display = 'none';
   
    // Cambiar el color de los botones (opcional, pero visualmente mejora la experiencia)
    document.getElementById('tab-virtual').classList.remove('active');
    document.getElementById('tab-fisica').classList.remove('active');
   
    // Mostrar la tabla seleccionada
    if (tab === 'virtual') {
      document.getElementById('tabla-virtual').style.display = 'block';
      document.getElementById('tab-virtual').classList.add('active');
    } else if (tab === 'fisica') {
      document.getElementById('tabla-fisica').style.display = 'block';
      document.getElementById('tab-fisica').classList.add('active');
    }
  }
