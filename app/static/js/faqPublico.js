document.addEventListener('alpine:init', () => {
    Alpine.data('faqSistema', () => ({
        search: '',
        filtroCategoria: '',
        categorias: window._categoriasFaqData || [],
        perguntas: window._perguntasFaqData || [],

        get filteredPerguntas() {
            return this.perguntas.filter(p => {
                const categoriaMatch = this.filtroCategoria ? p.categoria_id == this.filtroCategoria : true;
                
                if (this.search.trim() === '') {
                    return categoriaMatch;
                }

                const searchTerm = this.search.toLowerCase();
                const searchMatch = p.pergunta.toLowerCase().includes(searchTerm) ||
                                  p.resposta.toLowerCase().includes(searchTerm) ||
                                  (p.palavras_chave && p.palavras_chave.toLowerCase().includes(searchTerm));
                
                return categoriaMatch && searchMatch;
            });
        }
    }));
});