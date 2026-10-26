const escapeHtml = (text) => String(text).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

async function render() {
  const response = await fetch('/api/summary');
  const { summary, events, feedback, check_in } = await response.json();
  const cards = [
    ['Events captured', summary.events],
    ['Rapid switches', summary.rapid_switches],
    ['Recovery opportunity', `${summary.estimated_recovery_minutes} min`],
  ];
  document.querySelector('#cards').innerHTML = cards.map(([label, value]) => `<article><span>${label}</span><strong>${value}</strong></article>`).join('');
  document.querySelector('#message').textContent = summary.message;
  document.querySelector('#feedback').innerHTML = feedback.length
    ? feedback.map(item => `<div><b>${escapeHtml(item.label)}</b><span>${escapeHtml(item.message)}</span></div>`).join('')
    : '<p>AI feedback starts after the first 30-second behavior window.</p>';
  if (check_in) document.querySelector('#checkin-status').textContent = `Current goal: ${check_in.intention} · energy ${check_in.energy}/5`;
  document.querySelector('#transitions').innerHTML = summary.top_transitions.length
    ? summary.top_transitions.map(row => `<div><b>${escapeHtml(row.from)}</b><span>→</span><b>${escapeHtml(row.to)}</b><em>${row.count}×</em></div>`).join('')
    : '<p>No transitions yet.</p>';
  document.querySelector('#activity').innerHTML = events.length
    ? events.map(event => `<div><time>${new Date(event.occurred_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</time><b>${escapeHtml(event.app_name)}</b><span>${escapeHtml(event.window_title)}</span></div>`).join('')
    : '<p>No local activity recorded yet.</p>';
}
document.querySelector('#checkin-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const intention = document.querySelector('#intention').value.trim();
  if (!intention) return;
  const response = await fetch('/api/check-in', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({intention, energy: document.querySelector('#energy').value})});
  document.querySelector('#checkin-status').textContent = response.ok ? 'Check-in saved. The next AI reflection will use it.' : 'Could not save check-in.';
  if (response.ok) document.querySelector('#intention').value = '';
});
render();
setInterval(render, 2000);

