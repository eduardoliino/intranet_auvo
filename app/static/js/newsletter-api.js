async function react(tipo, postId) {
  await fetch(`/api/news/post/${postId}/reacao`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tipo })
  });
}

async function unreact(postId) {
  await fetch(`/api/news/post/${postId}/reacao`, { method: 'DELETE' });
}

async function listComments(postId, page=1, limit=20) {
  const resp = await fetch(`/api/news/post/${postId}/comentarios?page=${page}&limit=${limit}`);
  return resp.json();
}

async function createComment(postId, texto, gif_id=null) {
  await fetch(`/api/news/post/${postId}/comentarios`, {
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
  renderPollResults(enqueteId, r);
}

async function pollResults(enqueteId) {
  const resp = await fetch(`/api/news/enquete/${enqueteId}/resultado`);
  if (resp.status === 200) return resp.json();
  return null;
}
