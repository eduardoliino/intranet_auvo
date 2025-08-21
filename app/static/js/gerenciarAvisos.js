/**
 * @file gerenciarAvisos.js
 * Componente para administração de avisos, permitindo criar e remover avisos.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarAvisos', () => ({
        avisos: window._avisosData || [], // Lista de avisos existentes
        novoAviso: {
            titulo: '',
            conteudo: '',
            link_url: '',
            link_texto: ''
        }, // Modelo do formulário para um novo aviso
        feedback: { message: '', type: '' }, // Mensagem de feedback ao utilizador

        // Envia os dados para criar um novo aviso
        adicionarAviso() {
            fetch('/admin/avisos/adicionar', {
                method: 'POST',
                body: new URLSearchParams(this.novoAviso)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.avisos.unshift(data.aviso);
                    this.novoAviso = { titulo: '', conteudo: '', link_url: '', link_texto: '' };
                    this.showFeedback('Aviso publicado com sucesso!', 'success');
                } else {
                    this.showFeedback(data.message || 'Erro ao adicionar aviso.', 'danger');
                }
            });
        },

        // Remove um aviso específico após confirmação do utilizador
        removerAviso(id) {
            if (confirm('Tem a certeza de que deseja remover este aviso?')) {
                fetch(`/admin/avisos/remover/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.avisos = this.avisos.filter(a => a.id !== id);
                        this.showFeedback(data.message, 'info');
                    } else {
                        this.showFeedback('Erro ao remover aviso.', 'danger');
                    }
                });
            }
        },

        // Exibe uma mensagem temporária de feedback
        showFeedback(message, type) {
            this.feedback.message = message;
            this.feedback.type = type;
            setTimeout(() => {
                this.feedback.message = '';
            }, 3000);
        }
    }));
});