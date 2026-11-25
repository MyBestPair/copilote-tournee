// Icônes de l'application : le pictogramme d'itinéraire en blanc sur le vert du panneau
const { chromium } = require('playwright');
const out = process.argv[2];
const svg = (pad) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#0c6a47"/><g transform="translate(${pad} ${pad}) scale(${(100-2*pad)/30})"><circle cx="6" cy="24" r="3.5" fill="none" stroke="#fff" stroke-width="2.4"/><circle cx="24" cy="6" r="3.5" fill="#fff"/><path d="M6 20.5 V14 a5 5 0 0 1 5-5 h3 a5 5 0 0 0 5-5" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></g></svg>`;
(async () => { const b = await chromium.launch();
  for (const [name, size, pad] of [['icon-192.png',192,18],['icon-512.png',512,18],['icon-180.png',180,18],['icon-maskable-512.png',512,28]]){
    const p = await b.newPage({ viewport:{ width:size, height:size } });
    await p.setContent(`<html><body style="margin:0">${svg(pad).replace('<svg ', `<svg width="${size}" height="${size}" `)}</body></html>`);
    await p.screenshot({ path:`${out}/${name}` }); await p.close(); }
  await b.close(); console.log('icônes ok'); })();
