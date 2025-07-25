document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarOuvidoria', () => ({
        entradas: window._ouvidoriaData || [],
        filtroStatus: '',

        get filteredEntradas() {
            if (this.filtroStatus === '') {
                return this.entradas;
            }
            return this.entradas.filter(e => e.status === this.filtroStatus);
        },

        atualizarStatus(id, novoStatus) {
            fetch(`/admin/ouvidoria/atualizar_status/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: novoStatus })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const index = this.entradas.findIndex(e => e.id === id);
                    if (index !== -1) {
                        this.entradas[index].status = novoStatus;
                    }
                } else {
                    alert('Erro ao atualizar o status.');
                }
            });
        }
    }));
});