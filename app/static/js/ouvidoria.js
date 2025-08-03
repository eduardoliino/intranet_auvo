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
        tsInstance: null, // Para guardar a instância do Tom Select

        init() {
            // Inicializa o Tom Select no nosso campo <select>
            this.tsInstance = new TomSelect(this.$refs.assuntoSelect, {
                // A opção onChange atualiza o nosso modelo de dados no AlpineJS
                onChange: (value) => {
                    this.formData.tipo_denuncia = value;
                }
            });
        },

        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        },

        async submitForm() {
            if (!this.formData.tipo_denuncia) {
                this.showToast('Por favor, selecione um assunto antes de enviar.', 'warning');
                return;
            }
            
            this.submitting = true;

            const response = await fetch('/ouvidoria', {
                method: 'POST',
                body: new URLSearchParams(this.formData)
            });
            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                // Reseta o formulário de dados
                this.formData = { 
                    tipo_denuncia: '', 
                    mensagem: '', 
                    identificado: false, 
                    nome: '', 
                    contato: '' 
                };
                // Limpa visualmente o campo Tom Select
                this.tsInstance.clear();
            } else {
                this.showToast(data.message || 'Ocorreu um erro.', 'danger');
            }
            
            this.submitting = false;
        }
    }));
});