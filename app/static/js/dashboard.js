document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        // --- Dados Iniciais (vindos do Flask) ---
        eventos: window._eventosData || [],
        totalColaboradores: window._totalColaboradoresData || 0,
        
        // --- Estado da Página ---
        selectedEvent: null,
        count: 0,

        // --- Método de Inicialização ---
        // Este método é executado assim que a página carrega
        init() {
            // Lógica para o efeito de "fade-in" dos cards
            this.$nextTick(() => {
                document.querySelectorAll('.fade-in-card').forEach((el, index) => {
                    setTimeout(() => {
                        el.classList.add('visible');
                    }, index * 100);
                });
            });

            // Lógica para a animação do contador de colaboradores
            if (this.totalColaboradores > 0) {
                let step = this.totalColaboradores / 100;
                let current = 0;
                let timer = setInterval(() => {
                    current += step;
                    if (current >= this.totalColaboradores) {
                        current = this.totalColaboradores;
                        clearInterval(timer);
                    }
                    this.count = Math.floor(current);
                }, 10);
            }
        },

        // --- Métodos de Ação ---
        // Função para abrir o modal com os detalhes do evento
        openEventModal(eventId) {
            this.selectedEvent = this.eventos.find(e => e.id === eventId);
            const eventModal = new bootstrap.Modal(document.getElementById('eventDetailModal'));
            eventModal.show();
        }
    }));
});