/* JavaScript principal para NetManager */

// Auto-fechar alertas após 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});

// Função auxiliar para fazer requisições AJAX
function makeRequest(method, url, data = null) {
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : null
    });
}

// Confirmação antes de deletar
function confirmDelete(message = 'Tem certeza que deseja deletar este item?') {
    return confirm(message);
}

// Toast de notificação (simples)
function showToast(message, type = 'info') {
    const alertClass = `alert alert-${type}`;
    const alertHTML = `
        <div class="${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container-lg');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHTML);
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                new bootstrap.Alert(alert).close();
            }
        }, 5000);
    }
}
