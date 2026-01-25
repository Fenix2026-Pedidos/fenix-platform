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
    init: function() {
        // Cargar filtros desde localStorage
        this.loadFromStorage();
        
        // Asegurar que todos los productos estén visibles inicialmente si no hay filtros
        if (this.activeType === 'todos' && this.activeFilters.size === 0) {
            this.activeFilters.clear();
            this.activeType = 'todos';
            this.searchQuery = '';
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
    loadFromStorage: function() {
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
    saveToStorage: function() {
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
    bindPanelToggle: function() {
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
    bindFilterEvents: function() {
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
     * Vincula eventos a los radio buttons de tipos de producto
     */
    bindTypeEvents: function() {
        document.querySelectorAll('.filter-type-radio').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    const type = e.target.getAttribute('data-type') || 'todos';
                    this.setType(type);
                }
            });
        });
    },
    
    /**
     * Vincula eventos a la búsqueda
     */
    bindSearchEvents: function() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            // Búsqueda en tiempo real (opcional, solo UI)
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase().trim();
                this.applyFilters();
            });
        }
    },
    
    /**
     * Establece un tipo de producto activo
     */
    setType: function(type) {
        this.activeType = type === 'todos' || type === null ? 'todos' : type;
        this.saveToStorage();
        this.applyFilters();
    },
    
    /**
     * Limpia todos los filtros
     */
    clearFilters: function() {
        this.activeFilters.clear();
        this.activeType = 'todos';
        
        // Desmarcar todos los checkboxes
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Marcar "Todos" en tipos de producto
        const todosRadio = document.querySelector('.filter-type-radio[data-type="todos"]');
        if (todosRadio) {
            todosRadio.checked = true;
        }
        
        // Limpiar localStorage
        try {
            localStorage.removeItem(this.STORAGE_TYPE_KEY);
            localStorage.removeItem(this.STORAGE_FEATURES_KEY);
        } catch (e) {
            console.warn('No se pudieron limpiar los filtros de localStorage:', e);
        }
        
        this.applyFilters();
    },
    
    /**
     * Aplica los filtros activos al grid de productos
     */
    applyFilters: function() {
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
            return;
        }
        
        productCards.forEach(card => {
            let shouldShow = true;
            
            // Filtro por tipo de producto
            if (hasActiveType) {
                const cardType = card.getAttribute('data-product-type');
                if (cardType !== this.activeType) {
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
                const productName = card.querySelector('.product-name');
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
    },
    
    /**
     * Muestra/oculta el estado vacío
     */
    showEmptyState: function(show) {
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
