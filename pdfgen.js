// Minimal dependency-free PDF generator (text-only, Helvetica) used to create
// seed study notes / papers so downloads are real files out of the box.
'use strict';

function esc(s) {
  return String(s)
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)')
    .replace(/[^\x20-\x7E]/g, '?'); // keep ASCII-safe for the base font
}

function wrap(text, width) {
  const out = [];
  const words = String(text).split(/\s+/).filter(Boolean);
  let cur = '';
  for (const w of words) {
    if ((cur ? cur.length + 1 + w.length : w.length) > width) {
      if (cur) out.push(cur);
      cur = w;
    } else {
      cur = cur ? cur + ' ' + w : w;
    }
  }
  if (cur) out.push(cur);
  return out;
}

/**
 * makePdf(title, paragraphs[]) -> Buffer
 */
function makePdf(title, paragraphs) {
  const lines = [];
  for (const p of paragraphs) {
    if (p === '') { lines.push(''); continue; }
    wrap(p, 84).forEach((l) => lines.push(l));
    lines.push('');
  }
  const perPage = 43;
  const pages = [];
  for (let i = 0; i < lines.length; i += perPage) pages.push(lines.slice(i, i + perPage));
  if (pages.length === 0) pages.push([]);

  const objects = {}; // id -> body
  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>';
  objects[3] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';
  objects[4] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>';
  const kidIds = [];

  pages.forEach((pageLines, i) => {
    const pageId = 5 + i * 2;
    const contentId = pageId + 1;
    kidIds.push(pageId);
    let s = 'BT /F2 16 Tf 56 764 Td (' + esc(title) + ') Tj ET\n';
    s += '0.35 0.35 0.9 RG 2 w 56 754 m 556 754 l S\n';
    s += 'BT /F1 10.5 Tf 56 730 Td 15 TL\n';
    pageLines.forEach((l) => { s += (l === '' ? 'T*\n' : '(' + esc(l) + ') Tj T*\n'); });
    s += 'ET\n';
    s += 'BT /F1 9 Tf 460 30 Td (AL Planner - alplanner.lk) Tj ET';
    objects[pageId] =
      '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] ' +
      '/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ' + contentId + ' 0 R >>';
    objects[contentId] =
      '<< /Length ' + Buffer.byteLength(s, 'binary') + ' >>\nstream\n' + s + '\nendstream';
  });

  objects[2] = '<< /Type /Pages /Kids [' + kidIds.map((k) => k + ' 0 R').join(' ') + '] /Count ' + kidIds.length + ' >>';

  const N = 4 + pages.length * 2;
  let out = '%PDF-1.4\n';
  const offsets = [0];
  for (let id = 1; id <= N; id++) {
    offsets[id] = Buffer.byteLength(out, 'binary');
    out += id + ' 0 obj\n' + objects[id] + '\nendobj\n';
  }
  const xrefPos = Buffer.byteLength(out, 'binary');
  out += 'xref\n0 ' + (N + 1) + '\n0000000000 65535 f \n';
  for (let id = 1; id <= N; id++) {
    out += String(offsets[id]).padStart(10, '0') + ' 00000 n \n';
  }
  out += 'trailer\n<< /Size ' + (N + 1) + ' /Root 1 0 R >>\nstartxref\n' + xrefPos + '\n%%EOF\n';
  return Buffer.from(out, 'binary');
}

module.exports = { makePdf };
