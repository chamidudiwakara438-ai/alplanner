'use strict';
/**
 * Student database for Netlify.
 * Accounts / progress / planner / payments live in Netlify Blobs (cloud)
 * or data/students.json when you run `npm start` locally.
 * No Python. No SQLite. No Express.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', '..', 'data', 'students.json');
const UP_DIR = path.join(__dirname, '..', '..', 'data', 'uploads');
const COOKIE = 'al_session';
const MAX_FILE = 3.5 * 1024 * 1024;

function emptyDb() {
  return {
    users: [], sessions: [], progress: {}, plans: [], resources: [],
    payments: [], exams: [], settings: {}, messages: [],
  };
}

async function blobStore(name) {
  try {
    const { getStore } = require('@netlify/blobs');
    return getStore(name || 'alplanner');
  } catch (_) {
    return null;
  }
}

async function putFile(id, buf, mime) {
  const store = await blobStore('alplanner-files');
  if (store) {
    await store.set(String(id), buf, { metadata: { mime: mime || 'application/octet-stream' } });
    return;
  }
  fs.mkdirSync(UP_DIR, { recursive: true });
  fs.writeFileSync(path.join(UP_DIR, String(id)), buf);
  fs.writeFileSync(path.join(UP_DIR, String(id) + '.json'), JSON.stringify({ mime: mime || 'application/octet-stream' }));
}

async function getFile(id) {
  const store = await blobStore('alplanner-files');
  if (store) {
    const buf = await store.get(String(id), { type: 'arrayBuffer' });
    if (!buf) return null;
    let mime = 'application/octet-stream';
    try {
      const meta = await store.getMetadata(String(id));
      if (meta && meta.metadata && meta.metadata.mime) mime = meta.metadata.mime;
    } catch (_) {}
    return { buf: Buffer.from(buf), mime };
  }
  const fp = path.join(UP_DIR, String(id));
  if (!fs.existsSync(fp)) return null;
  let mime = 'application/octet-stream';
  try { mime = JSON.parse(fs.readFileSync(fp + '.json', 'utf8')).mime || mime; } catch (_) {}
  return { buf: fs.readFileSync(fp), mime };
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
  db.sessions = (db.sessions || []).filter((s) => s.expires > Date.now()).slice(-400);
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
    premium_until: u.premium_until || '', status: u.status || 'active',
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
function cookieHdr(token, clear, event) {
  const proto = String((event && event.headers && (event.headers['x-forwarded-proto'] || event.headers['X-Forwarded-Proto'])) || '');
  const secure = /https/i.test(proto) ? '; Secure' : '';
  if (clear) return COOKIE + '=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax' + secure;
  return COOKIE + '=' + token + '; Path=/; Max-Age=' + (30 * 86400) + '; HttpOnly; SameSite=Lax' + secure;
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
  if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);
  return p;
}
function newToken() { return crypto.randomBytes(24).toString('hex'); }
function loginSession(db, user) {
  const token = newToken();
  db.sessions.push({ token, uid: user.id, expires: Date.now() + 30 * 864e5 });
  return token;
}
function boardRows(db) {
  return (db.users || []).filter((u) => u.role !== 'admin').map((u) => {
    const done = Object.keys(db.progress || {}).filter((k) => k.startsWith(u.id + ':') && db.progress[k].completed).length;
    const exams = (db.exams || []).filter((e) => String(e.uid) === String(u.id));
    const pts = done * 20 + exams.reduce((a, e) => a + (Number(e.score) || 0) * 2, 0);
    return { id: u.id, name: String(u.name || 'Student').split(' ')[0], school: u.school || '', pts, done };
  }).sort((a, b) => b.pts - a.pts || b.done - a.done).slice(0, 20);
}

exports.handler = async (event) => {
  const method = (event.httpMethod || 'GET').toUpperCase();
  if (method === 'OPTIONS') {
    return { statusCode: 204, headers: { 'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' }, body: '' };
  }
  const p = apiPath(event);
  let body = {};
  if (event.body) {
    try { body = JSON.parse(event.body); } catch (_) { body = {}; }
  }
  const db = await loadDb();
  const me = userFrom(db, event);

  if (method === 'GET' && (p === '/' || p === '/health')) {
    return json({
      ok: true,
      students: db.users.filter((u) => u.role === 'student').length,
      save: (await blobStore()) ? 'cloud' : 'file',
    });
  }

  if (method === 'GET' && p === '/meta') {
    return json({
      districts: ['Ampara','Anuradhapura','Badulla','Batticaloa','Colombo','Galle','Gampaha','Hambantota','Jaffna','Kalutara','Kandy','Kegalle','Kilinochchi','Kurunegala','Mannar','Matale','Matara','Monaragala','Mullaitivu','Nuwara Eliya','Polonnaruwa','Puttalam','Ratnapura','Trincomalee','Vavuniya'],
      streams: ['Physical Science','Biological Science','Commerce','Arts','Engineering Technology','Bio Systems Technology'],
      years: ['A/L 2027','A/L 2028','A/L 2029'],
    });
  }

  if (method === 'GET' && p === '/stats') {
    return json({ students: db.users.filter((u) => u.role === 'student').length, users: db.users.length });
  }

  if (method === 'GET' && p === '/leaderboard') {
    return json({ rows: boardRows(db) });
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
      school: String(body.school || '').slice(0, 120),
      district: String(body.district || '').slice(0, 40),
      al_year: body.al_year || 'A/L 2027', medium: body.medium || 'en',
      stream: String(body.stream || '').slice(0, 60),
      premium_until: '', status: 'active', created_at: new Date().toISOString(),
    };
    db.users.push(user);
    const token = loginSession(db, user);
    await saveDb(db);
    return json({ user: publicUser(user) }, 200, { 'Set-Cookie': cookieHdr(token, false, event) });
  }

  if (method === 'POST' && p === '/auth/login') {
    const email = String(body.email || '').trim().toLowerCase();
    const password = String(body.password || '');
    const u = db.users.find((x) => x.email === email);
    if (!u || u.pass !== hashPass(password, u.salt)) return json({ error: 'Incorrect email or password' }, 401);
    if (u.status === 'suspended') return json({ error: 'This account is suspended' }, 403);
    const token = loginSession(db, u);
    await saveDb(db);
    return json({ user: publicUser(u) }, 200, { 'Set-Cookie': cookieHdr(token, false, event) });
  }

  if (method === 'POST' && p === '/auth/logout') {
    const tok = parseCookies(event)[COOKIE];
    db.sessions = db.sessions.filter((s) => s.token !== tok);
    await saveDb(db);
    return json({ ok: true }, 200, { 'Set-Cookie': cookieHdr('', true, event) });
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

  if (method === 'POST' && p === '/contact') {
    const row = {
      id: String(Date.now()),
      name: String(body.name || '').slice(0, 80) || 'Anonymous',
      email: String(body.email || '').slice(0, 120),
      message: String(body.message || '').slice(0, 2000),
      created_at: new Date().toISOString(),
    };
    if (!row.message) return json({ error: 'Write a message' }, 400);
    db.messages.push(row);
    await saveDb(db);
    return json({ ok: true });
  }

  if (!me) return json({ error: 'Please sign in' }, 401);

  if (method === 'POST' && p === '/auth/password') {
    const old = String(body.old || '');
    const password = String(body.password || '');
    if (password.length < 6) return json({ error: 'Password must be 6+ characters' }, 400);
    if (me.pass !== hashPass(old, me.salt)) return json({ error: 'Current password is wrong' }, 400);
    me.salt = crypto.randomBytes(12).toString('hex');
    me.pass = hashPass(password, me.salt);
    await saveDb(db);
    return json({ ok: true });
  }

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
    db.settings[me.id] = Object.assign(
      { exam_date: '2027-08-09', weekly_target: '10' },
      db.settings[me.id] || {},
      {
        exam_date: String(body.exam_date || '2027-08-09').slice(0, 10),
        weekly_target: String(body.weekly_target || '10').slice(0, 4),
      }
    );
    await saveDb(db);
    return json({ settings: db.settings[me.id] });
  }

  if (method === 'POST' && p === '/planner') {
    const row = { id: String(Date.now()), uid: me.id, lesson_id: Number(body.lessonId), plan_date: String(body.date || '').slice(0, 10), done: 0 };
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
    if (!u) return json({ error: 'Not found' }, 404);
    if (body.role) {
      const next = body.role === 'admin' ? 'admin' : 'student';
      if (u.id === me.id && next !== 'admin') return json({ error: 'You cannot remove your own admin role' }, 400);
      u.role = next;
    }
    if (body.status) u.status = body.status === 'suspended' ? 'suspended' : 'active';
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'DELETE' && p.startsWith('/users/') && me.role === 'admin') {
    const id = p.split('/')[2];
    if (String(id) === String(me.id)) return json({ error: 'You cannot delete yourself' }, 400);
    db.users = db.users.filter((x) => String(x.id) !== String(id));
    db.sessions = db.sessions.filter((s) => String(s.uid) !== String(id));
    Object.keys(db.progress || {}).forEach((k) => { if (k.startsWith(id + ':')) delete db.progress[k]; });
    db.plans = (db.plans || []).filter((x) => String(x.uid) !== String(id));
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'POST' && p === '/exam') {
    const rec = {
      uid: me.id,
      at: new Date().toISOString(),
      subj: String(body.subj || 'mixed').slice(0, 20),
      score: Number(body.score) || 0,
      total: Number(body.total) || 0,
      seconds: Number(body.seconds) || 0,
    };
    db.exams.push(rec);
    await saveDb(db);
    return json({ ok: true });
  }

  if (method === 'GET' && p === '/admin/overview' && me.role === 'admin') {
    return json({
      students: db.users.filter((u) => u.role === 'student').length,
      admins: db.users.filter((u) => u.role === 'admin').length,
      payments: db.payments.length,
      pending: db.payments.filter((p0) => p0.status === 'pending').length,
      exams: db.exams.length,
      messages: (db.messages || []).slice(-50).reverse(),
    });
  }

  return json({ error: 'Not found' }, 404);
};
