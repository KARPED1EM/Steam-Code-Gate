// Modal management
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.dispatchEvent(new CustomEvent('modal:closed', { detail: { modalId } }));
    }
}

// Close modal on background click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});

// Confirm dialog
function showConfirm(message, onConfirm, title = '确认操作') {
    return new Promise((resolve) => {
        const modalId = 'confirm-dialog-' + Date.now();
        const modalHTML = `
            <div id="${modalId}" class="modal show">
                <div class="modal-content confirm-dialog">
                    <h2>${title}</h2>
                    <div class="confirm-dialog-message">${message}</div>
                    <div class="confirm-dialog-actions">
                        <button class="btn btn-secondary" id="${modalId}-cancel">取消</button>
                        <button class="btn btn-danger" id="${modalId}-confirm">确定</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        const modal = document.getElementById(modalId);
        const cancelBtn = document.getElementById(`${modalId}-cancel`);
        const confirmBtn = document.getElementById(`${modalId}-confirm`);

        function cleanup() {
            modal.remove();
        }

        cancelBtn.onclick = () => {
            cleanup();
            resolve(false);
        };

        confirmBtn.onclick = async () => {
            cleanup();
            if (onConfirm) {
                await onConfirm();
            }
            resolve(true);
        };

        modal.onclick = (e) => {
            if (e.target === modal) {
                cleanup();
                resolve(false);
            }
        };
    });
}

// Alert dialog
function showAlert(message, title = '提示', type = 'info') {
    const modalId = 'alert-dialog-' + Date.now();
    const modalHTML = `
        <div id="${modalId}" class="modal show">
            <div class="modal-content confirm-dialog">
                <h2>${title}</h2>
                <div class="confirm-dialog-message">${message}</div>
                <div class="confirm-dialog-actions">
                    <button class="btn btn-primary" id="${modalId}-ok">确定</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = document.getElementById(modalId);
    const okBtn = document.getElementById(`${modalId}-ok`);

    function cleanup() {
        modal.remove();
    }

    okBtn.onclick = cleanup;
    modal.onclick = (e) => {
        if (e.target === modal) {
            cleanup();
        }
    };
}

// Export to global scope
window.showModal = showModal;
window.closeModal = closeModal;
window.showConfirm = showConfirm;
window.showAlert = showAlert;
