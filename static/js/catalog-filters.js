/**
 * FENIX - Filtros del Catálogo (solo UI)
 * Manejo de filtros por características especiales y categorías
 */

const CatalogFilters = {
    activeFilters: new Set(),
    activeCategory: null,
    searchQuery: '',
    
    /**
     * Inicializa los filtros
     */
    init: function() {
        // Asegurar que todos los productos estén visibles inicialmente
        this.activeFilters.clear();
        this.activeCategory = null;
        this.searchQuery = '';
        
        this.bindFilterEvents();
        this.bindCategoryEvents();
        this.bindSearchEvents();
        this.bindPanelToggle();
        
        // Aplicar filtros iniciales (mostrar todos)
        this.applyFilters();
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
     * Vincula eventos a los checkboxes de filtros
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
     * Vincula eventos a las categorías del sidebar
     */
    bindCategoryEvents: function() {
        // Los eventos de categorías se manejan desde el sidebar
        // Este método está preparado para cuando se implemente
        document.querySelectorAll('[data-category]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const category = e.currentTarget.getAttribute('data-category');
                this.setCategory(category);
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
     * Establece una categoría activa
     */
    setCategory: function(category) {
        this.activeCategory = category === 'all' || category === null ? null : category;
        this.applyFilters();
    },
    
    /**
     * Limpia todos los filtros
     */
    clearFilters: function() {
        this.activeFilters.clear();
        this.activeCategory = null;
        
        // Desmarcar todos los checkboxes
        document.querySelectorAll('.filter-input').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Limpiar categoría activa en el sidebar
        document.querySelectorAll('.sidebar-menu-sublink').forEach(link => {
            link.classList.remove('active');
        });
        // Activar "Todos"
        const allLink = document.querySelector('.sidebar-menu-sublink[data-category="all"]');
        if (allLink) {
            allLink.classList.add('active');
        }
        
        this.applyFilters();
    },
    
    /**
     * Aplica los filtros activos al grid de productos
     */
    applyFilters: function() {
        const productCards = document.querySelectorAll('.product-card');
        let visibleCount = 0;
        
        // Si no hay filtros activos ni categoría, mostrar todos
        const hasActiveFilters = this.activeFilters.size > 0;
        const hasActiveCategory = this.activeCategory && this.activeCategory !== 'all';
        const hasSearchQuery = this.searchQuery && this.searchQuery.trim() !== '';
        
        if (!hasActiveFilters && !hasActiveCategory && !hasSearchQuery) {
            // Mostrar todos los productos
            productCards.forEach(card => {
                card.classList.remove('hidden');
                visibleCount++;
            });
            this.showEmptyState(false);
            return;
        }
        
        productCards.forEach(card => {
            let shouldShow = true;
            
            // Filtro por categoría
            if (hasActiveCategory) {
                const cardCategory = card.getAttribute('data-product-category');
                if (cardCategory !== this.activeCategory) {
                    shouldShow = false;
                }
            }
            
            // Filtro por características especiales
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
