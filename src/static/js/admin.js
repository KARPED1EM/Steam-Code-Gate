// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        document.getElementById(`${tab}-panel`).classList.add('active');
    });
});

// Toast notification
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.textContent = message;
    toast.style.marginBottom = '12px';

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Modal functions
function showCreateAccountModal() {
    showModal('create-account-modal');
}

function showEditAccountModal(id) {
    // TODO: Load account data and populate form
    showModal('edit-account-modal');
}

function showCreateAdminModal() {
    showModal('create-admin-modal');
}

function showEditAdminModal(id) {
    // TODO: Load admin data and populate form
    showModal('edit-admin-modal');
}

function toggleProviderConfig() {
    const providerType = document.getElementById('create-provider-type').value;
    const emailConfig = document.getElementById('email-config');
    const otpConfig = document.getElementById('otp-config');

    if (providerType === 'email') {
        emailConfig.classList.remove('hidden');
        otpConfig.classList.add('hidden');
    } else {
        emailConfig.classList.add('hidden');
        otpConfig.classList.remove('hidden');
    }

    updateProviderValidation(providerType);
}

function getLengthHint(input) {
    const minLength = input.minLength > 0 ? input.minLength : null;
    const maxLength = input.maxLength > 0 ? input.maxLength : null;
    if (minLength && maxLength) {
        return `（${minLength}-${maxLength} 个字符）`;
    }
    if (minLength) {
        return `（至少 ${minLength} 个字符）`;
    }
    if (maxLength) {
        return `（最多 ${maxLength} 个字符）`;
    }
    if (input.type === 'number' && (input.min || input.max)) {
        if (input.min && input.max) {
            return `（${input.min}-${input.max}）`;
        }
        if (input.min) {
            return `（不小于 ${input.min}）`;
        }
        if (input.max) {
            return `（不大于 ${input.max}）`;
        }
    }
    return '';
}

function getValidationMessage(input, label) {
    const validity = input.validity;
    if (validity.valueMissing) {
        return `请输入${label}${getLengthHint(input)}`;
    }
    if (validity.typeMismatch && input.type === 'email') {
        return `请输入有效的${label}`;
    }
    if (validity.tooShort) {
        return `${label}至少需要 ${input.minLength} 个字符`;
    }
    if (validity.tooLong) {
        return `${label}不能超过 ${input.maxLength} 个字符`;
    }
    if (validity.rangeUnderflow || validity.rangeOverflow) {
        return `${label}需在 ${input.min} 到 ${input.max} 之间`;
    }
    return '';
}

function prepareFormValidation(form, fields) {
    fields.forEach(({ input, label }) => {
        if (input.disabled) {
            input.setCustomValidity('');
            return;
        }
        input.setCustomValidity('');
        const message = getValidationMessage(input, label);
        if (message) {
            input.setCustomValidity(message);
        }
    });

    if (!form.checkValidity()) {
        form.reportValidity();
        return false;
    }
    return true;
}

function attachFieldValidation(fields) {
    fields.forEach(({ input, label }) => {
        input.addEventListener('input', () => input.setCustomValidity(''));
        input.addEventListener('invalid', () => {
            if (input.disabled) {
                return;
            }
            const message = getValidationMessage(input, label);
            if (message) {
                input.setCustomValidity(message);
            }
        });
    });
}

function updateProviderValidation(providerType) {
    const emailFields = [
        document.getElementById('create-imap-server'),
        document.getElementById('create-imap-port'),
        document.getElementById('create-email-address'),
        document.getElementById('create-email-password')
    ];
    const otpField = document.getElementById('create-otp-token');
    const useEmail = providerType === 'email';

    emailFields.forEach((field) => {
        field.required = useEmail;
        field.disabled = !useEmail;
        field.setCustomValidity('');
    });

    otpField.required = !useEmail;
    otpField.disabled = useEmail;
    otpField.setCustomValidity('');
}

const profileFormFields = [
    { input: document.getElementById('profile-username'), label: '用户名' },
    { input: document.getElementById('profile-password'), label: '新密码' },
    { input: document.getElementById('profile-contact'), label: '联系方式' }
];

const createAccountFields = [
    { input: document.getElementById('create-name'), label: '显示名称' },
    { input: document.getElementById('create-account-name'), label: '账号名' },
    { input: document.getElementById('create-password'), label: '密码' },
    { input: document.getElementById('create-imap-server'), label: 'IMAP 服务器' },
    { input: document.getElementById('create-imap-port'), label: 'IMAP 端口' },
    { input: document.getElementById('create-email-address'), label: '邮箱地址' },
    { input: document.getElementById('create-email-password'), label: '邮箱密码' },
    { input: document.getElementById('create-otp-token'), label: 'OTP Token' },
    { input: document.getElementById('create-passphrase'), label: '访问口令' }
];

