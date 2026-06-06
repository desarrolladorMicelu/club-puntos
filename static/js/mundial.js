/* ============================================================================
   POLLA MUNDIALISTA 2026 · Lógica de cliente (rediseño "estadio tricolor")
   ============================================================================ */
(function () {
  'use strict';

  let partidos = [];
  let filtroActual = 'todos';

  const $matches = document.getElementById('munMatches');
  const $loader = document.getElementById('munLoader');
  const $empty = document.getElementById('munEmpty');
  const $aviso = document.getElementById('munAviso');
  const $filters = document.getElementById('munFilters');

  // -------------------------------------------------- utils
  function toast(msg, tipo) {
    const t = document.getElementById('munToast');
    t.textContent = msg;
    t.className = 'toast ' + (tipo || 'ok');
    void t.offsetWidth;
    t.classList.add('show');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 2800);
  }

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatFecha(iso) {
    if (!iso) return 'Fecha por confirmar';
    try {
      const d = new Date(iso);
      const s = d.toLocaleString('es-CO', {
        weekday: 'short', day: 'numeric', month: 'short',
        hour: '2-digit', minute: '2-digit'
      });
      return s.charAt(0).toUpperCase() + s.slice(1);
    } catch (e) { return 'Fecha por confirmar'; }
  }

  function crestHtml(crest, tla) {
    const code = (tla || '??').slice(0, 3);
    if (crest) {
      return `<img src="${escapeHtml(crest)}" alt="${escapeHtml(code)}"
                 onerror="this.parentNode.innerHTML='<div class=\\'flag-fallback\\'>${escapeHtml(code)}</div>'">`;
    }
    return `<div class="flag-fallback">${escapeHtml(code)}</div>`;
  }

  // Confeti tricolor (al guardar / marcador exacto)
  function confeti() {
    const cont = document.getElementById('confetti');
    const colores = ['#FFD400', '#0033A0', '#E4002B', '#ffffff'];
    for (let i = 0; i < 40; i++) {
      const c = document.createElement('i');
      c.style.left = Math.random() * 100 + 'vw';
      c.style.background = colores[i % colores.length];
      c.style.animationDuration = (1.6 + Math.random() * 1.4) + 's';
      c.style.animationDelay = (Math.random() * 0.3) + 's';
      c.style.transform = `scale(${0.6 + Math.random()})`;
      cont.appendChild(c);
      setTimeout(() => c.remove(), 3200);
    }
  }

  // -------------------------------------------------- estado UI
  function statusChip(p) {
    if (p.estado === 'FINISHED') return { cls: 'final', txt: 'Final' };
    if (p.estado === 'IN_PLAY' || p.estado === 'PAUSED') return { cls: 'vivo', txt: 'En vivo' };
    if (p.abierto) return { cls: 'abierto', txt: 'Abierto' };
    return { cls: 'cerrado', txt: 'Cerrado' };
  }

  function tituloFase(p) {
    if (p.grupo) return p.grupo;
    if (p.stage) return p.stage.replace(/_/g, ' ');
    return 'Mundial';
  }

  // -------------------------------------------------- render tarjeta
  function renderMatch(p) {
    const chip = statusChip(p);
    const pron = p.pronostico;

    // Centro del tablero: marcador real o VS
    let centro;
    if (p.estado === 'FINISHED') {
      centro = `<div class="scoreline">${p.goles_local}<i>:</i>${p.goles_visitante}</div>`;
    } else {
      centro = `<div class="match__vs">VS</div>`;
    }

    // Cuerpo bajo la perforación
    let cuerpo = '';

    if (p.estado === 'FINISHED') {
      if (pron && pron.calificado) {
        const tipo = (pron.tipo_acierto || 'FALLO').toLowerCase();
        if (tipo === 'exacto') {
          cuerpo = `<div class="resultado exacto">
              <div class="r-tag">¡Marcador exacto!</div>
              <div class="r-pts">+${pron.puntos_obtenidos} pts</div>
              <span class="r-pred">Tu pronóstico fue ${pron.pred_local} : ${pron.pred_visitante}</span>
            </div>`;
        } else if (tipo === 'resultado') {
          cuerpo = `<div class="resultado resultado-acierto">
              <div class="r-tag">Acertaste el resultado</div>
              <div class="r-pts">+${pron.puntos_obtenidos} pts</div>
              <span class="r-pred">Tu pronóstico fue ${pron.pred_local} : ${pron.pred_visitante}</span>
            </div>`;
        } else {
          cuerpo = `<div class="resultado fallo">
              <div class="r-tag">Esta no era</div>
              <div class="r-pts">0 pts</div>
              <span class="r-pred">Tu pronóstico fue ${pron.pred_local} : ${pron.pred_visitante}</span>
            </div>`;
        }
      } else if (pron) {
        cuerpo = `<div class="resultado resultado-acierto">
            <div class="r-tag">Calculando…</div>
            <span class="r-pred">Tu pronóstico: ${pron.pred_local} : ${pron.pred_visitante}</span>
          </div>`;
      } else {
        cuerpo = `<div class="resultado bloqueado">
            <div class="r-tag">No participaste</div>
          </div>`;
      }
    } else if (p.abierto) {
      const vl = pron ? pron.pred_local : 0;
      const vv = pron ? pron.pred_visitante : 0;
      cuerpo = `
        <div class="predict">
          <div class="pcell">
            <button class="step" data-act="up" data-target="pl-${p.api_id}">▲</button>
            <input type="number" min="0" max="99" inputmode="numeric"
                   id="pl-${p.api_id}" value="${vl}" aria-label="Goles ${escapeHtml(p.equipo_local)}">
            <button class="step" data-act="down" data-target="pl-${p.api_id}">▼</button>
          </div>
          <span class="predict__dash">:</span>
          <div class="pcell">
            <button class="step" data-act="up" data-target="pv-${p.api_id}">▲</button>
            <input type="number" min="0" max="99" inputmode="numeric"
                   id="pv-${p.api_id}" value="${vv}" aria-label="Goles ${escapeHtml(p.equipo_visitante)}">
            <button class="step" data-act="down" data-target="pv-${p.api_id}">▼</button>
          </div>
        </div>
        <button class="btn-save" data-id="${p.api_id}">
          ${pron ? 'Actualizar marcador' : 'Lanzar pronóstico'}
        </button>
        ${pron ? `<div class="pred-saved"><i class="fa-solid fa-circle-check"></i> Guardado: ${pron.pred_local} : ${pron.pred_visitante}</div>` : ''}`;
    } else {
      if (pron) {
        cuerpo = `<div class="resultado bloqueado">
            <div class="r-tag"><i class="fa-solid fa-lock"></i> Pronóstico bloqueado</div>
            <span class="r-pred">Tu pronóstico: ${pron.pred_local} : ${pron.pred_visitante}</span>
          </div>`;
      } else {
        cuerpo = `<div class="resultado bloqueado">
            <div class="r-tag"><i class="fa-solid fa-lock"></i> Cerrado · sin pronóstico</div>
          </div>`;
      }
    }

    return `
      <article class="match" data-estado="${chip.cls}">
        <div class="match__top">
          <span class="match__grupo">${escapeHtml(tituloFase(p))}</span>
          <span class="status status--${chip.cls}">${chip.txt}</span>
        </div>
        <div class="match__board">
          <div class="team">
            <div class="team__crest">${crestHtml(p.equipo_local_crest, p.equipo_local_tla)}</div>
            <div class="team__name">${escapeHtml(p.equipo_local)}</div>
            <div class="team__tla">${escapeHtml(p.equipo_local_tla || '')}</div>
          </div>
          <div class="match__center">${centro}</div>
          <div class="team">
            <div class="team__crest">${crestHtml(p.equipo_visitante_crest, p.equipo_visitante_tla)}</div>
            <div class="team__name">${escapeHtml(p.equipo_visitante)}</div>
            <div class="team__tla">${escapeHtml(p.equipo_visitante_tla || '')}</div>
          </div>
        </div>
        <div class="match__time"><i class="fa-regular fa-calendar"></i> ${formatFecha(p.fecha)}</div>
        <div class="match__perf"></div>
        <div class="match__pred">${cuerpo}</div>
      </article>`;
  }

  // -------------------------------------------------- filtros
  function aplicaFiltro(p) {
    if (filtroActual === 'todos') return true;
    if (filtroActual === 'abiertos') return p.abierto && p.estado !== 'FINISHED';
    if (filtroActual === 'finalizados') return p.estado === 'FINISHED';
    if (filtroActual === 'mis') return !!p.pronostico;
    return true;
  }

  function render() {
    const lista = partidos.filter(aplicaFiltro);
    if (!lista.length) {
      $matches.innerHTML = '';
      $empty.style.display = 'block';
      return;
    }
    $empty.style.display = 'none';
    $matches.innerHTML = lista.map(renderMatch).join('');
    bindCard();
  }

  // -------------------------------------------------- interacción tarjeta
  function bindCard() {
    // steppers ▲▼
    $matches.querySelectorAll('.step').forEach(btn => {
      btn.addEventListener('click', function () {
        const inp = document.getElementById(this.dataset.target);
        if (!inp) return;
        let v = parseInt(inp.value, 10);
        if (isNaN(v)) v = 0;
        v = this.dataset.act === 'up' ? Math.min(99, v + 1) : Math.max(0, v - 1);
        inp.value = v;
      });
    });

    // guardar
    $matches.querySelectorAll('.btn-save').forEach(btn => {
      btn.addEventListener('click', () => guardar(btn));
    });
  }

  async function guardar(btn) {
    const id = btn.dataset.id;
    const pl = document.getElementById('pl-' + id).value;
    const pv = document.getElementById('pv-' + id).value;
    const nl = parseInt(pl, 10);
    const nv = parseInt(pv, 10);

    if (isNaN(nl) || isNaN(nv) || nl < 0 || nv < 0) {
      toast('Marcador inválido', 'err');
      return;
    }

    btn.disabled = true;
    const original = btn.textContent;
    btn.textContent = 'Enviando…';
    try {
      const resp = await fetch('/api/mundial/pronosticar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_id: parseInt(id, 10), pred_local: nl, pred_visitante: nv })
      });
      const data = await resp.json();
      if (data.success) {
        toast('¡Pronóstico registrado! ⚽', 'ok');
        confeti();
        const p = partidos.find(x => String(x.api_id) === String(id));
        if (p) {
          p.pronostico = Object.assign({}, p.pronostico, {
            pred_local: nl, pred_visitante: nv, calificado: false
          });
        }
        render();
      } else {
        toast(data.message || 'No se pudo guardar', 'err');
        btn.disabled = false;
        btn.textContent = original;
      }
    } catch (e) {
      toast('Error de conexión', 'err');
      btn.disabled = false;
      btn.textContent = original;
    }
  }

  // -------------------------------------------------- mi posición
  async function cargarMiPosicion() {
    try {
      const resp = await fetch('/api/mundial/mi_posicion');
      const data = await resp.json();
      if (!data.success) return;

      const mp = data.mi_posicion;
      document.getElementById('statPuntos').textContent = mp.puntos;
      document.getElementById('statPosicion').innerHTML =
        mp.posicion ? (mp.posicion + ' <small>/ ' + data.total_participantes + '</small>') : '—';
      document.getElementById('statExactos').textContent = mp.exactos;
      document.getElementById('statAciertos').textContent = (mp.exactos + mp.resultados);

      const podio = document.getElementById('podio');
      if (data.top3 && data.top3.length) {
        const medallas = ['1', '2', '3'];
        const clases = ['p1', 'p2', 'p3'];
        // reordenar visualmente 2-1-3
        const orden = [];
        if (data.top3[1]) orden.push({ d: data.top3[1], i: 1 });
        if (data.top3[0]) orden.push({ d: data.top3[0], i: 0 });
        if (data.top3[2]) orden.push({ d: data.top3[2], i: 2 });
        podio.innerHTML = orden.map(o => `
          <div class="podio-item ${clases[o.i]}">
            <div class="medal">${medallas[o.i]}°</div>
            <div class="nombre">${escapeHtml(o.d.nombre)}</div>
            <div class="pts">${o.d.puntos} PTS</div>
          </div>`).join('');
      } else {
        podio.innerHTML = '';
      }
    } catch (e) { /* silencioso */ }
  }

  // -------------------------------------------------- carga inicial
  async function cargarPartidos() {
    try {
      const resp = await fetch('/api/mundial/partidos');
      const data = await resp.json();
      $loader.style.display = 'none';
      if (!data.success) { $empty.style.display = 'block'; return; }
      partidos = data.partidos || [];
      render();
    } catch (e) {
      $loader.style.display = 'none';
      $aviso.style.display = 'flex';
      $aviso.querySelector('span').textContent = 'No se pudieron cargar los partidos. Intenta recargar.';
    }
  }

  // -------------------------------------------------- eventos
  if ($filters) {
    $filters.addEventListener('click', function (e) {
      const btn = e.target.closest('.filtro');
      if (!btn) return;
      $filters.querySelectorAll('.filtro').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filtroActual = btn.dataset.filtro;
      render();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    cargarPartidos();
    cargarMiPosicion();
    setInterval(cargarMiPosicion, 60000);
  });
})();
