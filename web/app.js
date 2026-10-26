const escapeHtml = (text) => String(text).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

async function render() {
  const response = await fetch('/api/summary');
  const { summary, events } = await response.json();
  const cards = [
    ['Events captured', summary.events],
    ['Rapid switches', summary.rapid_switches],
    ['Recovery opportunity', `${summary.estimated_recovery_minutes} min`],
  ];
  document.querySelector('#cards').innerHTML = cards.map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`).join('');
  document.querySelector('#message').textContent = summary.message;
  document.querySelector('#transitions').innerHTML = summary.top_transitions.length
    ? summary.top_transitions.map(row => `<div><b>${escapeHtml(row.from)}</b><span>→</span><b>${escapeHtml(row.to)}</b><em>${row.count}×</em></div>`).join('')
    : '<p>No transitions yet.</p>';
  document.querySelector('#activity').innerHTML = events.length
    ? events.map(event => `<div><time>${new Date(event.occurred_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</time><b>${escapeHtml(event.app_name)}</b><span>${escapeHtml(event.window_title)}</span></div>`).join('')
    : '<p>No local activity recorded yet.</p>';
}
render();
setInterval(render, 2000);

