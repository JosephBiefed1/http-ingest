const out = document.getElementById('messages');
const input = document.getElementById('msg');
const btn = document.getElementById('send');

function append(text){
  const el = document.createElement('div');
  el.textContent = text;
  out.appendChild(el);
  out.scrollTop = out.scrollHeight;
}

// EventSource to receive server-sent events
const es = new EventSource('/events');
es.onopen = () => append('EventSource connected');
es.onmessage = (e) => append('Received: ' + e.data);
es.onerror = () => append('EventSource error/closed');

btn.addEventListener('click', async () => {
  const v = input.value.trim();
  if (!v) return;
  try {
    const res = await fetch('/ingest', { method: 'POST', body: v });
    if (res.ok) append('Sent (POST): ' + v);
    else append('POST failed: ' + res.status);
  } catch (err) {
    append('POST error: ' + err.message);
  }
  input.value = '';
});
