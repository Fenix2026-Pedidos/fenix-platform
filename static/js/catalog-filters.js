/**
 * FENIX - Filtros del Catálogo (solo UI)
 * Manejo de filtros por tipos de producto y características especiales
 */

const CatalogFilters = {
    activeFilters: new Set(),
    activeType: 'todos',
    searchQuery: '',

    // Keys para localStorage
    STORAGE_TYPE_KEY: 'fenix_filter_type',
    STORAGE_FEATURES_KEY: 'fenix_filter_features',

    /**
     * Inicializa los filtros
     */
    init: function () {
        // Cargar filtros desde localStorage
        this.loadFromStorage();

        // Actualizar el contador de resultados (valores iniciales se determinarán en applyFilters)
        // Esta llamada aquí es un placeholder, los valores reales se pasarán en applyFilters
        // this.updateResultCount(visibleCount, totalCount); 

        // Limpiar estados inconsistentes si el tipo es todos
        if (this.activeType === 'todos' && this.activeFilters.size === 0) {
            localStorage.removeItem(this.STORAGE_TYPE_KEY);
            localStorage.removeItem(this.STORAGE_FEATURES_KEY);
        }

        this.bindFilterEvents();
        this.bindTypeEvents();
        this.bindSearchEvents();
        this.bindPanelToggle();

        // Aplicar filtros iniciales
        this.applyFilters();
    },

    /**
     * Carga filtros desde localStorage
     */
    loadFromStorage: function () {
        try {
            // Cargar tipo de producto
            const savedType = localStorage.getItem(this.STORAGE_TYPE_KEY);
            if (savedType) {
                this.activeType = savedType;
                // Marcar radio button correspondiente
                const radio = document.querySelector(`.filter-type-radio[data-type="${savedType}"]`);
                if (radio) {
                    radio.checked = true;
                }
            }

            // Cargar características especiales
            const savedFeatures = localStorage.getItem(this.STORAGE_FEATURES_KEY);
            if (savedFeatures) {
                const features = savedFeatures.split(',');
                features.forEach(feature => {
                    const trimmed = feature.trim();
                    if (trimmed) {
                        this.activeFilters.add(trimmed);
                        // Marcar checkbox correspondiente
                        const checkbox = document.querySelector(`.filter-input[data-filter="${trimmed}"]`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    }
                });
            }
        } catch (e) {
            console.warn('No se pudieron cargar los filtros desde localStorage:', e);
        }
    },

    /**
     * Guarda filtros en localStorage
     */
    saveToStorage: function () {
        try {
            // Guardar tipo de producto
            localStorage.setItem(this.STORAGE_TYPE_KEY, this.activeType || 'todos');

            // Guardar características especiales
            const featuresArray = Array.from(this.activeFilters);
            localStorage.setItem(this.STORAGE_FEATURES_KEY, featuresArray.join(','));
        } catch (e) {
            console.warn('No se pudieron guardar los filtros en localStorage:', e);
        }
    },

    /**
     * Vincula eventos para abrir/cerrar el panel de filtros
     */
    bindPanelToggle: function () {
        const toggleBtn = document.getElementById('filtersToggle');
        const closeBtn = document.getElementById('closeFiltersPanel');
        const panel = document.getElementById('filtersPanel');
        const overlay = document.getElementById('filtersOverlay');

        if (toggleBtn && panel) {
            toggleBtn.addEventListener('click', () => {
                panel.classList.add('open');
                if (overlay) {
                    overlay.classList.add('active');
                }
                document.body.style.overflow = 'hidden';
            });
        }

        const closePanel = () => {
            if (panel) {
                panel.classList.remove('open');
            }
            if (overlay) {
                overlay.classList.remove('active');
            }
            document.body.style.overflow = '';
        };

        if (closeBtn) {
            closeBtn.addEventListener('click', closePanel);
        }

        if (overlay) {
            overlay.addEventListener('click', closePanel);
        }

        // Cerrar con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel && panel.classList.contains('open')) {
                closePanel();
            }
        });
    },

    /**
     * Vincula eventos a los checkboxes de características especiales
     */
    bindFilterEvents: function () {
        // Checkboxes de características especiales
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const filter = e.target.getAttribute('data-filter');
                if (e.target.checked) {
                    this.activeFilters.add(filter);
                } else {
                    this.activeFilters.delete(filter);
                }
                this.saveToStorage();
                this.applyFilters();
            });
        });

        // Botón eliminar selección
        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    },

    /**
     * Vincula eventos a los radio buttons de tipos de producto (Tabs)
     */
    bindTypeEvents: function () {
        // En category_tabs.html los tabs son botones con data-category-tab
        document.querySelectorAll('[data-category-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Actualizar UI de tabs
                document.querySelectorAll('[data-category-tab]').forEach(t => t.classList.remove('is-active'));
                tab.classList.add('is-active');

                const type = tab.getAttribute('data-category-tab') || 'todos';
                this.setType(type);
            });
        });
    },

    /**
     * Vincula eventos a la búsqueda
     */
    bindSearchEvents: function () {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has('q')) {
                this.searchQuery = urlParams.get('q').toLowerCase().trim();
            }

            // Búsqueda en tiempo real (opcional, solo UI)
            searchInput.addEventListener('input', (e) => {
                const val = e.target.value;
                this.searchQuery = val.toLowerCase().trim();

                // Si borran la búsqueda manualmente y hay query en backend, recargar para limpiar
                if (val === '' && urlParams.has('q')) {
                    window.location.href = window.location.pathname;
                    return;
                }

                this.applyFilters();
            });
        }
    },

    /**
     * Establece un tipo de producto activo
     */
    setType: function (type) {
        this.activeType = type === 'todos' || type === null ? 'todos' : type;
        this.saveToStorage();

        // Evitar que el catálogo se quede bloqueado por un backend search residual
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('q')) {
            window.location.href = window.location.pathname;
            return;
        }

        this.applyFilters();
    },

    /**
     * Limpia todos los filtros
     */
    clearFilters: function () {
        this.activeFilters.clear();
        this.activeType = 'todos';
        this.searchQuery = '';

        // Desmarcar todos los checkboxes
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Marcar "Todos" en tipos de producto
        document.querySelectorAll('[data-category-tab]').forEach(t => t.classList.remove('is-active'));
        const todosTab = document.querySelector('[data-category-tab="todos"]');
        if (todosTab) {
            todosTab.classList.add('is-active');
        }

        // Limpiar localStorage
        try {
            localStorage.removeItem(this.STORAGE_TYPE_KEY);
            localStorage.removeItem(this.STORAGE_FEATURES_KEY);
        } catch (e) {
            console.warn('No se pudieron limpiar los filtros de localStorage:', e);
        }

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('q')) {
            window.location.href = window.location.pathname;
            return;
        }

        this.applyFilters();
    },

    /**
     * Aplica los filtros activos al grid de productos
     */
    applyFilters: function () {
        const productCards = document.querySelectorAll('.product-card');
        let visibleCount = 0;

        // Verificar si hay filtros activos
        const hasActiveFilters = this.activeFilters.size > 0;
        const hasActiveType = this.activeType && this.activeType !== 'todos';
        const hasSearchQuery = this.searchQuery && this.searchQuery.trim() !== '';

        // Si no hay filtros activos, mostrar todos
        if (!hasActiveFilters && !hasActiveType && !hasSearchQuery) {
            productCards.forEach(card => {
                card.classList.remove('hidden');
                visibleCount++;
            });
            this.showEmptyState(false);
            this.updateResultCount(visibleCount, productCards.length);
            return;
        }

        productCards.forEach(card => {
            let shouldShow = true;

            // Filtro por tipo de producto (Normalizar a minúsculas)
            if (hasActiveType) {
                const cardType = (card.getAttribute('data-product-type') || '').toLowerCase();
                if (cardType !== this.activeType.toLowerCase()) {
                    shouldShow = false;
                }
            }

            // Filtro por características especiales (AND: debe tener TODAS las seleccionadas)
            if (hasActiveFilters && shouldShow) {
                const cardFeatures = card.getAttribute('data-product-features');
                if (cardFeatures && cardFeatures.trim() !== '') {
                    const features = cardFeatures.split(',').map(f => f.trim());
                    // El producto debe tener TODAS las características seleccionadas
                    for (const filter of this.activeFilters) {
                        if (!features.includes(filter)) {
                            shouldShow = false;
                            break;
                        }
                    }
                } else {
                    // Si no tiene características, ocultar si hay filtros activos
                    shouldShow = false;
                }
            }

            // Filtro por búsqueda (solo UI, busca en el nombre)
            if (hasSearchQuery && shouldShow) {
                const productName = card.querySelector('.card-product-name');
                if (productName) {
                    const nameText = productName.textContent.toLowerCase();
                    if (!nameText.includes(this.searchQuery)) {
                        shouldShow = false;
                    }
                }
            }

            // Mostrar/ocultar card
            if (shouldShow) {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });

        // Mostrar mensaje si no hay resultados
        this.showEmptyState(visibleCount === 0);

        // Actualizar el contador de resultados
        this.updateResultCount(visibleCount, productCards.length);
    },

    /**
     * Actualiza el texto del contador (ej: "Mostrando 1-4 de 8 productos")
     */
    updateResultCount: function (visible, total) {
        const countBadge = document.querySelector('.catalog-count-badge');
        if (!countBadge) return;

        const numbersSpan = countBadge.querySelector('.count-numbers');
        const totalSpan = countBadge.querySelector('.count-total');
        const label产品 = countBadge.querySelector('.count-label:last-child'); // El que dice "productos"

        if (numbersSpan) {
            // Si solo hay 1, poner "1"
            if (visible === 1) numbersSpan.textContent = "1";
            else if (visible === 0) numbersSpan.textContent = "0";
            else numbersSpan.textContent = `1–${visible}`;
        }

        if (totalSpan) {
            totalSpan.textContent = total;
        }

        // Si no hay resultados, podemos cambiar el estilo
        if (visible === 0) {
            countBadge.classList.add('no-results');
        } else {
            countBadge.classList.remove('no-results');
        }
    },

    /**
     * Muestra/oculta el estado vacío
     */
    showEmptyState: function (show) {
        let emptyState = document.querySelector('.empty-state');

        if (show && !emptyState) {
            // Crear estado vacío si no existe
            const grid = document.getElementById('productsGrid');
            if (grid) {
                emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                emptyState.innerHTML = `
                    <i class="bi bi-inbox"></i>
                    <p class="text-muted">No se encontraron productos con los filtros seleccionados.</p>
                `;
                grid.appendChild(emptyState);
            }
        } else if (!show && emptyState) {
            // Remover estado vacío si existe y no es el original
            const grid = document.getElementById('productsGrid');
            if (grid && grid.querySelector('.product-card:not(.hidden)')) {
                emptyState.remove();
            }
        }
    }
};

// Exportar para uso global
window.CatalogFilters = CatalogFilters;
