// app/static/js/listarColaboradores.js

document.addEventListener('alpine:init', () => {
    Alpine.data('colaboradoresFiltro', () => ({
        search: '',
        // A lista de colaboradores será lida da variável _colaboradoresData
        // que o nosso template HTML irá criar.
        colaboradores: window._colaboradoresData || [],
        
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