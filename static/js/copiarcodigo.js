function copiarCodigo() {
    var codigo = document.getElementById("couponCode").textContent;
    navigator.clipboard.writeText(codigo).then(function() {
        alert("Código copiado al portapapeles: " + codigo);
    }, function(err) {
        console.error('Error al copiar el texto: ', err);
    });
}
 
function copiarCodigo2() {
    var codigo = document.getElementById("redemptionCode").textContent;
    navigator.clipboard.writeText(codigo).then(function() {
        alert("Código copiado al portapapeles: " + codigo);
    }, function(err) {
        console.error('Error al copiar el texto: ', err);
    });
}