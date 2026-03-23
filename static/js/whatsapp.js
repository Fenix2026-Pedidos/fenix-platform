/**
 * WhatsApp Chat Widget Logic
 */

// Asegurar que las funciones sean globales para los atributos onclick
window.toggleWhatsAppChat = function() {
    const chatWindow = document.getElementById('whatsapp-chat-window');
    const fabIcon = document.getElementById('whatsapp-fab');
    if (!chatWindow || !fabIcon) return;

    if (chatWindow.classList.contains('active')) {
        chatWindow.classList.remove('active');
        fabIcon.classList.remove('active');
        chatWindow.style.display = 'none';
    } else {
        chatWindow.style.display = 'block';
        // Pequeño delay para permitir que la animación CSS se active
        setTimeout(() => {
            chatWindow.classList.add('active');
            fabIcon.classList.add('active');
        }, 10);
    }
};

window.startWhatsAppChat = function(phone, message) {
    const encodedMessage = encodeURIComponent(message);
    const url = `https://wa.me/${phone}?text=${encodedMessage}`;
    
    window.open(url, '_blank');
    window.toggleWhatsAppChat(); // Ocultar después de iniciar
};

// Cerrar si se hace clic fuera del widget
document.addEventListener('click', function(event) {
    const container = document.getElementById('whatsapp-fab-container');
    const chatWindow = document.getElementById('whatsapp-chat-window');
    const fabIcon = document.getElementById('whatsapp-fab');
    
    if (container && !container.contains(event.target) && chatWindow && chatWindow.classList.contains('active')) {
        chatWindow.classList.remove('active');
        fabIcon.classList.remove('active');
        setTimeout(() => {
            chatWindow.style.display = 'none';
        }, 300);
    }
});
