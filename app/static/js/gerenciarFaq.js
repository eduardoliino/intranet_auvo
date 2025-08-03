document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarFaq', () => ({
        perguntas: window._perguntasData || [],
        search: '',

        get filteredPerguntas() {
            if (this.search.trim() === '') {
                return this.perguntas;
            }
            const searchTerm = this.search.toLowerCase();
            return this.perguntas.filter(p => 
                p.pergunta.toLowerCase().includes(searchTerm) ||
                (p.resposta && p.resposta.toLowerCase().includes(searchTerm)) ||
                (p.palavras_chave && p.palavras_chave.toLowerCase().includes(searchTerm)) ||
                (p.categoria_nome && p.categoria_nome.toLowerCase().includes(searchTerm))
            );
        },
        
        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        },

        async removerPergunta(id) {
            if (confirm('Tem a certeza de que deseja remover esta pergunta?')) {
                const response = await fetch(`/admin/faq/perguntas/remover/${id}`, { method: 'DELETE' });
                const data = await response.json();

                if (data.success) {
                    this.perguntas = this.perguntas.filter(p => p.id !== id);
                    this.showToast(data.message, 'info');
                } else {
                    this.showToast('Erro ao remover pergunta.', 'danger');
                }
            }
        }
    }));
});