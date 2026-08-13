'use strict';
/**
 * Student database for Netlify — saves accounts/progress in Netlify Blobs
 * (or data/students.json when run locally).
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', '..', 'data', 'students.json');
const COOKIE = 'al_session';

function emptyDb() {
  return { users: [], sessions: [], progress: {}, plans: [], resources: [], payments: [], exams: [], settings: {} };
}

async function blobStore() {
  try {
    const { getStore } = require('@netlify/blobs');
    return getStore('alplanner');
  } catch (_) {
    return null;
  }
}

async function loadDb() {
  const store = await blobStore();
  if (store) {
    try {
      const data = await store.get('db', { type: 'json' });
      if (data && typeof data === 'object') return Object.assign(emptyDb(), data);
    } catch (_) {}
    return emptyDb();
  }
  try {
    fs.mkdirSync(path.dirname(FILE), { recursive: true });
    if (fs.existsSync(FILE)) return Object.assign(emptyDb(), JSON.parse(fs.readFileSync(FILE, 'utf8')));
  } catch (_) {}
  return emptyDb();
}

async function saveDb(db) {
  const store = await blobStore();
  if (store) {
    await store.setJSON('db', db);
    return;
  }
  fs.mkdirSync(path.dirname(FILE), { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify(db));
}

function hashPass(pass, salt) {
  return crypto.pbkdf2Sync(String(pass), salt, 120000, 32, 'sha256').toString('hex');
}
function publicUser(u) {
  if (!u) return null;
  return {
    id: u.id, name: u.name, email: u.email, role: u.role, school: u.school,
    district: u.district, al_year: u.al_year, medium: u.medium, stream: u.stream,
    premium_until: u.premium_until || '',
  };
}
function parseCookies(event) {
  const out = {};
  const raw = (event.headers && (event.headers.cookie || event.headers.Cookie)) || '';
  raw.split(';').forEach((p) => {
    const i = p.indexOf('=');
    if (i > -1) out[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim());
  });
  return out;
}
function userFrom(db, event) {
  const tok = parseCookies(event)[COOKIE];
  if (!tok) return null;
  const se = (db.sessions || []).find((s) => s.token === tok && s.expires > Date.now());
  if (!se) return null;
  return (db.users || []).find((u) => u.id === se.uid) || null;
}
function cookieHdr(token, clear) {
  if (clear) return COOKIE + '=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax';
  return COOKIE + '=' + token + '; Path=/; Max-Age=' + (30 * 86400) + '; HttpOnly; SameSite=Lax';
}
function json(body, status, extraHdr) {
  return {
    statusCode: status || 200,
    headers: Object.assign({ 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }, extraHdr || {}),
    body: JSON.stringify(body),
  };
}
function apiPath(event) {
  const raw = event.rawUrl || event.path || '';
  let p = '';
  try { p = new URL(raw, 'https://x').pathname; } catch (_) { p = event.path || ''; }
  p = p.replace(/^\/.netlify\/functions\/api\/?/, '/').replace(/^\/api\/?/, '/');
  if (!p.startsWith('/')) p = '/' + p;
  return p;
}

exports.handler = async (event) => {
  const method = (event.httpMethod || 'GET').toUpperCase();
  const p = apiPath(event);
  let body = {};
  if (event.body) {
    try { body = JSON.parse(event.body); } catch (_) { body = {}; }
  }
  const db = await loadDb();
  const me = userFrom(db, event);

  if (method === 'GET' && (p === '/' || p === '/health')) {
    return json({ ok: true, students: db.users.filter((u) => u.role === 'student').length, save: 'cloud' });
  }

  if (method === 'POST' && p === '/auth/register') {
    const email = String(body.email || '').trim().toLowerCase();
    const password = String(body.password || '');
    const name = String(body.name || '').trim() || 'Student';
    if (!email.includes('@')) return json({ error: 'Enter a valid email' }, 400);
    if (password.length < 6) return json({ error: 'Password must be 6+ characters' }, 400);
    if (db.users.some((u) => u.email === email)) return json({ error: 'That email is already registered' }, 409);
    const salt = crypto.randomBytes(12).toString('hex');
    const user = {
      id: String(Date.now()), name, email, salt, pass: hashPass(password, salt),
      role: db.users.length === 0 ? 'admin' : 'student',
      school: body.school || '', district: body.district || '',
      al_year: body.al_year || 'A/L 2027', medium: body.medium || 'en', stream: body.stream || '',
      premium_until: '', created_at: new Date().toISOString(),
    };
    db.users.push(user);
    const token = crypto.randomBytes(24).toString('hex');
    db.sessions.push({ token, uid: user.id, expires: Date.now() + 30 * 864e5 });
    await saveDb(db);
    return json({ user: publicUser(user) }, 200, { 'Set-Cookie': cookieHdr(token) });
  }

  if (method === 'POST' && p === '/auth/login') {
    const email = String(body.email || '').trim().toLowerCase();
    const password = String(body.password || '');
    const u = db.users.find((x) => x.email === email);
    if (!u || u.pass !== hashPass(password, u.salt)) return json({ error: 'Incorrect email or password' }, 401);
    const token = crypto.randomBytes(24).toString('hex');
    db.sessions.push({ token, uid: u.id, expires: Date.now() + 30 * 864e5 });
    await saveDb(db);
    return json({ user: publicUser(u) }, 200, { 'Set-Cookie': cookieHdr(token) });
  }

  if (method === 'POST' && p === '/auth/logout') {
    const tok = parseCookies(event)[COOKIE];
    db.sessions = db.sessions.filter((s) => s.token !== tok);
    await saveDb(db);
    return json({ ok: true }, 200, { 'Set-Cookie': cookieHdr('', true) });
  }

  if (method === 'GET' && p === '/auth/me') return json({ user: publicUser(me) });

  if (method === 'GET' && p === '/state') {
    if (!me) return json({ user: null, progress: {}, plans: [], settings: {}, payments: [], resources: [], exams: [], users: [] });
    const progress = {};
    Object.keys(db.progress || {}).forEach((k) => {
      if (k.startsWith(me.id + ':') || me.role === 'admin') progress[k] = db.progress[k];
    });
    return json({
      user: publicUser(me),
      progress,
      plans: (db.plans || []).filter((x) => x.uid === me.id),
      settings: db.settings[me.id] || { exam_date: '2027-08-09', weekly_target: '10' },
      payments: (db.payments || []).filter((x) => x.uid === me.id || me.role === 'admin'),
      resources: db.resources || [],
      exams: (db.exams || []).filter((x) => x.uid === me.id),
      users: me.role === 'admin' ? db.users.map(publicUser) : [],
    });
  }

  if (!me) return json({ error: 'Please sign in' }, 401);

  if (method === 'POST' && p === '/progress/toggle') {
    const lessonId = String(body.lessonId || '');
    const field = String(body.field || '');
    if (!['completed', 'watched', 'favourite'].includes(field)) return json({ error: 'Bad field' }, 400);
    const key = me.id + ':' + lessonId;
    const row = Object.assign({ completed: 0, watched: 0, favourite: 0 }, db.progress[key] || {});
    row[field] = row[field] ? 0 : 1;
    if (field === 'completed' && row.completed) row.completed_at = new Date().toISOString();
    db.progress[key] = row;
    await saveDb(db);
    return json(row);
  }

  if (method === 'PUT' && p === '/settings') {
    db.settings[me.id] = Object.assign({ exam_date: '2027-08-09', weekly_target: '10' }, db.settings[me.id] || {}, body || {});
    await saveDb(db);
    return json({ settings: db.settings[me.id] });
  }

  if (method === 'POST' && p === '/planner') {
    const row = { id: String(Date.now()), uid: me.id, lesson_id: Number(body.lessonId), plan_date: body.date, done: 0 };
    db.plans.push(row);
    await saveDb(db);
    return json({ plan: row });
  }
  if (method === 'POST' && p.startsWith('/planner/') && p.endsWith('/toggle')) {
    const id = p.split('/')[2];
    const row = db.plans.find((x) => x.id === id && x.uid === me.id);
    if (row) row.done = row.done ? 0 : 1;
    await saveDb(db);
    return json({ ok: true });
  }
  if (method === 'DELETE' && p.startsWith('/planner/')) {
    const id = p.split('/')[2];
    db.plans = db.plans.filter((x) => !(x.id === id && x.uid === me.id));
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'POST' && p === '/resources') {
    const row = {
      id: String(Date.now()), title: String(body.title || '').slice(0, 140),
      category: body.category || 'notes', subject_id: body.subjectId || null,
      status: me.role === 'admin' ? 'approved' : 'pending', by: me.name, uid: me.id,
    };
    db.resources.push(row);
    await saveDb(db);
    return json({ resource: row });
  }
  if (method === 'PUT' && p.startsWith('/resources/') && me.role === 'admin') {
    const id = p.split('/')[2];
    const r = db.resources.find((x) => x.id === id);
    if (r) r.status = body.status || r.status;
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'POST' && p === '/premium') {
    const row = {
      id: String(Date.now()), uid: me.id, name: me.name,
      method: body.method || 'slip', note: String(body.note || '').slice(0, 200),
      status: 'pending', amount: 990, created_at: new Date().toISOString(),
    };
    db.payments.push(row);
    await saveDb(db);
    return json({ payment: row });
  }
  if (method === 'PUT' && p.startsWith('/payments/') && me.role === 'admin') {
    const id = p.split('/')[2];
    const pay = db.payments.find((x) => x.id === id);
    if (!pay) return json({ error: 'Not found' }, 404);
    pay.status = body.ok ? 'approved' : 'rejected';
    if (body.ok) {
      const u = db.users.find((x) => x.id === pay.uid);
      if (u) u.premium_until = new Date(Date.now() + 31 * 864e5).toISOString().slice(0, 10);
    }
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'PUT' && p.startsWith('/users/') && me.role === 'admin') {
    const id = p.split('/')[2];
    const u = db.users.find((x) => x.id === id);
    if (u) u.role = body.role === 'admin' ? 'admin' : 'student';
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'POST' && p === '/exam') {
    const rec = Object.assign({ uid: me.id, at: new Date().toISOString() }, body || {});
    db.exams.push(rec);
    await saveDb(db);
    return json({ ok: true });
  }

  return json({ error: 'Not found' }, 404);
};
