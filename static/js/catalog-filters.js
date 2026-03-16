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
     * APLICA LOS FILTROS REALMENTE (Recarga la página)
     */
    applyFilters: function () {
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

        // Navegar — el hash #productsGrid provoca que el navegador posicione
        // la vista en el grid de resultados, no en el top de la home.
        window.location.href = url.toString() + '#productsGrid';
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
// Cuando la URL tiene #productsGrid, el navegador hace un salto brusco al
// ancla. Sustituimos ese salto por un scroll suave con pequeño offset para
// dejar el encabezado visible.
document.addEventListener('DOMContentLoaded', function () {
    if (window.location.hash === '#productsGrid') {
        const grid = document.getElementById('productsGrid');
        if (grid) {
            // Primero vamos al top sin animación para que el scroll siguiente
            // parta desde cero y no desde donde el navegador saltó.
            window.scrollTo(0, 0);
            requestAnimationFrame(function () {
                const OFFSET = 80; // px de cabecera fija
                const top = grid.getBoundingClientRect().top + window.pageYOffset - OFFSET;
                window.scrollTo({ top: top, behavior: 'smooth' });
            });
        }
    }
});
