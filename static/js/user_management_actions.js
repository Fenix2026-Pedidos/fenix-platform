(() => {
    'use strict';

    const actionDropdown = document.getElementById('actionDropdown');
    const confirmModal = document.getElementById('confirmModal');
    const detailsModal = document.getElementById('detailsModal');
    const requestModal = document.getElementById('requestModal');
    const toast = document.getElementById('managementToast');
    let activeActionButton = null;
    let openMenuId = null;
    let toastTimer = null;
    let actionInProgress = false;

    if (!actionDropdown) {
        return;
    }

    function csrfToken() {
        const formToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (formToken?.value) {
            return formToken.value;
        }
        const cookie = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
    }

    function showToast(message, type = 'success') {
        if (!toast || !message) return;
        window.clearTimeout(toastTimer);
        toast.textContent = message;
        toast.className = `management-toast ${type} show`;
        toastTimer = window.setTimeout(() => {
            toast.classList.remove('show');
        }, 5200);
    }

    function setModalVisibility(modal, visible) {
        if (!modal) return;
        modal.style.display = visible ? 'flex' : 'none';
        modal.setAttribute('aria-hidden', visible ? 'false' : 'true');
        document.body.classList.toggle(
            'modal-open',
            Boolean(
                visible
                || [confirmModal, detailsModal, requestModal].some(
                    (item) => item && item.style.display === 'flex'
                )
            )
        );
    }

    function closeActionMenu({ restoreFocus = false } = {}) {
        if (activeActionButton) {
            activeActionButton.setAttribute('aria-expanded', 'false');
        }
        actionDropdown.classList.remove('show');
        actionDropdown.setAttribute('aria-hidden', 'true');
        actionDropdown.style.top = '';
        actionDropdown.style.left = '';
        actionDropdown.replaceChildren();
        const previousButton = activeActionButton;
        activeActionButton = null;
        openMenuId = null;
        if (restoreFocus && previousButton?.isConnected) {
            previousButton.focus();
        }
    }

    function menuItem({ label, icon, action, href = '', danger = false }) {
        const item = document.createElement(href ? 'a' : 'button');
        if (href) {
            item.href = href;
        } else {
            item.type = 'button';
        }
        item.className = `dropdown-item${danger ? ' item-delete' : ''}`;
        item.setAttribute('role', 'menuitem');
        item.dataset.action = action;

        const iconElement = document.createElement('i');
        iconElement.className = `bi ${icon}`;
        iconElement.setAttribute('aria-hidden', 'true');
        const labelElement = document.createElement('span');
        labelElement.textContent = label;
        item.append(iconElement, labelElement);
        return item;
    }

    function separator() {
        const item = document.createElement('div');
        item.className = 'dropdown-separator';
        item.setAttribute('role', 'separator');
        return item;
    }

    function buildRegisteredMenu(button) {
        const fragment = document.createDocumentFragment();
        fragment.append(
            menuItem({
                label: 'Ver detalles',
                icon: 'bi-eye',
                action: 'view-details',
            })
        );
        if (button.dataset.editDisabled !== 'true' && button.dataset.editUrl) {
            fragment.append(
                menuItem({
                    label: 'Editar usuario',
                    icon: 'bi-pencil-square',
                    action: 'navigate-edit',
                    href: button.dataset.editUrl,
                }),
                menuItem({
                    label: 'Cambiar rol',
                    icon: 'bi-person-badge',
                    action: 'navigate-role',
                    href: button.dataset.editUrl,
                })
            );
        }
        if (button.dataset.userStatus === 'active') {
            fragment.append(
                menuItem({
                    label: 'Restablecer contraseña',
                    icon: 'bi-key',
                    action: 'reset-password',
                })
            );
        }
        if (button.dataset.isSelf !== 'true') {
            fragment.append(separator());
            const activating = button.dataset.userStatus === 'disabled';
            fragment.append(
                menuItem({
                    label: activating ? 'Activar usuario' : 'Desactivar usuario',
                    icon: activating ? 'bi-person-check' : 'bi-person-x',
                    action: activating ? 'activate-user' : 'deactivate-user',
                    danger: !activating,
                })
            );
        }
        return fragment;
    }

    function buildPendingMenu() {
        const fragment = document.createDocumentFragment();
        fragment.append(
            menuItem({
                label: 'Ver solicitud',
                icon: 'bi-eye',
                action: 'view-request',
            }),
            menuItem({
                label: 'Editar solicitud',
                icon: 'bi-pencil-square',
                action: 'edit-request',
            }),
            menuItem({
                label: 'Aprobar solicitud',
                icon: 'bi-check-circle',
                action: 'approve',
            }),
            separator(),
            menuItem({
                label: 'Rechazar solicitud',
                icon: 'bi-x-circle',
                action: 'reject',
                danger: true,
            })
        );
        return fragment;
    }

    function positionDropdown(button) {
        const rect = button.getBoundingClientRect();
        const menuRect = actionDropdown.getBoundingClientRect();
        const spacing = 8;
        let top = rect.top;
        let left = rect.left - menuRect.width - spacing;

        // Mantener libre la columna de botones permite abrir el menú de otra
        // fila sin que el desplegable actual intercepte el clic.
        if (left < spacing) {
            left = rect.right + spacing;
        }
        top = Math.max(spacing, Math.min(top, window.innerHeight - menuRect.height - spacing));
        left = Math.max(spacing, Math.min(left, window.innerWidth - menuRect.width - spacing));
        actionDropdown.style.top = `${Math.round(top)}px`;
        actionDropdown.style.left = `${Math.round(left)}px`;
    }

    window.openActionMenu = function openActionMenu(event, button) {
        event.preventDefault();
        event.stopPropagation();
        const userId = button.dataset.userId;
        const menuKey = `${button.dataset.menu}:${userId}`;

        if (openMenuId === menuKey && actionDropdown.classList.contains('show')) {
            closeActionMenu({ restoreFocus: true });
            return;
        }

        closeActionMenu();
        activeActionButton = button;
        openMenuId = menuKey;
        button.setAttribute('aria-expanded', 'true');
        actionDropdown.append(
            button.dataset.menu === 'pending'
                ? buildPendingMenu(button)
                : buildRegisteredMenu(button)
        );
        actionDropdown.classList.add('show');
        actionDropdown.setAttribute('aria-hidden', 'false');
        positionDropdown(button);
        actionDropdown.querySelector('[role=menuitem]')?.focus();
    };

    function detailsRows(button, requestMode) {
        const values = requestMode
            ? [
                ['Nombre', button.dataset.userName],
                ['Email', button.dataset.userEmail],
                ['Empresa', button.dataset.userCompany],
                ['Rol solicitado', button.dataset.userRoleLabel],
                ['Estado', button.dataset.userStatusLabel],
                ['Fecha de solicitud', button.dataset.userJoined],
                ['Email verificado', button.dataset.userEmailVerified === 'true' ? 'Sí' : 'No'],
                ['ID interno', button.dataset.userId],
            ]
            : [
                ['Nombre', button.dataset.userName],
                ['Email', button.dataset.userEmail],
                ['Empresa', button.dataset.userCompany],
                ['Rol', button.dataset.userRoleLabel],
                ['Estado', button.dataset.userStatusLabel],
                ['Fecha de alta', button.dataset.userJoined],
                ['Último acceso', button.dataset.userLastLogin],
                ['ID interno', button.dataset.userId],
            ];

        const grid = document.getElementById('detailsGrid');
        grid.replaceChildren();
        values.forEach(([term, value]) => {
            const wrapper = document.createElement('div');
            const dt = document.createElement('dt');
            const dd = document.createElement('dd');
            dt.textContent = term;
            dd.textContent = value || '—';
            wrapper.append(dt, dd);
            grid.append(wrapper);
        });
    }

    function openDetails(button, requestMode = false) {
        document.getElementById('detailsModalEyebrow').textContent =
            requestMode ? 'Solicitud pendiente' : 'Usuario registrado';
        document.getElementById('detailsModalTitle').textContent =
            button.dataset.userName || button.dataset.userEmail;
        detailsRows(button, requestMode);
        setModalVisibility(detailsModal, true);
        detailsModal.querySelector('.modal-close')?.focus();
    }

    function closeDetailsModal() {
        setModalVisibility(detailsModal, false);
    }

    function openRequestModal(button) {
        document.getElementById('requestModalTitle').textContent = 'Editar solicitud';
        document.getElementById('requestModalSubtitle').textContent = button.dataset.userEmail;
        document.getElementById('requestUserId').value = button.dataset.userId;
        document.getElementById('requestFullName').value = button.dataset.userFullName || '';
        document.getElementById('requestCompany').value =
            button.dataset.userCompany === '—' ? '' : (button.dataset.userCompany || '');
        document.getElementById('requestStatus').value = 'pending';
        document.getElementById('requestRole').value = button.dataset.userRole;
        document.getElementById('requestEmailVerified').checked =
            button.dataset.userEmailVerified === 'true';
        const error = document.getElementById('requestModalError');
        error.textContent = '';
        error.classList.remove('visible');
        requestModal.dataset.userId = button.dataset.userId;
        setModalVisibility(requestModal, true);
        document.getElementById('requestFullName').focus();
    }

    window.closeRequestModal = function closeRequestModal() {
        if (actionInProgress) return;
        setModalVisibility(requestModal, false);
    };

    function updateCounts(counts) {
        if (!counts) return;
        const registered = document.getElementById('registeredCount');
        const pending = document.getElementById('pendingCount');
        if (registered) registered.textContent = counts.registered;
        if (pending) pending.textContent = counts.pending;
    }

    function updateRegisteredStatus(user) {
        document.querySelectorAll(
            `#registered-row-${user.id} .status-badge, #registered-card-${user.id} .status-badge`
        ).forEach((badge) => {
            badge.textContent = user.status_label;
            badge.className = `status-badge status-${user.status}`;
        });
        document.querySelectorAll(
            `.btn-kebab[data-menu="registered"][data-user-id="${user.id}"]`
        ).forEach((button) => {
            button.dataset.userStatus = user.status;
            button.dataset.userStatusLabel = user.status_label;
        });
    }

    function updatePendingRecord(user) {
        document.querySelectorAll(
            `.btn-kebab[data-menu="pending"][data-user-id="${user.id}"]`
        ).forEach((button) => {
            button.dataset.userFullName = user.full_name;
            button.dataset.userName = user.full_name;
            button.dataset.userCompany = user.company || '—';
            button.dataset.userRole = user.role;
            button.dataset.userRoleLabel = user.role_label;
        });
        document.querySelectorAll(
            `#pending-row-${user.id} .user-fullname, #pending-card-${user.id} .user-fullname`
        ).forEach((name) => {
            name.textContent = user.full_name;
        });
        document.querySelectorAll(
            `#pending-row-${user.id} .user-role-label, #pending-card-${user.id} .user-role-label`
        ).forEach((role) => {
            role.textContent = user.role_label;
        });
    }

    function removePendingRecord(userId) {
        document.getElementById(`pending-row-${userId}`)?.remove();
        document.getElementById(`pending-card-${userId}`)?.remove();
        const panel = document.getElementById('tab-pending');
        if (!panel?.querySelector('[id^="pending-row-"]')) {
            panel.querySelector('.users-container')?.remove();
            panel.querySelector('.table-footer')?.remove();
            if (!panel.querySelector('.dynamic-empty')) {
                const empty = document.createElement('div');
                empty.className = 'empty-state dynamic-empty';
                empty.innerHTML = '<i class="bi bi-check-circle"></i><p>No hay solicitudes pendientes</p>';
                panel.querySelector('.table-card')?.append(empty);
            }
        }
    }

    async function refreshPanels(panelNames) {
        const response = await fetch(window.location.href, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Accept': 'text/html',
                'X-Requested-With': 'XMLHttpRequest',
            },
        });
        if (!response.ok || response.redirected) {
            throw new Error('No se pudo actualizar la tabla automáticamente.');
        }
        const html = await response.text();
        const parsed = new DOMParser().parseFromString(html, 'text/html');
        panelNames.forEach((panelName) => {
            const current = document.getElementById(`tab-${panelName}`);
            const updated = parsed.getElementById(`tab-${panelName}`);
            if (current && updated) {
                current.replaceChildren(...updated.childNodes);
            }
        });
    }

    async function jsonRequest(url, formData = new FormData()) {
        let response;
        try {
            response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken(),
                },
                body: formData,
            });
        } catch (_error) {
            throw new Error('No hay conexión con el servidor. Inténtalo de nuevo.');
        }

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            if (response.status === 401 || response.redirected) {
                throw new Error('La sesión ha caducado. Inicia sesión de nuevo.');
            }
            throw new Error('El servidor devolvió una respuesta no válida.');
        }
        const payload = await response.json();
        if (!response.ok || !payload.ok) {
            throw new Error(payload.message || `No se pudo completar la acción (${response.status}).`);
        }
        return payload;
    }

    function modalError(message) {
        const error = document.getElementById('confirmModalError');
        error.textContent = message;
        error.classList.add('visible');
    }

    function openConfirmation({
        title,
        message,
        confirmLabel,
        loadingLabel,
        danger = false,
        onConfirm,
    }) {
        const titleElement = document.getElementById('modalTitle');
        const messageElement = document.getElementById('modalMessage');
        const confirmButton = document.getElementById('modalConfirmBtn');
        const error = document.getElementById('confirmModalError');
        titleElement.textContent = title;
        messageElement.textContent = message;
        confirmButton.textContent = confirmLabel;
        confirmButton.className = `btn ${danger ? 'btn-danger' : 'btn-primary'}`;
        confirmButton.disabled = false;
        error.textContent = '';
        error.classList.remove('visible');
        confirmButton.onclick = async () => {
            if (actionInProgress) return;
            actionInProgress = true;
            confirmButton.disabled = true;
            confirmButton.innerHTML = `<i class="bi bi-arrow-repeat"></i> ${loadingLabel}`;
            try {
                const payload = await onConfirm();
                setModalVisibility(confirmModal, false);
                showToast(payload.message);
                if (payload.warning) showToast(payload.warning, 'warning');
            } catch (errorValue) {
                modalError(errorValue.message);
                confirmButton.disabled = false;
                confirmButton.textContent = confirmLabel;
            } finally {
                actionInProgress = false;
            }
        };
        setModalVisibility(confirmModal, true);
        confirmButton.focus();
    }

    window.closeModal = function closeModal() {
        if (actionInProgress) return;
        setModalVisibility(confirmModal, false);
    };

    function statusAction(button, activate) {
        const formData = new FormData();
        formData.append('status', activate ? 'active' : 'disabled');
        openConfirmation({
            title: activate ? '¿Activar usuario?' : '¿Desactivar usuario?',
            message: activate
                ? `${button.dataset.userName} podrá volver a iniciar sesión.`
                : `${button.dataset.userName} no podrá acceder a Fenix hasta que se reactive su cuenta.`,
            confirmLabel: activate ? 'Activar usuario' : 'Desactivar usuario',
            loadingLabel: activate ? 'Activando…' : 'Desactivando…',
            danger: !activate,
            onConfirm: async () => {
                const payload = await jsonRequest(button.dataset.statusUrl, formData);
                updateRegisteredStatus(payload.user);
                updateCounts(payload.counts);
                return payload;
            },
        });
    }

    function resetPassword(button) {
        openConfirmation({
            title: 'Enviar enlace de restablecimiento',
            message: `Se enviará un enlace seguro a ${button.dataset.userEmail}. No se generará ni mostrará ninguna contraseña.`,
            confirmLabel: 'Enviar enlace',
            loadingLabel: 'Enviando…',
            onConfirm: () => jsonRequest(button.dataset.resetUrl),
        });
    }

    function pendingAction(button, approve) {
        const url = approve ? button.dataset.approveUrl : button.dataset.rejectUrl;
        openConfirmation({
            title: approve ? '¿Aprobar solicitud?' : '¿Rechazar solicitud?',
            message: approve
                ? `Se aprobará a ${button.dataset.userName} para ${button.dataset.userCompany} con el rol ${button.dataset.userRoleLabel}.`
                : `La solicitud de ${button.dataset.userEmail} será rechazada y la cuenta no podrá acceder.`,
            confirmLabel: approve ? 'Aprobar solicitud' : 'Rechazar solicitud',
            loadingLabel: approve ? 'Aprobando…' : 'Rechazando…',
            danger: !approve,
            onConfirm: async () => {
                const payload = await jsonRequest(url);
                removePendingRecord(button.dataset.userId);
                updateCounts(payload.counts);
                try {
                    await refreshPanels(approve ? ['registered', 'pending'] : ['pending']);
                } catch (_error) {
                    payload.warning = [
                        payload.warning,
                        'La operación se guardó, pero no se pudo refrescar la tabla automáticamente.',
                    ].filter(Boolean).join(' ');
                }
                return payload;
            },
        });
    }

    actionDropdown.addEventListener('click', (event) => {
        const item = event.target.closest('[role=menuitem]');
        if (!item || !activeActionButton) return;
        const button = activeActionButton;
        const action = item.dataset.action;

        if (item.tagName === 'A') {
            closeActionMenu();
            return;
        }
        event.preventDefault();
        closeActionMenu();

        if (action === 'view-details') openDetails(button, false);
        if (action === 'view-request') openDetails(button, true);
        if (action === 'edit-request') openRequestModal(button);
        if (action === 'activate-user') statusAction(button, true);
        if (action === 'deactivate-user') statusAction(button, false);
        if (action === 'reset-password') resetPassword(button);
        if (action === 'approve') pendingAction(button, true);
        if (action === 'reject') pendingAction(button, false);
    });

    document.addEventListener('click', (event) => {
        if (
            actionDropdown.classList.contains('show')
            && !event.target.closest('#actionDropdown')
            && !event.target.closest('.btn-kebab')
        ) {
            closeActionMenu();
        }
        const closeButton = event.target.closest('[data-close-modal]');
        if (closeButton) {
            setModalVisibility(
                document.getElementById(closeButton.dataset.closeModal),
                false
            );
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Tab' && actionDropdown.classList.contains('show')) {
            closeActionMenu();
            return;
        }
        if (event.key !== 'Escape') return;
        if (actionDropdown.classList.contains('show')) {
            closeActionMenu({ restoreFocus: true });
            return;
        }
        if (!actionInProgress) {
            closeDetailsModal();
            window.closeRequestModal();
            window.closeModal();
        }
    });

    [confirmModal, detailsModal, requestModal].forEach((modal) => {
        modal?.addEventListener('click', (event) => {
            if (event.target === modal && !actionInProgress) {
                setModalVisibility(modal, false);
            }
        });
    });

    window.addEventListener('resize', () => {
        if (activeActionButton && actionDropdown.classList.contains('show')) {
            positionDropdown(activeActionButton);
        }
    });
    window.addEventListener('scroll', () => {
        if (activeActionButton && actionDropdown.classList.contains('show')) {
            const rect = activeActionButton.getBoundingClientRect();
            if (rect.bottom < 0 || rect.top > window.innerHeight) {
                closeActionMenu();
            } else {
                positionDropdown(activeActionButton);
            }
        }
    }, true);

    window.switchTab = function switchTab(event, tabName) {
        closeActionMenu();
        document.querySelectorAll('.tab-panel').forEach((panel) => {
            panel.classList.toggle('active', panel.id === `tab-${tabName}`);
        });
        document.querySelectorAll('.tab-button').forEach((button) => {
            button.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        const url = new URL(window.location);
        url.searchParams.set('tab', tabName);
        url.searchParams.delete('page');
        window.history.replaceState({}, '', url);
    };

    window.toggleSelectAll = function toggleSelectAll(checkbox) {
        checkbox.closest('table')?.querySelectorAll('.row-checkbox').forEach((item) => {
            item.checked = checkbox.checked;
        });
    };

    document.getElementById('requestForm')?.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (actionInProgress) return;
        const form = event.currentTarget;
        const submitButton = document.getElementById('requestSubmitBtn');
        const error = document.getElementById('requestModalError');
        actionInProgress = true;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Guardando…';
        error.textContent = '';
        error.classList.remove('visible');
        try {
            const payload = await jsonRequest(form.action, new FormData(form));
            updatePendingRecord(payload.user);
            updateCounts(payload.counts);
            setModalVisibility(requestModal, false);
            showToast(payload.message);
            if (payload.warning) showToast(payload.warning, 'warning');
        } catch (errorValue) {
            error.textContent = errorValue.message;
            error.classList.add('visible');
        } finally {
            actionInProgress = false;
            submitButton.disabled = false;
            submitButton.textContent = 'Guardar';
        }
    });
})();
