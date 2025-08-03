// app/static/js/organograma.js

document.addEventListener('DOMContentLoaded', function () {
    const chartContainer = document.querySelector('.chart-container');
    if (!chartContainer) {
        console.error("Container do organograma não encontrado!");
        return;
    }

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

            // --- LÓGICA DE CORES ADICIONADA AQUI ---
            // 1. Define uma paleta de cores para usar nas bordas dos cards
            const colors = ['#7A28B8', '#00D29D', '#345978', '#C051FF', '#3A1B4A'];
            let colorIndex = 0;

            // 2. Agrupa os colaboradores por quem é o seu superior (parentId)
            const nodesByParent = data.nodes.reduce((acc, node) => {
                const parentId = node.parentId || 'root'; // Agrupa os que não têm pai (CEO)
                if (!acc[parentId]) {
                    acc[parentId] = [];
                }
                acc[parentId].push(node);
                return acc;
            }, {});

            // 3. Atribui uma cor a cada grupo de "irmãos" (mesmo superior)
            for (const parentId in nodesByParent) {
                const siblings = nodesByParent[parentId];
                const groupColor = colors[colorIndex % colors.length]; // Cicla através das cores
                siblings.forEach(node => {
                    node.color = groupColor; // Adiciona a propriedade 'color' a cada colaborador
                });
                colorIndex++;
            }
            // --- FIM DA LÓGICA DE CORES ---


            new d3.OrgChart()
                .container('.chart-container')
                .data(data.nodes)
                .nodeId(d => d.id)
                .parentNodeId(d => d.parentId)
                .scaleExtent([0.5, 2])
                .nodeWidth(d => 280 + 25) 
                .nodeContent(function (d) {
                    // 4. Usa a cor que definimos, ou uma cor padrão se não houver
                    const borderColor = d.data.color || '#7A28B8';
                    return `
                        <div class="card org-node-card shadow-sm" style="border-top-color: ${borderColor};">
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