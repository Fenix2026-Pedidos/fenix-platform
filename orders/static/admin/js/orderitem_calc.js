// Cálculo automático de line_total = quantity * unit_price
(function() {
    'use strict';
    
    function calculateLineTotal() {
        var quantityEl = document.getElementById('id_quantity');
        var unitPriceEl = document.getElementById('id_unit_price');
        var lineTotalEl = document.getElementById('id_line_total');
        
        if (!quantityEl || !unitPriceEl || !lineTotalEl) {
            return;
        }
        
        var quantity = parseFloat(quantityEl.value) || 0;
        var unitPriceStr = unitPriceEl.value || '0';
        // Reemplazar coma por punto para parseFloat
        var unitPrice = parseFloat(unitPriceStr.replace(',', '.')) || 0;
        var lineTotal = quantity * unitPrice;
        
        if (!isNaN(lineTotal) && lineTotal >= 0) {
            // Formatear con 2 decimales
            var formatted = lineTotal.toFixed(2);
            // Quitar readonly temporalmente para poder escribir
            lineTotalEl.removeAttribute('readonly');
            lineTotalEl.value = formatted;
            lineTotalEl.setAttribute('readonly', 'readonly');
        } else {
            lineTotalEl.removeAttribute('readonly');
            lineTotalEl.value = '';
            lineTotalEl.setAttribute('readonly', 'readonly');
        }
    }
    
    // Esperar a que la página cargue completamente
    function initCalc() {
        var quantityEl = document.getElementById('id_quantity');
        var unitPriceEl = document.getElementById('id_unit_price');
        
        if (quantityEl && unitPriceEl) {
            // Calcular cuando cambian quantity o unit_price
            quantityEl.addEventListener('input', calculateLineTotal);
            quantityEl.addEventListener('change', calculateLineTotal);
            unitPriceEl.addEventListener('input', calculateLineTotal);
            unitPriceEl.addEventListener('change', calculateLineTotal);
            
            // Calcular al cargar (por si ya hay valores)
            calculateLineTotal();
        } else {
            // Reintentar después de un breve delay
            setTimeout(initCalc, 100);
        }
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCalc);
    } else {
        initCalc();
    }
})();
