/**
 * FENIX - Filtros del Catálogo (solo UI)
 * Manejo de filtros por tipos de producto y características especiales
 */

const CatalogFilters = {
    // Estado aplicado (basado en la URL)
    appliedFilters: {
        type: 'todos',
        features: [],
        q: ''
    },

    // Estado temporal (lo que el usuario marca en el panel pero no ha pulsado "Ver resultados")
    temporalFilters: {
        type: 'todos',
        features: [],
        q: ''
    },

    /**
     * Inicializa los filtros
     */
    init: function () {
        this.loadFromUrl();
        this.bindPanelToggle();
        this.bindFilterEvents();
        this.bindTypeEvents();
        this.bindSearchEvents();
        
        // Sincronizar UI con el estado aplicado inicial
        this.syncUI(this.appliedFilters);
        this.bindPromoEvents();
        this.checkInitialHash();
    },

    /**
     * Carga el estado inicial desde los parámetros de la URL
     */
    loadFromUrl: function () {
        const urlParams = new URLSearchParams(window.location.search);
        
        this.appliedFilters.type = urlParams.get('type') || 'todos';
        this.appliedFilters.q = urlParams.get('q') || '';
        
        const featuresStr = urlParams.get('features') || '';
        this.appliedFilters.features = featuresStr ? featuresStr.split(',') : [];

        // Inicializar el estado temporal con el aplicado
        this.temporalFilters = JSON.parse(JSON.stringify(this.appliedFilters));
    },

    /**
     * Sincroniza los controles visuales con un estado dado
     */
    syncUI: function (state) {
        // 1. Tipos / Categorías
        const type = state.type || 'todos';
        
        // Radio buttons de escritorio y móvil
        document.querySelectorAll(`.filter-type-radio[data-type="${type}"], .filter-type-radio[value="${type}"]`).forEach(radio => {
            radio.checked = true;
        });
        
        // Tabs de escritorio
        document.querySelectorAll('[data-category-tab]').forEach(tab => {
            if (tab.getAttribute('data-category-tab') === type) {
                tab.classList.add('is-active');
            } else {
                tab.classList.remove('is-active');
            }
        });

        // 2. Características (Checkboxes)
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            const filter = checkbox.getAttribute('data-filter');
            checkbox.checked = state.features.includes(filter);
        });

        // 3. Búsqueda
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value !== state.q) {
            searchInput.value = state.q;
        }
    },

    /**
     * Eventos del panel (Abrir/Cerrar/Aplicar)
     */
    bindPanelToggle: function () {
        const toggleBtn = document.getElementById('filtersToggle');
        const mToggleBtn = document.getElementById('mFiltersToggle');
        const closeBtn = document.getElementById('closeFiltersPanel');
        const applyBtn = document.getElementById('applyMobileFilters');
        const panel = document.getElementById('filtersPanel');
        const overlay = document.getElementById('filtersOverlay');

        const openPanel = () => {
            // Al abrir, el estado temporal vuelve a ser el aplicado (reset)
            this.temporalFilters = JSON.parse(JSON.stringify(this.appliedFilters));
            this.syncUI(this.temporalFilters);
            
            panel.classList.add('open');
            if (overlay) overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        };

        const closePanel = () => {
            panel.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            document.body.style.overflow = '';
        };

        if (toggleBtn) toggleBtn.addEventListener('click', openPanel);
        if (mToggleBtn) mToggleBtn.addEventListener('click', openPanel);
        if (closeBtn) closeBtn.addEventListener('click', closePanel);
        if (overlay) overlay.addEventListener('click', closePanel);

        // BOTÓN CRÍTICO: "Ver resultados"
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyFilters();
                closePanel();
            });
        }
    },

    /**
     * Eventos de Checkboxes (Características)
     */
    bindFilterEvents: function () {
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const filter = e.target.getAttribute('data-filter');
                if (e.target.checked) {
                    if (!this.temporalFilters.features.includes(filter)) {
                        this.temporalFilters.features.push(filter);
                    }
                } else {
                    this.temporalFilters.features = this.temporalFilters.features.filter(f => f !== filter);
                }
            });
        });

        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    },

    /**
     * Eventos de Tipos / Categorías
     */
    bindTypeEvents: function () {
        // Tabs de escritorio (estos suelen ser directos)
        document.querySelectorAll('[data-category-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const type = tab.getAttribute('data-category-tab') || 'todos';
                // En escritorio los tabs aplican directamente (comportamiento esperado)
                this.temporalFilters.type = type;
                this.applyFilters();
            });
        });

        // Radios de panel (móvil/desplegable)
        document.querySelectorAll('.filter-type-radio').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.temporalFilters.type = e.target.value;
            });
        });
    },

    /**
     * Eventos de Tarjetas Promo (Hero)
     */
    bindPromoEvents: function () {
        console.log('Fenix UX: Binding Promo Events (Delegation)');
        document.addEventListener('click', (e) => {
            const card = e.target.closest('.js-promo-card');
            if (!card) return;

            // Solo interceptamos si NO es un clic con tecla especial
            if (e.ctrlKey || e.metaKey || e.shiftKey) return;
            
            e.preventDefault();
            console.log('Fenix UX: Promo Card Intercepted');
            
            const category = card.getAttribute('data-promo-type') || 'todos';
            const query = card.getAttribute('data-promo-q') || '';
            const name = card.getAttribute('data-promo-name') || '';

            this.handlePromoClick(category, query, name);
        });
    },

    /**
     * Maneja el clic en una promo: filtra y scrollea
     */
    handlePromoClick: function (category, query, name) {
        console.log('Fenix UX: Promo Clicked', { category, query, name });
        
        this.temporalFilters.type = category;
        this.temporalFilters.q = query;
        this.temporalFilters.features = []; // Reset features on promo click for clarity

        // Actualizar URL y AJAX
        this.applyFilters(true, name); // true = AJAX mode
    },

    /**
     * Eventos de Búsqueda
     */
    bindSearchEvents: function () {
        const searchInput = document.getElementById('searchInput');
        const searchForm = document.getElementById('searchForm');

        if (searchInput) {
            // Sincronizar temporalmente el query
            searchInput.addEventListener('input', (e) => {
                this.temporalFilters.q = e.target.value;
            });
        }

        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters();
            });
        }
    },

    /**
     * APLICA LOS FILTROS REALMENTE
     */
    applyFilters: function (isAjax = false, promoName = null) {
        const url = new URL(window.location.origin + window.location.pathname);
        
        // 1. Tipo
        if (this.temporalFilters.type && this.temporalFilters.type !== 'todos') {
            url.searchParams.set('type', this.temporalFilters.type);
        }

        // 2. Características
        if (this.temporalFilters.features.length > 0) {
            url.searchParams.set('features', this.temporalFilters.features.join(','));
        }

        // 3. Búsqueda
        if (this.temporalFilters.q && this.temporalFilters.q.trim() !== '') {
            url.searchParams.set('q', this.temporalFilters.q.trim());
        }

        // 4. Mantenemos el tamaño de página pero reseteamos la página a 1
        const currentParams = new URLSearchParams(window.location.search);
        const pageSize = currentParams.get('page_size');
        if (pageSize) url.searchParams.set('page_size', pageSize);
        
        url.searchParams.set('page', '1');

        if (isAjax) {
            this.updateCatalogAJAX(url.toString(), promoName);
        } else {
            // Navegar — el hash provoque que el navegador posicione
            window.location.href = url.toString() + '#catalogo-productos';
        }
    },

    /**
     * Actualiza el catálogo vía AJAX
     */
    updateCatalogAJAX: function (url, promoName) {
        const gridContainer = document.querySelector('.catalog-container');
        const countBar = document.querySelector('.catalog-controls-bar');
        
        if (!gridContainer) {
            window.location.href = url; // Fallback
            return;
        }

        // Mostrar estado de carga
        gridContainer.style.opacity = '0.5';

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // 1. Reemplazar contenedores clave
                const newGrid = doc.querySelector('.catalog-container');
                const newCountBar = doc.querySelector('.catalog-controls-bar');
                
                if (newGrid) gridContainer.innerHTML = newGrid.innerHTML;
                if (newCountBar) countBar.innerHTML = newCountBar.innerHTML;

                // 2. Sincronizar UI interna (filtros, tabs)
                this.appliedFilters = JSON.parse(JSON.stringify(this.temporalFilters));
                this.syncUI(this.appliedFilters);

                // 3. Mostrar badge de filtro activo
                const badge = document.getElementById('activeFilterBadge');
                const badgeText = document.getElementById('activeFilterText');
                if (badge && badgeText && promoName) {
                    badgeText.textContent = promoName;
                    badge.style.display = 'inline-block';
                } else if (badge) {
                    badge.style.display = 'none';
                }

                // 4. Actualizar Historial
                history.pushState(this.appliedFilters, '', url);

                // 5. Scroll suave
                this.scrollToCatalog();
                
                gridContainer.style.opacity = '1';
                
                // Re-inicializar componentes del catálogo (imágenes, Amazon prices, etc.)
                this.reinitCatalogUI();
            })
            .catch(err => {
                console.error('Fenix UX: Fetch error', err);
                window.location.href = url;
            });
    },

    /**
     * Reinicializa UI tras carga AJAX
     */
    reinitCatalogUI: function() {
        // Amazon style prices
        document.querySelectorAll('.card-price-main[data-price]').forEach(function (priceElement) {
            const priceValue = parseFloat(priceElement.getAttribute('data-price'));
            if (!isNaN(priceValue)) {
                const parts = priceValue.toFixed(2).split('.');
                const intPart = parts[0];
                const decPart = parts[1] || '00';
                priceElement.innerHTML = `<span class="price-int">${intPart}</span><span class="price-dec">,${decPart}</span><span class="price-currency">€</span>`;
            }
        });
    },

    scrollToCatalog: function () {
        const target = document.getElementById('catalogo-productos');
        if (target) {
            const OFFSET = 100;
            const top = target.getBoundingClientRect().top + window.pageYOffset - OFFSET;
            window.scrollTo({ top: top, behavior: 'smooth' });
        }
    },

    checkInitialHash: function () {
        if (window.location.hash === '#catalogo-productos' || window.location.hash === '#productsGrid') {
            setTimeout(() => this.scrollToCatalog(), 100);
        }
    },

    /**
     * Limpia todo y vuelve al catálogo base
     */
    clearFilters: function () {
        const url = new URL(window.location.origin + window.location.pathname);
        
        // Mantener page_size si existe
        const currentParams = new URLSearchParams(window.location.search);
        const pageSize = currentParams.get('page_size');
        if (pageSize) url.searchParams.set('page_size', pageSize);

        window.location.href = url.toString();
    }
};

window.CatalogFilters = CatalogFilters;

// ─── Scroll suave al grid tras recarga por filtros ─────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    if (window.location.hash === '#catalogo-productos' || window.location.hash === '#productsGrid') {
        const grid = document.getElementById('catalogo-productos') || document.getElementById('productsGrid');
        if (grid) {
            window.scrollTo(0, 0);
            requestAnimationFrame(function () {
                const OFFSET = 100;
                const top = grid.getBoundingClientRect().top + window.pageYOffset - OFFSET;
                window.scrollTo({ top: top, behavior: 'smooth' });
            });
        }
    }
});
