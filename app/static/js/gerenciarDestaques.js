// app/static/js/gerenciarDestaques.js

document.addEventListener('alpine:init', () => {
    Alpine.data('gerenciarDestaques', () => ({
        destaques: window._destaquesData || [],
        colaboradores: window._colaboradoresData || [],

        filtroMes: '',
        filtroAno: '',
        filtroDepto: '',

        form: { id: null, titulo: '', colaborador_id: '', descricao: '', mes: '', ano: '' },
        filtroColaborador: '',
        isEditing: false,
        showCollaboratorList: false,

        modal: null,

        init() {
            this.modal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));

            // --- ALTERAÇÃO APLICADA AQUI ---
            // Adiciona o plugin 'clear_button' para permitir que o utilizador limpe a seleção.
            new TomSelect(this.$refs.filtroMesSelect, {
                plugins: ['clear_button'],
                onChange: (value) => this.filtroMes = value
            });
            new TomSelect(this.$refs.filtroAnoSelect, {
                plugins: ['clear_button'],
                onChange: (value) => this.filtroAno = value
            });
            new TomSelect(this.$refs.filtroDeptoSelect, {
                plugins: ['clear_button'],
                onChange: (value) => this.filtroDepto = value
            });
        },

        get filteredDestaques() {
            return this.destaques.filter(d => {
                const mesMatch = this.filtroMes ? d.mes == this.filtroMes : true;
                const anoMatch = this.filtroAno ? d.ano == this.filtroAno : true;
                const deptoMatch = this.filtroDepto ? d.departamento_id == this.filtroDepto : true;
                return mesMatch && anoMatch && deptoMatch;
            });
        },
        get filteredColaboradores() {
            if (this.filtroColaborador.trim() === '') return [];
            const searchTerm = this.filtroColaborador.toLowerCase();
            return this.colaboradores
                .filter(c => c.nome.toLowerCase().includes(searchTerm))
                .slice(0, 5);
        },

        showToast(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('toast', { detail: { type, message } }));
        },

        submitForm() {
            this.isEditing ? this.editarDestaque() : this.adicionarDestaque();
        },

        adicionarDestaque() {
            const formData = new FormData();
            Object.keys(this.form).forEach(key => formData.append(key, this.form[key]));
            formData.append('imagem_destaque', this.$refs.imagemInput.files[0]);

            fetch('/admin/destaques/adicionar', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.destaques.unshift(data.destaque);
                    this.resetForm();
                    this.showToast('Destaque adicionado com sucesso!', 'success');
                } else {
                    this.showToast(data.message || 'Erro ao adicionar destaque.', 'danger');
                }
            });
        },

        editarDestaque() {
            const formData = new FormData();
            Object.keys(this.form).forEach(key => formData.append(key, this.form[key]));
            const imagemFile = this.$refs.imagemInput.files[0];
            if (imagemFile) formData.append('imagem_destaque', imagemFile);

            fetch(`/admin/destaques/editar/${this.form.id}`, { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const index = this.destaques.findIndex(d => d.id === data.destaque.id);
                    this.destaques[index] = data.destaque;
                    this.resetForm();
                    this.showToast('Destaque atualizado com sucesso!', 'success');
                } else {
                    this.showToast(data.message || 'Erro ao editar destaque.', 'danger');
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
                        this.showToast(data.message, 'info');
                    } else {
                        this.showToast('Erro ao remover destaque.', 'danger');
                    }
                });
            }
        },

        confirmarRemocaoEmMassa() {
            if (this.filtroMes && this.filtroAno) {
                this.modal.show();
            } else {
                this.showToast('Por favor, selecione um mês e um ano para a remoção em massa.', 'warning');
            }
        },

        async removerDestaquesEmMassa() {
            const response = await fetch('/admin/destaques/remover-em-massa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mes: this.filtroMes, ano: this.filtroAno })
            });
            const data = await response.json();

            if (data.success) {
                this.destaques = this.destaques.filter(d => d.mes != this.filtroMes || d.ano != this.filtroAno);
                this.showToast(data.message, 'success');
            } else {
                this.showToast(data.message, 'danger');
            }
            this.modal.hide();
        },

        selectCollaborator(colaborador) {
            this.form.colaborador_id = colaborador.id;
            this.filtroColaborador = colaborador.nome;
            this.showCollaboratorList = false;
        },

        startEdit(destaque) {
            this.isEditing = true;
            this.form = { ...destaque };
            const col = this.colaboradores.find(c => c.id === destaque.colaborador_id);
            if (col) this.filtroColaborador = col.nome;
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        resetForm() {
            this.isEditing = false;
            this.form = { id: null, titulo: '', colaborador_id: '', descricao: '', mes: '', ano: '' };
            this.filtroColaborador = '';
            if (this.$refs.imagemInput) this.$refs.imagemInput.value = null;
            if (this.$refs.formMesSelect) this.$refs.formMesSelect.value = '';
            if (this.$refs.formAnoSelect) this.$refs.formAnoSelect.value = '';
        },

        getInitials(nome, sobrenome) {
            return `${nome ? nome.charAt(0) : ''}${sobrenome ? sobrenome.charAt(0) : ''}`.toUpperCase();
        },
        getAvatarColor(nome) {
            const colors = ['#C051FF', '#7A28B8', '#3A1B4A', '#00D29D', '#345978'];
            let hash = 0;
            if (!nome || nome.length === 0) return colors[0];
            for (let i = 0; i < nome.length; i++) {
                hash = nome.charCodeAt(i) + ((hash << 5) - hash);
            }
            return colors[Math.abs(hash % colors.length)];
        }
    }));
});