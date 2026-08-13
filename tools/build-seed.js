'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const outDir = path.join(ROOT, 'public', 'data');
fs.mkdirSync(outDir, { recursive: true });

function read(p) { return fs.readFileSync(path.join(ROOT, p), 'utf8'); }

function ytIdsFromChem() {
  const src = read('add-chemistry-lessons.py');
  const m = src.match(/RAW = r'''([\s\S]*?)'''/);
  if (!m) throw new Error('chem RAW not found');
  const raw = m[1];
  const UNIT_NAME = {
    '1': 'Atomic Structure', '2': 'Chemical Bonding', '3': 'Chemical Calculations',
    '4': 'Matter and Its Properties', '5': 'Energetics', '6': 'Inorganic Chemistry',
    '7-10': 'Organic Chemistry', '11': 'Chemical Kinetics', '12': 'Chemical Equilibrium',
    '13': 'Electrochemistry', '14': 'Industrial Chemistry',
  };
  const TEACHERS = {
    'KALUM SENANAYAKA': 'Kalum Senanayaka',
    'AMILA DASANAYAKA': 'Amila Dasanayaka',
    'NIPUN MADDUMAGE': 'Nipun Maddumage',
    'UJITH HEMACHANDRA': 'Ujith Hemachandra',
    'NIRANDIKA JAYAWARDANA': 'Nirandika Jayawardana',
    'AMILA SIR': 'Amila Dasanayaka',
  };
  const urlRe = /(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:live\/|embed\/|shorts\/|watch\?v=))([A-Za-z0-9_-]{6,20})/;
  const out = [];
  let cur = null;
  for (const line0 of raw.split(/\n/)) {
    const line = line0.trim();
    if (!line) continue;
    if (line.toUpperCase().startsWith('UNIT')) {
      const parts = line.split('—').map((s) => s.trim());
      const um = parts[0].match(/(\d+)(?:\s*[–-]\s*(\d+))?/);
      if (!um) { cur = null; continue; }
      const key = um[1] + (um[2] ? '-' + um[2] : '');
      const unit = UNIT_NAME[key];
      if (!unit) { cur = null; continue; }
      let teacher = null, tag = null;
      for (const extra of parts.slice(1)) {
        const u = extra.toUpperCase();
        if (TEACHERS[u]) teacher = TEACHERS[u];
        else if (u.includes('REVISION')) tag = '2024 Revision';
      }
      cur = { unit, teacher, tag };
    } else if (cur) {
      const mm = line.match(urlRe);
      if (mm) out.push({ ...cur, yt: mm[1] });
    }
  }
  return out;
}

function pyStr(s) {
  if (s.startsWith("'''") || s.startsWith('"""')) return s.slice(3, -3);
  const q = s[0];
  let out = '';
  for (let i = 1; i < s.length - 1; i++) {
    const c = s[i];
    if (c === '\\') {
      const n = s[++i];
      if (n === 'u') { out += String.fromCharCode(parseInt(s.slice(i + 1, i + 5), 16)); i += 4; }
      else if (n === 'n') out += '\n';
      else if (n === 't') out += '\t';
      else out += n;
    } else out += c;
  }
  return out;
}

