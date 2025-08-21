document.addEventListener('alpine:init', () => {
    Alpine.data('gestaoEventos', () => ({
        eventos: [],
        editando: false,
        form: {
            id: null,
            title: '',
            start: '',
            end: '',
            description: '',
            location: '',
        },
        modalInstance: null,
        // Referências ao modal de confirmação
        eventoParaRemover: {},
        confirmacaoModal: null,

        init() {
            this.eventos = window._eventosData || [];
            
            const eventoModalEl = document.getElementById('eventoModal');
            if (eventoModalEl) {
                this.modalInstance = new bootstrap.Modal(eventoModalEl);
            }
            
            // Inicializa o modal de confirmação
            const confirmacaoModalEl = document.getElementById('confirmacaoModal');
            if (confirmacaoModalEl) {
                this.confirmacaoModal = new bootstrap.Modal(confirmacaoModalEl);
            }
        },

        resetarForm() {
            this.editando = false;
            this.form = { id: null, title: '', start: '', end: '', description: '', location: '' };
        },

        abrirModal(evento = null) {
            this.resetarForm();
            if (evento) {
                this.editando = true;
                this.form = {
                    ...evento,
                    start: evento.start ? evento.start.slice(0, 16) : '',
                    end: evento.end ? evento.end.slice(0, 16) : '',
                };
            }
            this.modalInstance.show();
        },

        salvarEvento() {
            const url = this.editando ? `/admin/eventos/editar/${this.form.id}` : '/admin/eventos/novo';
            
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (this.editando) {
                        const index = this.eventos.findIndex(e => e.id === data.evento.id);
                        this.eventos[index] = data.evento;
                    } else {
                        this.eventos.unshift(data.evento);
                    }
                    this.eventos.sort((a, b) => new Date(b.start) - new Date(a.start));
                    this.modalInstance.hide();
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'success', message: `Evento ${this.editando ? 'atualizado' : 'criado'} com sucesso!` }}));
                } else {
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'danger', message: data.message || 'Ocorreu um erro.' }}));
                }
            });
        },

        // Abre o modal de confirmação antes de remover
        abrirModalConfirmacao(evento) {
            this.eventoParaRemover = evento;
            this.confirmacaoModal.show();
        },

        // Remove o evento após confirmação
        removerEvento() {
            const id = this.eventoParaRemover.id;
            if (!id) return;

            fetch(`/admin/eventos/remover/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.eventos = this.eventos.filter(e => e.id !== id);
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'info', message: 'Evento removido com sucesso.' }}));
                } else {
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'danger', message: 'Erro ao remover evento.' }}));
                }
                this.confirmacaoModal.hide();
                this.eventoParaRemover = {};
            });
        },

        
        isEventoPassado(evento) {
            const dataEvento = new Date(evento.start);
            const agora = new Date();
            return dataEvento < agora;
        },

        formatarData(isoString) {
            if (!isoString) return '';
            const data = new Date(isoString);
            return data.toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }));
});