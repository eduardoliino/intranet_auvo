window.react = react;
window.unreact = unreact;
window.createComment = createComment;
window.updateComment = updateComment;
window.deleteComment = deleteComment;
window.ratePost = ratePost;
window.votePoll = votePoll;
window.pollResults = pollResults;

function renderPollResults(enqueteId, data){
  if(!data) return;
  const cont = document.getElementById(`resultado-${enqueteId}`);
  if(!cont) return;
  cont.innerHTML='';
  data.opcoes.forEach(o=>{
    const p=document.createElement('p');
    p.textContent=`${o.texto} - ${o.votos} votos`;
    cont.appendChild(p);
  });
}
window.renderPollResults = renderPollResults;
