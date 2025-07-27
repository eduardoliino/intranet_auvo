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
            color: '#3788d8',
        },
        modalInstance: null,

        init() {
            this.eventos = window._eventosData || [];
            const modalEl = document.getElementById('eventoModal');
            if (modalEl) {
                this.modalInstance = new bootstrap.Modal(modalEl);
            }
        },

        resetarForm() {
            this.editando = false;
            this.form = { id: null, title: '', start: '', end: '', description: '', location: '', color: '#3788d8' };
        },

        abrirModal(evento = null) {
            this.resetarForm();
            if (evento) {
                this.editando = true;
                // Formata as datas para o input datetime-local (YYYY-MM-DDTHH:mm)
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
            const method = 'POST';

            fetch(url, {
                method: method,
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
                    this.modalInstance.hide();
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'success', message: `Evento ${this.editando ? 'atualizado' : 'criado'} com sucesso!` }}));
                } else {
                    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'danger', message: data.message || 'Ocorreu um erro.' }}));
                }
            });
        },

        removerEvento(id) {
            if (confirm('Tem a certeza de que deseja apagar este evento?')) {
                fetch(`/admin/eventos/remover/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.eventos = this.eventos.filter(e => e.id !== id);
                        window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'info', message: 'Evento removido com sucesso.' }}));
                    }
                });
            }
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