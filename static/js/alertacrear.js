window.onload = function() {
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
