const out = document.getElementById('messages');

function append(text){
  const el = document.createElement('div');
  el.textContent = text;
  out.appendChild(el);
  out.scrollTop = out.scrollHeight;
}

// EventSource to receive server-sent events
const es = new EventSource('/events');
es.onopen = () => append('EventSource connected');
es.onmessage = (e) => {
  // Try to parse JSON messages and display nicely
  try {
    const obj = JSON.parse(e.data);
    if (obj && typeof obj === 'object') {
      if ('temperature' in obj) {
        append('Temperature: ' + obj.temperature);
        return;
      }
      // otherwise show key: value lines
      const parts = Object.entries(obj).map(([k,v]) => `${k}: ${v}`);
      append(parts.join(', '));
      return;
    }
  } catch (err) {
    // not JSON
  }
  append('Received: ' + e.data);
};
es.onerror = () => append('EventSource error/closed');
