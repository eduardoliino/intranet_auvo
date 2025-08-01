// app/static/js/organograma.js

document.addEventListener('DOMContentLoaded', function () {
    const chartContainer = document.querySelector('.chart-container');
    if (!chartContainer) {
        console.error("Container do organograma não encontrado!");
        return;
    }

    // Usamos .then() para garantir que a lógica só rode após os dados chegarem
    fetch('/api/organograma-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na rede: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || !data.nodes || data.nodes.length === 0) {
                chartContainer.innerHTML = '<p class="text-center text-muted mt-5">Nenhum colaborador para exibir no organograma.</p>';
                return;
            }

            // Inicializa o gráfico com a configuração corrigida
            new d3.OrgChart()
                .container('.chart-container')
                .data(data.nodes)
                .nodeId(d => d.id)
                .parentNodeId(d => d.parentId)
                .nodeContent(function (d) {
                    // Esta função é mais segura para renderizar o HTML de cada card
                    return `
                        <div class="card org-node-card shadow-sm" style="border-top-color: #7A28B8;">
                            <div class="card-body p-3">
                                <div class="d-flex align-items-center">
                                    <img src="${d.data.imageUrl}" class="org-node-image">
                                    <div class="ms-3 text-start">
                                        <h6 class="org-node-name mb-0">${d.data.nome || ''}</h6>
                                        <p class="org-node-title text-muted mb-1">${d.data.cargo || ''}</p>
                                        <span class="org-node-dept">${d.data.departamento || ''}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                })
                .render();
        })
        .catch(error => {
            console.error('Erro detalhado ao inicializar o organograma:', error);
            chartContainer.innerHTML = `<div class="alert alert-danger">Ocorreu um erro ao carregar o organograma. Verifique o console para mais detalhes.</div>`;
        });
});