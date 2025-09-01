// Alpine component to show latest news post modal on the home page
document.addEventListener('alpine:init', () => {
  // Componente recebe: postId, reações iniciais, comentários iniciais
  Alpine.data('latestNewsCard', (postId, initialReactions = 0, initialComments = 0) => ({
    isModalOpen: false,
    isLoading: false,
    newCommentText: '',
    isSubmitting: false,
    scrollPct: 0,
    socket: null,
    latestCounts: { reactions: initialReactions, comments: initialComments },
    showEmojiPicker: false,
    showNewCommentButton: false,
    newCommentCount: 0,
    modalContent: {
      postId: postId || null,
      postTitle: 'Carregando...',
      post_html: '',
      reactions: { counts: {}, user_reaction: null },
      comments: [],
    },
    reactionTypes: [
      { type: 'heart', icon: 'bi-heart-fill' },
      { type: 'lightbulb', icon: 'bi-lightbulb-fill' },
      { type: 'rocket', icon: 'bi-rocket-takeoff-fill' },
      { type: 'grin', icon: 'bi-emoji-grin-fill' },
      { type: 'hearteyes', icon: 'bi-emoji-heart-eyes-fill' },
      { type: 'surprise', icon: 'bi-emoji-surprise-fill' },
    ],

    // Utilitário: remove itens com id inválido e deduplica por id
    uniqById(list){
      if(!Array.isArray(list)) return [];
      const map = new Map();
      for(const it of list){
        if(!it || typeof it.id === 'undefined' || it.id === null) continue;
        map.set(it.id, it);
      }
      return Array.from(map.values());
    },

    init(){
      // Home: não abre Socket.IO na carga para evitar atrasos.
      // Conectamos apenas quando o modal é aberto.
      this.socket = null;
    },

    onBodyScroll(e){
      const el = e?.target || this.$refs.modalBody;
      if(!el) return;
      const max = el.scrollHeight - el.clientHeight;
      this.scrollPct = max > 0 ? Math.round((el.scrollTop / max) * 100) : 0;
    },

    normalizeEmbeds(container){
      if(!container) return;
      container.querySelectorAll('iframe').forEach((f)=>{
        f.removeAttribute('width'); f.style.width='100%'; f.style.maxWidth='100%'; f.style.display='block'; f.style.margin='0 auto';
        f.setAttribute('loading', f.getAttribute('loading') || 'lazy');
      });
      container.querySelectorAll('img').forEach((img)=>{
        img.style.maxWidth='100%'; img.style.height='auto'; img.style.display='block'; img.style.margin='0 auto';
      });
    },

    async openModal(event, postId){
      // Conecta Socket.IO sob demanda (apenas quando o modal abre)
      if(!this.socket && typeof io === 'function'){
        try{
          this.socket = io({ transports: ['websocket'] });
          this.socket.on('update_reactions', (data) => this.handleReactionUpdate(data));
          this.socket.on('new_comment', (data) => this.handleNewComment(data));
        }catch{}
      }
      this.isModalOpen = true;
      this.isLoading = true;
      this.modalContent = { postId, postTitle: 'Carregando...', post_html: '', reactions: { counts: {}, user_reaction: null }, comments: [] };
      this.modalContent.postId = postId;
      this.showNewCommentButton = false;
      this.newCommentCount = 0;

      try{
        const r = await fetch(`/api/news/post_details?post_id=${postId}`);
        const data = await r.json();
        if(!data.success){
          this.modalContent.postTitle = 'Erro';
          this.modalContent.post_html = `<p class="text-danger text-center">${data.error || 'Falha ao carregar o post.'}</p>`;
        } else {
          // Garante que comments sempre exista e sem duplicatas
          data.comments = this.uniqById(data.comments || []);
          this.modalContent = data;
          // Sincroniza os contadores do card com os dados carregados
          try {
            const sum = Object.values(this.modalContent.reactions?.counts || {}).reduce((a,b)=>a+b,0);
            this.latestCounts.reactions = sum;
            this.latestCounts.comments = (this.modalContent.comments || []).length;
          } catch {}
        }
      } finally {
        await this.$nextTick();
        this.normalizeEmbeds(this.$refs.embedContent || this.$refs.modalBody);
        // Reprocessa embeds do Instagram após injetar HTML
        try { if(window.instgrm && window.instgrm.Embeds) { window.instgrm.Embeds.process(); } } catch {}
        // Tenta novamente pouco depois (caso o iframe demore a surgir)
        setTimeout(() => { try { window.instgrm && window.instgrm.Embeds.process(); } catch {} }, 500);
        this.isLoading = false;
      }
    },

    closeModal(){
      this.isModalOpen = false;
      this.scrollPct = 0;
      this.showEmojiPicker = false;
      this.showNewCommentButton = false;
      this.newCommentCount = 0;
    },

    async toggleReaction(type){
      const postId = this.modalContent.postId;
      const current = this.modalContent.reactions.user_reaction;
      if(current === type){
        this.modalContent.reactions.user_reaction = null;
        this.modalContent.reactions.counts[type]--;
      } else {
        if(current) this.modalContent.reactions.counts[current]--;
        this.modalContent.reactions.user_reaction = type;
        this.modalContent.reactions.counts[type] = (this.modalContent.reactions.counts[type] || 0) + 1;
      }
      // Atualiza o total do card imediatamente
      try {
        const sum = Object.values(this.modalContent.reactions.counts || {}).reduce((a,b)=>a+b,0);
        this.latestCounts.reactions = sum;
      } catch {}
      try{
        await fetch(`/api/news/post/${postId}/reacao`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ tipo:type }) });
      }catch{}
    },

    autosizeTextarea(el){ el.style.height='auto'; el.style.height=el.scrollHeight+'px'; },

    handleCommentKey(e){ if(!e.shiftKey) { e.preventDefault(); this.submitComment(); } },

    async submitComment(){
      const text = this.newCommentText.trim();
      if(!text || this.isSubmitting) return;
      this.isSubmitting = true;
      try{
        const response = await fetch(`/api/news/post/${this.modalContent.postId}/comentarios`, {
          method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ texto:text })
        });
        if(response.ok){
          const data = await response.json();
          this.newCommentText = '';
          if(data && data.comment){
            // Usa nova referência e deduplica por id (evita duplicação com socket)
            this.modalContent.comments = this.uniqById([...(this.modalContent.comments || []), data.comment]);
            // Não incrementa latestCounts aqui; deixa o socket fazer
            this.$nextTick(() => { try { this.autosizeTextarea(this.$refs.commentInput); } catch{} });
            // Se estiver perto do fim, rola junto
            try {
              const el = this.$refs.modalBody;
              const isNearBottom = el && (el.scrollHeight - el.scrollTop - el.clientHeight < 100);
              if(isNearBottom) this.scrollToBottom();
            } catch {}
          }
        }
      } finally { this.isSubmitting = false; }
    },

    handleReactionUpdate(data){
      if(!data) return;
      // Atualiza card sempre que o evento for deste post
      if(typeof postId === 'number' && data.post_id === postId){
        try { this.latestCounts.reactions = Object.values(data.counts||{}).reduce((a,b)=>a+b,0); } catch{}
      }
      // Se o modal aberto for deste post, atualiza as contagens do modal
      if(this.isModalOpen && this.modalContent.postId === data.post_id){
        this.modalContent.reactions.counts = data.counts;
      }
    },

    handleNewComment(data){
      if(!data || !data.comment) return;
      const pid = data.comment.post_id;
      if(typeof postId === 'number' && pid === postId){
        if(this.isModalOpen && this.modalContent.postId === pid){
          const el = this.$refs.modalBody;
          const isNearBottom = el ? (el.scrollHeight - el.scrollTop - el.clientHeight < 100) : true;
          const next = this.uniqById([...(this.modalContent.comments || []), data.comment]);
          const grew = next.length > (this.modalContent.comments || []).length;
          this.modalContent.comments = next;
          if(grew){
            if(isNearBottom){
              this.$nextTick(()=> this.scrollToBottom());
            } else {
              this.showNewCommentButton = true;
              this.newCommentCount += 1;
            }
          }
          this.latestCounts.comments = this.modalContent.comments.length;
        } else {
          this.latestCounts.comments++;
        }
      }
    },

    // UX helpers (scroll + emoji)
    scrollToBottom(){
      const el = this.$refs.modalBody;
      if(!el) return;
      el.scrollTop = el.scrollHeight;
      this.showNewCommentButton = false;
      this.newCommentCount = 0;
    },

    onEmojiClick(e){
      const emoji = e.detail?.unicode || '';
      if(!emoji) return;
      const el = this.$refs.commentInput;
      this.insertAtCursor(el, emoji);
    },

    insertAtCursor(el, text){
      if(!el) return;
      const start = el.selectionStart ?? el.value.length;
      const end = el.selectionEnd ?? el.value.length;
      const before = el.value.substring(0, start);
      const after = el.value.substring(end);
      el.value = before + text + after;
      el.selectionStart = el.selectionEnd = start + text.length;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      this.$nextTick(() => this.autosizeTextarea(el));
    }
  }))
});
