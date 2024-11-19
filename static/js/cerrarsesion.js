document.addEventListener('DOMContentLoaded', function() {
    // Botón para abrir el modal
    var logoutButton = document.getElementById('customLogoutButton');
    // Modal de Bootstrap
    var logoutModal = new bootstrap.Modal(document.getElementById('customLogoutModal'));
    // Botón "No" dentro del modal
    var cancelLogoutButton = document.getElementById('cancelLogoutButton');
  
    // Si el botón de logout está presente, agrega el evento de click para abrir el modal
    if (logoutButton) {
        logoutButton.addEventListener('click', function (e) {
            e.preventDefault();
            logoutModal.show();
        });
    }
  
    // Si el botón "No" está presente, agrega el evento de click para cerrar el modal
    if (cancelLogoutButton) {
        cancelLogoutButton.addEventListener('click', function () {
            logoutModal.hide(); // Cierra el modal cuando se selecciona "No"
        });
    }
});