function extractPyTuples(src, name) {
  const start = src.indexOf(name + ' = [');
  if (start < 0) return [];
  let i = src.indexOf('[', start) + 1;
  const rows = [];
  while (i < src.length) {
    while (i < src.length && /\s|,/.test(src[i])) i++;
    if (src[i] === ']') break;
    if (src[i] !== '(') { i++; continue; }
    i++;
    while (i < src.length && /\s/.test(src[i])) i++;
    let num = '';
    while (/\d/.test(src[i])) num += src[i++];
    while (i < src.length && (src[i] === ',' || /\s/.test(src[i]))) i++;
    if (src[i] !== "'" && src[i] !== '"') break;
    const q1 = src[i++];
    let yt = '';
    while (i < src.length && src[i] !== q1) {
      if (src[i] === '\\') { yt += src[i] + src[i + 1]; i += 2; } else yt += src[i++];
    }
    i++;
    while (i < src.length && (src[i] === ',' || /\s/.test(src[i]))) i++;
    if (src[i] !== "'" && src[i] !== '"') break;
    const q2 = src[i];
    let titleRaw = src[i];
    i++;
    while (i < src.length) {
      if (src[i] === '\\') { titleRaw += src[i] + src[i + 1]; i += 2; continue; }
      titleRaw += src[i];
      if (src[i] === q2) { i++; break; }
      i++;
    }
    while (i < src.length && (src[i] === ',' || /\s/.test(src[i]))) i++;
    if (src[i] !== "'" && src[i] !== '"') break;
    const q3 = src[i];
    let teachRaw = src[i];
    i++;
    while (i < src.length) {
      if (src[i] === '\\') { teachRaw += src[i] + src[i + 1]; i += 2; continue; }
      teachRaw += src[i];
      if (src[i] === q3) { i++; break; }
      i++;
    }
    while (i < src.length && src[i] !== ')') i++;
    i++;
    rows.push({ unitOrd: +num, yt, title: pyStr(titleRaw), teacher: pyStr(teachRaw) });
  }
  return rows;
}

function extractJsonLessons(src, varName) {
  const re = new RegExp(varName + '\\s*=\\s*json\\.loads\\((?:\'|")([\\s\\S]*?)(?:\'|")\\)');
  const m = src.match(re);
  if (!m) return [];
  let raw = m[1];
  raw = raw.replace(/\\n/g, '\n').replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
  try {
    const arr = JSON.parse(raw);
    return arr.map((r) => ({ yt: r[0], unitOrd: r[1], teacher: r[2], title: r[3] }));
  } catch (e) {
    // try unescaping remaining
    try {
      const arr = JSON.parse(m[1].replace(/\\n/g, ''));
      return arr.map((r) => ({ yt: r[0], unitOrd: r[1], teacher: r[2], title: r[3] }));
    } catch (e2) {
      console.warn('JSON parse fail', varName, e.message);
      return [];
    }
  }
}

function extractCmLessons() {
  const src = read('add-cm-lessons.py');
  const re = /NEW\s*=\s*\[([\s\S]*?)\]\s*\nDESC_EN/;
  const m = src.match(re);
  if (!m) return [];
  const rows = [];
  const rowRe = /\[\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*"([^"]+)"\s*,\s*"((?:\\.|[^"\\])*)"\s*\]/g;
  let mm;
  while ((mm = rowRe.exec(m[1]))) {
    rows.push({ yt: mm[1], unitOrd: +mm[2], teacher: mm[3], title: JSON.parse('"' + mm[4] + '"') });
  }
  return rows;
}

const chemVids = ytIdsFromChem();
const physSrc = read('add-physics-lessons.py');
const phys1 = ['LESSONS', 'BULK', 'BULK2', 'BULK3', 'BULK4', 'BULK5'].flatMap((n) => extractPyTuples(physSrc, n));
const phys2 = extractJsonLessons(read('add-physics-batch2.py'), 'NEW');
const phys3 = extractJsonLessons(read('add-physics-batch3.py'), 'NEW');
const cmVids = extractCmLessons();

console.log({ chem: chemVids.length, phys1: phys1.length, phys2: phys2.length, phys3: phys3.length, cm: cmVids.length });

const seed = {
  version: '2026.08.13w-netlify',
  generated: new Date().toISOString(),
  chemistryVideos: chemVids,
  physicsVideos: [...phys1, ...phys2, ...phys3],
  cmVideos: cmVids,
};

fs.writeFileSync(path.join(outDir, 'videos.json'), JSON.stringify(seed));
fs.copyFileSync(path.join(ROOT, 'offline_kb.json'), path.join(outDir, 'offline_kb.json'));
console.log('wrote', path.join(outDir, 'videos.json'));
