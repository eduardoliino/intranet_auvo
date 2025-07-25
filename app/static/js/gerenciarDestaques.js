// app/static/js/gerenciarDestaques.js

document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarDestaques', () => ({
        // --- Dados Iniciais ---
        destaques: window._destaquesData || [],
        colaboradores: window._colaboradoresData || [],
        
        // --- Estado dos Filtros da Lista ---
        filtroMes: '',
        filtroAno: '',

        // --- Estado do Formulário ---
        form: { id: null, titulo: '', colaborador_id: '', descricao: '', mes: '', ano: '' },
        filtroColaborador: '',
        isEditing: false,
        showCollaboratorList: false,

        // --- Lógica de Exibição ---
        get filteredDestaques() {
            return this.destaques.filter(d => {
                const mesMatch = this.filtroMes ? d.mes == this.filtroMes : true;
                const anoMatch = this.filtroAno ? d.ano == this.filtroAno : true;
                return mesMatch && anoMatch;
            });
        },
        get filteredColaboradores() {
            if (this.filtroColaborador.trim() === '') {
                return []; // Não mostra ninguém se o campo estiver vazio
            }
            const searchTerm = this.filtroColaborador.toLowerCase();
            return this.colaboradores
                .filter(c => c.nome.toLowerCase().includes(searchTerm))
                .slice(0, 4);
        },

        // --- Funções de API ---
        submitForm() {
            if (this.isEditing) {
                this.editarDestaque();
            } else {
                this.adicionarDestaque();
            }
        },
        adicionarDestaque() {
            const formData = new FormData();
            Object.keys(this.form).forEach(key => formData.append(key, this.form[key]));
            formData.append('imagem_destaque', this.$refs.imagemInput.files[0]);

            fetch('/admin/destaques/adicionar', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    this.destaques.unshift(data.destaque);
                    this.resetForm();
                }
            });
        },
        editarDestaque() {
            const formData = new FormData();
            Object.keys(this.form).forEach(key => formData.append(key, this.form[key]));
            const imagemFile = this.$refs.imagemInput.files[0];
            if (imagemFile) {
                formData.append('imagem_destaque', imagemFile);
            }

            fetch(`/admin/destaques/editar/${this.form.id}`, { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const index = this.destaques.findIndex(d => d.id === data.destaque.id);
                    this.destaques[index] = data.destaque;
                    this.resetForm();
                }
            });
        },
        removerDestaque(id) {
            if (confirm('Tem a certeza de que deseja remover este destaque?')) {
                fetch(`/admin/destaques/remover/${id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.destaques = this.destaques.filter(d => d.id !== id);
                    }
                });
            }
        },
        
        // --- Funções Auxiliares ---
        selectCollaborator(colaborador) {
            this.form.colaborador_id = colaborador.id;
            this.filtroColaborador = colaborador.nome;
            this.showCollaboratorList = false;
        },
        startEdit(destaque) {
            this.isEditing = true;
            this.form = { ...destaque };
            const col = this.colaboradores.find(c => c.id === destaque.colaborador_id);
            if (col) {
                this.filtroColaborador = col.nome;
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },
        resetForm() {
            this.isEditing = false;
            this.form = { id: null, titulo: '', colaborador_id: '', descricao: '', mes: '', ano: '' };
            this.filtroColaborador = '';
            this.$refs.imagemInput.value = null;
        }
    }));
});