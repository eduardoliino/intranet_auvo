document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarFaq', () => ({
        // --- Dados Iniciais ---
        categorias: window._categoriasData || [],
        perguntas: window._perguntasData || [],
        search: '',

        // --- Estado dos Formulários ---
        novaCategoriaNome: '',
        novaPergunta: {
            pergunta: '',
            resposta: '',
            categoria_id: '',
            palavras_chave: '',
            link_url: '',
            link_texto: ''
        },

        // --- Lógica de Exibição ---
        get filteredPerguntas() {
            if (this.search.trim() === '') {
                return this.perguntas;
            }
            const searchTerm = this.search.toLowerCase();
            return this.perguntas.filter(p => 
                p.pergunta.toLowerCase().includes(searchTerm) ||
                p.resposta.toLowerCase().includes(searchTerm) ||
                (p.palavras_chave && p.palavras_chave.toLowerCase().includes(searchTerm))
            );
        },

        // --- Funções de API ---
        adicionarCategoria() {
            fetch('/admin/faq/categorias/adicionar', {
                method: 'POST',
                body: new URLSearchParams({ nome: this.novaCategoriaNome })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.categorias.push(data.categoria);
                    this.novaCategoriaNome = ''; // Limpa o campo
                } else {
                    alert(data.message); // Exibe o erro
                }
            });
        },
        removerCategoria(id) {
            if (confirm('Tem a certeza? Remover uma categoria também removerá todas as perguntas associadas.')) {
                fetch(`/admin/faq/categorias/remover/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.categorias = this.categorias.filter(c => c.id !== id);
                        // Recarrega as perguntas, pois as associadas foram removidas
                        this.perguntas = this.perguntas.filter(p => p.categoria_id !== id);
                    } else {
                        alert('Erro ao remover categoria.');
                    }
                });
            }
        },
        adicionarPergunta() {
            fetch('/admin/faq/perguntas/adicionar', {
                method: 'POST',
                body: new URLSearchParams(this.novaPergunta)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.perguntas.unshift(data.pergunta); // Adiciona no topo da lista
                    // Limpa o formulário
                    this.novaPergunta = { pergunta: '', resposta: '', categoria_id: '', palavras_chave: '', link_url: '', link_texto: '' };
                } else {
                    alert(data.message);
                }
            });
        },
        removerPergunta(id) {
            if (confirm('Tem a certeza de que deseja remover esta pergunta?')) {
                fetch(`/admin/faq/perguntas/remover/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.perguntas = this.perguntas.filter(p => p.id !== id);
                    } else {
                        alert('Erro ao remover pergunta.');
                    }
                });
            }
        }
    }));
});