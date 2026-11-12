(() => {
    const config = window.NOMADA;
    if (!config) return;

    const $ = (selector) => document.querySelector(selector);
    const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
    const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    const money = (value, currency='COP') => new Intl.NumberFormat(document.documentElement.lang || 'es', {style:'currency', currency, maximumFractionDigits:currency === 'COP' ? 0 : 2}).format(value);
    const toast = (message, error=false) => {
        const element = $('#toast');
        if (!element) return;
        element.textContent = message;
        element.className = `toast show${error ? ' error' : ''}`;
        window.clearTimeout(element._timer);
        element._timer = window.setTimeout(() => element.className = 'toast', 3500);
    };
    async function api(url, options={}) {
        const response = await fetch(url, {credentials:'same-origin', ...options, headers:{'Accept':'application/json', ...(options.body ? {'Content-Type':'application/json','X-CSRFToken':csrf()} : {}), ...(options.headers || {})}});
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || data.error || config.text.error);
        return data;
    }

    document.querySelectorAll('[data-scroll]').forEach(button => button.addEventListener('click', () => $(button.dataset.scroll)?.scrollIntoView({behavior:'smooth'})));

    async function cargarCatalogo() {
        const grid = $('#catalogo-grid');
        if (!grid) return;
        grid.innerHTML = `<div class="empty-state">${escapeHtml(config.text.loading)}</div>`;
        try {
            const data = await api(config.urls.catalogo);
            const productos = data.productos || [];
            grid.innerHTML = productos.length ? productos.map(producto => `
                <article class="product-card">
                    <div class="product-art">${producto.imagen ? `<img src="${escapeHtml(producto.imagen)}" alt="${escapeHtml(producto.nombre)}" loading="lazy">` : escapeHtml(producto.nombre.slice(0,1).toUpperCase())}</div>
                    <div class="product-body">
                        <div class="product-meta"><span>${escapeHtml(producto.categoria || '—')}</span><span>${escapeHtml(producto.vendedor)}</span></div>
                        <h3>${escapeHtml(producto.nombre)}</h3><p>${escapeHtml(producto.descripcion || '')}</p>
                        <div class="variant-list">${producto.variantes.map(v => `<span class="variant-chip">${escapeHtml(v.talla)} · ${escapeHtml(v.color)} · ${money(v.precio)} · ${v.stock} ${escapeHtml(config.text.stock)}</span>`).join('')}</div>
                    </div>
                </article>`).join('') : `<div class="empty-state">${escapeHtml(config.text.emptyCatalog)}</div>`;
            const select = $('#variante');
            if (select) {
                const variantes = productos.flatMap(producto => producto.variantes.filter(v => v.stock > 0).map(v => ({...v, producto:producto.nombre})));
                select.innerHTML = '<option value="">—</option>' + variantes.map(v => `<option value="${v.id}">${escapeHtml(v.producto)} · ${escapeHtml(v.talla)} ${escapeHtml(v.color)} · ${money(v.precio)} (${v.stock})</option>`).join('');
            }
        } catch (error) { grid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`; toast(error.message, true); }
    }

    async function cargarOrdenes() {
        const list = $('#ordenes-lista');
        if (!list) return;
        list.innerHTML = `<div class="empty-state">${escapeHtml(config.text.loading)}</div>`;
        try {
            const orders = await api(config.urls.ordenes);
            list.innerHTML = orders.length ? orders.map(order => `
                <article class="order-card" data-order="${order.id}">
                    <div class="order-top"><div><strong>${escapeHtml(config.text.order)} #${order.id}</strong><div>${escapeHtml(config.text.total)}: ${money(order.total)}</div></div><span class="order-status">${escapeHtml(order.estado_display || order.estado)}</span></div>
                    ${order.estado === 'PENDIENTE' ? `<div class="order-actions"><select aria-label="Método de pago"><option>TARJETA</option><option>PSE</option><option>NEQUI</option><option>EFECTIVO</option></select><button data-action="pay">${escapeHtml(config.text.pay)}</button><button data-action="cancel">${escapeHtml(config.text.cancel)}</button></div>` : ''}
                </article>`).join('') : `<div class="empty-state">${escapeHtml(config.text.emptyOrders)}</div>`;
        } catch (error) { list.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`; toast(error.message, true); }
    }

    $('#cargar-catalogo')?.addEventListener('click', cargarCatalogo);
    $('#cargar-ordenes')?.addEventListener('click', cargarOrdenes);
    $('#orden-form')?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const variante = Number($('#variante').value), cantidad = Number($('#cantidad').value), cupon = $('#cupon').value.trim();
        if (!variante) return toast(config.text.error, true);
        try {
            await api(config.urls.ordenes, {method:'POST', body:JSON.stringify({items:[{variante,cantidad}], cupon_codigo:cupon})});
            toast(config.text.created); event.target.reset(); await Promise.all([cargarCatalogo(), cargarOrdenes()]);
        } catch (error) { toast(error.message, true); }
    });
    $('#ordenes-lista')?.addEventListener('click', async (event) => {
        const action = event.target.dataset.action;
        if (!action) return;
        const card = event.target.closest('[data-order]'), id = card.dataset.order;
        try {
            if (action === 'pay') {
                const metodo = card.querySelector('select').value;
                await api(`${config.urls.ordenes}${id}/pagar/`, {method:'POST', body:JSON.stringify({metodo})}); toast(config.text.paid);
            } else {
                await api(`${config.urls.ordenes}${id}/cancelar/`, {method:'POST', body:'{}'}); toast(config.text.cancelled);
            }
            await cargarOrdenes();
        } catch (error) { toast(error.message, true); }
    });

    async function consultarIntegracion(url, externa=false, aliado=false) {
        const result = $('#integracion-resultado');
        result.innerHTML = `<div class="empty-state">${escapeHtml(config.text.loading)}</div>`;
        try {
            const data = await api(url);
            if (externa) result.innerHTML = `<div class="external-grid">${(data.productos || []).map(item => `<article class="external-item">${item.imagen ? `<img src="${escapeHtml(item.imagen)}" alt="">` : ''}<h4>${escapeHtml(item.nombre)}</h4><div>${escapeHtml(item.categoria)} · ${money(item.precio, item.moneda || 'USD')}</div></article>`).join('')}</div>`;
            else if (aliado && data.datos?.tarifas) result.innerHTML = `<div class="external-grid">${data.datos.tarifas.map(t => `<article class="external-item"><h4>${escapeHtml(t.ciudad)}</h4><div>${escapeHtml(config.text.shipping)}: ${money(t.costo, data.datos.moneda || 'COP')} · ${t.dias} ${escapeHtml(config.text.days)}</div></article>`).join('')}</div>`;
            else result.innerHTML = `<pre class="json-result">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        } catch (error) { result.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`; toast(error.message, true); }
    }
    $('#aliado-form')?.addEventListener('submit', (event) => {
        event.preventDefault();
        const ciudad = $('#ciudad-aliado').value.trim();
        consultarIntegracion(config.urls.aliado + (ciudad ? `?ciudad=${encodeURIComponent(ciudad)}` : ''), false, true);
    });
    $('#consultar-externo')?.addEventListener('click', () => consultarIntegracion(config.urls.externo, true));
})();
