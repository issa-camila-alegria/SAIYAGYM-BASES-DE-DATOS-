/* SAIYAGYM - comportamiento minimo (sin dependencias, compatible con CSP script-src 'self'). */
(function () {
  // Avisos: se ocultan solos tras unos segundos
  document.querySelectorAll('.aviso').forEach(function (a) {
    setTimeout(function () { a.classList.add('sale'); setTimeout(function () { a.remove(); }, 350); },
      a.classList.contains('error') ? 7000 : 4200);
  });
  // Confirmacion antes de acciones destructivas: <form data-confirmar="mensaje">
  document.querySelectorAll('form[data-confirmar]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      if (!window.confirm(f.getAttribute('data-confirmar'))) { e.preventDefault(); }
    });
  });
  // Evita doble envio de formularios
  document.querySelectorAll('form').forEach(function (f) {
    f.addEventListener('submit', function () {
      if (f.dataset.enviando) { return; }
      f.dataset.enviando = '1';
      f.querySelectorAll('button[type=submit]').forEach(function (b) { b.disabled = true; b.style.opacity = '.7'; });
    });
  });
  // Si el navegador restaura la pagina (boton Atras), reactiva los botones
  window.addEventListener('pageshow', function () {
    document.querySelectorAll('form').forEach(function (f) {
      delete f.dataset.enviando;
      f.querySelectorAll('button[type=submit]').forEach(function (b) { b.disabled = false; b.style.opacity = ''; });
    });
  });
  // Los selectores con data-auto envian el formulario al cambiar (filtros)
  document.querySelectorAll('select[data-auto]').forEach(function (s) {
    s.addEventListener('change', function () { s.form.submit(); });
  });
})();
// Menus desplegables del encabezado: se cierran al hacer clic fuera o con Escape
(function () {
  function cerrar(excepto) {
    document.querySelectorAll('.nav details[open]').forEach(function (d) { if (d !== excepto) { d.removeAttribute('open'); } });
  }
  document.addEventListener('click', function (e) { cerrar(e.target.closest('.nav details')); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { cerrar(null); } });
})();

// Numeros que cuentan hasta su valor al cargar (se omite con prefers-reduced-motion)
(function () {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) { return; }
  document.querySelectorAll('.dato .valor, .contar').forEach(function (el) {
    var txt = el.textContent.trim();
    var m = txt.match(/^(\D*?)(\d[\d.,]*)(.*)$/);
    if (!m) { return; }
    var crudo = m[2], dec = 0, num;
    if (/,\d{1,2}$/.test(crudo)) {
      dec = crudo.split(',')[1].length;
      num = parseFloat(crudo.replace(/\./g, '').replace(',', '.'));
    } else {
      num = parseFloat(crudo.replace(/[.,]/g, ''));
    }
    if (!isFinite(num) || num === 0) { return; }
    var miles = /\d\.\d{3}/.test(crudo);
    function formato(v) {
      var p = v.toFixed(dec).split('.');
      if (miles) { p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
      return p.join(',');
    }
    var ini = null, dur = 1100;
    function paso(t) {
      if (ini === null) { ini = t; }
      var p = Math.min((t - ini) / dur, 1), e = 1 - Math.pow(1 - p, 3);
      el.textContent = p < 1 ? m[1] + formato(num * e) + m[3] : txt;
      if (p < 1) { window.requestAnimationFrame(paso); }
    }
    window.requestAnimationFrame(paso);
    window.setTimeout(function () { el.textContent = txt; }, dur + 400);   // respaldo: siempre termina en el valor real
  });
})();