const createAdminFields = [
    { input: document.getElementById('admin-username'), label: '用户名' },
    { input: document.getElementById('admin-password'), label: '密码' },
    { input: document.getElementById('admin-contact'), label: '联系方式' }
];

attachFieldValidation(profileFormFields);
attachFieldValidation(createAccountFields);
attachFieldValidation(createAdminFields);

updateProviderValidation(document.getElementById('create-provider-type').value);

// Profile form
document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!prepareFormValidation(e.target, profileFormFields)) {
        return;
    }

    const data = {
        username: document.getElementById('profile-username').value,
        contact_info: document.getElementById('profile-contact').value
    };

    const password = document.getElementById('profile-password').value;
    if (password) {
        data.password = password;
    }

    try {
        const response = await fetch('/api/admin/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast('个人资料已更新', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '更新失败', 'error');
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'error');
    }
});

// Create Steam account
document.getElementById('create-account-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const providerType = document.getElementById('create-provider-type').value;
    updateProviderValidation(providerType);

    if (!prepareFormValidation(e.target, createAccountFields)) {
        return;
    }

    const data = {
        name: document.getElementById('create-name').value,
        account_name: document.getElementById('create-account-name').value,
        password: document.getElementById('create-password').value || null,
        is_password_public: document.getElementById('create-password-public').checked,
        code_provider_type: providerType,
        access_passphrase: document.getElementById('create-passphrase').value
    };

    if (providerType === 'email') {
        data.email_config = {
            imap_server: document.getElementById('create-imap-server').value,
            imap_port: parseInt(document.getElementById('create-imap-port').value),
            email_address: document.getElementById('create-email-address').value,
            email_password: document.getElementById('create-email-password').value,
            use_ssl: document.getElementById('create-use-ssl').checked
        };
    } else {
        data.otp_token = document.getElementById('create-otp-token').value;
    }

    try {
        const response = await fetch('/api/admin/steam-accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast('Steam 账号已创建', 'success');
            closeModal('create-account-modal');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '创建失败', 'error');
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'error');
    }
});

// Create admin
document.getElementById('create-admin-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!prepareFormValidation(e.target, createAdminFields)) {
        return;
    }

    const data = {
        username: document.getElementById('admin-username').value,
        password: document.getElementById('admin-password').value,
        contact_info: document.getElementById('admin-contact').value || null,
        is_super_admin: document.getElementById('admin-is-super').checked
    };

    try {
        const response = await fetch('/api/super-admin/administrators', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast('管理员已创建', 'success');
            closeModal('create-admin-modal');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '创建失败', 'error');
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'error');
    }
});

// Delete Steam account
async function deleteAccount(id) {
    const confirmed = await showConfirm(
        '确定要删除这个 Steam 账号吗？此操作不可撤销，该账号的所有数据将被永久删除。',
        null,
        '删除 Steam 账号'
    );

    if (!confirmed) return;

    try {
        const response = await fetch(`/api/admin/steam-accounts/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('账号已删除', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '删除失败', 'error');
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'error');
    }
}

// Delete admin
async function deleteAdmin(id) {
    const confirmed = await showConfirm(
        '确定要删除这个管理员吗？此操作不可撤销，该管理员的账号及其所有 Steam 托管账号都将被删除。',
        null,
        '删除管理员'
    );

    if (!confirmed) return;

    try {
        const response = await fetch(`/api/super-admin/administrators/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('管理员已删除', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '删除失败', 'error');
        }
    } catch (error) {
        showToast('网络错误，请稍后重试', 'error');
    }
}

async function loadEmailStatuses() {
    const statusElements = document.querySelectorAll('.email-status');
    if (!statusElements.length) {
        return;
    }

    try {
        const response = await fetch('/api/admin/steam-accounts/email-status');
        if (!response.ok) {
            throw new Error('status load failed');
        }

        const data = await response.json();
        const statusMap = new Map(
            (data.statuses || []).map((item) => [String(item.account_id), item])
        );

        statusElements.forEach((el) => {
            const accountId = el.dataset.accountId;
            const status = statusMap.get(accountId);
            if (!status) {
                el.textContent = '未知';
                el.classList.remove('status-pending');
                el.classList.add('status-error');
                return;
            }

            if (status.status === 'ok') {
                el.textContent = '正常';
                el.classList.remove('status-pending', 'status-error');
                el.classList.add('status-ok');
            } else {
                el.textContent = '异常';
                el.classList.remove('status-pending', 'status-ok');
                el.classList.add('status-error');
                if (status.detail) {
                    el.title = status.detail;
                }
            }
        });
    } catch (error) {
        statusElements.forEach((el) => {
            el.textContent = '检测失败';
            el.classList.remove('status-pending');
            el.classList.add('status-error');
        });
    }
}

loadEmailStatuses();
