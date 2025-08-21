/**
 * @file faqPublico.js
 * Componente responsável por listar e filtrar perguntas frequentes públicas.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('faqSistema', () => ({
        search: '', // Texto pesquisado pelo utilizador
        filtroCategoria: '', // Filtro da categoria selecionada
        categorias: window._categoriasFaqData || [], // Categorias disponíveis
        perguntas: [], // Lista de perguntas carregadas

        page: 1, // Página atual para paginação
        isLoading: false, // Estado de carregamento das perguntas
        hasMore: true, // Indica se existem mais perguntas a carregar

        init() {
            this.fetchPerguntas();
        },

        // Obtém perguntas do backend com base nos filtros aplicados
        async fetchPerguntas() {
            if (this.isLoading || !this.hasMore) return;
            this.isLoading = true;

            const params = {
                page: this.page,
                search: this.search
            };
            if (this.filtroCategoria) {
                params.category = this.filtroCategoria;
            }
            const queryString = new URLSearchParams(params).toString();

            try {
                const response = await fetch(`/api/faq?${queryString}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                if (data.perguntas && data.perguntas.length > 0) {
                    this.perguntas.push(...data.perguntas);
                }

                this.hasMore = data.has_next;
                this.page += 1;
            } catch (error) {
                console.error('Erro ao buscar perguntas do FAQ:', error);
                this.showToast('Não foi possível carregar as perguntas. Verifique o console para mais detalhes.', 'danger');
            } finally {
                this.isLoading = false;
            }
        },

        resetAndFetch() {
            this.page = 1;
            this.perguntas = [];
            this.hasMore = true;
            // Usamos um pequeno timeout para garantir que os modelos do Alpine sejam atualizados antes da busca
            setTimeout(() => this.fetchPerguntas(), 50);
        },

        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        }
    }));
});