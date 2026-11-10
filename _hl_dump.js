const t = JSON.parse(require('fs').readFileSync('_hl_55813.json', 'utf8'));
const html = t.data.content.content;
const tokens = html.match(/<h[1-6][^>]*>[\s\S]*?<\/h[1-6]>|<img[^>]*>|<strong[^>]*>[\s\S]*?<\/strong>|<p[^>]*>[\s\S]*?<\/p>/g) || [];
for (const tk of tokens) {
  if (tk.startsWith('<img')) {
    const s = tk.match(/src="([^"]+)"/)[1];
    console.log('IMG :', s.split('/').pop());
  } else {
    const tag = tk.match(/^<(h[1-6]|strong|p)/)[1];
    const txt = tk.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
    if (txt) console.log(tag.toUpperCase() + ':', txt.slice(0, 80));
  }
}
