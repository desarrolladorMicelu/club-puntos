function toggleEdit(field) {
    const displayElement = document.getElementById(`${field}-display`);
    const inputElement = document.getElementById(`${field}-input`);
    const editButton = document.querySelector(`[onclick="toggleEdit('${field}')"]`);
    const saveButton = document.querySelector(`[onclick="saveEdit('${field}')"]`);
 
    displayElement.style.display = 'none';
    inputElement.style.display = 'inline';
    editButton.style.display = 'none';
    saveButton.style.display = 'inline';
}
 
function saveEdit(field) {
    const displayElement = document.getElementById(`${field}-display`);
    const inputElement = document.getElementById(`${field}-input`);
    const editButton = document.querySelector(`[onclick="toggleEdit('${field}')"]`);
    const saveButton = document.querySelector(`[onclick="saveEdit('${field}')"]`);
    const newValue = inputElement.value;
 
    fetch('/editar_perfil', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ field: field, value: newValue }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayElement.textContent = newValue;
            displayElement.style.display = 'inline';
            inputElement.style.display = 'none';
            editButton.style.display = 'inline';
            saveButton.style.display = 'none';
        } else {
            alert('Error al actualizar el perfil');
        }
    });
}