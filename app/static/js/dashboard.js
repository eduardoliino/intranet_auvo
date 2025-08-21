/**
 * @file dashboard.js
 * Componente do painel principal responsável por animar o contador de colaboradores
 * e exibir detalhes de avisos e eventos em modais.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        totalColaboradores: window._totalColaboradores || 0, // Número total de colaboradores exibidos no contador

        count: 0, // Valor animado do contador
        modalData: {
            title: '',
            content: '',
            footer: '',
            link_url: '',
            link_texto: ''
        }, // Dados dinâmicos do modal
        bsModal: null, // Instância do modal Bootstrap

        // Inicializa o componente e prepara o modal
        init() {
            this.$nextTick(() => {
                const modalElement = document.getElementById('detailModal');
                if (modalElement) {
                    this.bsModal = new bootstrap.Modal(modalElement);
                } else {
                    console.error('O elemento do Modal #detailModal não foi encontrado.');
                }
            });

            this.animateCounter();
        },

        // Anima de forma incremental o contador de colaboradores
        animateCounter() {
            if (this.totalColaboradores <= 0) return;
            let step = Math.max(1, Math.ceil(this.totalColaboradores / 100));
            let current = 0;
            let timer = setInterval(() => {
                current += step;
                if (current >= this.totalColaboradores) {
                    current = this.totalColaboradores;
                    clearInterval(timer);
                }
                this.count = Math.floor(current);
            }, 15);
        },

        // Abre o modal e exibe as informações completas de um aviso
        openAvisoModal(aviso) {
            if (!this.bsModal) {
                console.error('Modal não está inicializado.');
                return;
            }

            this.modalData.title = aviso.titulo;
            this.modalData.content = `<p style="white-space: pre-wrap; word-break: break-word;">${aviso.conteudo}</p>`;
            this.modalData.link_url = aviso.link_url;
            this.modalData.link_texto = aviso.link_texto || 'Saber mais';

            const dataAviso = new Date(aviso.data_criacao_iso);
            this.modalData.footer = `Publicado em: ${dataAviso.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' })}`;

            this.bsModal.show();
        },

        // Abre o modal com detalhes formatados de um evento do calendário
        openEventoModal(evento) {
            if (!this.bsModal) {
                console.error('Modal não está inicializado.');
                return;
            }

            const dataInicio = new Date(evento.start);
            const dataFim = evento.end ? new Date(evento.end) : null;

            let dataFormatada = dataInicio.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
            let horaFormatada = `Início: ${dataInicio.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;

            if (dataFim) {
                if (dataInicio.toDateString() === dataFim.toDateString()) {
                    horaFormatada += ` - Fim: ${dataFim.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
                } else {
                    horaFormatada += ` | Fim: ${dataFim.toLocaleDateString('pt-BR')} às ${dataFim.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
                }
            }

            this.modalData.title = evento.title;

            let conteudoHtml = `<div style="white-space: pre-wrap; word-break: break-word;">${evento.description || 'Nenhuma descrição fornecida.'}</div><hr class="my-2">`;
            if (evento.location) {
                conteudoHtml += `<p class="mb-1"><strong><i class="bi bi-geo-alt-fill"></i> Local:</strong> ${evento.location}</p>`;
            }
            conteudoHtml += `<p class="mb-0"><strong><i class="bi bi-clock-fill"></i> Quando:</strong> ${dataFormatada}</p>`;
            conteudoHtml += `<p class="text-muted ms-4 ps-1 small">${horaFormatada}</p>`;

            this.modalData.content = conteudoHtml;
            this.modalData.link_url = '';
            this.modalData.footer = '';

            this.bsModal.show();
        }
    }));
});
