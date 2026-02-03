/**
 * WhatsApp FAB - Manejo del botón flotante y formulario de contacto
 */

(function() {
    'use strict';

    // Elementos del DOM
    const fab = document.getElementById('whatsapp-fab');
    const modal = document.getElementById('whatsapp-modal');
    const modalOverlay = document.getElementById('whatsapp-modal-overlay');
    const modalClose = document.getElementById('whatsapp-modal-close');
    const modalCancel = document.getElementById('whatsapp-btn-cancel');
    const form = document.getElementById('whatsapp-contact-form');
    const submitBtn = document.getElementById('whatsapp-btn-submit');
    const btnText = submitBtn.querySelector('.whatsapp-btn-text');
    const btnSpinner = submitBtn.querySelector('.whatsapp-btn-spinner');
    const toast = document.getElementById('whatsapp-toast');
    const toastMessage = document.getElementById('whatsapp-toast-message');

    // URL del endpoint
    const API_URL = '/api/whatsapp/send/';

    /**
     * Abre el modal
     */
    function openModal() {
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevenir scroll del body
            // Focus en el primer input
            const nameInput = document.getElementById('whatsapp-name');
            if (nameInput) {
                setTimeout(() => nameInput.focus(), 100);
            }
        }
    }

    /**
     * Cierra el modal
     */
    function closeModal() {
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = ''; // Restaurar scroll
            // Resetear formulario
            if (form) {
                form.reset();
            }
        }
    }

    /**
     * Muestra toast de mensaje
     */
    function showToast(message, isSuccess = true) {
        if (!toast || !toastMessage) return;

        toastMessage.textContent = message;
        toast.className = 'whatsapp-toast ' + (isSuccess ? 'whatsapp-toast-success' : 'whatsapp-toast-error');
        toast.style.display = 'block';

        // Ocultar después de 4 segundos
        setTimeout(() => {
            toast.style.display = 'none';
        }, 4000);
    }

    /**
     * Muestra estado de carga en el botón
     */
    function setLoading(loading) {
        if (!submitBtn || !btnText || !btnSpinner) return;

        if (loading) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnSpinner.style.display = 'inline-block';
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
        }
    }

    /**
     * Obtiene el token CSRF
     */
    function getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
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

    /**
     * Maneja el envío del formulario
     */
    function handleSubmit(e) {
        e.preventDefault();

        if (!form) return;

        // Obtener datos del formulario
        const formData = new FormData(form);
        const name = formData.get('name').trim();
        const message = formData.get('message').trim();

        // Validación básica
        if (!name || !message) {
            showToast('Por favor, completa todos los campos', false);
            return;
        }

        // Obtener URL de la página actual
        const pageUrl = window.location.href;

        // Preparar payload
        const payload = {
            name: name,
            message: message,
            page_url: pageUrl
        };

        // Mostrar estado de carga
        setLoading(true);

        // Enviar request
        fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            setLoading(false);

            if (data.success) {
                showToast('Mensaje enviado correctamente', true);
                // Cerrar modal después de 1 segundo
                setTimeout(() => {
                    closeModal();
                }, 1000);
            } else {
                showToast(data.error || 'No se pudo enviar el mensaje', false);
            }
        })
        .catch(error => {
            setLoading(false);
            console.error('Error al enviar mensaje:', error);
            showToast('Error de conexión. Por favor, intenta de nuevo.', false);
        });
    }

    // Event listeners
    if (fab) {
        fab.addEventListener('click', openModal);
    }

    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    if (modalCancel) {
        modalCancel.addEventListener('click', closeModal);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeModal);
    }

    if (form) {
        form.addEventListener('submit', handleSubmit);
    }

    // Cerrar modal con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal && modal.style.display === 'block') {
            closeModal();
        }
    });

})();
