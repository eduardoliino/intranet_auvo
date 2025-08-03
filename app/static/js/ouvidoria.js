document.addEventListener('alpine:init', () => {
    Alpine.data('formOuvidoria', () => ({
        formData: {
            tipo_denuncia: '',
            mensagem: '',
            identificado: false,
            nome: '',
            contato: ''
        },
        submitting: false,

        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        },

        async submitForm() {
            this.submitting = true;

            const response = await fetch('/ouvidoria', {
                method: 'POST',
                body: new URLSearchParams(this.formData)
            });
            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                this.formData = { tipo_denuncia: '', mensagem: '', identificado: false, nome: '', contato: '' };
            } else {
                this.showToast(data.message || 'Ocorreu um erro.', 'danger');
            }
            
            this.submitting = false;
        }
    }));
});