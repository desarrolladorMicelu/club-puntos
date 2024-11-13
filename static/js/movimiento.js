const slider = document.querySelector('.image-track');
let isMoving = true;
let animationId;

function moveSlider() {
  if (!isMoving) {
    cancelAnimationFrame(animationId);
    return;
  }

  slider.style.transform = `translateX(-${(Date.now() / 20) % slider.offsetWidth}px)`;
  animationId = requestAnimationFrame(moveSlider);
}

function resetSliderPosition() {
  const currentTranslate = parseFloat(slider.style.transform.match(/-?[\d.]+/)[0]);
  if (Math.abs(currentTranslate) >= slider.offsetWidth / 2) {
    slider.style.transform = `translateX(${currentTranslate + slider.offsetWidth}px)`;
  }
}

slider.addEventListener('mouseenter', () => {
  isMoving = false;
});

slider.addEventListener('mouseleave', () => {
  isMoving = true;
  moveSlider();
});

// Duplicar el contenido del slider para crear el efecto infinito
slider.innerHTML += slider.innerHTML;

moveSlider();
setInterval(resetSliderPosition, 100); // Revisa y ajusta la posición periódicamente