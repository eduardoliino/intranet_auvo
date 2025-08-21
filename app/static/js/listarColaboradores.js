/**
 * @file listarColaboradores.js
 * Componente para filtrar colaboradores pelo nome ou email.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('colaboradoresFiltro', () => ({
        search: '', // Texto de pesquisa introduzido pelo utilizador
        colaboradores: window._colaboradoresData || [], // Lista total de colaboradores

        get filteredColaboradores() {
            if (this.search.trim() === '') {
                return this.colaboradores;
            }
            const searchTerm = this.search.toLowerCase();
            return this.colaboradores.filter(
                col => {
                    const nomeCompleto = `${col.nome} ${col.sobrenome}`.toLowerCase();
                    const email = col.email_corporativo.toLowerCase();
                    return nomeCompleto.includes(searchTerm) || email.includes(searchTerm);
                }
            );
        }
    }));
});