/**
 * @file gerenciarOuvidoria.js
 * Componente para visualização e atualização de entradas da ouvidoria.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarOuvidoria', () => ({
        entradas: window._ouvidoriaData || [], // Lista de denúncias recebidas
        filtroStatus: '', // Filtro aplicado pelo estado da denúncia
        search: '', // Texto de pesquisa
        modal: null, // Instância do modal de detalhes
        tsInstance: null, // Instância do Tom Select
        modalData: { id: null, title: '', content: '', status: '' }, // Dados exibidos no modal

        init() {
            const modalEl = document.getElementById('ouvidoriaModal');
            this.modal = new bootstrap.Modal(modalEl);

            modalEl.addEventListener('hidden.bs.modal', () => {
                if (this.tsInstance) {
                    this.tsInstance.destroy();
                    this.tsInstance = null;
                }
            });
        },

        get filteredEntradas() {
            const searchLower = this.search.toLowerCase();
            return this.entradas.filter(e => {
                const statusMatch = this.filtroStatus === '' || e.status === this.filtroStatus;

                const searchMatch = this.search.trim() === '' ||
                    e.tipo_denuncia.toLowerCase().includes(searchLower) ||
                    e.mensagem.toLowerCase().includes(searchLower) ||
                    (!e.anonima && e.nome && e.nome.toLowerCase().includes(searchLower)) ||
                    (!e.anonima && e.contato && e.contato.toLowerCase().includes(searchLower));

                return statusMatch && searchMatch;
            });
        },

        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        },

        // Abre o modal com os detalhes completos da entrada
        verDetalhes(entrada) {
            this.modalData.id = entrada.id;
            this.modalData.title = `Ocorrência #${entrada.id} - ${entrada.tipo_denuncia}`;
            this.modalData.status = entrada.status;

            let remetenteHtml = entrada.anonima
                ? `<p class="text-muted fst-italic">O remetente optou por permanecer anônimo.</p>`
                : `
                    <p class="mb-1"><strong>Nome:</strong> ${entrada.nome || 'Não fornecido'}</p>
                    <p class="mb-0"><strong>Contato:</strong> ${entrada.contato || 'Não fornecido'}</p>
                `;

            this.modalData.content = `
                <h6>Mensagem:</h6>
                <p style="white-space: pre-wrap; word-break: break-word;" class="p-3 bg-light rounded">${entrada.mensagem}</p>
                <hr>
                <h6>Remetente:</h6>
                ${remetenteHtml}
            `;

            this.$nextTick(() => {
                const selectEl = document.getElementById('status-select');
                this.tsInstance = new TomSelect(selectEl, {
                    create: false,
                    onInitialize: function() {
                        this.control_input.readOnly = true;
                    },
                    onChange: (value) => {
                        this.atualizarStatus(this.modalData.id, value);
                    }
                });
                this.tsInstance.setValue(entrada.status, true);
            });

            this.modal.show();
        },

        // Atualiza o status de uma entrada através da API
        async atualizarStatus(id, novoStatus) {
            const response = await fetch(`/admin/ouvidoria/atualizar_status/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: novoStatus })
            });
            const data = await response.json();

            if (data.success) {
                const index = this.entradas.findIndex(e => e.id === id);
                if (index !== -1) {
                    let items = [...this.entradas];
                    items[index].status = novoStatus;
                    this.entradas = items;
                }

                this.modalData.status = novoStatus;
                this.showToast('Status atualizado com sucesso!', 'success');
                window.dispatchEvent(new CustomEvent('ouvidoria-updated'));
            } else {
                this.showToast('Erro ao atualizar o status.', 'danger');
            }
        }
    }));
});