document.addEventListener('DOMContentLoaded', function() {
    const redeemButton = document.getElementById('redeem-button');
    const pointsInput = document.getElementById('points-input');
    const currentPointsDisplay = document.getElementById('current-points');
    const navPointsDisplay = document.getElementById('nav-points');
    const redemptionModal = new bootstrap.Modal(document.getElementById('redemptionModal'), {
        backdrop: 'static',
        keyboard: false
    });
    const redemptionCodeElement = document.getElementById('redemptionCode');
    const redemptionDiscountElement = document.getElementById('redemptionDiscount');
    const closeModalButton = document.getElementById('closeModalButton');
 
    let lastRedemptionCode = null;
    let lastRedemptionDiscount = null;
 
    function updatePointsDisplay(newTotal) {
        currentPointsDisplay.textContent = newTotal;
        navPointsDisplay.textContent = newTotal;
 
        [currentPointsDisplay, navPointsDisplay].forEach(element => {
            element.classList.add('updated');
            setTimeout(() => {
                element.classList.remove('updated');
            }, 1000);
        });
    }
 
    function generateRandomCode() {
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let result = '';
        for (let i = 0; i < 8; i++) {
            result += characters.charAt(Math.floor(Math.random() * characters.length));
        }
        return result;
    }
 
    function validatePoints(points) {
        if (isNaN(points) || points <= 0) {
            alert('Por favor, ingrese un número válido mayor que cero.');
            return false;
        }
 
        const currentPoints = parseInt(currentPointsDisplay.textContent);
        if (points > currentPoints) {
            alert('No tiene suficientes puntos para canjear esta cantidad.');
            return false;
        }
 
        return true;
    }
 
    redeemButton.addEventListener('click', function() {
        const pointsToRedeem = parseInt(pointsInput.value);
 
        if (!validatePoints(pointsToRedeem)) {
            return;
        }
 
        const randomCode = generateRandomCode();
 
        fetch('/redimir_puntos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ points: pointsToRedeem, code: randomCode })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePointsDisplay(data.new_total);
                pointsInput.value = '';
                lastRedemptionCode = data.codigo;
                lastRedemptionDiscount = data.descuento;
                redemptionCodeElement.textContent = lastRedemptionCode;
                redemptionDiscountElement.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(lastRedemptionDiscount);
                redemptionModal.show();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al procesar la solicitud');
        });
    });
 
    closeModalButton.addEventListener('click', function() {
        redemptionModal.hide();
    });
 
    const verCuponButton = document.getElementById('ver-cupon');
    const couponModal = new bootstrap.Modal(document.getElementById('couponModal'), {
        backdrop: 'static',
        keyboard: false
    });
 
    verCuponButton.addEventListener('click', function() {
        fetch('/ver_ultimo_coupon', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error al obtener el último cupón');
            }
        })
        .then(data => {
            if (data.success) {
                lastRedemptionCode = data.codigo;
                lastRedemptionDiscount = data.descuento;
                document.getElementById('couponCode').textContent = lastRedemptionCode;
                couponModal.show();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al obtener el último cupón');
        });
    });
 
    const closeCouponModalButton = document.getElementById('closeCouponModalButton');
    closeCouponModalButton.addEventListener('click', function() {
        couponModal.hide();
    });
 
});