'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const { handler } = require('../netlify/functions/api');

const ROOT = path.join(__dirname, '..', 'public');
const PORT = process.env.PORT || 3000;
const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const event = {
      httpMethod: req.method,
      path: url.pathname,
      rawUrl: 'http://127.0.0.1' + req.url,
      headers: Object.assign({ cookie: req.headers.cookie || '' }, req.headers),
      body: Buffer.concat(chunks).toString('utf8') || null,
    };
    const out = await handler(event);
    const headers = out.headers || {};
    res.writeHead(out.statusCode || 200, headers);
    if (out.isBase64Encoded) res.end(Buffer.from(out.body || '', 'base64'));
    else res.end(out.body || '');
    return;
  }
  let file = path.normalize(path.join(ROOT, url.pathname === '/' ? '/index.html' : url.pathname));
  if (!file.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(ROOT, 'index.html');
  const ext = path.extname(file);
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('AL Planner (static + student DB) http://0.0.0.0:' + PORT);
});
