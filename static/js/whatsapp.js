/**
 * WhatsApp Chat Widget Logic
 */

function toggleWhatsAppChat() {
    const chatWindow = document.getElementById('whatsapp-chat-window');
    const fabIcon = document.getElementById('whatsapp-fab');
    if (chatWindow.classList.contains('active')) {
        chatWindow.classList.remove('active');
        fabIcon.classList.remove('active');
    } else {
        chatWindow.classList.add('active');
        fabIcon.classList.add('active');
    }
}

function startWhatsAppChat(phone, message) {
    const isMobile = /iPhone|Android|iPad|iPod|Windows Phone/i.test(navigator.userAgent);
    const encodedMessage = encodeURIComponent(message);
    
    let url;
    if (isMobile) {
        url = `https://wa.me/${phone}?text=${encodedMessage}`;
    } else {
        url = `https://web.whatsapp.com/send?phone=${phone}&text=${encodedMessage}`;
    }
    
    window.open(url, '_blank');
    toggleWhatsAppChat(); // Ocultar después de iniciar
}

// Cerrar si se hace clic fuera del widget
document.addEventListener('click', function(event) {
    const container = document.getElementById('whatsapp-fab-container');
    const chatWindow = document.getElementById('whatsapp-chat-window');
    if (container && !container.contains(event.target)) {
        chatWindow.classList.remove('active');
        document.getElementById('whatsapp-fab').classList.remove('active');
    }
});
