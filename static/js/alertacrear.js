window.onload = function() {
    // Cierra la alerta automáticamente después de 10 segundos
    setTimeout(function() {
        var flashMessage = document.querySelector('.flash-messages');
        if (flashMessage) {
            flashMessage.style.transition = 'opacity 0.5s ease';
            flashMessage.style.opacity = '0';
            setTimeout(function() {
                flashMessage.style.display = 'none';
            }, 500);
        }
    }, 10000);

    // Permite que el usuario cierre la alerta manualmente
    var closeBtn = document.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.onclick = function() {
            var flashMessage = document.querySelector('.flash-messages');
            if (flashMessage) {
                flashMessage.style.transition = 'opacity 0.5s ease';
                flashMessage.style.opacity = '0';
                setTimeout(function() {
                    flashMessage.style.display = 'none';
                }, 500);
            }
        };
    }
};
