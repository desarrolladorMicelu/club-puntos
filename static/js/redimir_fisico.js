document.addEventListener('DOMContentLoaded', function() {
    const redeemButton1 = document.getElementById('redeem-button1');
    const pointsInput1 = document.getElementById('points-input1');
    const redemptionModal1 = new bootstrap.Modal(document.getElementById('redemptionModal1'), {
        backdrop: 'static',
        keyboard: false
    });
    const redemptionCodeElement1 = document.getElementById('redemptionCode1');
    const redemptionDiscountElement1 = document.getElementById('redemptionDiscount1');
    const redemptionExpirationElement1 = document.getElementById('redemptionExpiration1');
    const closeModalButton1 = document.getElementById('closeModalButton1');
 
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
                    code: code,
                    expiration_minutes: 1
                })
            });
           
            const data = await response.json();
           
            if (data.success) {
                // Guardar el cupón en localStorage con su estado actual
                localStorage.setItem('lastPhysicalCoupon', JSON.stringify({
                    codigo: data.codigo,
                    descuento: data.descuento,
                    expiracion: data.tiempo_expiracion,
                    estado: data.estado  // Guardar el estado correcto
                }));
 
                redemptionCodeElement1.textContent = data.codigo;
                redemptionDiscountElement1.textContent = new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    minimumFractionDigits: 0
                }).format(data.descuento);
                redemptionExpirationElement1.textContent = new Date(data.tiempo_expiracion).toLocaleString();
 
                // Mostrar el modal
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
 
    closeModalButton1.addEventListener('click', function() {
        redemptionModal1.hide();
    });
 
    document.getElementById('ver-cupon1').addEventListener('click', function() {
        const storedCouponData = localStorage.getItem('lastPhysicalCoupon');
       
        if (!storedCouponData) {
            alert('No hay cupón generado recientemente');
            return;
        }
        try {
            const { codigo, descuento, expiracion, estado } = JSON.parse(storedCouponData);
            redemptionCodeElement1.textContent = codigo;
            redemptionDiscountElement1.textContent = new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(descuento);
            redemptionExpirationElement1.textContent = new Date(expiracion).toLocaleString();
            redemptionModal1.show();
        } catch (error) {
            console.error('Error al procesar el cupón almacenado:', error);
            alert('Error al mostrar el cupón');
        }
    });
});
document.getElementById('copyCodeButton1').addEventListener('click', function () {
    const code = document.getElementById('redemptionCode1').textContent;
    navigator.clipboard.writeText(code).then(() => {
        alert('¡Código copiado al portapapeles!');
    });
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