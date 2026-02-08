/**
 * FENIX - Catálogo de Productos
 * ==================================
 * Patrón: Selector local + Añadir a cesta
 * 
 * REGLAS ESTRICTAS:
 * 1. qtyLocal[productId] = cantidad en el SELECTOR de la tarjeta (NO en cesta)
 * 2. cart[productId] = cantidad REAL en la cesta (persistida en servidor)
 * 3. Botones +/- SOLO modifican qtyLocal (NUNCA tocan el servidor)
 * 4. Botón "Añadir" es la ÚNICA acción que llama al servidor
 * 5. El badge del topbar muestra SOLO cart (no qtyLocal)
 */

const CatalogCart = {
    // Cantidad LOCAL por tarjeta (selector visual, NO en cesta)
    qtyLocal: {},
    
    // Cantidad REAL en cesta (persistida en servidor)
    cart: {},
    
    // Flag para evitar múltiples inicializaciones
    initialized: false,
    
    /**
     * Inicializa el catálogo (solo una vez)
     */
    init: function() {
        if (this.initialized) {
            console.log('[CatalogCart] Ya inicializado, ignorando');
            return;
        }
        
        console.log('[CatalogCart] Inicializando...');
        this.initialized = true;
        
        // Inicializar todas las tarjetas con qtyLocal = 0
        this.initializeAllCards();
        
        // Vincular eventos (con protección contra duplicados)
        this.bindEvents();
        
        // Actualizar badge del topbar con lo que hay en cart
        this.updateTopbarBadge();
        
        console.log('[CatalogCart] Inicialización completa');
    },
    
    /**
     * Inicializa todas las tarjetas con qtyLocal = 0
     */
    initializeAllCards: function() {
        document.querySelectorAll('.product-card').forEach(card => {
            const productId = card.getAttribute('data-product-id');
            if (productId) {
                this.qtyLocal[productId] = 0;
                this.updateCardUI(productId);
            }
        });
    },
    
    /**
     * Vincula eventos a los botones (protegido contra duplicados)
     */
    bindEvents: function() {
        const self = this;
        
        // Remover eventos previos clonando y reemplazando botones
        // Botones + (incrementar SOLO qtyLocal, NUNCA servidor)
        document.querySelectorAll('.qty-plus').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const productId = this.getAttribute('data-product-id');
                console.log('[+] Click - qtyLocal SOLO');
                self.incrementLocal(productId);
            });
        });
        
        // Botones - (decrementar SOLO qtyLocal, NUNCA servidor)
        document.querySelectorAll('.qty-minus').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const productId = this.getAttribute('data-product-id');
                console.log('[-] Click - qtyLocal SOLO');
                self.decrementLocal(productId);
            });
        });
        
        // Botones "Añadir" (ÚNICA acción que llama al servidor)
        document.querySelectorAll('.btn-add-product').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const productId = this.getAttribute('data-product-id');
                console.log('[Añadir] Click - LLAMAR SERVIDOR');
                self.addToCart(productId);
            });
        });
    },
    
    /**
     * Incrementa qtyLocal (SOLO UI, NUNCA toca servidor)
     */
    incrementLocal: function(productId) {
        const currentQty = this.qtyLocal[productId] || 0;
        this.qtyLocal[productId] = currentQty + 1;
        console.log(`[qtyLocal] ${productId}: ${currentQty} -> ${this.qtyLocal[productId]} (SOLO UI)`);
        this.updateCardUI(productId);
        // IMPORTANTE: NO se llama al servidor aquí
    },
    
    /**
     * Decrementa qtyLocal (SOLO UI, NUNCA toca servidor)
     * No puede bajar de 0
     */
    decrementLocal: function(productId) {
        const currentQty = this.qtyLocal[productId] || 0;
        if (currentQty > 0) {
            this.qtyLocal[productId] = currentQty - 1;
            console.log(`[qtyLocal] ${productId}: ${currentQty} -> ${this.qtyLocal[productId]} (SOLO UI)`);
            this.updateCardUI(productId);
        }
        // IMPORTANTE: NO se llama al servidor aquí
    },
    
    /**
     * Añade a la cesta - ÚNICA acción que modifica el carrito
     * SUMA la cantidad local a la cantidad existente en cesta
     */
    addToCart: function(productId) {
        const localQty = this.qtyLocal[productId] || 0;
        
        // Si la cantidad local es 0, no hacer nada
        if (localQty === 0) {
            this.showToast('Selecciona una cantidad primero', 'warning');
            return;
        }
        
        // Deshabilitar botón mientras se procesa
        const btn = document.querySelector(`.btn-add-product[data-product-id="${productId}"]`);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Añadiendo...';
        }
        
        // Llamar al servidor para SUMAR la cantidad a la cesta
        fetch('/orders/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: localQty,
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar el carrito local con la cantidad del servidor
                if (data.product_quantity !== undefined) {
                    this.cart[productId] = data.product_quantity;
                } else {
                    // Si no devuelve la cantidad específica, sumarla localmente
                    this.cart[productId] = (this.cart[productId] || 0) + localQty;
                }
                
                // Actualizar badge del topbar con el total del servidor
                if (data.cart_count !== undefined) {
                    this.updateTopbarBadgeCount(data.cart_count);
                }
                
                // Mostrar feedback
                this.showToast(`Añadidas ${localQty} uds a la cesta`, 'success');
                
                // Resetear qtyLocal a 0 para evitar duplicados
                this.qtyLocal[productId] = 0;
                this.updateCardUI(productId);
                
                // Actualizar badge overlay con cantidad en cesta
                this.updateCartBadgeOverlay(productId);
            } else {
                this.showToast(data.message || 'Error al añadir a la cesta', 'error');
            }
        })
        .catch(error => {
            console.error('Error al añadir a la cesta:', error);
            this.showToast('Error de conexión', 'error');
        })
        .finally(() => {
            // Restaurar botón
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-cart-plus"></i> Añadir';
                this.updateAddButtonState(productId);
            }
        });
    },
    
    /**
     * Actualiza la UI de una tarjeta (solo visual, NO toca la cesta)
     */
    updateCardUI: function(productId) {
        const card = document.querySelector(`.product-card[data-product-id="${productId}"]`);
        if (!card) return;
        
        const localQty = this.qtyLocal[productId] || 0;
        
        // Actualizar input de cantidad
        const input = card.querySelector('.qty-input');
        if (input) {
            input.value = localQty;
        }
        
        // Actualizar estado del botón -
        const minusBtn = card.querySelector('.qty-minus');
        if (minusBtn) {
            minusBtn.disabled = localQty === 0;
            minusBtn.classList.toggle('disabled', localQty === 0);
        }
        
        // Actualizar estado del botón "Añadir"
        this.updateAddButtonState(productId);
    },
    
    /**
     * Actualiza el estado del botón "Añadir"
     */
    updateAddButtonState: function(productId) {
        const btn = document.querySelector(`.btn-add-product[data-product-id="${productId}"]`);
        if (!btn) return;
        
        const localQty = this.qtyLocal[productId] || 0;
        
        if (localQty === 0) {
            btn.disabled = true;
            btn.classList.add('disabled');
            btn.innerHTML = '<i class="bi bi-cart-plus"></i> Selecciona cantidad';
        } else {
            btn.disabled = false;
            btn.classList.remove('disabled');
            btn.innerHTML = `<i class="bi bi-cart-plus"></i> Añadir (${localQty})`;
        }
    },
    
    /**
     * Actualiza el badge overlay en la imagen del producto
     * Muestra la cantidad REAL en cesta (no la selección local)
     */
    updateCartBadgeOverlay: function(productId) {
        const card = document.querySelector(`.product-card[data-product-id="${productId}"]`);
        if (!card) return;
        
        const badgeOverlay = card.querySelector('.product-cart-badge-overlay');
        const badgeQuantity = card.querySelector('.cart-badge-quantity');
        
        const cartQty = this.cart[productId] || 0;
        
        if (badgeOverlay && badgeQuantity) {
            if (cartQty > 0) {
                badgeQuantity.textContent = cartQty;
                badgeOverlay.classList.add('visible');
                badgeOverlay.style.display = 'flex';
            } else {
                badgeOverlay.classList.remove('visible');
                badgeOverlay.style.display = 'none';
            }
        }
    },
    
    /**
     * Actualiza el badge del topbar
     */
    updateTopbarBadge: function() {
        const totalItems = Object.values(this.cart).reduce((sum, qty) => sum + qty, 0);
        this.updateTopbarBadgeCount(totalItems);
    },
    
    /**
     * Actualiza el contador del badge del topbar
     */
    updateTopbarBadgeCount: function(count) {
        const topbarBadge = document.getElementById('topbarCartBadge');
        const topbarCartBtn = document.getElementById('topbarCartBtn');
        
        if (topbarBadge) {
            const totalCount = count || 0;
            if (totalCount > 0) {
                topbarBadge.textContent = totalCount;
                topbarBadge.setAttribute('data-count', totalCount);
                topbarBadge.style.display = 'flex';
                
                // Ajustar tamaño del badge si el número es mayor a 9
                if (totalCount > 9) {
                    topbarBadge.style.minWidth = '18px';
                    topbarBadge.style.height = '18px';
                    topbarBadge.style.fontSize = '12px';
                    topbarBadge.style.padding = '0 5px';
                } else {
                    topbarBadge.style.minWidth = '16px';
                    topbarBadge.style.height = '16px';
                    topbarBadge.style.fontSize = '11px';
                    topbarBadge.style.padding = '0 4px';
                }
                
                // Actualizar aria-label y title
                if (topbarCartBtn) {
                    const cartLabel = 'Carrito (' + totalCount + ')';
                    topbarCartBtn.setAttribute('aria-label', cartLabel);
                    topbarCartBtn.setAttribute('title', cartLabel);
                }
            } else {
                topbarBadge.textContent = '';
                topbarBadge.setAttribute('data-count', '0');
                topbarBadge.style.display = 'none';
                
                if (topbarCartBtn) {
                    topbarCartBtn.setAttribute('aria-label', 'Carrito');
                    topbarCartBtn.setAttribute('title', 'Carrito');
                }
            }
        }
    },
    
    /**
     * Establece la cantidad en cesta para un producto (usado al cargar carrito inicial)
     */
    setQuantity: function(productId, quantity) {
        quantity = Math.max(0, parseInt(quantity) || 0);
        if (quantity === 0) {
            delete this.cart[productId];
        } else {
            this.cart[productId] = quantity;
        }
        this.updateCartBadgeOverlay(productId);
    },
    
    /**
     * Muestra un toast/notificación
     */
    showToast: function(message, type = 'info') {
        // Crear contenedor si no existe
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
            document.body.appendChild(container);
        }
        
        // Crear toast
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        
        // Icono según tipo
        let icon = 'bi-info-circle';
        if (type === 'success') icon = 'bi-check-circle-fill';
        if (type === 'error') icon = 'bi-x-circle-fill';
        if (type === 'warning') icon = 'bi-exclamation-triangle-fill';
        
        // Colores según tipo
        let bgColor = '#3b82f6'; // info (azul)
        if (type === 'success') bgColor = '#22c55e';
        if (type === 'error') bgColor = '#ef4444';
        if (type === 'warning') bgColor = '#f59e0b';
        
        toast.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: ${bgColor};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-size: 14px;
            animation: slideIn 0.3s ease;
            min-width: 250px;
        `;
        
        toast.innerHTML = `<i class="bi ${icon}"></i> <span>${message}</span>`;
        
        // Añadir estilos de animación si no existen
        if (!document.getElementById('toastStyles')) {
            const style = document.createElement('style');
            style.id = 'toastStyles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        container.appendChild(toast);
        
        // Auto-eliminar después de 3 segundos
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },
    
    /**
     * Obtiene el token CSRF
     */
    getCsrfToken: function() {
        let token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        return '';
    }
};

// Exportar para uso global
window.CatalogCart = CatalogCart;
