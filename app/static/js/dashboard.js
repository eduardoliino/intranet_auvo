document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        // --- Dados Iniciais ---
        totalColaboradores: window._totalColaboradores || 0,
        
        // --- Estado da Página ---
        selectedAviso: null,
        count: 0,

        // --- Método de Inicialização ---
        init() {
            // Animação do contador de colaboradores
            if (this.totalColaboradores > 0) {
                let step = Math.max(1, this.totalColaboradores / 100);
                let current = 0;
                let timer = setInterval(() => {
                    current += step;
                    if (current >= this.totalColaboradores) {
                        current = this.totalColaboradores;
                        clearInterval(timer);
                    }
                    this.count = Math.floor(current);
                }, 15);
            }
        },

        // Abre o modal de detalhes do Aviso
        openAvisoModal(aviso) {
            this.selectedAviso = aviso;
            const avisoModal = new bootstrap.Modal(document.getElementById('avisoDetailModal'));
            avisoModal.show();
        }
    }));
});