// Lightweight UI handler for reaction chips rendered by server-side templates
// Works with blocks that contain buttons with class `nl-reaction-chip`
// inside containers like <div id="reactions-block-<postId>"> ... </div>

(function () {
  function getCount(btn) {
    const span = btn.querySelector('.nl-count, span');
    if (!span) return { el: null, val: 0 };
    const v = parseInt(span.textContent, 10);
    return { el: span, val: isNaN(v) ? 0 : v };
  }

  async function sendReaction(postId, type) {
    try {
      await fetch(`/api/news/post/${postId}/reacao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo: type })
      });
    } catch (e) {
      // Silent failure; backend sockets will eventually reconcile counts.
    }
  }

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.nl-reaction-chip');
    if (!btn) return;
    const container = btn.closest('[id^="reactions-block-"]');
    if (!container) return;

    const idMatch = container.id.match(/^reactions-block-(\d+)$/);
    if (!idMatch) return;
    const postId = parseInt(idMatch[1], 10);
    const type = btn.dataset.type;
    if (!type || !postId) return;

    // Current selected in this block
    const currentSelected = container.querySelector('.nl-reaction-chip.selected');

    // If clicking the already selected one => unselect
    if (btn.classList.contains('selected')) {
      btn.classList.remove('selected');
      const { el, val } = getCount(btn);
      if (el) {
        const newVal = Math.max(0, val - 1);
        el.textContent = newVal;
        btn.classList.toggle('zero-count', newVal <= 0);
      }
      sendReaction(postId, type);
      e.preventDefault();
      return;
    }

    // Switch selection from previous to this one
    if (currentSelected && currentSelected !== btn) {
      currentSelected.classList.remove('selected');
      const { el: oldEl, val: oldVal } = getCount(currentSelected);
      if (oldEl) {
        const nv = Math.max(0, oldVal - 1);
        oldEl.textContent = nv;
        currentSelected.classList.toggle('zero-count', nv <= 0);
      }
    }

    // Select clicked button and bump its count
    btn.classList.add('selected');
    btn.classList.remove('zero-count');
    const { el: newEl, val: newVal } = getCount(btn);
    if (newEl) newEl.textContent = newVal + 1;

    sendReaction(postId, type);
    e.preventDefault();
  });
})();

