/* ============================================================================
   ADMIN POLLA MUNDIAL 2026 - Lógica de cliente
   ============================================================================ */
(function () {
  'use strict';

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function toast(msg, ok) {
    const t = document.getElementById('amToast');
    t.textContent = msg;
    t.className = 'am-toast ' + (ok ? 'ok' : 'err');
    void t.offsetWidth;
    t.classList.add('show');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 3000);
  }

  // ---------- Estado / métricas ----------
  async function cargarEstado() {
    try {
      const resp = await fetch('/admin/api/mundial/estado');
      const data = await resp.json();
      if (!data.success) return;
      document.getElementById('mTotalPartidos').textContent = data.total_partidos;
      document.getElementById('mTerminados').textContent = data.partidos_terminados;
      document.getElementById('mParticipantes').textContent = data.participantes;
      document.getElementById('mPronosticos').textContent = data.total_pronosticos;

      const badge = document.getElementById('mTokenBadge');
      if (data.token_configurado) {
        badge.className = 'am-badge ok';
        badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> API conectada';
      } else {
        badge.className = 'am-badge warn';
        badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Modo DEMO (sin token API)';
      }
    } catch (e) { /* silencioso */ }
  }

  // ---------- Leaderboard completo ----------
  async function cargarLeaderboard() {
    const cont = document.getElementById('amTableWrap');
    cont.innerHTML = '<div class="am-loading"><div class="am-spinner"></div> Cargando tabla…</div>';
    try {
      const resp = await fetch('/admin/api/mundial/leaderboard');
      const data = await resp.json();
      if (!data.success) {
        cont.innerHTML = '<p class="am-error">Error: ' + escapeHtml(data.message || 'desconocido') + '</p>';
        return;
      }
      window._amLeaderboard = data.leaderboard || [];
      renderTabla(window._amLeaderboard);
    } catch (e) {
      cont.innerHTML = '<p class="am-error">Error de conexión al cargar la tabla.</p>';
    }
  }

  function renderTabla(lista) {
    const cont = document.getElementById('amTableWrap');
    if (!lista.length) {
      cont.innerHTML = '<div class="am-empty">Aún no hay participantes con pronósticos.</div>';
      return;
    }

    const filtro = (document.getElementById('amSearch').value || '').toLowerCase().trim();
    const filtrada = filtro
      ? lista.filter(x =>
          (x.nombre || '').toLowerCase().includes(filtro) ||
          (x.documento || '').toLowerCase().includes(filtro))
      : lista;

    let html = `
      <table class="am-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Participante</th>
            <th>Documento</th>
            <th>Puntos</th>
            <th>Exactos</th>
            <th>Resultados</th>
            <th>Pronósticos</th>
          </tr>
        </thead>
        <tbody>`;

    filtrada.forEach(x => {
      const top = x.posicion <= 3 ? ' class="am-top"' : '';
      html += `
        <tr${top}>
          <td class="am-pos">${x.posicion}°</td>
          <td class="am-name">${escapeHtml(x.nombre)}</td>
          <td class="am-doc">${escapeHtml(x.documento)}</td>
          <td class="am-pts">${x.puntos}</td>
          <td>${x.exactos}</td>
          <td>${x.resultados}</td>
          <td>${x.total}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    if (!filtrada.length) html = '<div class="am-empty">Sin resultados para "' + escapeHtml(filtro) + '".</div>';
    cont.innerHTML = html;
  }

  // ---------- Acciones ----------
  async function accion(url, btn, labelOk) {
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando…';
    try {
      const resp = await fetch(url, { method: 'POST' });
      const data = await resp.json();
      if (data.success) {
        let detalle = labelOk;
        if (data.nuevos !== undefined) {
          detalle = `Sincronizado: ${data.nuevos} nuevos, ${data.actualizados} actualizados (${data.fuente}).`;
        } else if (data.partidos_calificados !== undefined) {
          detalle = `Calificados ${data.partidos_calificados} partidos, ${data.pronosticos_calificados} pronósticos.`;
        }
        toast(detalle, true);
        if (data.aviso) toast(data.aviso, false);
        cargarEstado();
        cargarLeaderboard();
      } else {
        toast(data.message || data.error || 'Operación fallida', false);
      }
    } catch (e) {
      toast('Error de conexión', false);
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  }

  // ---------- Exportar CSV ----------
  function exportarCSV() {
    const lista = window._amLeaderboard || [];
    if (!lista.length) { toast('No hay datos para exportar', false); return; }
    let csv = 'Posicion,Participante,Documento,Puntos,Exactos,Resultados,Pronosticos\n';
    lista.forEach(x => {
      csv += [x.posicion, '"' + (x.nombre || '').replace(/"/g, '""') + '"',
              x.documento, x.puntos, x.exactos, x.resultados, x.total].join(',') + '\n';
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'polla_mundial_2026.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  }

  // ---------- Init ----------
  document.addEventListener('DOMContentLoaded', function () {
    cargarEstado();
    cargarLeaderboard();

    document.getElementById('btnSincronizar').addEventListener('click', function () {
      accion('/admin/api/mundial/sincronizar', this, 'Sincronización completa.');
    });
    document.getElementById('btnCalificar').addEventListener('click', function () {
      accion('/admin/api/mundial/calificar', this, 'Calificación completa.');
    });
    document.getElementById('btnRefrescar').addEventListener('click', function () {
      cargarEstado(); cargarLeaderboard(); toast('Tabla actualizada', true);
    });
    document.getElementById('btnExportar').addEventListener('click', exportarCSV);
    document.getElementById('amSearch').addEventListener('input', function () {
      renderTabla(window._amLeaderboard || []);
    });
  });
})();
