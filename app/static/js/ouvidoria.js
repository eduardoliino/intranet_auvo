document.addEventListener('alpine:init', () => {
    Alpine.data('formOuvidoria', () => ({
        // --- Estado do Formulário ---
        formData: {
            tipo_denuncia: '',
            mensagem: '',
            identificado: false,
            nome: '',
            contato: ''
        },
        feedback: { message: '', type: '' },
        submitting: false,

        // --- Funções ---
        submitForm() {
            this.submitting = true;

            fetch('/ouvidoria', {
                method: 'POST',
                body: new URLSearchParams(this.formData)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.showFeedback(data.message, 'success');
                    // Limpa o formulário após o sucesso
                    this.formData = { tipo_denuncia: '', mensagem: '', identificado: false, nome: '', contato: '' };
                } else {
                    this.showFeedback(data.message || 'Ocorreu um erro.', 'danger');
                }
            })
            .finally(() => {
                this.submitting = false;
            });
        },

        showFeedback(message, type) {
            this.feedback.message = message;
            this.feedback.type = type;
            // A mensagem desaparece após 5 segundos
            setTimeout(() => {
                this.feedback.message = '';
            }, 5000);
        }
    }));
});