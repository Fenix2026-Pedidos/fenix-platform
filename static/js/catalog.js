/**
 * FENIX - Catálogo de Productos
 * Manejo del carrito y selectores de cantidad (solo UI)
 */

const CatalogCart = {
    cart: {},
    productPrices: {},
    
    /**
     * Inicializa el catálogo
     */
    init: function() {
        this.loadCart();
        this.loadProductPrices();
        this.bindEvents();
        this.updateCartPanel();
        this.updateProductQuantities();
    },
    
    /**
     * Carga el carrito desde el servidor (usando endpoint existente)
     */
    loadCart: function() {
        // Cargar carrito desde los inputs de cantidad en las cards
        this.cart = {};
        const inputs = document.querySelectorAll('.qty-input');
        inputs.forEach(input => {
            const productId = input.getAttribute('data-product-id');
            const quantity = parseInt(input.value) || 0;
            if (quantity > 0) {
                this.cart[productId] = quantity;
            }
        });
        
        this.updateProductQuantities();
        this.updateCartPanel();
    },
    
    /**
     * Carga los precios de los productos desde las cards
     */
    loadProductPrices: function() {
        const productCards = document.querySelectorAll('.product-card');
        productCards.forEach(card => {
            const productId = card.getAttribute('data-product-id');
            const priceElement = card.querySelector('.product-price');
            if (priceElement) {
                const priceText = priceElement.textContent.trim();
                const price = parseFloat(priceText.replace('€', '').replace(',', '.').trim());
                if (!isNaN(price)) {
                    this.productPrices[productId] = price;
                }
            }
        });
    },
    
    /**
     * Vincula eventos a los botones y inputs
     */
    bindEvents: function() {
        // Botones de incrementar/decrementar
        document.querySelectorAll('.qty-plus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = btn.getAttribute('data-product-id');
                this.incrementQuantity(productId);
            });
        });
        
        document.querySelectorAll('.qty-minus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = btn.getAttribute('data-product-id');
                this.decrementQuantity(productId);
            });
        });
        
        // Botones "Añadir"
        document.querySelectorAll('.btn-add-product').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = btn.getAttribute('data-product-id');
                this.addProduct(productId);
            });
        });
        
        // Inputs de cantidad (solo lectura, pero por si acaso)
        document.querySelectorAll('.qty-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const productId = input.getAttribute('data-product-id');
                const quantity = parseInt(input.value) || 0;
                this.setQuantity(productId, quantity);
            });
        });
    },
    
    /**
     * Incrementa la cantidad de un producto
     */
    incrementQuantity: function(productId) {
        const currentQty = this.cart[productId] || 0;
        this.setQuantity(productId, currentQty + 1);
    },
    
    /**
     * Decrementa la cantidad de un producto
     */
    decrementQuantity: function(productId) {
        const currentQty = this.cart[productId] || 0;
        if (currentQty > 0) {
            this.setQuantity(productId, currentQty - 1);
        }
    },
    
    /**
     * Establece la cantidad de un producto
     */
    setQuantity: function(productId, quantity) {
        quantity = Math.max(0, parseInt(quantity) || 0);
        
        if (quantity === 0) {
            delete this.cart[productId];
        } else {
            this.cart[productId] = quantity;
        }
        
        // Actualizar UI
        this.updateProductQuantity(productId, quantity);
        this.updateCartPanel();
        
        // Sincronizar con el servidor (usando endpoint existente)
        this.syncWithServer(productId, quantity);
    },
    
    /**
     * Actualiza la cantidad mostrada en una card de producto
     */
    updateProductQuantity: function(productId, quantity) {
        const card = document.querySelector(`.product-card[data-product-id="${productId}"]`);
        if (!card) return;
        
        const input = card.querySelector('.qty-input');
        const badgeOverlay = card.querySelector('.product-cart-badge-overlay');
        const badgeQuantity = card.querySelector('.cart-badge-quantity');
        const minusBtn = card.querySelector('.qty-minus');
        
        if (input) {
            input.value = quantity;
        }
        
        if (minusBtn) {
            minusBtn.disabled = quantity === 0;
        }
        
        // Actualizar badge overlay en la imagen
        if (badgeOverlay && badgeQuantity) {
            if (quantity > 0) {
                badgeQuantity.textContent = quantity;
                badgeOverlay.classList.add('visible');
                badgeOverlay.style.display = 'flex';
            } else {
                badgeOverlay.classList.remove('visible');
                badgeOverlay.style.display = 'none';
            }
        }
    },
    
    /**
     * Actualiza todas las cantidades de productos
     */
    updateProductQuantities: function() {
        Object.keys(this.cart).forEach(productId => {
            this.updateProductQuantity(productId, this.cart[productId]);
        });
        
        // Asegurar que los productos sin cantidad muestren 0
        document.querySelectorAll('.product-card').forEach(card => {
            const productId = card.getAttribute('data-product-id');
            if (!this.cart[productId]) {
                this.updateProductQuantity(productId, 0);
            }
        });
    },
    
    /**
     * Actualiza el contador del carrito en el topbar
     */
    updateCartPanel: function() {
        const totalItems = Object.values(this.cart).reduce((sum, qty) => sum + qty, 0);
        
        // Actualizar badge del carrito en topbar
        const topbarBadge = document.getElementById('topbarCartBadge');
        if (topbarBadge) {
            if (totalItems > 0) {
                topbarBadge.textContent = totalItems;
                topbarBadge.setAttribute('data-count', totalItems);
                topbarBadge.style.display = 'flex';
            } else {
                topbarBadge.textContent = '';
                topbarBadge.setAttribute('data-count', '0');
                topbarBadge.style.display = 'none';
            }
        }
    },
    
    /**
     * Calcula el subtotal del carrito
     */
    calculateSubtotal: function() {
        let subtotal = 0;
        Object.keys(this.cart).forEach(productId => {
            const quantity = this.cart[productId];
            const price = this.productPrices[productId] || 0;
            subtotal += price * quantity;
        });
        return subtotal;
    },
    
    /**
     * Sincroniza con el servidor usando los endpoints existentes
     */
    syncWithServer: function(productId, quantity) {
        if (quantity === 0) {
            // Eliminar del carrito
            fetch('/orders/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    product_id: productId,
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.cart_count !== undefined) {
                    this.updateCartCount(data.cart_count);
                }
            })
            .catch(error => {
                console.error('Error al eliminar del carrito:', error);
            });
        } else {
            // Actualizar cantidad usando el endpoint de update
            fetch('/orders/cart/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity,
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.cart_count !== undefined) {
                        this.updateCartCount(data.cart_count);
                    }
                }
            })
            .catch(error => {
                console.error('Error al actualizar carrito:', error);
            });
        }
    },
    
    /**
     * Actualiza el contador del carrito (topbar badge)
     */
    updateCartCount: function(count) {
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
                
                // Actualizar aria-label y title cuando está vacío
                if (topbarCartBtn) {
                    topbarCartBtn.setAttribute('aria-label', 'Carrito');
                    topbarCartBtn.setAttribute('title', 'Carrito');
                }
            }
        }
    },
    
    /**
     * Obtiene el token CSRF
     */
    getCsrfToken: function() {
        // Buscar en diferentes lugares donde puede estar el token
        let token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        
        // Buscar en cookies como fallback
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
