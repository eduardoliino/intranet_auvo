/**
 * Dispara uma reação para um post e atualiza a UI.
 * @param {string} tipo - O tipo de reação (ex: 'like').
 * @param {number} postId - O ID do post.
 */
async function react(tipo, postId) {
  await fetch(`/api/news/post/${postId}/reacao`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tipo })
  });
  // Força a atualização do footer do card para refletir a nova reação.
  htmx.trigger(`[hx-get='/newsletter/post/${postId}/_footer']`, 'load');
}

/**
 * Remove uma reação de um post.
 * @param {number} postId - O ID do post.
 */
async function unreact(postId) {
  await fetch(`/api/news/post/${postId}/reacao`, { method: 'DELETE' });
  // Força a atualização do footer também ao remover a reação.
  htmx.trigger(`[hx-get='/newsletter/post/${postId}/_footer']`, 'load');
}

/**
 * Busca a lista de comentários de um post.
 * @param {number} postId - O ID do post.
 * @param {number} page - O número da página.
 * @param {number} limit - O limite de itens por página.
 */
async function listComments(postId, page = 1, limit = 20) {
  const resp = await fetch(`/api/news/post/${postId}/comentarios?page=${page}&limit=${limit}`);
  return resp.json();
}

/**
 * Envia um novo comentário para a API.
 * @param {number} postId - O ID do post.
 * @param {string} texto - O conteúdo do comentário.
 * @param {string|null} gif_id - O ID de um GIF (opcional).
 * @returns {Promise<Response>} - Retorna a promessa da requisição fetch.
 */
async function createComment(postId, texto, gif_id = null) {
  return fetch(`/api/news/post/${postId}/comentarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto, gif_id })
  });
}



async function updateComment(id, texto) {
  await fetch(`/api/news/comentario/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto })
  });
}

async function deleteComment(id) {
  await fetch(`/api/news/comentario/${id}`, { method: 'DELETE' });
}

async function ratePost(postId, estrelas) {
  await fetch(`/api/news/post/${postId}/avaliacao`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ estrelas: parseInt(estrelas) })
  });
}

async function votePoll(enqueteId) {
  const container = document.getElementById(`enquete-opts-${enqueteId}`);
  const inputs = container.querySelectorAll('input[name="opcao"]');
  const opcoes = [];
  inputs.forEach(i => { if (i.checked) opcoes.push(parseInt(i.value)); });
  await fetch(`/api/news/enquete/${enqueteId}/voto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ opcoes })
  });
  const r = await pollResults(enqueteId);
  // A função renderPollResults precisa estar disponível globalmente ou ser importada.
  if (window.renderPollResults) {
    renderPollResults(enqueteId, r);
  }
}

async function pollResults(enqueteId) {
  const resp = await fetch(`/api/news/enquete/${enqueteId}/resultado`);
  if (resp.status === 200) return resp.json();
  return null;
}
