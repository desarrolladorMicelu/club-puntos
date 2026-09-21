(function () {
  const PREMIOS_REALES = [
    'Audífonos de Cable Plug',
    'Cabezote Dual C-USB Miccell',
    'Apple AirPods Serie 2 Premium 1.1',
    'Kit Cargador Inalámbrico Verizon (Carro y Pared)',
    'Diadema Bluetooth VQ-B15 Miccell',
    'PopSocket',
    'Estuche Protector AirPods (Todas las Referencias)',
    'Llaveros',
    'Estuche Protector de Cargador',
    'Estuche Space Transparente (Todas las Referencias)',
    'Cargador Completo C a C Miccell',
    'Diadema Bluetooth VQ-B15 Miccell',
    'Audífonos de Cable Lightning',
    'Audífonos Bluetooth VQ-BH32 Miccell',
    'Apple AirPods Serie 3 Genérico 1.1'
  ];

  const SIGUE_INTENTANDO = 'Sin premio';

  const N_SEGMENTOS = 8;

  const NOMBRE_REGEX = /^[A-Za-zÀ-ÖØ-öø-ÿ\s]+$/;

  const els = {};
  let rotationActual = 0;
  let girando = false;
  let infoStep = 1;

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    els.ring = document.getElementById('rl-ring');
    els.btnGirarModal = document.getElementById('btn-girar-modal');
    els.formOverlay = document.getElementById('rl-form-overlay');
    els.formClose = document.getElementById('rl-form-close');
    els.nombreInput = document.getElementById('rl-nombre');
    els.nombreField = document.getElementById('rl-field-nombre');
    els.docInput = document.getElementById('rl-doc');
    els.docField = document.getElementById('rl-field-documento');
    els.formMsg = document.getElementById('rl-form-msg');

    els.infoBtn = document.getElementById('rl-info-btn');
    els.infoOverlay = document.getElementById('rl-info-overlay');
    els.infoHeading = document.getElementById('rl-info-heading');
    els.infoClose = document.getElementById('rl-info-close');
    els.infoPrev = document.getElementById('rl-info-prev');
    els.infoNext = document.getElementById('rl-info-next');
    els.infoDone = document.getElementById('rl-info-done');
    els.infoPrizesList = document.getElementById('rl-info-prizes');
    els.panelSteps = document.getElementById('rl-panel-steps');
    els.panelStepItems = document.querySelectorAll('#rl-panel-steps .rl-panel-step-item');
    els.panelPanes = document.querySelectorAll('#rl-info-overlay .rl-panel-pane');

    els.wheelSparkles = document.getElementById('rl-wheel-sparkles');

    els.resultOverlay = document.getElementById('rl-result-overlay');
    els.resultClose = document.getElementById('rl-result-close');
    els.resultCloseX = document.getElementById('rl-result-close-x');
    els.resultTitle = document.getElementById('rl-result-title');
    els.resultKicker = document.getElementById('rl-result-kicker');
    els.resultIcon = document.getElementById('rl-result-icon');
    els.resultNombre = document.getElementById('rl-result-nombre');
    els.resultDoc = document.getElementById('rl-result-doc');
    els.resultNote = document.getElementById('rl-result-note');
    els.resultNoteIcon = document.getElementById('rl-result-note-icon');
    els.confettiLayer = document.getElementById('rl-confetti-layer');

    dibujarRuedaSVG();
    pintarListaPremios();

    els.nombreInput.addEventListener('input', () => {
      const limpio = els.nombreInput.value.replace(/[^A-Za-zÀ-ÖØ-öø-ÿ\s]/g, '');
      if (limpio !== els.nombreInput.value) els.nombreInput.value = limpio;
      limpiarError(els.nombreField);
    });
    els.docInput.addEventListener('input', () => {
      const limpio = els.docInput.value.replace(/\D/g, '').slice(0, 10);
      if (limpio !== els.docInput.value) els.docInput.value = limpio;
      limpiarError(els.docField);
    });

    els.hubBoton.addEventListener('click', abrirFormulario);
    els.btnGirarModal.addEventListener('click', enviarGiro);
    els.formClose.addEventListener('click', cerrarFormulario);
    els.formOverlay.addEventListener('click', (event) => {
      if (event.target === els.formOverlay) cerrarFormulario();
    });

    els.infoBtn.addEventListener('click', abrirInfo);
    els.infoClose.addEventListener('click', cerrarInfo);
    els.infoDone.addEventListener('click', cerrarInfo);
    els.infoNext.addEventListener('click', () => irAPasoInfo(2));
    els.infoPrev.addEventListener('click', () => irAPasoInfo(1));

    els.resultClose.addEventListener('click', cerrarResultado);
    els.resultCloseX.addEventListener('click', cerrarResultado);

    // El panel informativo ("¿Cómo funciona?" / "Premios en juego") aparece
    // automáticamente al entrar a la página, deslizándose desde la derecha.
    abrirInfo();
  }

  // ---------------- Rueda SVG ----------------

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const CX = 320;
  const CY = 320;
  const R_CARA = 262;
  const R_TEXTO = 158;

  function puntoPolar(radio, anguloDeg) {
    const rad = ((anguloDeg - 90) * Math.PI) / 180;
    return {
      x: CX + radio * Math.cos(rad),
      y: CY + radio * Math.sin(rad)
    };
  }

  function pathCuna(radio, desde, hasta) {
    const p1 = puntoPolar(radio, desde);
    const p2 = puntoPolar(radio, hasta);
    const largeArc = hasta - desde > 180 ? 1 : 0;
    return `M ${CX} ${CY} L ${p1.x.toFixed(2)} ${p1.y.toFixed(2)} A ${radio} ${radio} 0 ${largeArc} 1 ${p2.x.toFixed(2)} ${p2.y.toFixed(2)} Z`;
  }

  function crearEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
  }

  function crearDefs(svg) {
    const defs = crearEl('defs', {});

    const rimShade = crearEl('radialGradient', { id: 'rl-rim-shade', cx: '38%', cy: '26%', r: '78%' });
    rimShade.appendChild(crearEl('stop', { offset: '0%', 'stop-color': '#fffdf7' }));
    rimShade.appendChild(crearEl('stop', { offset: '62%', 'stop-color': '#f3e8d4' }));
    rimShade.appendChild(crearEl('stop', { offset: '100%', 'stop-color': '#ddcdb1' }));
    defs.appendChild(rimShade);

    const faceLight = crearEl('linearGradient', { id: 'rl-face-light', x1: '24%', y1: '0%', x2: '72%', y2: '100%' });
    faceLight.appendChild(crearEl('stop', { offset: '0%', 'stop-color': '#ffffff', 'stop-opacity': '.22' }));
    faceLight.appendChild(crearEl('stop', { offset: '42%', 'stop-color': '#ffffff', 'stop-opacity': '.02' }));
    faceLight.appendChild(crearEl('stop', { offset: '72%', 'stop-color': '#06272b', 'stop-opacity': '.06' }));
    faceLight.appendChild(crearEl('stop', { offset: '100%', 'stop-color': '#06272b', 'stop-opacity': '.2' }));
    defs.appendChild(faceLight);

    const hubFill = crearEl('radialGradient', { id: 'rl-hub-fill', cx: '34%', cy: '24%', r: '86%' });
    hubFill.appendChild(crearEl('stop', { offset: '0%', 'stop-color': '#1c565c' }));
    hubFill.appendChild(crearEl('stop', { offset: '100%', 'stop-color': '#0c2b30' }));
    defs.appendChild(hubFill);

    const gold = crearEl('linearGradient', { id: 'rl-gold', x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
    gold.appendChild(crearEl('stop', { offset: '0%', 'stop-color': '#f1d79a' }));
    gold.appendChild(crearEl('stop', { offset: '48%', 'stop-color': '#d8b26b' }));
    gold.appendChild(crearEl('stop', { offset: '100%', 'stop-color': '#b98f43' }));
    defs.appendChild(gold);

    svg.appendChild(defs);
  }

  function dibujarRuedaSVG() {
    const svg = crearEl('svg', { viewBox: '0 0 640 640' });
    crearDefs(svg);

    // Aro exterior con degradado suave y líneas de acento en tono teal.
    svg.appendChild(crearEl('circle', { cx: CX, cy: CY, r: 308, fill: 'url(#rl-rim-shade)' }));
    svg.appendChild(crearEl('circle', { cx: CX, cy: CY, r: R_CARA + 20, fill: 'none', stroke: 'url(#rl-gold)', 'stroke-width': '2' }));

    // Grupo que gira: casillas + etiquetas orientadas en forma radial,
    // igual que una ruleta real (el texto "mira" hacia el centro/borde).
    const grupoRueda = crearEl('g', { id: 'rl-rueda-grupo' });
    grupoRueda.style.transformOrigin = `${CX}px ${CY}px`;
    svg.appendChild(crearEl('circle', { cx: CX, cy: CY, r: R_CARA, fill: '#edf8f8' }));

    // Un producto real (abreviado para caber en una sola línea) por cada casilla de premio.
    const muestraPremios = ['PopSocket', 'Llaveros', 'Audífonos Plug', 'AirPods Serie 2'];
    let indicePremio = 0;

    const anchoCuna = 360 / N_SEGMENTOS;
    for (let index = 0; index < N_SEGMENTOS; index++) {
      const desde = index * anchoCuna;
      const hasta = desde + anchoCuna;
      const esPremio = index % 2 === 0;
      const centro = desde + anchoCuna / 2;

      const path = crearEl('path', {
        d: pathCuna(R_CARA, desde, hasta),
        fill: esPremio ? '#28A0A8' : '#edf8f8',
        stroke: '#cda95f',
        'stroke-opacity': '.4',
        'stroke-width': '1.2'
      });
      grupoRueda.appendChild(path);

      const p = puntoPolar(R_TEXTO, centro);
      // Rotación tangencial (perpendicular al radio) para que el texto quede
      // "acostado" en cada casilla, con corrección de 180° para que nunca
      // se lea al revés en la mitad inferior de la rueda.
      let anguloTexto = centro - 90;
      if (centro > 90 && centro < 270) anguloTexto += 180;

      const grupoCasilla = crearEl('g', {
        transform: `translate(${p.x.toFixed(2)}, ${p.y.toFixed(2)}) rotate(${anguloTexto.toFixed(2)})`
      });

      if (esPremio) {
        const nombreProducto = muestraPremios[indicePremio % muestraPremios.length];
        indicePremio += 1;

        const nombreText = crearEl('text', {
          x: 0,
          y: 0,
          'text-anchor': 'middle',
          'dominant-baseline': 'middle',
          fill: '#ffffff',
          'font-family': "'Poppins', Arial, sans-serif",
          'font-weight': '800',
          'font-size': '17'
        });
        nombreText.textContent = nombreProducto;
        grupoCasilla.appendChild(nombreText);
      } else {
        const text = crearEl('text', {
          x: 0,
          y: 0,
          'text-anchor': 'middle',
          'dominant-baseline': 'middle',
          fill: '#123a3f',
          'font-family': "'Poppins', Arial, sans-serif",
          'font-weight': '800',
          'font-size': '17'
        });
        text.textContent = 'Sin premio';
        grupoCasilla.appendChild(text);
      }
      grupoRueda.appendChild(grupoCasilla);
    }
    svg.appendChild(grupoRueda);
    els.grupoRueda = grupoRueda;

    // Brillo superior sutil, sin afectar el fondo del sitio.
    svg.appendChild(crearEl('circle', { cx: CX, cy: CY, r: R_CARA, fill: 'url(#rl-face-light)', style: 'pointer-events:none' }));

    // Hub central: funciona como botón para girar la ruleta.
    const hub = crearEl('g', { id: 'rl-hub-boton', class: 'rl-hub-boton' });
    hub.appendChild(crearEl('circle', { cx: CX, cy: CY + 3, r: 60, fill: '#0d2b2f', 'fill-opacity': '.12' }));
    hub.appendChild(crearEl('circle', { cx: CX, cy: CY, r: 60, fill: 'url(#rl-gold)' }));
    hub.appendChild(crearEl('circle', { cx: CX, cy: CY, r: 55, fill: 'url(#rl-hub-fill)' }));
    hub.appendChild(crearEl('circle', { cx: CX, cy: CY, r: 49, fill: 'none', stroke: '#e2be74', 'stroke-opacity': '.38', 'stroke-width': '1' }));
    const hubTexto = crearEl('text', {
      x: CX,
      y: CY,
      'text-anchor': 'middle',
      'dominant-baseline': 'middle',
      fill: '#ffffff',
      'font-family': "'Poppins', Arial, sans-serif",
      'font-weight': '800',
      'font-size': '20',
      'letter-spacing': '1'
    });
    hubTexto.textContent = 'GIRAR';
    hub.appendChild(hubTexto);
    svg.appendChild(hub);
    els.hubBoton = hub;

    els.ring.innerHTML = '';
    els.ring.appendChild(svg);
  }

  function pintarListaPremios() {
    const html = PREMIOS_REALES.map((label, i) => {
      return `<div class="rl-info-prize"><span class="rl-info-chip">${i + 1}</span>${escapeHtml(label)}</div>`;
    }).join('');
    els.infoPrizesList.innerHTML = html;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ---------------- Modal de datos (nombre + documento) ----------------

  function bloquearFondoModal(activo) {
    document.body.classList.toggle('rl-modal-open', activo);
  }

  function abrirFormulario() {
    if (girando) return;
    if (els.infoOverlay.classList.contains('rl-open')) cerrarInfo();
    limpiarError(els.nombreField);
    limpiarError(els.docField);
    els.formMsg.textContent = '';
    // Deja el botón y el campo de documento listos para un nuevo intento
    // (con otro documento), sin necesidad de recargar la página.
    els.btnGirarModal.disabled = false;
    els.btnGirarModal.textContent = 'Girar ahora';
    els.docInput.value = '';
    els.formOverlay.classList.add('rl-open');
    els.formOverlay.setAttribute('aria-hidden', 'false');
    bloquearFondoModal(true);
  }

  function cerrarFormulario() {
    els.formOverlay.classList.remove('rl-open');
    els.formOverlay.setAttribute('aria-hidden', 'true');
    if (!els.resultOverlay.classList.contains('rl-open')) {
      bloquearFondoModal(false);
    }
  }

  // ---------------- Panel lateral informativo (2 pasos) ----------------

  function abrirInfo() {
    irAPasoInfo(1);
    els.infoOverlay.classList.add('rl-open');
    els.infoOverlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('rl-panel-open');
    els.infoBtn.classList.add('rl-hidden');
  }

  function cerrarInfo() {
    els.infoOverlay.classList.remove('rl-open');
    els.infoOverlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('rl-panel-open');
    els.infoBtn.classList.remove('rl-hidden');
  }

  function irAPasoInfo(paso) {
    infoStep = Math.min(Math.max(paso, 1), 2);

    els.panelPanes.forEach((pane) => {
      pane.classList.toggle('rl-active', Number(pane.dataset.panelStep) === infoStep);
    });
    els.panelStepItems.forEach((item, i) => {
      const numero = i + 1;
      item.classList.toggle('rl-step-current', numero === infoStep);
      item.classList.toggle('rl-step-done', numero < infoStep);
    });
    els.panelSteps.classList.toggle('rl-step-2', infoStep === 2);
    els.infoHeading.textContent = infoStep === 1 ? '¿Cómo funciona?' : 'Premios en juego';
  }

  // ---------------- Validación y envío ----------------

  function marcarError(field, mensaje) {
    field.classList.add('rl-invalid');
    field.querySelector('.rl-error').textContent = mensaje;
  }

  function limpiarError(field) {
    field.classList.remove('rl-invalid');
    field.querySelector('.rl-error').textContent = '';
  }

  function validarNombre() {
    limpiarError(els.nombreField);
    const nombre = els.nombreInput.value.trim();
    if (!nombre || !NOMBRE_REGEX.test(nombre)) {
      marcarError(els.nombreField, 'Ingresa un nombre válido (solo letras y espacios).');
      return false;
    }
    return true;
  }

  function validarDocumento() {
    limpiarError(els.docField);
    const documento = els.docInput.value.trim();
    if (!/^\d{6,10}$/.test(documento)) {
      marcarError(els.docField, 'El documento debe tener entre 6 y 10 dígitos.');
      return false;
    }
    return true;
  }

  async function enviarGiro() {
    if (girando) return;

    els.formMsg.textContent = '';

    if (!validarNombre()) return;
    if (!validarDocumento()) return;

    // El nombre se usa solo para mostrarlo en el resultado; nunca se envía al backend.
    const nombre = els.nombreInput.value.trim();
    const documento = els.docInput.value.trim();

    els.btnGirarModal.disabled = true;
    els.btnGirarModal.textContent = 'Girando...';

    try {
      const response = await fetch('/api/ruleta/girar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documento })
      });
      const data = await response.json();

      if (!response.ok || !data.success) {
        els.formMsg.textContent = data.message || 'No se pudo completar el giro.';
        marcarError(els.docField, data.message || 'No se pudo completar el giro.');
        els.btnGirarModal.disabled = false;
        els.btnGirarModal.textContent = 'Girar ahora';
        return;
      }

      cerrarFormulario();
      girarRuleta(data.premio || SIGUE_INTENTANDO, nombre, documento);
    } catch (error) {
      els.formMsg.textContent = 'Ocurrió un error al procesar el giro.';
      els.btnGirarModal.disabled = false;
      els.btnGirarModal.textContent = 'Girar ahora';
    }
  }

  // ---------------- Giro y revelación ----------------

  function girarRuleta(premio, nombre, documento) {
    girando = true;

    const esPremio = premio !== SIGUE_INTENTANDO;
    const candidatos = [];
    for (let i = 0; i < N_SEGMENTOS; i++) {
      if ((i % 2 === 0) === esPremio) candidatos.push(i);
    }
    const landIndex = candidatos[Math.floor(Math.random() * candidatos.length)];
    const anchoCuna = 360 / N_SEGMENTOS;
    const centroCuna = landIndex * anchoCuna + anchoCuna / 2;

    const vueltas = 6;
    const objetivoMod = ((360 - centroCuna) % 360 + 360) % 360;
    const delta = ((objetivoMod - rotationActual) % 360 + 360) % 360;
    rotationActual += delta + 360 * vueltas;

    els.grupoRueda.style.transform = `rotate(${rotationActual}deg)`;

    lanzarChispasRueda();

    setTimeout(() => {
      girando = false;
      mostrarResultado(premio, nombre, documento);
    }, 3450);
  }

  // Trazos y estrellitas que titilan alrededor de la rueda mientras gira.
  const CHISPA_LINEA = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 15 15 5"/></svg>';
  const CHISPA_ESTRELLA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 13.8 9 21 9.5 15.3 14 17 21 12 17 7 21 8.7 14 3 9.5 10.2 9Z"/></svg>';

  function lanzarChispasRueda() {
    els.wheelSparkles.innerHTML = '';
    const total = 14;

    for (let i = 0; i < total; i++) {
      const angulo = Math.random() * 360;
      const radio = 42 + Math.random() * 14; // % desde el centro, alrededor del borde
      const rad = (angulo * Math.PI) / 180;
      const x = 50 + radio * Math.cos(rad);
      const y = 50 + radio * Math.sin(rad);
      const esEstrella = Math.random() < 0.4;

      const chispa = document.createElement('span');
      chispa.className = 'rl-sparkle ' + (esEstrella ? 'rl-sparkle-star' : 'rl-sparkle-line');
      chispa.style.left = x.toFixed(1) + '%';
      chispa.style.top = y.toFixed(1) + '%';
      chispa.style.setProperty('--rl-sp-rot', Math.round(Math.random() * 360) + 'deg');
      chispa.style.animationDuration = 1.1 + Math.random() * 1.3 + 's';
      chispa.style.animationDelay = Math.random() * 2.6 + 's';
      chispa.style.animationIterationCount = 'infinite';
      chispa.innerHTML = esEstrella ? CHISPA_ESTRELLA : CHISPA_LINEA;
      els.wheelSparkles.appendChild(chispa);
    }
  }

  // Íconos sutiles (trazo fino, sin relleno) para acompañar el resultado.
  const ICONO_TROFEO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 5H4a2 2 0 0 0 0 4h1"/><path d="M17 5h3a2 2 0 0 1 0 4h-1"/></svg>';
  const ICONO_TRISTE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.5 15.5c1-1.2 2.2-1.8 3.5-1.8s2.5.6 3.5 1.8"/><path d="M9 9.5h.01"/><path d="M15 9.5h.01"/></svg>';
  const ICONO_CORAZON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.5s-7-4.4-9.3-8.7C1.2 8.6 3 5.5 6.2 5.2c1.9-.2 3.6.8 4.8 2.4 1.2-1.6 2.9-2.6 4.8-2.4 3.2.3 5 3.4 3.5 6.6-2.3 4.3-9.3 8.7-9.3 8.7Z"/></svg>';

  function mostrarResultado(premio, nombre, documento) {
    const gano = premio !== SIGUE_INTENTANDO;

    els.resultKicker.textContent = gano ? '¡Felicidades!' : 'Resultado';
    els.resultIcon.innerHTML = gano ? ICONO_TROFEO : ICONO_TRISTE;
    els.resultNoteIcon.innerHTML = ICONO_CORAZON;
    els.resultTitle.textContent = gano ? premio : SIGUE_INTENTANDO;
    els.resultNombre.textContent = nombre;
    els.resultDoc.textContent = 'Documento: ' + documento;
    els.resultNote.textContent = gano
      ? 'Un asesor validará tu premio con tu número de documento.'
      : 'Esta vez no ganaste, pero gracias por participar.';

    els.resultOverlay.classList.add('rl-open');
    els.resultOverlay.setAttribute('aria-hidden', 'false');
    bloquearFondoModal(true);

    // rl-play dispara toda la secuencia de animación (caja, luz, card) vía CSS.
    requestAnimationFrame(() => {
      els.resultOverlay.classList.add('rl-play');
    });

    if (gano) {
      setTimeout(lanzarConfetti, 3350);
    }
  }

  function cerrarResultado() {
    els.resultOverlay.classList.remove('rl-open', 'rl-play');
    els.resultOverlay.setAttribute('aria-hidden', 'true');
    els.confettiLayer.innerHTML = '';
    if (!els.formOverlay.classList.contains('rl-open')) {
      bloquearFondoModal(false);
    }
  }

  function lanzarConfetti() {
    const colores = ['#d8b26b', '#0f6f74', '#f1d79a', '#22b6ba', '#b98f43'];
    const total = 60;
    els.confettiLayer.innerHTML = '';

    for (let i = 0; i < total; i++) {
      const piece = document.createElement('span');
      piece.className = 'rl-confetti-piece';
      piece.style.left = Math.random() * 100 + '%';
      piece.style.background = colores[Math.floor(Math.random() * colores.length)];
      piece.style.animationDuration = 3.2 + Math.random() * 2 + 's';
      piece.style.animationDelay = Math.random() * 1.2 + 's';
      els.confettiLayer.appendChild(piece);
    }
  }
})();
