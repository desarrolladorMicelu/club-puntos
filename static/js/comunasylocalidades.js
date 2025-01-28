const comunasMedellin = [
    "Popular",
    "Santa Cruz",
    "Manrique",
    "Aranjuez",
    "Castilla",
    "Doce de Octubre",
    "Robledo",
    "Villa Hermosa",
    "La Candelaria",
    "La América",
    "Belén",
    "San Javier",
    "San Cristóbal",
    "El Poblado",
    "Envigado",
    "Guayabal",
    "Caldas",
    "San Antonio de Prado"
];
 
// Listado de localidades para Bogotá
const localidadesBogota = [
    "La Candelaria",
    "Santa Fe",
    "San Cristóbal",
    "Usme",
    "Tunjuelito",
    "Bosa",
    "Kennedy",
    "Fontibón",
    "Engativá",
    "Suba",
    "Barrios Unidos",
    "Teusaquillo",
    "Los Mártires",
    "Chapinero",
    "Usaquén",
    "Rafael Uribe Uribe",
    "Ciudad Bolívar",
    "Sumapaz"
];
const ciudadesColombia = [
    "Medellín", "Bogotá", "Cali", "Barranquilla", "Cartagena",
    "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué",
    "Pasto", "Manizales", "Neiva", "Villavicencio", "Armenia"
];
 
 
document.addEventListener('DOMContentLoaded', function() {
    const ciudadSelect = document.getElementById('ciudad');
    const barrioSelect = document.getElementById('barrio');

    // Poblar el select de ciudades
    ciudadSelect.innerHTML = '<option value="" disabled selected>Seleccione ciudad</option>';
    ciudadesColombia.forEach(ciudad => {
        const option = document.createElement('option');
        option.value = ciudad;
        option.textContent = ciudad;
        ciudadSelect.appendChild(option);
    });

    ciudadSelect.addEventListener('change', function() {
        const ciudad = this.value;
        barrioSelect.innerHTML = '<option value="" disabled selected>Seleccione barrio</option>';

        switch(ciudad) {
            case 'Medellín':
                comunasMedellin.forEach(comuna => {
                    const option = document.createElement('option');
                    option.value = comuna;
                    option.textContent = comuna;
                    barrioSelect.appendChild(option);
                });
                break;
            
            case 'Bogotá':
                localidadesBogota.forEach(localidad => {
                    const option = document.createElement('option');
                    option.value = localidad;
                    option.textContent = localidad;
                    barrioSelect.appendChild(option);
                });
                break;
            
            default:
                // Para cualquier otra ciudad, agregar la ciudad como única opción
                const option = document.createElement('option');
                option.value = ciudad;
                option.textContent = ciudad;
                barrioSelect.appendChild(option);
                break;
        }
    });
});