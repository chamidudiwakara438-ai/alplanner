'use strict';
// Self-heal: workspace snapshots drop any folder named `node_modules`. If it's gone,
// fall back to the vendored copy saved inside the project (name avoids the exclusion).
const path = require('path');
const fs = require('fs');
if (!fs.existsSync(path.join(__dirname, 'node_modules', 'express'))) {
  const vendor = path.join(__dirname, 'vendored-deps');
  if (fs.existsSync(path.join(vendor, 'express'))) {
    process.env.NODE_PATH = vendor;
    require('module').Module._initPaths();
    console.log('node_modules missing — using vendored dependencies (run `npm install` to restore).');
  }
}
const crypto = require('crypto');
const express = require('express');
const bcrypt = require('bcryptjs');
const multer = require('multer');

const { db, DATA_DIR, UPLOAD_DIR, DISTRICTS, STREAMS, MEDIUMS, RESOURCE_CATEGORIES } = require('./db');
const BOOT_T0 = Date.now();
const SITE_VER = '2026.08.13w';
const { seed } = require('./seed');

seed(false); // seed on first run only

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

app.disable('x-powered-by');
app.use(express.json({ limit: '2mb' }));

// ------------------------------------------------------------ helpers
const ah = (fn) => (req, res) => {
  try {
    const out = fn(req, res);
    if (out && typeof out.catch === 'function') out.catch((e) => { console.error(e); res.status(500).json({ error: 'Server error' }); });
  } catch (e) { console.error(e); res.status(500).json({ error: 'Server error' }); }
};
const str = (v, max = 500) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const bad = (res, msg, code = 400) => res.status(code).json({ error: msg });
const COOKIE = 'al_session';
const SESSION_DAYS = 30;

function parseCookies(req) {
  const out = {};
  (req.headers.cookie || '').split(';').forEach((p) => {
    const i = p.indexOf('=');
    if (i > -1) out[p.slice(0, i).trim()] = decodeURIComponent(p.slice(i + 1).trim());
  });
  return out;
}

function createSession(res, userId) {
  const token = crypto.randomBytes(32).toString('hex');
  db.prepare('INSERT INTO sessions (token,user_id,expires_at) VALUES (?,?,?)')
    .run(token, userId, Date.now() + SESSION_DAYS * 864e5);
  res.cookie(COOKIE, token, {
    httpOnly: true, sameSite: 'lax', path: '/', maxAge: SESSION_DAYS * 864e5,
  });
}

function publicUser(u) {
  if (!u) return null;
  let subjects = [];
  try { subjects = JSON.parse(u.subjects || '[]'); } catch (e) { subjects = []; }
  return {
    id: u.id, name: u.name, email: u.email, role: u.role, school: u.school,
    district: u.district, al_year: u.al_year, medium: u.medium, stream: u.stream,
    subjects, created_at: u.created_at, premium_until: u.premium_until || '',
  };
}

app.use((req, res, next) => {
  const token = parseCookies(req)[COOKIE];
  req.user = null;
  if (token) {
    const row = db.prepare(`SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
      WHERE s.token=? AND s.expires_at>?`).get(token, Date.now());
    if (row) req.user = row;
  }
  next();
});

const requireAuth = (req, res, next) => {
  if (!req.user) return res.status(401).json({ error: 'Please sign in to continue' });
  if (req.user.status === 'suspended') return bad(res, 'Your account was suspended. Please contact the AL Planner team.', 403);
  next();
};
const requireAdmin = (req, res, next) => (req.user && req.user.role === 'admin') ? next() : res.status(403).json({ error: 'Admins only' });

// YouTube helpers ------------------------------------------------------
function ytEmbed(yid) {
  if (!yid) return null;
  if (yid.startsWith('playlist:')) return 'https://www.youtube.com/embed/videoseries?list=' + yid.slice(9);
  return 'https://www.youtube-nocookie.com/embed/' + yid + '?rel=0';
}
function ytNormalize(input) {
  const v = str(input, 300);
  if (!v) return '';
  if (/^[a-zA-Z0-9_-]{11}$/.test(v)) return v;
  let m = v.match(/(?:youtube\.com\/(?:watch\?[^#]*v=|embed\/|shorts\/|v\/|live\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  if (m) return m[1];
  m = v.match(/[?&]list=([a-zA-Z0-9_-]{10,})/);
  if (m) return 'playlist:' + m[1];
  return v.length === 11 ? v : '';
}

function lessonOut(l, extra = {}) {
  return {
    ...l,
    embed_url: ytEmbed(l.youtube_id),
    has_video: !!l.youtube_id,
    ...extra,
  };
}

// ------------------------------------------------------------ AUTH
app.post('/api/auth/register', ah((req, res) => {
  const b = req.body || {};
  if (!sw('register_open')) return bad(res, 'Registrations are closed by admin right now. Please check back soon!', 403);
  const name = str(b.name, 80), email = str(b.email, 120).toLowerCase(), password = String(b.password || '');
  if (name.length < 2) return bad(res, 'Please enter your full name');
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return bad(res, 'Please enter a valid email address');
  if (!email.endsWith('@gmail.com')) return bad(res, 'Please register with a Gmail address (@gmail.com)');
  if (password.length < 6) return bad(res, 'Password must be at least 6 characters');
  const school = str(b.school, 120), district = str(b.district, 60), alYear = str(b.alYear, 20);
  const medium = MEDIUMS.includes(b.medium) ? b.medium : 'en';
  const stream = str(b.stream, 60);
  if (!district) return bad(res, 'Please select your district');
  if (!alYear) return bad(res, 'Please select your A/L year');
  if (!stream) return bad(res, 'Please select your stream');
  const subjects = Array.isArray(b.subjects) ? b.subjects.map((s) => str(s, 60)).filter(Boolean).slice(0, 6) : [];
  if (db.prepare('SELECT id FROM users WHERE email=?').get(email)) return bad(res, 'An account with this email already exists', 409);
  const info = db.prepare(`INSERT INTO users (name,email,password_hash,role,school,district,al_year,medium,stream,subjects)
    VALUES (?,?,?,?,?,?,?,?,?,?)`)
    .run(name, email, bcrypt.hashSync(password, 10), 'student', school, district, alYear, medium, stream, JSON.stringify(subjects));
  createSession(res, info.lastInsertRowid);
  res.json({ user: publicUser(db.prepare('SELECT * FROM users WHERE id=?').get(info.lastInsertRowid)) });
}));

app.post('/api/auth/login', ah((req, res) => {
  const email = str((req.body || {}).email, 120).toLowerCase();
  const password = String((req.body || {}).password || '');
  const u = db.prepare('SELECT * FROM users WHERE email=?').get(email);
  if (!u || !bcrypt.compareSync(password, u.password_hash)) return bad(res, 'Incorrect email or password', 401);
  if (u.status === 'suspended') return bad(res, 'Your account was suspended. Please contact the AL Planner team.', 403);
  createSession(res, u.id);
  res.json({ user: publicUser(u) });
}));

app.post('/api/auth/logout', (req, res) => {
  const token = parseCookies(req)[COOKIE];
  if (token) db.prepare('DELETE FROM sessions WHERE token=?').run(token);
  res.clearCookie(COOKIE, { path: '/' });
  res.json({ ok: true });
});

app.get('/api/auth/me', (req, res) => res.json({ user: publicUser(req.user) }));

app.post('/api/auth/password', requireAuth, ah((req, res) => {
  const current = String((req.body || {}).current || '');
  const next = String((req.body || {}).new || '');
  if (next.length < 6) return bad(res, 'New password must be at least 6 characters');
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.user.id);
  if (!u || !bcrypt.compareSync(current, u.password_hash)) return bad(res, 'Current password is incorrect');
  db.prepare('UPDATE users SET password_hash=? WHERE id=?').run(bcrypt.hashSync(next, 10), u.id);
  res.json({ ok: true });
}));

// ------------------------------------------------------------ META
app.get('/api/meta', ah((req, res) => {
  res.json({
    districts: DISTRICTS,
    streams: STREAMS,
    mediums: MEDIUMS,
    years: db.prepare('SELECT * FROM al_years WHERE active=1 ORDER BY id').all(),
    categories: RESOURCE_CATEGORIES,
    subjects: db.prepare('SELECT id,name,name_si,name_ta,code,icon,color1,color2 FROM subjects ORDER BY id').all(),
    units: db.prepare('SELECT id,subject_id,name,ord FROM units ORDER BY subject_id,ord').all(),
  });
}));

// ------------------------------------------------------------ SUBJECTS / LESSONS
function userProgressMap(userId) {
  if (!userId) return {};
  const map = {};
  db.prepare('SELECT * FROM progress WHERE user_id=?').all(userId).forEach((p) => { map[p.lesson_id] = p; });
  return map;
}

app.get('/api/subjects', ah((req, res) => {
  const subs = db.prepare(`
    SELECT s.*,
      (SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=s.id) AS lesson_count,
      (SELECT COUNT(*) FROM units u WHERE u.subject_id=s.id) AS unit_count,
      (SELECT COUNT(*) FROM resources r WHERE r.subject_id=s.id AND r.status='approved') AS resource_count
    FROM subjects s ORDER BY s.id`).all();
  res.json({ subjects: subs });
}));

app.get('/api/videos', ah((req, res) => {
  const sid = str(req.query.subject || '', 12);
  let q = `SELECT l.id,l.title,l.youtube_id,l.ord,t.name AS teacher_name,t.photo AS teacher_photo,
                  u.name AS unit_name,s.id AS subject_id,s.name AS subject_name,s.color1,s.color2
           FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
           LEFT JOIN teachers t ON t.id=l.teacher_id WHERE l.youtube_id<>''`;
  const args = [];
  if (/^\d+$/.test(sid)) { q += ' AND s.id=?'; args.push(+sid); }
  q += ' ORDER BY s.id,l.ord,l.id';
  res.json({ videos: db.prepare(q).all(...args) });
}));

app.get('/api/subjects/:id', ah((req, res) => {
  const s = db.prepare('SELECT * FROM subjects WHERE id=?').get(req.params.id);
  if (!s) return bad(res, 'Subject not found', 404);
  const prog = userProgressMap(req.user && req.user.id);
  const units = db.prepare(`
    SELECT u.* FROM units u WHERE u.subject_id=? ORDER BY u.ord, u.id`).all(s.id)
    .map((u) => ({
      ...u,
      lessons: db.prepare(`
        SELECT l.id,l.title,l.ord,l.youtube_id,t.name AS teacher_name,t.photo AS teacher_photo
        FROM lessons l LEFT JOIN teachers t ON t.id=l.teacher_id
        WHERE l.unit_id=? ORDER BY l.ord, l.id`).all(u.id)
        .map((l) => ({ ...lessonOut(l), state: prog[l.id] || null })),
    }));
  res.json({ subject: s, units });
}));

// ---------------- Virtual Lab & NIE Practicals API (Part 1) ----------------
app.get('/api/practicals', ah((req, res) => {
  const subj = str(req.query.subject || '', 40).trim();
  const cat = str(req.query.category || '', 60).trim();
  const qq = str(req.query.q || '', 60).trim().toLowerCase();
  const cond = [], params = [];
  if (subj) { cond.push('subject=?'); params.push(subj); }
  if (cat) { cond.push('category=?'); params.push(cat); }
  if (qq) { cond.push("lower(practical_title_en || ' ' || practical_title_si || ' ' || category || ' ' || unit_lesson) LIKE ?"); params.push('%' + qq + '%'); }
  const w = cond.length ? ' WHERE ' + cond.join(' AND ') : '';
  const ls = db.prepare(`SELECT id, subject, category, practical_title_en, practical_title_si, unit_lesson FROM practicals${w} ORDER BY subject, category, id`).all(...params);
  res.json({ practicals: ls, total: ls.length });
}));

app.get('/api/practicals/:id', ah((req, res) => {
  const p = db.prepare('SELECT * FROM practicals WHERE id=?').get(Number(req.params.id) || 0);
  if (!p) return bad(res, 'Practical not found', 404);
  ['viva_questions', 'past_paper_questions'].forEach((k) => { try { p[k] = JSON.parse(p[k] || '[]'); } catch (_) { p[k] = []; } });
  res.json({ practical: p });
}));

app.get('/api/lessons/:id', ah((req, res) => {
  const l = db.prepare(`
    SELECT l.*, t.name AS teacher_name, t.bio AS teacher_bio, t.photo AS teacher_photo, u.name AS unit_name, u.subject_id, u.ord AS unit_ord,
           s.name AS subject_name, s.name_si AS subject_name_si, s.name_ta AS subject_name_ta, s.color1, s.color2, s.icon AS subject_icon
    FROM lessons l
    LEFT JOIN teachers t ON t.id=l.teacher_id
    JOIN units u ON u.id=l.unit_id
    JOIN subjects s ON s.id=u.subject_id
    WHERE l.id=?`).get(req.params.id);  if (!l) return bad(res, 'Lesson not found', 404);
  const state = req.user ? db.prepare('SELECT * FROM progress WHERE user_id=? AND lesson_id=?').get(req.user.id, l.id) : null;
  const resources = db.prepare(`
    SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,u.name AS uploader
    FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by
    WHERE r.lesson_id=? AND r.status='approved' ORDER BY r.id DESC`).all(l.id);
  const related = db.prepare(`
    SELECT l.id,l.title,l.youtube_id,t.name AS teacher_name,t.photo AS teacher_photo
    FROM lessons l JOIN units u ON u.id=l.unit_id LEFT JOIN teachers t ON t.id=l.teacher_id
    WHERE u.subject_id=? AND l.id!=? ORDER BY l.id LIMIT 8`).all(l.subject_id, l.id);
  const questions = db.prepare('SELECT * FROM lesson_questions WHERE lesson_id=? ORDER BY ord, id').all(l.id);
  const sim = resolveSim(l);
  try { sim.config = JSON.parse(l.sim_config || '{}'); } catch (e) { sim.config = {}; }
  sim.progress = req.user ? db.prepare('SELECT started,completed,attempts,best_score,last_score FROM sim_progress WHERE user_id=? AND lesson_id=?').get(req.user.id, l.id) : null;
  const lout = lessonOut(l);
  lout.simulation_type = l.simulation_type || '';
  lout.simulation_enabled = l.simulation_enabled == null ? null : l.simulation_enabled;
  res.json({ lesson: lout, state: state || { completed: 0, watched: 0, favourite: 0 }, resources, related: related.map(lessonOut), questions, sim });
}));

app.put('/api/lessons/:id/theory', requireAdmin, ah((req, res) => {
  const l = db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id);
  if (!l) return bad(res, 'Lesson not found', 404);
  db.prepare('UPDATE lessons SET theory=? WHERE id=?').run(str((req.body || {}).theory, 20000), l.id);
  res.json({ ok: true });
}));

app.post('/api/lessons/:id/questions', requireAdmin, ah((req, res) => {
  const l = db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id);
  if (!l) return bad(res, 'Lesson not found', 404);
  const b = req.body || {};
  const q = str(b.q, 600);
  if (!q) return bad(res, 'Question text required');
  let ans = String(b.answer || 'a').trim().toLowerCase();
  if (!['a', 'b', 'c', 'd'].includes(ans)) ans = 'a';
  const mx = db.prepare('SELECT COALESCE(MAX(ord),0) m FROM lesson_questions WHERE lesson_id=?').get(l.id).m;
  const r = db.prepare('INSERT INTO lesson_questions (lesson_id,q,a,b,c,d,answer,explanation,ord) VALUES (?,?,?,?,?,?,?,?,?)')
    .run(l.id, q, str(b.a, 300), str(b.b, 300), str(b.c, 300), str(b.d, 300), ans, str(b.explanation, 1000), mx + 1);
  res.json({ ok: true, id: r.lastInsertRowid });
}));

app.delete('/api/questions/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM lesson_questions WHERE id=?').run(req.params.id);
  res.json({ ok: true });
}));

app.post('/api/lessons/:id/toggle', requireAuth, ah((req, res) => {
  const field = str((req.body || {}).field, 20);
  if (!['completed', 'watched', 'favourite'].includes(field)) return bad(res, 'Invalid field');
  const l = db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id);
  if (!l) return bad(res, 'Lesson not found', 404);
  const uid = req.user.id;
  let row = db.prepare('SELECT * FROM progress WHERE user_id=? AND lesson_id=?').get(uid, l.id);
  if (!row) {
    db.prepare('INSERT INTO progress (user_id,lesson_id) VALUES (?,?)').run(uid, l.id);
    row = { completed: 0, watched: 0, favourite: 0 };
  }
  const nv = row[field] ? 0 : 1;
  const col = field === 'favourite' ? 'favourite' : field;
  const ts = field === 'completed' ? 'completed_at' : field === 'watched' ? 'watched_at' : null;
  if (ts) db.prepare(`UPDATE progress SET ${col}=?, ${ts}=? WHERE user_id=? AND lesson_id=?`)
    .run(nv, nv ? new Date().toISOString() : null, uid, l.id);
  else db.prepare(`UPDATE progress SET ${col}=? WHERE user_id=? AND lesson_id=?`).run(nv, uid, l.id);
  res.json(db.prepare('SELECT * FROM progress WHERE user_id=? AND lesson_id=?').get(uid, l.id));
}));

app.get('/api/teachers', ah((req, res) => {
  res.json({ teachers: db.prepare('SELECT * FROM teachers ORDER BY name').all() });
}));

app.get('/api/teachers/:id', ah((req, res) => {
  const t = db.prepare('SELECT * FROM teachers WHERE id=?').get(req.params.id);
  if (!t) return bad(res, 'Teacher not found', 404);
  const lessons = db.prepare(`SELECT l.id,l.title,l.youtube_id,l.ord,u.name AS unit_name,u.ord AS unit_ord,s.name AS subject_name,s.id AS subject_id
    FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
    WHERE l.teacher_id=? ORDER BY s.id,u.ord,l.ord,l.id`).all(req.params.id);
  const resources = db.prepare(`SELECT r.id,r.title,r.category,r.downloads,s.name AS subject_name FROM resources r
    LEFT JOIN subjects s ON s.id=r.subject_id
    WHERE r.status='approved' AND r.lesson_id IN (SELECT id FROM lessons WHERE teacher_id=?) ORDER BY r.id DESC LIMIT 60`).all(req.params.id);
  const subs = new Set(lessons.map((l) => l.subject_name).filter(Boolean));
  const units = new Set(lessons.map((l) => l.subject_id + '|' + l.unit_name));
  res.json({ teacher: t, lessons, resources,
    stats: { lessons: lessons.length, units: units.size, subjects: subs.size, videos: lessons.filter((l) => l.youtube_id).length } });
}));

// ------------------------------------------------------------ DASHBOARD
// weak-area detector + achievement badges
function activityDates(uid) {
  const ds = new Set();
  for (const r of db.prepare('SELECT substr(completed_at,1,10) d FROM progress WHERE user_id=? AND completed_at IS NOT NULL').all(uid)) if (r.d) ds.add(r.d);
  for (const r of db.prepare('SELECT substr(created_at,1,10) d FROM mcq_attempts WHERE user_id=?').all(uid)) if (r.d) ds.add(r.d);
  for (const r of db.prepare('SELECT substr(updated_at,1,10) d FROM sim_progress WHERE user_id=?').all(uid)) if (r.d) ds.add(r.d);
  return [...ds].sort();
}
function longestStreak(dates) {
  let best = 0, cur = 0, prev = null;
  for (const d of dates) {
    const day = new Date(d + 'T00:00:00Z').getTime();
    if (isNaN(day)) continue;
    cur = prev && day - prev === 86400000 ? cur + 1 : 1;
    if (cur > best) best = cur;
    prev = day;
  }
  return best;
}
app.get('/api/weakareas', requireAuth, ah((req, res) => {
  const uid = req.user.id; const agg = {};
  for (const r of db.prepare(`SELECT u.id uid,u.name uname,u.ord uord,s.id sid,s.name sname,s.name_si ssi,s.name_ta sta,
      SUM(a.score) sc,SUM(a.total) tot,COUNT(*) n FROM mcq_attempts a
      JOIN lessons l ON l.id=a.lesson_id JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
      WHERE a.user_id=? GROUP BY u.id`).all(uid)) agg[r.uid] = r;
  for (const r of db.prepare(`SELECT u.id uid,COUNT(*) n,SUM(sp.last_score)/100.0*5 sc FROM sim_progress sp
      JOIN lessons l ON l.id=sp.lesson_id JOIN units u ON u.id=l.unit_id
      WHERE sp.user_id=? AND sp.last_score IS NOT NULL GROUP BY u.id`).all(uid)) {
    if (agg[r.uid]) { agg[r.uid].sc = (agg[r.uid].sc || 0) + (r.sc || 0); agg[r.uid].tot = (agg[r.uid].tot || 0) + r.n * 5; agg[r.uid].n += r.n; }
    else {
      const u = db.prepare('SELECT u.id uid,u.name uname,u.ord uord,s.id sid,s.name sname,s.name_si ssi,s.name_ta sta FROM units u JOIN subjects s ON s.id=u.subject_id WHERE u.id=?').get(r.uid);
      if (u) agg[r.uid] = { ...u, sc: r.sc || 0, tot: r.n * 5, n: r.n };
    }
  }
  const areas = Object.values(agg).filter((a) => a.tot > 0).map((a) => {
    const pct = Math.round(100 * a.sc / a.tot);
    return { unit_id: a.uid, unit: a.uname, ord: a.uord, subject_id: a.sid, subject: a.sname,
      subject_si: a.ssi, subject_ta: a.sta, pct, right: Math.round(a.sc * 10) / 10, of: a.tot, attempts: a.n,
      status: pct < 50 ? 'weak' : pct < 75 ? 'good' : 'excellent' };
  }).sort((x, y) => x.subject_id - y.subject_id || x.ord - y.ord);
  res.json({ areas, summary: { weak: areas.filter((x) => x.status === 'weak').length, good: areas.filter((x) => x.status === 'good').length, excellent: areas.filter((x) => x.status === 'excellent').length } });
}));

// ---------------- A/L Exam Mode (timed practice papers) ----------------
app.post('/api/exam/attempt', requireAuth, ah((req, res) => {
  const uid = req.user.id; const b = req.body || {};
  const subj = str(b.subject, 10);
  if (!['chem', 'phys', 'bio', 'mixed'].includes(subj)) return bad(res, 'Bad subject');
  const mode = str(b.mode, 10);
  if (!['m1', 'm2', 'm3'].includes(mode)) return bad(res, 'Bad mode');
  let cnt = parseInt(b.count, 10), sc = parseInt(b.score, 10), secs = parseInt(b.seconds || 0, 10);
  if (isNaN(cnt) || isNaN(sc) || cnt < 1 || cnt > 100 || sc < 0 || sc > cnt) return bad(res, 'Bad numbers');
  secs = isNaN(secs) ? 0 : Math.max(0, Math.min(secs, 4 * 3600));
  const clean = [];
  if (Array.isArray(b.topics)) {
    for (const tp of b.topics.slice(0, 60)) {
      if (!tp || typeof tp !== 'object') continue;
      const ty = str(tp.t, 30);
      if (!SIM_TYPES.includes(ty)) continue;
      const c2 = parseInt(tp.c, 10), n2 = parseInt(tp.n, 10);
      if (isNaN(c2) || isNaN(n2) || n2 < 1 || n2 > 100 || c2 < 0 || c2 > n2) continue;
      clean.push({ t: ty, c: c2, n: n2 });
    }
  }
  db.prepare('INSERT INTO exam_attempts (user_id,subject,mode,qcount,score,seconds,topics) VALUES (?,?,?,?,?,?,?)')
    .run(uid, subj, mode, cnt, sc, secs, JSON.stringify(clean));
  res.json({ ok: true });
}));

app.get('/api/exam/stats', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const att = db.prepare('SELECT id,subject,mode,qcount AS count,score,seconds,created_at FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 8').all(uid);
  const agg = db.prepare('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?').get(uid);
  const tt = {};
  for (const r of db.prepare('SELECT topics FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 20').all(uid)) {
    let arr; try { arr = JSON.parse(r.topics || '[]'); } catch (_) { arr = []; }
    for (const tp of arr) { const d = tt[tp.t] || (tt[tp.t] = [0, 0]); d[0] += tp.c; d[1] += tp.n; }
  }
  const topics = Object.entries(tt).filter(([, v]) => v[1]).map(([k, v]) => ({ t: k, c: v[0], n: v[1], pct: Math.round(v[0] * 100 / v[1]) })).sort((x, y) => x.pct - y.pct);
  res.json({ attempts: att, taken: agg.c, avg: Math.round(agg.a), best: Math.round(agg.b),
    weak: topics.filter((x) => x.pct < 60).slice(0, 8), topics: topics.slice(0, 12) });
}));

// ---------------- 🤖 AI Tutor (Gemini API — admin pastes the key; free tier key works) ----------------
const AI_MODEL = 'gemini-2.5-flash';
const setGet = (k) => (db.prepare('SELECT value FROM site_settings WHERE key=?').get(k) || { value: '' }).value || '';
const isPrem = (u) => !!(u && u.premium_until && u.premium_until >= new Date().toISOString().slice(0, 10));

app.get('/api/admin/aikey', requireAdmin, ah((req, res) => {
  const k = setGet('ai_key');
  res.json({ set: !!k, tail: k ? '…' + k.slice(-4) : '', model: AI_MODEL, premium_price: setGet('premium_price'), premium_bank: setGet('premium_bank'), ezcash_number: setGet('ezcash_number'),
    free_limit: setGet('ai_free_limit') || '10', pro_limit: setGet('ai_pro_limit') || '100', model_eff: aiModel(), prompt: setGet('ai_prompt') });
}));

// ---------------- 🧠 Offline syllabus Guru (works with zero API key) ----------------
let OFFLINE_KB = { topics: [], guide: '' };
try { OFFLINE_KB = JSON.parse(fs.readFileSync(path.join(__dirname, 'offline_kb.json'), 'utf8')); } catch (_) { }
function offlineAnswer(text) {
  const t2 = (' ' + String(text || '').toLowerCase().replace(/[^a-z0-9+\- ]+/g, ' ') + ' ');
  let best = null, bestSc = 0;
  (OFFLINE_KB.topics || []).forEach((tp) => {
    let sc = 0;
    (tp.keys || []).forEach((k) => { const k2 = String(k).toLowerCase().trim(); if (k2 && t2.includes(k2)) sc += 1 + k2.split(' ').length * 2 - 2 + (k2.includes(' ') ? 2 : 0); });
    if (sc > bestSc) { best = tp; bestSc = sc; }
  });
  let loreHit = '';
  try {
    for (const r of db.prepare('SELECT text FROM ai_knowledge ORDER BY id DESC LIMIT 40').all()) {
      const words = new Set(String(r.text || '').toLowerCase().match(/[a-z]{4,}/g) || []);
      let hit = 0; words.forEach((w) => { if (t2.includes(w)) hit++; });
      if (hit >= 3) { loreHit = '\n\n📌 From the AL Planner team notes: ' + String(r.text || '').slice(0, 600); break; }
    }
  } catch (_) { }
  if (!best) return '🧠 ' + (OFFLINE_KB.guide || '') + loreHit;
  return '🧠 AL Guru (offline syllabus expert): ' + (best.title || '') + ' [' + (best.subj || '') + ']\n\n' + (best.body || '') + loreHit +
    '\n\n— Offline mode: for free open-ended chat, admin can add a FREE Gemini key (Admin → Site).';
}

app.post('/api/ai/chat', requireAuth, ah(async (req, res) => {
  const uid = req.user.id;
  if (!sw('ai_on')) return bad(res, 'AI Tutor is switched off by admin right now.', 403);
  const key = setGet('ai_key');
  const b = req.body || {};
  if (!Array.isArray(b.messages) || !b.messages.length) return bad(res, 'No message');
  const prem0 = isPrem(req.user);
  const cap0 = aiCap(prem0);
  const usedR0 = db.prepare('SELECT n FROM ai_usage WHERE user_id=? AND day=?').get(uid, new Date().toISOString().slice(0, 10));
  const left0 = cap0 - (usedR0 ? usedR0.n : 0);
  if (!key) {
    let last0 = '';
    for (let i = b.messages.length - 1; i >= 0; i--) { const m0 = b.messages[i]; if (m0 && m0.role !== 'model' && m0.text) { last0 = str(m0.text, 2000); break; } }
    return res.json({ reply: offlineAnswer(last0).slice(0, 4000), left: left0, premium: prem0, engine: 'offline' });
  }
  const msgs = b.messages.slice(-8).filter((m2) => m2 && typeof m2 === 'object').map((m2) => ({
    role: m2.role === 'model' ? 'model' : 'user', parts: [{ text: str(m2.text, 2000) }],
  })).filter((m2) => m2.parts[0].text);
  if (!msgs.length || msgs[msgs.length - 1].role !== 'user') return bad(res, 'No message');
  const langName = { si: 'Sinhala', ta: 'Tamil' }[str(b.lang, 5)] || 'English';
  const prem = isPrem(req.user);
  const cap = aiCap(prem);
  const today = new Date().toISOString().slice(0, 10);
  const usedRow = db.prepare('SELECT n FROM ai_usage WHERE user_id=? AND day=?').get(uid, today);
  const usedN = usedRow ? usedRow.n : 0;
  if (usedN >= cap) return res.status(429).json({ error: 'limit', premium: prem });
  let sysTxt = 'You are "Quantum AI" — the expert Sri Lankan G.C.E. A/L tutor of AL Planner, specialised in Chemistry, Physics, Combined Maths, Biology and ICT, aligned with the NIE syllabus. You are a friendly, precise study assistant inside AL Planner. ' +
    'Subjects: Chemistry, Physics, Combined Mathematics, Biology, ICT (2019 syllabus). ' +
    'Reply in ' + langName + ' unless the student writes in another language. ' +
    'Keep answers short and exam-focused: definitions, steps, one small example. ' +
    'If a question is off-topic (not study-related), politely steer back to A/L study. Never invent Sri Lankan syllabus facts you are unsure about.';
  const extra = setGetRaw('ai_prompt');
  if (extra) sysTxt += '\nExtra instructions from the AL Planner team:\n' + String(extra).slice(0, 1500);
  const lore = db.prepare('SELECT text FROM ai_knowledge ORDER BY id DESC LIMIT 40').all();
  if (lore.length) sysTxt += '\nApproved knowledge from the AL Planner team (trust this over your own memory):\n• ' + lore.map((r) => r.text).join('\n• ').slice(0, 5000);
  try {
    const r = await fetch('https://generativelanguage.googleapis.com/v1beta/models/' + aiModel() + ':generateContent?key=' + key, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system_instruction: { parts: [{ text: sysTxt }] }, contents: msgs, generationConfig: { maxOutputTokens: 700, temperature: 0.6 } }),
    });
    const lastQ = msgs.length ? msgs[msgs.length - 1].parts[0].text : '';
    if (!r.ok) {
      try { db.prepare('INSERT INTO admin_logs (admin,action,target) VALUES (?,?,?)').run(req.user.email, 'ai_gemini_err', 'HTTP ' + r.status); } catch (_) { }
      return res.json({ reply: offlineAnswer(lastQ).slice(0, 4000), left: cap - usedN, premium: prem, engine: 'offline_fallback', note: 'Gemini issue (HTTP ' + r.status + ') — offline syllabus Guru answered instead.' });
    }
    const data = await r.json();
    const text = (((data.candidates || [])[0] || {}).content || { parts: [] }).parts[0];
    if (!text || !text.text) return res.json({ reply: offlineAnswer(lastQ).slice(0, 4000), left: cap - usedN, premium: prem, engine: 'offline_fallback' });
    db.prepare('INSERT INTO ai_usage (user_id,day,n) VALUES (?,?,1) ON CONFLICT(user_id,day) DO UPDATE SET n=n+1').run(uid, today);
    res.json({ reply: str(text.text, 4000), left: cap - usedN - 1, premium: prem, engine: 'gemini' });
  } catch (_) {
    const lastQ = msgs.length ? msgs[msgs.length - 1].parts[0].text : '';
    try { db.prepare('INSERT INTO admin_logs (admin,action,target) VALUES (?,?,?)').run(req.user.email, 'ai_gemini_err', 'network'); } catch (_) { }
    res.json({ reply: offlineAnswer(lastQ).slice(0, 4000), left: cap - usedN, premium: prem, engine: 'offline_fallback', note: 'Online AI unreachable — offline syllabus Guru answered instead.' });
  }
}));

// ---------------- 💎 Premium via bank-slip upload (no payment gateway needed) ----------------
const SLIP_DIR = path.join(UPLOAD_DIR, 'slips');
const slipUpload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => { fs.mkdirSync(SLIP_DIR, { recursive: true }); cb(null, SLIP_DIR); },
    filename: (req, file, cb) => cb(null, 's-' + crypto.randomBytes(10).toString('hex') + path.extname(file.originalname).toLowerCase()),
  }),
  limits: { fileSize: 6 * 1024 * 1024 },
});

app.get('/api/premium/status', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const slips = db.prepare('SELECT id,amount,note,status,reason,created_at,method,txn_id,mobile,file FROM payments WHERE user_id=? ORDER BY id DESC LIMIT 10').all(uid);
  const today = new Date().toISOString().slice(0, 10);
  const used = db.prepare('SELECT n FROM ai_usage WHERE user_id=? AND day=?').get(uid, today);
  const prem = isPrem(req.user);
  res.json({ premium: prem, until: prem ? req.user.premium_until : '',
    price: setGet('premium_price'), bank: setGet('premium_bank'),
    ai_left: aiCap(prem) - (used ? used.n : 0), slips, ezcash: setGet('ezcash_number') });
}));

app.get('/api/premium/quote', requireAuth, ah((req, res) => {
  let base = parseInt(setGet('premium_price') || '0', 10); if (isNaN(base) || base < 0) base = 0;
  const out = { price: base, final: base, discount: 0, ok: true };
  const code = str(req.query.coupon, 40);
  if (code) {
    const cp = couponFind(code);
    if (!cp) out.ok = false;
    else { const [fin, cut] = couponCalc(cp, base); out.final = fin; out.discount = cut; out.code = cp.code; }
  }
  res.json(out);
}));

app.post('/api/premium/slip', requireAuth, slipUpload.single('file'), ah((req, res) => {
  const uid = req.user.id;
  const pend = db.prepare("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='pending'").get(uid).c;
  if (pend >= 3) return bad(res, 'You already have slips waiting for approval — please wait.');
  if (!req.file) return bad(res, 'Please attach a photo/PDF of the bank slip');
  const ext = path.extname(req.file.originalname).toLowerCase();
  if (!['.png', '.jpg', '.jpeg', '.webp', '.pdf'].includes(ext)) return bad(res, 'Slip must be an image or PDF');
  let amount = parseInt(req.body.amount || 0, 10); if (isNaN(amount) || amount < 0) amount = 0; if (amount > 1000000) amount = 1000000;
  const coupon = str(req.body.coupon, 40).toUpperCase();
  if (coupon) {
    const cp = couponFind(coupon);
    if (!cp) return bad(res, 'That coupon code is not valid (expired or fully used)');
    let base = parseInt(setGet('premium_price') || '0', 10); if (isNaN(base) || base < 0) base = 0;
    amount = couponCalc(cp, base)[0];
  }
  db.prepare('INSERT INTO payments (user_id,file,amount,note,coupon) VALUES (?,?,?,?,?)').run(uid, req.file.filename, amount, str(req.body.note, 300), coupon);
  res.json({ ok: true, pending: true });
}));

app.post('/api/premium/ezcash', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  if (!setGet('ezcash_number')) return bad(res, 'eZ Cash payments are not available yet — please use a bank slip');
  const pend = db.prepare("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='pending'").get(uid).c;
  if (pend >= 3) return bad(res, 'You already have payments waiting for approval — please wait.');
  const b = req.body || {};
  const mobile = str(b.mobile, 15);
  if (!/^0\d{9}$/.test(mobile)) return bad(res, 'Enter a valid mobile number, e.g. 0771234567');
  const txn = str(b.txn_id, 40).trim();
  if (!/^[A-Za-z0-9\-]{6,40}$/.test(txn)) return bad(res, 'Enter the Transaction ID exactly as in the eZ Cash SMS (6+ letters/digits)');
  const dup = db.prepare("SELECT COUNT(*) c FROM payments WHERE txn_id=? AND status IN ('pending','approved')").get(txn).c;
  if (dup) return bad(res, 'This Transaction ID was already submitted — contact admin if wrong');
  let amount = parseInt(b.amount || 0, 10); if (isNaN(amount) || amount < 0) amount = 0; if (amount > 1000000) amount = 1000000;
  const coupon = str(b.coupon, 40).toUpperCase();
  if (coupon) {
    const cp = couponFind(coupon);
    if (!cp) return bad(res, 'That coupon code is not valid (expired or fully used)');
    let base = parseInt(setGet('premium_price') || '0', 10); if (isNaN(base) || base < 0) base = 0;
    amount = couponCalc(cp, base)[0];
  }
  db.prepare('INSERT INTO payments (user_id,method,txn_id,mobile,amount,note,coupon) VALUES (?,?,?,?,?,?,?)')
    .run(uid, 'ezcash', txn, mobile, amount, (str(b.note, 300).trim() || ('eZ Cash ' + mobile)), coupon);
  try { db.prepare('INSERT INTO admin_logs (admin,action,target) VALUES (?,?,?)').run(req.user.email, 'ezcash_submit', 'txn ' + txn + ' user #' + uid + ' Rs.' + amount); } catch (_) {}
  res.json({ ok: true, pending: true });
}));

app.get('/api/slips/:id', requireAuth, ah((req, res) => {
  const row = db.prepare('SELECT * FROM payments WHERE id=?').get(req.params.id);
  if (!row || (req.user.role !== 'admin' && row.user_id !== req.user.id)) return bad(res, 'Not found', 404);
  if (!row.file) return bad(res, 'This payment has no slip image (eZ Cash)', 404);
  res.sendFile(path.join(SLIP_DIR, row.file));
}));

// ---------------- Chemistry Practical Lab (database-driven profiles + notes/progress) ----------------
const LAB_NOTE_FIELDS = ['Aim', 'Apparatus', 'Chemicals', 'Procedure', 'Observations', 'Equation', 'Calculation', 'Conclusion'];
const chemdbList = () => {
  try { const v = JSON.parse(setGet('chemdb_extra') || '[]'); return Array.isArray(v) ? v : []; } catch (_) { return []; }
};
const chemdbSet = (lst) => {
  db.prepare("INSERT INTO site_settings (key,value) VALUES ('chemdb_extra',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    .run(JSON.stringify(lst).slice(0, 8000));
};
app.get('/api/chemdb', ah((req, res) => { res.json({ extra: chemdbList() }); }));
app.post('/api/admin/chemdb', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const kind = str(b.kind, 10);
  let e;
  if (kind === 'flame') {
    e = { kind: 'flame', salt: str(b.salt, 60), ion: str(b.ion, 20), col: str(b.col, 10), cname: str(b.cname, 60) };
    if (!e.salt || !e.ion || !e.cname) return bad(res, 'Fill in salt name, ion symbol and the flame colour name');
    if (!/^#[0-9A-Fa-f]{6}$/.test(e.col)) return bad(res, 'Colour must be the TRUE flame colour as #RRGGBB (e.g. #ffc81e)');
  } else if (kind === 'precip') {
    e = { kind: 'precip', sample: str(b.sample, 60), reagent: str(b.reagent, 60), obs: str(b.obs, 300), col: str(b.col, 10), eq: str(b.eq, 160), ionic: str(b.ionic, 160), note: str(b.note, 300) };
    if (!e.sample || !e.reagent || !e.obs || !e.eq) return bad(res, 'Fill at least sample, reagent, observation and equation');
    if (e.col && !/^#[0-9A-Fa-f]{6}$/.test(e.col)) return bad(res, 'Precipitate colour must be the TRUE colour as #RRGGBB (or empty)');
  } else return bad(res, 'kind must be "flame" or "precip"');
  const lst = chemdbList();
  if (lst.length >= 60) return bad(res, 'Chemistry database is full (60 teacher entries) — delete some first');
  lst.push(e); chemdbSet(lst);
  logAdmin(req, 'chemdb_add', kind + ': ' + (e.salt || e.sample || ''));
  res.json({ ok: true, extra: lst });
}));
app.post('/api/admin/chemdb/del', requireAdmin, ah((req, res) => {
  const idx = parseInt((req.body || {}).idx, 10);
  const lst = chemdbList();
  if (isNaN(idx) || idx < 0 || idx >= lst.length) return bad(res, 'No such entry');
  const gone = lst.splice(idx, 1)[0]; chemdbSet(lst);
  logAdmin(req, 'chemdb_del', (gone.kind || '?') + ': ' + (gone.salt || gone.sample || ''));
  res.json({ ok: true, extra: lst });
}));
app.get('/api/lab/state', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const notes = {};
  db.prepare('SELECT prac, data FROM lab_notes WHERE user_id=?').all(uid).forEach((r) => {
    try { notes[r.prac] = JSON.parse(r.data || '{}'); } catch (_) { notes[r.prac] = {}; }
  });
  const progress = {};
  db.prepare('SELECT prac, best, done FROM lab_progress WHERE user_id=?').all(uid).forEach((r) => { progress[r.prac] = { best: r.best, done: r.done }; });
  res.json({ notes, progress });
}));
app.post('/api/lab/note', requireAuth, ah((req, res) => {
  const b = req.body || {};
  const prac = str(b.prac, 30);
  if (!prac || !/^[A-Za-z0-9_-]{2,30}$/.test(prac)) return bad(res, 'bad practical id');
  const clean = {};
  if (b.data && typeof b.data === 'object') LAB_NOTE_FIELDS.forEach((f) => { if (b.data[f] != null) clean[f] = str(b.data[f], 2000); });
  db.prepare("INSERT INTO lab_notes (user_id,prac,data,updated_at) VALUES (?,?,?,datetime('now')) ON CONFLICT(user_id,prac) DO UPDATE SET data=excluded.data, updated_at=datetime('now')")
    .run(req.user.id, prac, JSON.stringify(clean));
  res.json({ ok: true });
}));
app.post('/api/lab/progress', requireAuth, ah((req, res) => {
  const b = req.body || {};
  const prac = str(b.prac, 30);
  if (!prac || !/^[A-Za-z0-9_-]{2,30}$/.test(prac)) return bad(res, 'bad practical id');
  let score = parseInt(b.score || 0, 10); if (isNaN(score) || score < 0) score = 0; if (score > 100) score = 100;
  db.prepare("INSERT INTO lab_progress (user_id,prac,best,done,updated_at) VALUES (?,?,?,?,datetime('now')) ON CONFLICT(user_id,prac) DO UPDATE SET best=MAX(best,excluded.best), done=MAX(done,excluded.done), updated_at=datetime('now')")
    .run(req.user.id, prac, score, b.done ? 1 : 0);
  res.json({ ok: true });
}));

app.get('/api/admin/payments', requireAdmin, ah((req, res) => {
  res.json({ payments: db.prepare(`SELECT p.*, u.name, u.email, u.school FROM payments p
    JOIN users u ON u.id=p.user_id ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END, p.id DESC LIMIT 100`).all() });
}));

app.put('/api/admin/payments/:id', requireAdmin, ah((req, res) => {
  const row = db.prepare('SELECT * FROM payments WHERE id=?').get(req.params.id);
  if (!row) return bad(res, 'Not found', 404);
  const b = req.body || {}; const act = str(b.action, 10);
  const now = new Date().toISOString().slice(0, 19).replace('T', ' ') + 'Z';
  if (act === 'approve') {
    const today = new Date().toISOString().slice(0, 10);
    const u = db.prepare('SELECT premium_until FROM users WHERE id=?').get(row.user_id);
    const base = u && u.premium_until && u.premium_until > today ? u.premium_until : today;
    const until = new Date(new Date(base + 'T00:00:00Z').getTime() + 31 * 864e5).toISOString().slice(0, 10);
    db.prepare('UPDATE users SET premium_until=? WHERE id=?').run(until, row.user_id);
    db.prepare("UPDATE payments SET status='approved', decided_at=? WHERE id=?").run(now, row.id);
    if (row.coupon) db.prepare('UPDATE coupons SET uses=uses+1 WHERE code=?').run(row.coupon);
    logAdmin(req, 'payment_approve', 'slip #' + row.id + ' user #' + row.user_id + ' Rs.' + row.amount);
    return res.json({ ok: true, until });
  }
  if (act === 'reject') {
    db.prepare("UPDATE payments SET status='rejected', reason=?, decided_at=? WHERE id=?").run(str(b.reason, 200), now, row.id);
    logAdmin(req, 'payment_reject', 'slip #' + row.id + ' user #' + row.user_id);
    return res.json({ ok: true });
  }
  bad(res, 'Bad action');
}));

app.get('/api/badges', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const one = (q, p) => db.prepare(q).get(p) || {};
  const lessonsDone = one('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1', uid).c || 0;
  const q = one('SELECT COUNT(*) n, COALESCE(SUM(total),0) tot FROM mcq_attempts WHERE user_id=?', uid);
  const simsDone = one('SELECT COUNT(*) c FROM sim_progress WHERE user_id=? AND completed=1', uid).c || 0;
  const pp = one("SELECT COUNT(*) c FROM practice_marks pm JOIN practice_questions pq ON pq.id=pm.question_id WHERE pm.user_id=? AND pm.ok=1 AND pq.qtype='pastpaper'", uid).c || 0;
  const streak = longestStreak(activityDates(uid));
  const chalW = one('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?', uid).c || 0;
  const mathW = one("SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=? AND sim_type IN ('gplot','gtrans','deriv','integr','vector','trig','prob','stats')", uid).c || 0;
  const ictW = one("SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=? AND sim_type IN ('binary','logic','truthtab','cpu','network','ipaddr','sortvis','webplay')", uid).c || 0;
  const BD = [['first_lesson', '🎬', lessonsDone, 1], ['lessons_10', '📚', lessonsDone, 10],
    ['sim_first', '⚡', simsDone, 1], ['sims_10', '🧪', simsDone, 10],
    ['quizzes_5', '🎯', q.n || 0, 5], ['mcq_100', '❓', q.tot || 0, 100],
    ['pp_first', '📄', pp, 1], ['streak_7', '📅', streak, 7],
    ['chal_first', '🎖️', chalW, 1], ['chal_10', '🏆', chalW, 10],
    ['maths_solver', '📐', mathW, 3], ['ict_explorer', '💻', ictW, 3]];
  res.json({ badges: BD.map(([id, ic, p, rq]) => ({ id, icon: ic, prog: Math.min(p, rq), req: rq, earned: p >= rq })),
    stats: { lessons_done: lessonsDone, mcqs: q.tot || 0, quizzes: q.n || 0, sims: simsDone, past_papers: pp, streak, challenges: chalW } });
}));
app.get('/api/dashboard', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const subjects = db.prepare('SELECT id,name,name_si,name_ta,code,icon,color1,color2 FROM subjects ORDER BY id').all().map((s) => {
    const total = db.prepare('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?').get(s.id).c;
    const completed = db.prepare(`SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id
      JOIN progress p ON p.lesson_id=l.id AND p.user_id=? AND p.completed=1 WHERE u.subject_id=?`).get(uid, s.id).c;
    return { ...s, total, completed };
  });
  const lessonJoin = `
    SELECT l.id,l.title,l.youtube_id,u.name AS unit_name,s.name AS subject_name,s.color1,s.color2,t.name AS teacher_name,
           p.completed,p.watched,p.favourite,p.completed_at,p.watched_at
    FROM progress p
    JOIN lessons l ON l.id=p.lesson_id
    JOIN units u ON u.id=l.unit_id
    JOIN subjects s ON s.id=u.subject_id
    LEFT JOIN teachers t ON t.id=l.teacher_id
    WHERE p.user_id=?`;
  const completed = db.prepare(lessonJoin + ' AND p.completed=1 ORDER BY p.completed_at DESC').all(uid);
  const watched = db.prepare(lessonJoin + ' AND p.watched=1 ORDER BY p.watched_at DESC').all(uid);
  const favourites = db.prepare(lessonJoin + ' AND p.favourite=1').all(uid);
  const saved = db.prepare(`
    SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,s.name AS subject_name, u2.name AS uploader
    FROM saved_resources sv JOIN resources r ON r.id=sv.resource_id
    LEFT JOIN subjects s ON s.id=r.subject_id LEFT JOIN users u2 ON u2.id=r.uploaded_by
    WHERE sv.user_id=? ORDER BY sv.created_at DESC`).all(uid);
  const uploads = db.prepare(`
    SELECT r.id,r.title,r.category,r.status,r.size,r.downloads,r.created_at,r.valid_until,s.name AS subject_name
    FROM resources r LEFT JOIN subjects s ON s.id=r.subject_id
    WHERE r.uploaded_by=? ORDER BY r.id DESC`).all(uid);
  const counts = {
    completed: completed.length,
    watched: watched.length,
    saved: saved.length,
    uploads: uploads.length,
    favourites: favourites.length,
  };
  res.json({ subjects, counts, completed, watched, favourites, saved, uploads });
}));

// ------------------------------------------------------------ RESOURCES
const ALLOWED_EXT = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.md', '.zip', '.png', '.jpg', '.jpeg', '.webp'];
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname || '').toLowerCase();
    cb(null, 'u-' + crypto.randomBytes(10).toString('hex') + ext);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 25 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname || '').toLowerCase();
    cb(null, ALLOWED_EXT.includes(ext));
  },
});

app.get('/api/resources', ah((req, res) => {
  const { subjectId, category, search, unitId, medium, year } = req.query;
  const where = ["r.status='approved'", "(r.valid_until='' OR r.valid_until >= datetime('now'))"];
  const params = [];
  if (subjectId) { where.push('r.subject_id=?'); params.push(subjectId); }
  if (category) { where.push('r.category=?'); params.push(category); }
  if (unitId) { where.push('r.unit_id=?'); params.push(unitId); }
  if (medium) { where.push('r.medium=?'); params.push(medium); }
  if (year) { where.push('r.year=?'); params.push(year); }
  if (search) { where.push('r.title LIKE ?'); params.push('%' + str(search, 60) + '%'); }
  const uid = req.user ? req.user.id : -1;
  const rows = db.prepare(`
    SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,r.lesson_id,
           r.external_url,r.description,r.medium,r.year,r.unit_id,r.valid_until,r.premium,
           s.name AS subject_name, un.name AS unit_name, u.name AS uploader,
           CASE WHEN sv.user_id IS NULL THEN 0 ELSE 1 END AS saved
    FROM resources r
    LEFT JOIN subjects s ON s.id=r.subject_id
    LEFT JOIN units un ON un.id=r.unit_id
    LEFT JOIN users u ON u.id=r.uploaded_by
    LEFT JOIN saved_resources sv ON sv.resource_id=r.id AND sv.user_id=?
    WHERE ${where.join(' AND ')}
    ORDER BY r.id DESC LIMIT 200`).all(uid, ...params);
  res.json({ resources: rows });
}));

function handleUpload(req, res, autostatus) {
  upload.single('file')(req, res, (err) => {
    if (err) {
      if (err.code === 'LIMIT_FILE_SIZE') return bad(res, 'File is too large (max 25 MB)');
      return bad(res, 'Upload failed. Please try a different file.');
    }
    if (!req.file) return bad(res, 'Please attach a file (PDF, document, image or zip)');
    const savedPath = req.file.path;
    try {
      const title = str(req.body.title, 140);
      const category = str(req.body.category, 30);
      if (title.length < 3) { fs.unlinkSync(savedPath); return bad(res, 'Please give your resource a clear title'); }
      if (!RESOURCE_CATEGORIES.some((c) => c.id === category)) { fs.unlinkSync(savedPath); return bad(res, 'Please choose a valid category'); }
      const subjectId = req.body.subjectId ? Number(req.body.subjectId) : null;
      const lessonId = req.body.lessonId ? Number(req.body.lessonId) : null;
      const unitId = req.body.unitId ? Number(req.body.unitId) : null;
      const rmedium = MEDIUMS.includes(req.body.medium) ? req.body.medium : '';
      const ryear = str(req.body.year, 20);
      if (subjectId && !db.prepare('SELECT id FROM subjects WHERE id=?').get(subjectId)) { fs.unlinkSync(savedPath); return bad(res, 'Invalid subject'); }
      if (lessonId && !db.prepare('SELECT id FROM lessons WHERE id=?').get(lessonId)) { fs.unlinkSync(savedPath); return bad(res, 'Invalid lesson'); }
      if (unitId && !db.prepare('SELECT id FROM units WHERE id=?').get(unitId)) { fs.unlinkSync(savedPath); return bad(res, 'Invalid unit'); }
      const info = db.prepare(`INSERT INTO resources (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,unit_id,medium,year,uploaded_by,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`)
        .run(title, category, req.file.filename, str(req.file.originalname, 200), req.file.size,
          req.file.mimetype || '', subjectId, lessonId, unitId, rmedium, ryear, req.user.id, autostatus);
      res.json({ ok: true, id: info.lastInsertRowid, status: autostatus,
        approved: autostatus === 'approved' });
    } catch (e) {
      console.error(e);
      try { fs.unlinkSync(savedPath); } catch (_) {}
      res.status(500).json({ error: 'Could not save the resource' });
    }
  });
}

app.post('/api/resources', requireAuth, (req, res) => {
  if (!sw('upload_open')) return bad(res, 'Uploads are closed by admin right now.', 403);
  handleUpload(req, res, req.user.role === 'admin' ? 'approved' : 'pending');
});

app.get('/api/resources/:id/download', ah((req, res) => {
  const r = db.prepare('SELECT * FROM resources WHERE id=?').get(req.params.id);
  if (!r) return bad(res, 'Resource not found', 404);
  const allowed = r.status === 'approved' || (req.user && (req.user.role === 'admin' || req.user.id === r.uploaded_by));
  if (!allowed) return bad(res, 'This resource is not available yet (awaiting approval)', 403);
  const nowUtc = db.prepare("SELECT datetime('now') n").get().n;
  if (r.valid_until && r.valid_until < nowUtc && !(req.user && (req.user.role === 'admin' || req.user.id === r.uploaded_by)))
    return bad(res, 'This resource has expired', 403);
  if (r.premium && !(req.user && (isPrem(req.user) || req.user.role === 'admin' || req.user.id === r.uploaded_by)))
    return res.status(403).json({ error: 'This is a 💎 Premium resource', premium: true });
  const full = path.join(UPLOAD_DIR, r.file_path);
  if (!fs.existsSync(full)) return bad(res, 'File missing on server', 404);
  db.prepare('UPDATE resources SET downloads=downloads+1 WHERE id=?').run(r.id);
  res.download(full, r.orig_name || ('resource-' + r.id + path.extname(r.file_path)));
}));

app.post('/api/resources/:id/save', requireAuth, ah((req, res) => {
  const r = db.prepare("SELECT id,status FROM resources WHERE id=?").get(req.params.id);
  if (!r) return bad(res, 'Resource not found', 404);
  const uid = req.user.id;
  const ex = db.prepare('SELECT 1 FROM saved_resources WHERE user_id=? AND resource_id=?').get(uid, r.id);
  if (ex) { db.prepare('DELETE FROM saved_resources WHERE user_id=? AND resource_id=?').run(uid, r.id); return res.json({ saved: false }); }
  db.prepare('INSERT INTO saved_resources (user_id,resource_id) VALUES (?,?)').run(uid, r.id);
  res.json({ saved: true });
}));

app.delete('/api/resources/:id', requireAuth, ah((req, res) => {
  const r = db.prepare('SELECT * FROM resources WHERE id=?').get(req.params.id);
  if (!r) return bad(res, 'Resource not found', 404);
  if (req.user.role !== 'admin' && req.user.id !== r.uploaded_by) return bad(res, 'Not allowed', 403);
  db.prepare('DELETE FROM resources WHERE id=?').run(r.id);
  try { fs.unlinkSync(path.join(UPLOAD_DIR, r.file_path)); } catch (_) {}
  res.json({ ok: true });
}));

// ------------------------------------------------------------ TUTORS
function tutorOut(t) {
  let subjects = [], classes = [];
  try { subjects = JSON.parse(t.subjects || '[]'); } catch (_) {}
  try { classes = JSON.parse(t.classes || '[]'); } catch (_) {}
  return { ...t, subjects, classes };
}

app.get('/api/stats', ah((req, res) => {
  const n = (q) => db.prepare(q).get().c;
  res.json({
    subjects: n('SELECT COUNT(*) c FROM subjects'),
    units: n('SELECT COUNT(*) c FROM units'),
    lessons: n('SELECT COUNT(*) c FROM lessons'),
    resources: n("SELECT COUNT(*) c FROM resources WHERE status='approved'"),
    teachers: n('SELECT COUNT(*) c FROM teachers'),
    students: n("SELECT COUNT(*) c FROM users WHERE role='student'"),
  });
}));

app.get('/api/tutors', ah((req, res) => {
  const q = str(req.query.search || '', 60).toLowerCase();
  const subj = str(req.query.subject || '', 60).toLowerCase();
  let rows = db.prepare('SELECT * FROM tutors ORDER BY id').all().map(tutorOut);
  if (q) rows = rows.filter((t) => (t.name + ' ' + t.location + ' ' + t.subjects.join(' ')).toLowerCase().includes(q));
  if (subj) rows = rows.filter((t) => t.subjects.join(' ').toLowerCase().includes(subj));
  const dist = str(req.query.district || '', 40).toLowerCase();
  const mode = str(req.query.mode || '', 10).toLowerCase();
  const med = str(req.query.medium || '', 4).toLowerCase();
  const lvl = str(req.query.level || '', 6).toLowerCase();
  if (dist) rows = rows.filter((t) => (t.district || '').toLowerCase().includes(dist) || (t.location || '').toLowerCase().includes(dist));
  if (mode === 'online' || mode === 'physical') rows = rows.filter((t) => ['both', mode].includes((t.mode || '').toLowerCase()));
  if (MEDIUMS.includes(med)) rows = rows.filter((t) => ['', 'all', med].includes((t.medium || '').toLowerCase()));
  if (lvl === 'al' || lvl === 'ol') rows = rows.filter((t) => ['', 'both', lvl].includes((t.level || '').toLowerCase()));
  // public tutor comments: auto-delete after 3 months unless admin marked keep=1
  db.prepare("DELETE FROM tutor_comments WHERE keep=0 AND created_at < datetime('now','-3 months')").run();
  const counts = {};
  db.prepare('SELECT tutor_id, COUNT(*) c FROM tutor_comments GROUP BY tutor_id').all().forEach((r) => { counts[r.tutor_id] = r.c; });
  rows = rows.map((t) => ({ ...t, comment_count: counts[t.id] || 0 }));
  res.json({ tutors: rows });
}));

app.get('/api/tutors/:id', ah((req, res) => {
  const t = db.prepare('SELECT * FROM tutors WHERE id=?').get(req.params.id);
  if (!t) return bad(res, 'Tutor not found', 404);
  res.json({ tutor: tutorOut(t) });
}));

app.post('/api/tutors/:id/message', requireAuth, ah((req, res) => {
  const t = db.prepare('SELECT id FROM tutors WHERE id=?').get(req.params.id);
  if (!t) return bad(res, 'Tutor not found', 404);
  const message = str((req.body || {}).message, 2000);
  if (message.length < 5) return bad(res, 'Please write a short message');
  db.prepare('INSERT INTO tutor_messages (tutor_id,user_id,message) VALUES (?,?,?)').run(t.id, req.user.id, message);
  res.json({ ok: true });
}));

// ---------------- Tutor comments (public, moderated by admin) ----------------
const purgeOldComments = () => db.prepare("DELETE FROM tutor_comments WHERE keep=0 AND created_at < datetime('now','-3 months')").run();
const commentOut = (r) => { const { user_id, ...d } = r; d.days_left = Math.max(0, d.days_left || 0); return d; };
const COMMENT_SQL = `SELECT c.*, u.name AS author,
  CAST(julianday(c.created_at,'+3 months') - julianday('now') AS INTEGER) AS days_left
  FROM tutor_comments c JOIN users u ON u.id=c.user_id WHERE c.tutor_id=? ORDER BY c.id DESC`;

app.get('/api/tutors/:id/comments', ah((req, res) => {
  const t = db.prepare('SELECT id FROM tutors WHERE id=?').get(req.params.id);
  if (!t) return bad(res, 'Tutor not found', 404);
  purgeOldComments();
  if (!sw('tutor_comments')) return res.json({ enabled: false, comments: [], pending_count: 0 });
  const isAdmin = req.user && req.user.role === 'admin';
  const sql = isAdmin ? COMMENT_SQL : COMMENT_SQL.replace('WHERE c.tutor_id=?', 'WHERE c.tutor_id=? AND c.approved=1');
  const allr = db.prepare(sql).all(req.params.id);
  const pend = allr.filter((r) => !r.approved).length;
  res.json({ enabled: true, comments: allr.map(commentOut), pending_count: isAdmin ? pend : 0 });
}));

app.post('/api/tutors/:id/comments', requireAuth, ah((req, res) => {
  const t = db.prepare('SELECT id FROM tutors WHERE id=?').get(req.params.id);
  if (!t) return bad(res, 'Tutor not found', 404);
  if (!sw('tutor_comments')) return bad(res, 'Comments are disabled by admin right now.', 403);
  const body = str((req.body || {}).body, 500);
  if (body.length < 3) return bad(res, 'Please write a short comment');
  const approved = sw('comment_approve') ? 0 : 1;
  const info = db.prepare('INSERT INTO tutor_comments (tutor_id,user_id,body,approved) VALUES (?,?,?,?)').run(t.id, req.user.id, body, approved);
  const r = db.prepare(COMMENT_SQL.replace('ORDER BY c.id DESC', 'AND c.id=? ORDER BY c.id DESC')).get(req.params.id, info.lastInsertRowid);
  res.json({ ok: true, pending: !approved, comment: commentOut(r) });
}));

app.put('/api/admin/comments/:id/approve', requireAdmin, ah((req, res) => {
  db.prepare('UPDATE tutor_comments SET approved=1, is_read=1 WHERE id=?').run(req.params.id);
  res.json({ ok: true });
}));

app.delete('/api/admin/comments/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM tutor_comments WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.put('/api/admin/comments/:id/keep', requireAdmin, ah((req, res) => {
  const keep = (req.body || {}).keep ? 1 : 0;
  db.prepare('UPDATE tutor_comments SET keep=? WHERE id=?').run(keep, req.params.id);
  res.json({ ok: true, keep });
}));

// ---------------- Site settings (notification bar + contact details) + contact form ----------------
const SITE_KEYS = ['announcement', 'contact_email', 'contact_whatsapp', 'contact_address',
  'register_open', 'upload_open', 'leaderboard_on', 'tutor_comments', 'comment_approve', 'ai_on', 'careers_enabled'];
const SWITCH_DEFAULT = { register_open: '1', upload_open: '1', leaderboard_on: '1', tutor_comments: '1', comment_approve: '1', ai_on: '1', careers_enabled: '1' };
const sw = (key) => { // True when an admin switch is ON ('' / never set = default)
  const r = db.prepare('SELECT value FROM site_settings WHERE key=?').get(key);
  const v = r && r.value !== '' ? r.value : (SWITCH_DEFAULT[key] || '1');
  return v !== '0';
};
// ---------------- admin spec pack helpers ----------------
const logAdmin = (req, action, target) => {
  try { db.prepare('INSERT INTO admin_logs (admin,action,target) VALUES (?,?,?)').run((req.user && req.user.email) || '?', str(action, 80), str(target, 160)); } catch (_) {}
};
const aiCap = (prem) => {
  const v = parseInt(setGetRaw(prem ? 'ai_pro_limit' : 'ai_free_limit') || (prem ? '100' : '10'), 10);
  return isNaN(v) ? (prem ? 100 : 10) : Math.max(1, Math.min(1000, v));
};
function setGetRaw(k) { const r = db.prepare('SELECT value FROM site_settings WHERE key=?').get(k); return r ? r.value : ''; }
const aiModel = () => { const m = (setGetRaw('ai_model') || '').trim(); return /^[a-zA-Z0-9._-]{3,60}$/.test(m) ? m : AI_MODEL; };
const couponFind = (code) => {
  const cp = db.prepare('SELECT * FROM coupons WHERE code=? AND active=1').get(str(code, 40).toUpperCase());
  if (!cp) return null;
  const today = new Date().toISOString().slice(0, 10);
  if (cp.expires && cp.expires < today) return null;
  if (cp.max_uses && cp.uses >= cp.max_uses) return null;
  return cp;
};
const couponCalc = (cp, base) => {
  if (!cp) return [base, 0];
  const cut = cp.kind === 'percent' ? Math.round(base * Math.min(100, Math.max(0, cp.value)) / 100) : Math.min(base, Math.max(0, cp.value));
  return [base - cut, cut];
};
const siteOut = () => {
  const out = {};
  SITE_KEYS.forEach((k) => { const r = db.prepare('SELECT value FROM site_settings WHERE key=?').get(k); out[k] = r && r.value !== '' ? r.value : (SWITCH_DEFAULT[k] || ''); });
  return out;
};

app.get('/api/site', ah((req, res) => res.json({ site: siteOut() })));

app.put('/api/admin/site', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const up = db.prepare('INSERT INTO site_settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value');
  SITE_KEYS.forEach((k) => { if (k in b) up.run(k, str(b[k], 300)); });
  ['premium_price', 'premium_bank', 'ezcash_number', 'ai_free_limit', 'ai_pro_limit', 'ai_model', 'ai_prompt'].forEach((k) => { if (k in b) up.run(k, str(b[k], 900)); });
  if ('ai_key' in b) {
    const ak = str(b.ai_key, 200);
    if (ak === 'CLEAR') db.prepare("DELETE FROM site_settings WHERE key='ai_key'").run();
    else if (ak) up.run('ai_key', ak);
  }
  logAdmin(req, 'site_update', Object.keys(b).filter((k) => k !== 'ai_key').sort().join(',').slice(0, 150));
  res.json({ ok: true, site: siteOut() });
}));

app.post('/api/contact', ah((req, res) => {
  const b = req.body || {};
  const name = str(b.name, 80); const email = str(b.email, 120); const message = str(b.message, 1000);
  if (!name || message.length < 5) return bad(res, 'Name and a short message are required');
  db.prepare('INSERT INTO contact_messages (name,email,message) VALUES (?,?,?)').run(name, email, message);
  res.json({ ok: true });
}));

app.get('/api/admin/contact-messages', requireAdmin, ah((req, res) => {
  res.json({ messages: db.prepare('SELECT * FROM contact_messages ORDER BY id DESC LIMIT 200').all() });
}));

app.delete('/api/admin/contact-messages/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM contact_messages WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

// ---------------- Admin notification bell ----------------
try { db.exec('ALTER TABLE contact_messages ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0'); } catch (_) {}
try { db.exec('ALTER TABLE tutor_comments ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0'); } catch (_) {}
try { db.exec('ALTER TABLE tutor_comments ADD COLUMN approved INTEGER NOT NULL DEFAULT 1'); } catch (_) {}

app.get('/api/admin/notifications', requireAdmin, ah((req, res) => {
  const c = (q) => db.prepare(q).get().c;
  res.json({
    unread_msgs: c('SELECT COUNT(*) c FROM contact_messages WHERE is_read=0'),
    new_comments: c('SELECT COUNT(*) c FROM tutor_comments WHERE is_read=0'),
    pending: c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
    latest: db.prepare('SELECT id,name,message,created_at FROM contact_messages WHERE is_read=0 ORDER BY id DESC LIMIT 5').all(),
    latestc: db.prepare(`SELECT c.id,c.body,c.created_at,u.name AS author,t.name AS tutor FROM tutor_comments c
      JOIN users u ON u.id=c.user_id JOIN tutors t ON t.id=c.tutor_id WHERE c.is_read=0 ORDER BY c.id DESC LIMIT 5`).all(),
  });
}));

app.post('/api/admin/notifications/read-all', requireAdmin, ah((req, res) => {
  db.prepare('UPDATE contact_messages SET is_read=1').run();
  db.prepare('UPDATE tutor_comments SET is_read=1').run();
  res.json({ ok: true });
}));

// ------------------------------------------------------------ ADMIN
app.get('/api/admin/overview', requireAdmin, ah((req, res) => {
  const c = (sql, ...p) => db.prepare(sql).get(...p).c;
  res.json({
    students: c("SELECT COUNT(*) c FROM users WHERE role='student'"),
    lessons: c('SELECT COUNT(*) c FROM lessons'),
    units: c('SELECT COUNT(*) c FROM units'),
    subjects: c('SELECT COUNT(*) c FROM subjects'),
    teachers: c('SELECT COUNT(*) c FROM teachers'),
    tutors: c('SELECT COUNT(*) c FROM tutors'),
    pending: c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
    resources: c("SELECT COUNT(*) c FROM resources WHERE status='approved'"),
    messages: c('SELECT COUNT(*) c FROM tutor_messages'),
    years: db.prepare('SELECT * FROM al_years ORDER BY id').all(),
    recentStudents: db.prepare("SELECT id,name,email,school,district,al_year,created_at FROM users WHERE role='student' ORDER BY id DESC LIMIT 6").all(),
    pendingList: db.prepare(`SELECT r.id,r.title,r.category,r.created_at,u.name AS uploader,s.name AS subject_name
      FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by LEFT JOIN subjects s ON s.id=r.subject_id
      WHERE r.status='pending' ORDER BY r.id DESC LIMIT 6`).all(),
    recentMessages: db.prepare(`SELECT m.id,m.message,m.created_at,u.name AS student,t.name AS tutor
      FROM tutor_messages m JOIN users u ON u.id=m.user_id JOIN tutors t ON t.id=m.tutor_id ORDER BY m.id DESC LIMIT 6`).all(),
  });
}));

// ---------------- super admin dashboard (all real DB data) ----------------
app.get('/api/admin/super', requireAdmin, ah((req, res) => {
  const c = (sql, ...p) => db.prepare(sql).get(...p).c;
  const now = Date.now(); const week = 6048e5;
  const iso = (t2) => new Date(t2).toISOString().slice(0, 19).replace('T', ' ');
  const dstr = (t2) => new Date(t2).toISOString().slice(0, 10);
  const growth = [], activity = [];
  for (let i = 7; i >= 0; i--) {
    const a = now - (i + 1) * week, b2 = now - i * week;
    const lb = new Date(b2).toISOString().slice(5, 10).split('-').reverse().join(' ');
    growth.push({ label: lb, n: c("SELECT COUNT(*) c FROM users WHERE role='student' AND created_at>=? AND created_at<?", iso(a), iso(b2)) });
    activity.push({ label: lb, n: Math.floor((db.prepare('SELECT COALESCE(SUM(seconds),0) n FROM study_events WHERE day>=? AND day<?').get(dstr(a), dstr(b2)) || { n: 0 }).n / 60) });
  }
  const d30 = iso(now - 30 * 864e5), d7 = dstr(now - 6 * 864e5);
  const popular = db.prepare(`SELECT s.name, s.name_si, s.name_ta, COUNT(*) n FROM progress p
    JOIN lessons l ON l.id=p.lesson_id JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
    WHERE p.completed=1 GROUP BY s.id ORDER BY n DESC`).all();
  const feed = [];
  db.prepare("SELECT name, created_at ts FROM users WHERE role='student' ORDER BY id DESC LIMIT 4").all()
    .forEach((r) => feed.push({ ic: '🎓', text: r.name + ' registered', ts: r.ts }));
  db.prepare('SELECT r.title, r.created_at ts, u.name un FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by ORDER BY r.id DESC LIMIT 4').all()
    .forEach((r) => feed.push({ ic: '📤', text: (r.un || 'Someone') + ' uploaded "' + r.title + '"', ts: r.ts }));
  db.prepare('SELECT c.created_at ts, u.name un, t2.name tn FROM tutor_comments c JOIN users u ON u.id=c.user_id JOIN tutors t2 ON t2.id=c.tutor_id ORDER BY c.id DESC LIMIT 3').all()
    .forEach((r) => feed.push({ ic: '💬', text: r.un + ' commented on tutor ' + r.tn, ts: r.ts }));
  db.prepare('SELECT name, created_at ts FROM contact_messages ORDER BY id DESC LIMIT 2').all()
    .forEach((r) => feed.push({ ic: '✉️', text: r.name + ' sent a contact message', ts: r.ts }));
  feed.sort((x, y) => (x.ts < y.ts ? 1 : -1));
  feed.splice(8);
  feed.forEach((f) => { const t2 = new Date((f.ts || '').replace(' ', 'T') + 'Z').getTime(); f.ago = isNaN(t2) ? null : Math.max(0, Math.floor((now - t2) / 60000)); });
  const top = db.prepare(`SELECT u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
    (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done
    FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
    WHERE u.role='student' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id LIMIT 5`).all(d7);
  let upBytes = 0;
  try { fs.readdirSync(UPLOAD_DIR).forEach((f) => { const st2 = fs.statSync(path.join(UPLOAD_DIR, f)); if (st2.isFile()) upBytes += st2.size; }); } catch (_) {}
  const cards = {
    students: c("SELECT COUNT(*) c FROM users WHERE role='student'"),
    active7: c('SELECT COUNT(DISTINCT user_id) c FROM study_events WHERE day>=?', d7),
    new30: c("SELECT COUNT(*) c FROM users WHERE role='student' AND created_at>=?", d30),
    teachers: c('SELECT COUNT(*) c FROM teachers'), tutors: c('SELECT COUNT(*) c FROM tutors'),
    lessons: c('SELECT COUNT(*) c FROM lessons'),
    resources: c("SELECT COUNT(*) c FROM resources WHERE status='approved'"),
    pastpapers: c("SELECT COUNT(*) c FROM resources WHERE status='approved' AND category='past_papers'"),
    pending_uploads: c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
    pending_comments: c('SELECT COUNT(*) c FROM tutor_comments WHERE approved=0'),
    exams_sat: c('SELECT COUNT(*) c FROM exam_attempts'),
    exam_avg: Math.round((db.prepare('SELECT COALESCE(AVG(score*100.0/qcount),0) a FROM exam_attempts').get() || { a: 0 }).a),
    slips_pending: c("SELECT COUNT(*) c FROM payments WHERE status='pending'"),
    revenue: (db.prepare("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved'").get() || { s: 0 }).s,
    rev_today: (db.prepare("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)=?").get(dstr(now)) || { s: 0 }).s,
    rev_7d: (db.prepare("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)>=?").get(d7) || { s: 0 }).s,
    rev_30d: (db.prepare("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)>=?").get(dstr(now - 29 * 864e5)) || { s: 0 }).s,
    ai_today: (db.prepare('SELECT COALESCE(SUM(n),0) s FROM ai_usage WHERE day=?').get(dstr(now)) || { s: 0 }).s,
    ai_total: (db.prepare('SELECT COALESCE(SUM(n),0) s FROM ai_usage').get() || { s: 0 }).s,
    coupons: c('SELECT COUNT(*) c FROM coupons WHERE active=1'),
    challenges: c('SELECT COUNT(*) c FROM challenges'),
    reports_open: c("SELECT COUNT(*) c FROM ai_reports WHERE status='open'"),
  };
  const dbFile = path.join(DATA_DIR, 'alplanner.db');
  res.json({ cards, growth, activity, popular, feed, top,
    system: { db_bytes: fs.existsSync(dbFile) ? fs.statSync(dbFile).size : 0, uploads_bytes: upBytes,
      uptime_s: Math.floor((Date.now() - BOOT_T0) / 1000),
      premium_users: c("SELECT COUNT(*) c FROM users WHERE premium_until IS NOT NULL AND premium_until>=?", dstr(now)),
      ai_week: (db.prepare('SELECT COALESCE(SUM(n),0) s FROM ai_usage WHERE day>=?').get(d7) || { s: 0 }).s,
      ver: SITE_VER,
      backup_at: (db.prepare("SELECT value v FROM site_settings WHERE key='backup_at'").get() || { v: '' }).v } });
}));

// ---------------- one-click DB backup ----------------
const BACKUP_DIR = path.join(DATA_DIR, 'backups');

app.post('/api/admin/backup', requireAdmin, ah((req, res) => {
  fs.mkdirSync(BACKUP_DIR, { recursive: true });
  const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const fn = 'alplanner-' + new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14) + '.db';
  const dst = path.join(BACKUP_DIR, fn);
  fs.copyFileSync(path.join(DATA_DIR, 'alplanner.db'), dst);
  try { const files = fs.readdirSync(BACKUP_DIR).filter((f) => f.endsWith('.db')).sort(); files.slice(0, -10).forEach((f) => fs.unlinkSync(path.join(BACKUP_DIR, f))); } catch (_) {}
  db.prepare("INSERT INTO site_settings (key,value) VALUES ('backup_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").run(ts);
  logAdmin(req, 'backup', fn);
  res.json({ ok: true, file: fn, bytes: fs.statSync(dst).size, at: ts });
}));

app.get('/api/admin/backup/download', requireAdmin, ah((req, res) => {
  let files = [];
  try { files = fs.readdirSync(BACKUP_DIR).filter((f) => f.endsWith('.db')).sort(); } catch (_) {}
  if (!files.length) return bad(res, 'No backup yet — press Backup now first', 404);
  res.download(path.join(BACKUP_DIR, files[files.length - 1]), files[files.length - 1]);
}));

// ---------------- full student rankings for admin ----------------
app.get('/api/admin/rankings', requireAdmin, ah((req, res) => {
  const d7 = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10);
  const lb = db.prepare(`SELECT u.id, u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
    (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done,
    (SELECT COALESCE(AVG(a.score*100.0/a.qcount),0) FROM exam_attempts a WHERE a.user_id=u.id) examavg
    FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
    WHERE u.role='student' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id LIMIT 50`).all(d7);
  res.json({ top: lb.map((r) => ({ name: r.name, school: r.school || '', minutes: Math.floor(r.sec / 60), lessons: r.done, exam_avg: Math.round(r.examavg) })) });
}));

app.get('/api/admin/resources', requireAdmin, ah((req, res) => {
  const status = str(req.query.status || '', 20);
  const where = status ? 'WHERE r.status=?' : '';
  const params = status ? [status] : [];
  res.json({
    resources: db.prepare(`
      SELECT r.*, s.name AS subject_name, u.name AS uploader, l.title AS lesson_title,
        CASE WHEN r.valid_until<>'' AND r.valid_until < datetime('now') THEN 1 ELSE 0 END AS expired
      FROM resources r LEFT JOIN subjects s ON s.id=r.subject_id
      LEFT JOIN users u ON u.id=r.uploaded_by LEFT JOIN lessons l ON l.id=r.lesson_id
      ${where} ORDER BY r.id DESC LIMIT 300`).all(...params),
  });
}));

app.put('/api/admin/resources/:id', requireAdmin, ah((req, res) => {
  const r = db.prepare('SELECT * FROM resources WHERE id=?').get(req.params.id);
  if (!r) return bad(res, 'Resource not found', 404);
  const b = req.params.id && (req.body || {}) || {};
  const title = b.title !== undefined ? str(b.title, 140) : r.title;
  const category = b.category !== undefined && RESOURCE_CATEGORIES.some((c) => c.id === b.category) ? b.category : r.category;
  const status = ['pending', 'approved', 'rejected'].includes(b.status) ? b.status : r.status;
  const subjectId = b.subjectId !== undefined ? (b.subjectId ? Number(b.subjectId) : null) : r.subject_id;
  const unitId = b.unitId !== undefined ? (b.unitId ? Number(b.unitId) : null) : r.unit_id;
  const medium = MEDIUMS.includes(b.medium) ? b.medium : r.medium;
  const year = b.year !== undefined ? str(b.year, 20) : r.year;
  const prem = b.premium !== undefined ? (b.premium ? 1 : 0) : r.premium;
  db.prepare('UPDATE resources SET title=?, category=?, status=?, subject_id=?, unit_id=?, medium=?, year=?, premium=? WHERE id=?')
    .run(title, category, status, subjectId, unitId, medium, year, prem, r.id);
  // validity period: admin may set/change any time ('' / 'forever' = no expiry)
  const VDAYS = { '1w': 7, '1m': 30, '4m': 122, '6m': 183, '12m': 365, '24m': 730 };
  if (b.validity !== undefined) {
    if (b.validity === '' || b.validity === 'forever') db.prepare("UPDATE resources SET valid_until='' WHERE id=?").run(r.id);
    else if (VDAYS[b.validity]) db.prepare("UPDATE resources SET valid_until=datetime('now', ?) WHERE id=?").run('+' + VDAYS[b.validity] + ' days', r.id);
  }
  res.json({ ok: true });
}));

// Admin content management ---------------------------------------------
app.post('/api/admin/subjects', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const name = str(b.name, 80);
  if (!name) return bad(res, 'Subject name required');
  const info = db.prepare('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2,medium) VALUES (?,?,?,?,?,?,?,?)')
    .run(name, str(b.name_si, 80), str(b.name_ta, 80), str(b.code, 10), str(b.icon, 20) || 'book',
      str(b.color1, 10) || '#6366f1', str(b.color2, 10) || '#22d3ee', MEDIUMS.includes(b.medium) ? b.medium : 'en');
  res.json({ ok: true, id: info.lastInsertRowid });
}));
app.delete('/api/admin/subjects/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM subjects WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.get('/api/admin/units', requireAdmin, ah((req, res) => {
  const sid = Number(req.query.subjectId) || 0;
  res.json({ units: db.prepare('SELECT * FROM units WHERE subject_id=? ORDER BY ord,id').all(sid) });
}));
app.post('/api/admin/units', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const sid = Number(b.subjectId), name = str(b.name, 120);
  if (!sid || !name) return bad(res, 'Subject and unit name required');
  if (!db.prepare('SELECT id FROM subjects WHERE id=?').get(sid)) return bad(res, 'Invalid subject');
  const info = db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)').run(sid, name, Number(b.ord) || 0);
  res.json({ ok: true, id: info.lastInsertRowid });
}));
app.delete('/api/admin/units/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM units WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.post('/api/admin/lessons', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const uid = Number(b.unitId), title = str(b.title, 160);
  if (!uid || !title) return bad(res, 'Unit and lesson title required');
  if (!db.prepare('SELECT id FROM units WHERE id=?').get(uid)) return bad(res, 'Invalid unit');
  const teacherId = b.teacherId ? Number(b.teacherId) : null;
  const yt = ytNormalize(b.video || '');
  const info = db.prepare('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)')
    .run(uid, teacherId, title, str(b.description, 3000), yt, str(b.notes, 8000), Number(b.ord) || 0);
  res.json({ ok: true, id: info.lastInsertRowid });
}));
app.put('/api/admin/lessons/:id', requireAdmin, ah((req, res) => {
  const l = db.prepare('SELECT * FROM lessons WHERE id=?').get(req.params.id);
  if (!l) return bad(res, 'Lesson not found', 404);
  const b = req.body || {};
  db.prepare('UPDATE lessons SET title=?,description=?,youtube_id=?,notes=?,teacher_id=? WHERE id=?')
    .run(b.title !== undefined ? str(b.title, 160) : l.title,
      b.description !== undefined ? str(b.description, 3000) : l.description,
      b.video !== undefined ? ytNormalize(b.video) : l.youtube_id,
      b.notes !== undefined ? str(b.notes, 8000) : l.notes,
      b.teacherId !== undefined ? (b.teacherId ? Number(b.teacherId) : null) : l.teacher_id,
      l.id);
  res.json({ ok: true });
}));
app.delete('/api/admin/lessons/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM lessons WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.post('/api/admin/teachers', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  if (!str(b.name, 80)) return bad(res, 'Teacher name required');
  const info = db.prepare('INSERT INTO teachers (name,bio,subjects,photo) VALUES (?,?,?,?)')
    .run(str(b.name, 80), str(b.bio, 600), str(b.subjects, 120), str(b.photo, 200));
  res.json({ ok: true, id: info.lastInsertRowid });
}));
app.put('/api/admin/teachers/:id', requireAdmin, ah((req, res) => {
  const t0 = db.prepare('SELECT * FROM teachers WHERE id=?').get(req.params.id);
  if (!t0) return bad(res, 'Teacher not found', 404);
  const b = req.body || {};
  db.prepare('UPDATE teachers SET name=?,bio=?,subjects=?,photo=? WHERE id=?')
    .run(str(b.name, 80) || t0.name, str(b.bio, 600), str(b.subjects, 120), str(b.photo, 200), req.params.id);
  res.json({ ok: true });
}));
app.delete('/api/admin/teachers/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM teachers WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.post('/api/admin/tutors', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  if (!str(b.name, 80)) return bad(res, 'Tutor name required');
  const arr = (v) => { try { const a = typeof v === 'string' ? JSON.parse(v) : v; return JSON.stringify(Array.isArray(a) ? a.slice(0, 10).map((x) => str(x, 120)) : []); } catch (_) { return '[]'; } };
  const tutFields = (bb, t0) => {
    const mode = str(bb.mode, 10).toLowerCase(); const lvl = str(bb.level, 6).toLowerCase();
    return [str(bb.name, 80) || (t0 && t0.name), str(bb.photo, 200), arr(bb.subjects), str(bb.experience, 40), arr(bb.classes),
      str(bb.location, 80), str(bb.phone, 30), str(bb.whatsapp, 30), str(bb.email, 120), str(bb.bio, 600),
      DISTRICTS.includes(bb.district) ? bb.district : '', ['online', 'physical', 'both'].includes(mode) ? mode : '',
      MEDIUMS.includes(bb.medium) ? bb.medium : '', ['al', 'ol', 'both'].includes(lvl) ? lvl : ''];
  };
  const info = db.prepare(`INSERT INTO tutors (name,photo,subjects,experience,classes,location,phone,whatsapp,email,bio,district,mode,medium,level)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(...tutFields(b, null));
  res.json({ ok: true, id: info.lastInsertRowid });
}));
app.put('/api/admin/tutors/:id', requireAdmin, ah((req, res) => {
  const t0 = db.prepare('SELECT * FROM tutors WHERE id=?').get(req.params.id);
  if (!t0) return bad(res, 'Tutor not found', 404);
  const b = req.body || {}; const arr = (v) => { try { const a = typeof v === 'string' ? JSON.parse(v) : v; return JSON.stringify(Array.isArray(a) ? a.slice(0, 10).map((x) => str(x, 120)) : []); } catch (_) { return '[]'; } };
  const mode = str(b.mode, 10).toLowerCase(); const lvl = str(b.level, 6).toLowerCase();
  db.prepare(`UPDATE tutors SET name=?,photo=?,subjects=?,experience=?,classes=?,location=?,phone=?,whatsapp=?,email=?,bio=?,district=?,mode=?,medium=?,level=? WHERE id=?`)
    .run(str(b.name, 80) || t0.name, str(b.photo, 200), arr(b.subjects), str(b.experience, 40), arr(b.classes),
      str(b.location, 80), str(b.phone, 30), str(b.whatsapp, 30), str(b.email, 120), str(b.bio, 600),
      DISTRICTS.includes(b.district) ? b.district : '', ['online', 'physical', 'both'].includes(mode) ? mode : '',
      MEDIUMS.includes(b.medium) ? b.medium : '', ['al', 'ol', 'both'].includes(lvl) ? lvl : '', req.params.id);
  res.json({ ok: true });
}));
app.delete('/api/admin/tutors/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM tutors WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.post('/api/admin/years', requireAdmin, ah((req, res) => {
  const label = str((req.body || {}).label, 20);
  if (!label) return bad(res, 'Year label required (e.g. A/L 2029)');
  try { db.prepare('INSERT INTO al_years (label,active) VALUES (?,1)').run(label); }
  catch (_) { return bad(res, 'That year already exists'); }
  res.json({ ok: true });
}));
app.put('/api/admin/years/:id', requireAdmin, ah((req, res) => {
  const y = db.prepare('SELECT * FROM al_years WHERE id=?').get(req.params.id);
  if (!y) return bad(res, 'Not found', 404);
  db.prepare('UPDATE al_years SET active=? WHERE id=?').run(y.active ? 0 : 1, y.id);
  res.json({ ok: true, active: y.active ? 0 : 1 });
}));
app.delete('/api/admin/years/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM al_years WHERE id=?').run(req.params.id); res.json({ ok: true });
}));

app.get('/api/admin/students', requireAdmin, ah((req, res) => {
  const q = str(req.query.search || '', 60);
  const fy = str(req.query.year, 20), fd = str(req.query.district, 60), fm = str(req.query.medium, 5);
  let where = '';
  const params = [];
  if (q) { where += ' AND (name LIKE ? OR email LIKE ? OR school LIKE ?)'; params.push('%' + q + '%', '%' + q + '%', '%' + q + '%'); }
  if (fy) { where += ' AND al_year=?'; params.push(fy); }
  if (fd) { where += ' AND district=?'; params.push(fd); }
  if (['en', 'si', 'ta'].includes(fm)) { where += ' AND medium=?'; params.push(fm); }
  res.json({
    students: db.prepare(`SELECT id,name,email,role,school,district,al_year,medium,stream,subjects,status,created_at
      FROM users WHERE 1=1 ${where} ORDER BY id DESC LIMIT 400`).all(...params),
  });
}));
app.get('/api/admin/students/:id', requireAdmin, ah((req, res) => {
  const uid2 = req.params.id;
  const u = db.prepare('SELECT id,name,email,role,school,district,al_year,medium,stream,subjects,premium_until,created_at FROM users WHERE id=?').get(uid2);
  if (!u) return bad(res, 'Not found', 404);
  const c = (sql, ...p) => (db.prepare(sql).get(...p) || { c: 0 }).c;
  const d7 = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10);
  const today = new Date().toISOString().slice(0, 10);
  const ex = db.prepare('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?').get(uid2);
  const mcqA = db.prepare('SELECT AVG(b) a FROM (SELECT MAX(score*1.0/total) b FROM mcq_attempts WHERE user_id=? GROUP BY lesson_id)').get(uid2).a;
  const last = (db.prepare(`SELECT MAX(y) m FROM (
      SELECT day y FROM study_events WHERE user_id=?
      UNION SELECT substr(completed_at,1,10) FROM progress WHERE user_id=? AND completed_at<>''
      UNION SELECT substr(created_at,1,10) FROM exam_attempts WHERE user_id=?)`).get(uid2, uid2, uid2) || {}).m || null;
  const rec = [];
  db.prepare('SELECT l.title, p.completed_at ts FROM progress p JOIN lessons l ON l.id=p.lesson_id WHERE p.user_id=? AND p.completed=1 ORDER BY p.completed_at DESC LIMIT 5').all(uid2)
    .forEach((r) => rec.push({ ic: '✅', text: r.title, ts: r.ts }));
  db.prepare('SELECT subject, score, qcount, created_at ts FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 3').all(uid2)
    .forEach((r) => rec.push({ ic: '🎯', text: r.subject + ' exam — ' + r.score + '/' + r.qcount, ts: r.ts }));
  db.prepare('SELECT amount, status, created_at ts FROM payments WHERE user_id=? ORDER BY id DESC LIMIT 3').all(uid2)
    .forEach((r) => rec.push({ ic: '💎', text: 'Slip Rs. ' + (r.amount || 0) + ' — ' + r.status, ts: r.ts }));
  rec.sort((x, y) => (x.ts < y.ts ? 1 : -1)); rec.splice(8);
  res.json({ u, last_seen: last, recent: rec, stats: {
    lessons_done: c('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1', uid2),
    lessons_watched: c('SELECT COUNT(*) c FROM progress WHERE user_id=? AND watched=1', uid2),
    saved: c('SELECT COUNT(*) c FROM saved_resources WHERE user_id=?', uid2),
    uploads: c('SELECT COUNT(*) c FROM resources WHERE uploaded_by=?', uid2),
    sims_tried: c('SELECT COUNT(*) c FROM sim_progress WHERE user_id=?', uid2),
    study_min: Math.floor((db.prepare('SELECT COALESCE(SUM(seconds),0) s FROM study_events WHERE user_id=?').get(uid2).s || 0) / 60),
    study_7d: Math.floor((db.prepare('SELECT COALESCE(SUM(seconds),0) s FROM study_events WHERE user_id=? AND day>=?').get(uid2, d7).s || 0) / 60),
    exams: ex.c, exam_avg: Math.round(ex.a), exam_best: Math.round(ex.b),
    mcq_avg: Math.round((mcqA || 0) * 100),
    ai_today: (db.prepare('SELECT n FROM ai_usage WHERE user_id=? AND day=?').get(uid2, today) || { n: 0 }).n,
  } });
}));

app.put('/api/admin/users/:id', requireAdmin, ah((req, res) => {
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.params.id);
  if (!u) return bad(res, 'User not found', 404);
  const role = (req.body || {}).role === 'admin' ? 'admin' : 'student';
  if (u.id === req.user.id && role !== 'admin') return bad(res, 'You cannot remove your own admin role');
  db.prepare('UPDATE users SET role=? WHERE id=?').run(role, u.id);
  logAdmin(req, 'role_change', u.email + ' -> ' + role);
  res.json({ ok: true });
}));
app.delete('/api/admin/users/:id', requireAdmin, ah((req, res) => {
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.params.id);
  if (!u) return bad(res, 'User not found', 404);
  if (u.id === req.user.id) return bad(res, 'You cannot delete your own account');
  db.prepare('DELETE FROM users WHERE id=?').run(u.id);
  logAdmin(req, 'user_delete', u.email);
  res.json({ ok: true });
}));

app.get('/api/admin/messages', requireAdmin, ah((req, res) => {
  res.json({
    messages: db.prepare(`SELECT m.*, u.name AS student, u.email AS student_email, t.name AS tutor
      FROM tutor_messages m JOIN users u ON u.id=m.user_id JOIN tutors t ON t.id=m.tutor_id ORDER BY m.id DESC LIMIT 200`).all(),
  });
}));

// =================================================== ADMIN SPEC PACK (2026-08-11p)
const STATUS_MAP = { suspend: 'suspended', restore: 'active' };

app.post('/api/admin/students/:id/status', requireAdmin, ah((req, res) => {
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.params.id);
  if (!u) return bad(res, 'User not found', 404);
  if (u.role === 'admin') return bad(res, 'Admin accounts cannot be suspended');
  const act = str((req.body || {}).action, 12);
  if (!STATUS_MAP[act]) return bad(res, 'Bad action');
  db.prepare('UPDATE users SET status=? WHERE id=?').run(STATUS_MAP[act], u.id);
  if (act === 'suspend') db.prepare('DELETE FROM sessions WHERE user_id=?').run(u.id);
  logAdmin(req, 'student_' + act, u.email);
  res.json({ ok: true, status: STATUS_MAP[act] });
}));

app.post('/api/admin/students/:id/resetpw', requireAdmin, ah((req, res) => {
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.params.id);
  if (!u) return bad(res, 'User not found', 404);
  const temp = crypto.randomBytes(4).toString('hex');
  db.prepare('UPDATE users SET password_hash=? WHERE id=?').run(bcrypt.hashSync(temp, 10), u.id);
  db.prepare('DELETE FROM sessions WHERE user_id=?').run(u.id);
  logAdmin(req, 'password_reset', u.email);
  res.json({ ok: true, temp, email: u.email });
}));

app.post('/api/admin/students/:id/impersonate', requireAdmin, ah((req, res) => {
  const u = db.prepare('SELECT * FROM users WHERE id=?').get(req.params.id);
  if (!u) return bad(res, 'User not found', 404);
  if (u.role !== 'student') return bad(res, 'Only student accounts can be opened this way');
  logAdmin(req, 'impersonate', u.email);
  const back = parseCookies(req)[COOKIE] || '';
  createSession(res, u.id);
  res.json({ ok: true, user: publicUser(u), back });
}));

app.post('/api/auth/unimpersonate', ah((req, res) => {
  const tok = str((req.body || {}).back, 100);
  const u = db.prepare('SELECT u.* FROM sessions se JOIN users u ON u.id=se.user_id WHERE se.token=? AND se.expires_at>?').get(tok, Date.now());
  if (!u || u.role !== 'admin') return bad(res, 'Could not switch back — please log in again.', 400);
  res.cookie(COOKIE, tok, { httpOnly: true, sameSite: 'lax', path: '/', maxAge: SESSION_DAYS * 864e5 });
  res.json({ ok: true, user: publicUser(u) });
}));

// ---------------- audit log + CSV exports ----------------
app.get('/api/admin/logs', requireAdmin, ah((req, res) => {
  res.json({ logs: db.prepare('SELECT * FROM admin_logs ORDER BY id DESC LIMIT 250').all() });
}));

const csvSend = (res, name, header, data) => {
  const cell = (v) => { const s2 = v == null ? '' : String(v); return /[",\n]/.test(s2) ? '"' + s2.replace(/"/g, '""') + '"' : s2; };
  const txt = '﻿' + [header].concat(data).map((r) => r.map(cell).join(',')).join('\r\n');
  res.setHeader('Content-Type', 'text/csv; charset=utf-8');
  res.setHeader('Content-Disposition', 'attachment; filename=alplanner-' + name + '.csv');
  res.send(txt);
};

app.get('/api/admin/export/:kind', requireAdmin, ah((req, res) => {
  const kind = req.params.kind;
  if (kind === 'students') {
    const rs = db.prepare("SELECT id,name,email,school,district,al_year,medium,stream,subjects,status,premium_until,created_at FROM users WHERE role='student' ORDER BY id DESC").all();
    logAdmin(req, 'export', 'students');
    return csvSend(res, 'students', ['id', 'name', 'email', 'school', 'district', 'al_year', 'medium', 'stream', 'subjects', 'status', 'premium_until', 'created_at'],
      rs.map((r) => [r.id, r.name, r.email, r.school, r.district, r.al_year, r.medium, r.stream, r.subjects, r.status, r.premium_until, r.created_at]));
  }
  if (kind === 'payments') {
    const rs = db.prepare('SELECT p.id,u.name,u.email,p.amount,p.coupon,p.note,p.status,p.reason,p.created_at,p.decided_at FROM payments p JOIN users u ON u.id=p.user_id ORDER BY p.id DESC').all();
    logAdmin(req, 'export', 'payments');
    return csvSend(res, 'payments', ['id', 'student', 'email', 'amount', 'coupon', 'note', 'status', 'reason', 'created_at', 'decided_at'],
      rs.map((r) => [r.id, r.name, r.email, r.amount, r.coupon, r.note, r.status, r.reason, r.created_at, r.decided_at]));
  }
  if (kind === 'exams') {
    const rs = db.prepare('SELECT e.id,u.name,u.email,e.subject,e.mode,e.score,e.qcount,e.seconds,e.created_at FROM exam_attempts e JOIN users u ON u.id=e.user_id ORDER BY e.id DESC').all();
    logAdmin(req, 'export', 'exams');
    return csvSend(res, 'exam-results', ['id', 'student', 'email', 'subject', 'mode', 'score', 'out_of', 'seconds', 'created_at'],
      rs.map((r) => [r.id, r.name, r.email, r.subject, r.mode, r.score, r.qcount, r.seconds, r.created_at]));
  }
  if (kind === 'questions') {
    const rs = db.prepare('SELECT q.id,l.title,q.q,q.a,q.b,q.c,q.d,q.answer,q.explanation FROM lesson_questions q JOIN lessons l ON l.id=q.lesson_id ORDER BY q.lesson_id, q.ord, q.id').all();
    logAdmin(req, 'export', 'questions');
    return csvSend(res, 'questions', ['id', 'lesson', 'question', 'A', 'B', 'C', 'D', 'correct', 'explanation'],
      rs.map((r) => [r.id, r.title, r.q, r.a, r.b, r.c, r.d, r.answer, r.explanation]));
  }
  bad(res, 'Unknown export', 404);
}));

// ---------------- 🎟️ coupons ----------------
app.get('/api/admin/coupons', requireAdmin, ah((req, res) => {
  res.json({ coupons: db.prepare('SELECT * FROM coupons ORDER BY id DESC LIMIT 200').all() });
}));
app.post('/api/admin/coupons', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const code = str(b.code, 40).toUpperCase().replace(/ /g, '');
  if (!/^[A-Z0-9-]{3,40}$/.test(code)) return bad(res, 'Code must be 3-40 letters/numbers (e.g. AL2027)');
  const kind = b.kind === 'fixed' ? 'fixed' : 'percent';
  let value = parseInt(b.value || 0, 10); if (isNaN(value) || value < 0) value = 0; if (kind === 'percent' && value > 100) value = 100;
  if (!value) return bad(res, 'Please set the discount value');
  let maxu = parseInt(b.max_uses || 0, 10); if (isNaN(maxu) || maxu < 0) maxu = 0; if (maxu > 100000) maxu = 100000;
  const exp = str(b.expires, 12);
  if (exp && !/^\d{4}-\d{2}-\d{2}$/.test(exp)) return bad(res, 'Expiry must be a date (YYYY-MM-DD)');
  try { db.prepare('INSERT INTO coupons (code,kind,value,expires,max_uses) VALUES (?,?,?,?,?)').run(code, kind, value, exp, maxu); }
  catch (e) { return bad(res, 'That code already exists', 409); }
  logAdmin(req, 'coupon_create', code);
  res.json({ ok: true });
}));
app.put('/api/admin/coupons/:id', requireAdmin, ah((req, res) => {
  const cp = db.prepare('SELECT * FROM coupons WHERE id=?').get(req.params.id);
  if (!cp) return bad(res, 'Not found', 404);
  const nv = cp.active ? 0 : 1;
  db.prepare('UPDATE coupons SET active=? WHERE id=?').run(nv, cp.id);
  logAdmin(req, nv ? 'coupon_on' : 'coupon_off', cp.code);
  res.json({ ok: true, active: nv });
}));
app.delete('/api/admin/coupons/:id', requireAdmin, ah((req, res) => {
  const cp = db.prepare('SELECT * FROM coupons WHERE id=?').get(req.params.id);
  if (!cp) return bad(res, 'Not found', 404);
  db.prepare('DELETE FROM coupons WHERE id=?').run(cp.id);
  logAdmin(req, 'coupon_delete', cp.code);
  res.json({ ok: true });
}));

// ---------------- 🤖 AI studio ----------------
app.get('/api/admin/ailore', requireAdmin, ah((req, res) => {
  res.json({ lore: db.prepare('SELECT * FROM ai_knowledge ORDER BY id DESC LIMIT 100').all(),
    reports: db.prepare(`SELECT r.*, u.name, u.email FROM ai_reports r JOIN users u ON u.id=r.user_id
      ORDER BY CASE r.status WHEN 'open' THEN 0 ELSE 1 END, r.id DESC LIMIT 100`).all() });
}));
app.post('/api/admin/ailore', requireAdmin, ah((req, res) => {
  const txt = str((req.body || {}).text, 1500);
  if (txt.length < 5) return bad(res, 'Please write the knowledge note (5+ characters)');
  db.prepare('INSERT INTO ai_knowledge (text) VALUES (?)').run(txt);
  logAdmin(req, 'ai_knowledge', txt.slice(0, 60));
  res.json({ ok: true });
}));
app.delete('/api/admin/ailore/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM ai_knowledge WHERE id=?').run(req.params.id);
  logAdmin(req, 'ai_knowledge_delete', '#' + req.params.id);
  res.json({ ok: true });
}));
app.put('/api/admin/aireports/:id', requireAdmin, ah((req, res) => {
  const r = db.prepare('SELECT * FROM ai_reports WHERE id=?').get(req.params.id);
  if (!r) return bad(res, 'Not found', 404);
  const stt = (req.body || {}).action === 'resolve' ? 'resolved' : 'open';
  db.prepare('UPDATE ai_reports SET status=? WHERE id=?').run(stt, r.id);
  logAdmin(req, 'ai_report_' + stt, '#' + r.id);
  res.json({ ok: true, status: stt });
}));
app.post('/api/ai/report', requireAuth, ah((req, res) => {
  const b = req.body || {};
  const q = str(b.question, 1500), a = str(b.answer, 3000);
  if (!q || !a) return bad(res, 'Nothing to report');
  const today = new Date().toISOString().slice(0, 10);
  const n = db.prepare('SELECT COUNT(*) c FROM ai_reports WHERE user_id=? AND substr(created_at,1,10)=?').get(req.user.id, today).c;
  if (n >= 10) return bad(res, 'You have sent many reports today — the team will review them!');
  db.prepare('INSERT INTO ai_reports (user_id,question,answer) VALUES (?,?,?)').run(req.user.id, q, a);
  res.json({ ok: true });
}));

// ---------------- 🗂️ media manager ----------------
app.get('/api/admin/media', requireAdmin, ah((req, res) => {
  const out = [];
  const base = path.resolve(UPLOAD_DIR);
  const walk = (dir) => {
    let ents = [];
    try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
    ents.forEach((en) => {
      const fp = path.join(dir, en.name);
      if (en.isDirectory()) return walk(fp);
      try { const st2 = fs.statSync(fp); out.push({ f: path.relative(base, fp).split(path.sep).join('/'), size: st2.size, mtime: Math.floor(st2.mtimeMs / 1000) }); } catch (_) {}
    });
  };
  walk(base);
  out.sort((x, y) => y.mtime - x.mtime);
  res.json({ files: out.slice(0, 500), total: out.length });
}));
app.delete('/api/admin/media', requireAdmin, ah((req, res) => {
  const rel = str((req.body || {}).f, 300);
  const base = path.resolve(UPLOAD_DIR);
  const fp = path.resolve(base, rel);
  if (!rel || !fp.startsWith(base + path.sep) || !fs.existsSync(fp) || !fs.statSync(fp).isFile()) return bad(res, 'File not found', 404);
  try { fs.unlinkSync(fp); } catch (_) { return bad(res, 'Could not delete that file'); }
  logAdmin(req, 'media_delete', rel);
  res.json({ ok: true });
}));

// ---------------- 🏆 weekly challenge ----------------
const CH_SUBJECTS = ['mixed', 'chem', 'phys', 'bio'];
const CH_MODES = { m1: [10, 15], m2: [25, 35], m3: [50, 60] };
const chalBoard = (cid) => db.prepare(`SELECT a.id, a.score, a.qcount, a.seconds, a.prize_status, u.name, u.school
    FROM challenge_attempts a JOIN users u ON u.id=a.user_id
    WHERE a.challenge_id=? ORDER BY a.score DESC, a.seconds ASC, a.id ASC LIMIT 50`).all(cid)
  .map((r) => ({ aid: r.id, name: (r.name || '').split(' ')[0], school: r.school || '', score: r.score, qcount: r.qcount, seconds: r.seconds, prize_status: r.prize_status }));
const chalView = (ch, uid, today) => {
  const state = ch.active && ch.start <= today && today <= ch.end ? 'now' : (ch.active && today < ch.start ? 'upcoming' : 'past');
  const [qn, mins] = CH_MODES[ch.mode] || [10, 15];
  const d = { id: ch.id, title: ch.title, subject: ch.subject, mode: ch.mode, start: ch.start, end: ch.end,
    prize1: ch.prize1, prize2: ch.prize2, prize3: ch.prize3, state,
    players: db.prepare('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=?').get(ch.id).c, questions: qn, minutes: mins };
  if (uid) {
    const mine = db.prepare('SELECT score,qcount,seconds FROM challenge_attempts WHERE challenge_id=? AND user_id=?').get(ch.id, uid);
    if (mine) {
      d.mine = { score: mine.score, qcount: mine.qcount, seconds: mine.seconds };
      d.rank = db.prepare(`SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=? AND
        (score>?) OR (score=? AND seconds<?) OR (score=? AND seconds=? AND user_id<?)`).get(ch.id, mine.score, mine.score, mine.seconds, mine.score, mine.seconds, uid).c + 1;
    }
  }
  return d;
};

app.get('/api/challenge', ah((req, res) => {
  const uid = req.user ? req.user.id : null;
  const today = new Date().toISOString().slice(0, 10);
  const nowL = [], upL = [], pastL = [];
  db.prepare('SELECT * FROM challenges ORDER BY start DESC, id DESC LIMIT 20').all().forEach((ch) => {
    const v = chalView(ch, uid, today);
    (v.state === 'now' ? nowL : v.state === 'upcoming' ? upL : pastL).push(v);
  });
  pastL.splice(5);
  pastL.forEach((v) => { v.board = chalBoard(v.id); });
  res.json({ today, now: nowL, upcoming: upL, past: pastL });
}));

app.get('/api/challenge/:id/board', requireAuth, ah((req, res) => {
  const ch = db.prepare('SELECT * FROM challenges WHERE id=?').get(req.params.id);
  if (!ch) return bad(res, 'Not found', 404);
  const today = new Date().toISOString().slice(0, 10);
  if (ch.active && today <= ch.end && req.user.role !== 'admin') return bad(res, 'The leaderboard unlocks when this challenge ends', 403);
  res.json({ board: chalBoard(ch.id) });
}));

app.post('/api/challenge/:id/attempt', requireAuth, ah((req, res) => {
  const ch = db.prepare('SELECT * FROM challenges WHERE id=?').get(req.params.id);
  if (!ch) return bad(res, 'Challenge not found', 404);
  const today = new Date().toISOString().slice(0, 10);
  if (!(ch.active && ch.start <= today && today <= ch.end)) return bad(res, 'This challenge is not open right now', 403);
  const b = req.body || {};
  const [nQ] = CH_MODES[ch.mode] || [10, 15];
  let score = parseInt(b.score, 10); if (isNaN(score) || score < 0) score = 0; if (score > nQ) score = nQ;
  let secs = parseInt(b.seconds || 0, 10); if (isNaN(secs) || secs < 0) secs = 0; if (secs > 14400) secs = 14400;
  try { db.prepare('INSERT INTO challenge_attempts (challenge_id,user_id,score,qcount,seconds) VALUES (?,?,?,?,?)').run(ch.id, req.user.id, score, nQ, secs); }
  catch (e) { return bad(res, 'You already sat this challenge — one attempt each!', 409); }
  const rank = db.prepare('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=? AND (score>? OR (score=? AND seconds<?))').get(ch.id, score, score, secs).c + 1;
  res.json({ ok: true, rank });
}));

app.get('/api/admin/challenges', requireAdmin, ah((req, res) => {
  const out = db.prepare('SELECT * FROM challenges ORDER BY id DESC LIMIT 50').all().map((ch) => {
    const d = Object.assign({}, ch);
    d.players = db.prepare('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=?').get(ch.id).c;
    d.board = chalBoard(ch.id);
    return d;
  });
  res.json({ challenges: out });
}));
app.post('/api/admin/challenges', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const title = str(b.title, 120);
  if (title.length < 3) return bad(res, 'Please give the challenge a title');
  const subj = CH_SUBJECTS.includes(b.subject) ? b.subject : 'mixed';
  const mode = CH_MODES[b.mode] ? b.mode : 'm1';
  const start = str(b.start, 12), end = str(b.end, 12);
  if (!(/^\d{4}-\d{2}-\d{2}$/.test(start) && /^\d{4}-\d{2}-\d{2}$/.test(end))) return bad(res, 'Pick start and end dates');
  if (end < start) return bad(res, 'End date must be after the start date');
  db.prepare('INSERT INTO challenges (title,subject,mode,start,end,prize1,prize2,prize3) VALUES (?,?,?,?,?,?,?,?)')
    .run(title, subj, mode, start, end, str(b.prize1, 120), str(b.prize2, 120), str(b.prize3, 120));
  logAdmin(req, 'challenge_create', title);
  res.json({ ok: true });
}));
app.put('/api/admin/challenges/:id', requireAdmin, ah((req, res) => {
  const ch = db.prepare('SELECT * FROM challenges WHERE id=?').get(req.params.id);
  if (!ch) return bad(res, 'Not found', 404);
  const b = req.body || {};
  if ('prize_status' in b) {
    const aid = parseInt(b.attempt_id || 0, 10);
    const stt = str(b.prize_status, 12);
    if (!['', 'pending', 'verified', 'sent', 'delivered'].includes(stt)) return bad(res, 'Bad status');
    db.prepare('UPDATE challenge_attempts SET prize_status=? WHERE id=? AND challenge_id=?').run(stt, aid, ch.id);
    logAdmin(req, 'prize_status', 'challenge #' + ch.id + ' attempt #' + aid + ' -> ' + (stt || 'none'));
    return res.json({ ok: true });
  }
  const title = str(b.title != null ? b.title : ch.title, 120) || ch.title;
  const subj = CH_SUBJECTS.includes(b.subject) ? b.subject : ch.subject;
  const mode = CH_MODES[b.mode] ? b.mode : ch.mode;
  let start = str(b.start != null ? b.start : ch.start, 12), end = str(b.end != null ? b.end : ch.end, 12);
  if (!(/^\d{4}-\d{2}-\d{2}$/.test(start) && /^\d{4}-\d{2}-\d{2}$/.test(end))) { start = ch.start; end = ch.end; }
  const active = (b.active != null ? b.active : ch.active) ? 1 : 0;
  db.prepare('UPDATE challenges SET title=?,subject=?,mode=?,start=?,end=?,prize1=?,prize2=?,prize3=?,active=? WHERE id=?')
    .run(title, subj, mode, start, end, str(b.prize1 != null ? b.prize1 : ch.prize1, 120), str(b.prize2 != null ? b.prize2 : ch.prize2, 120), str(b.prize3 != null ? b.prize3 : ch.prize3, 120), active, ch.id);
  logAdmin(req, 'challenge_update', title);
  res.json({ ok: true });
}));
app.delete('/api/admin/challenges/:id', requireAdmin, ah((req, res) => {
  const ch = db.prepare('SELECT * FROM challenges WHERE id=?').get(req.params.id);
  if (!ch) return bad(res, 'Not found', 404);
  db.prepare('DELETE FROM challenges WHERE id=?').run(ch.id);
  logAdmin(req, 'challenge_delete', ch.title);
  res.json({ ok: true });
}));

// ------------------------------------------------------------ STATIC
app.use(express.static(path.join(__dirname, 'public'), { maxAge: '1h', index: 'index.html' }));

// ------------------------------------------------------------ SMART v2
const sv2 = (v, mx = 500) => String(v == null ? '' : v).slice(0, mx);
const SIM_TYPES = ['atomic', 'ionic', 'polarity', 'vsepr', 'states', 'gaslaws',
  'molarity', 'dilution', 'stoich', 'energy', 'ph', 'titration',
  'motion', 'projectile', 'newtons', 'workenergy', 'collide', 'circular', 'shm', 'waves',
  'sound', 'optics', 'refraction', 'efield', 'circuits', 'ohmslaw', 'emi', 'magfield',
  'cell', 'dna', 'heart', 'photosyn', 'transpire', 'micro',
  'react', 'organic', 'galvanic', 'ptable',
  'circbuild', 'lensmirror', 'mgraphs',
  'neuron', 'bloodflow', 'breath', 'mitosis', 'disease',
  'gplot', 'gtrans', 'deriv', 'integr', 'vector', 'trig', 'prob', 'stats',
  'binary', 'logic', 'truthtab', 'cpu', 'network', 'ipaddr', 'sortvis', 'webplay',
  // Biology pack 3 / Chemistry pack 3 / Physics pack 3 / Maths pack 2 / ICT pack 2 (v r)
  'meiosis', 'natsel', 'popgrow', 'enzyme', 'respire', 'foodweb',
  'equil', 'vlab', 'chemlab', 'flametest', 'phtitration',
  'freefall', 'friction', 'reflect', 'rescolor', 'rc', 'transformer', 'econserv', 'screwgauge', 'potentiometer',
  'verniercaliper', 'metrebridge',
  // Premium Physics FX pack — PhET-style practical sims
  'pendulum', 'springshm', 'restube', 'gaspiston',
  // Premium Physics FX pack wave 2
  'parallelogram', 'sonometer', 'lensuv', 'youngsmodulus',
  // Premium Physics FX pack wave 3 — Waves & Fluids FX
  'rippletank', 'melde', 'statwaves', 'beats',
  'quilltube', 'hare', 'utubeshm', 'archimedes',
  'matrix', 'complexnum', 'cogo', 'seqser', 'projmath',
  'sqlplay', 'flowchart', 'boolalg', 'memunits', 'progviz'];
const SIM_SUBJECTS = {};
for (const ty of ['atomic', 'ionic', 'polarity', 'vsepr', 'states', 'gaslaws', 'molarity', 'dilution',
  'stoich', 'energy', 'ph', 'titration', 'react', 'organic', 'galvanic', 'ptable',
  'equil', 'vlab', 'chemlab', 'flametest', 'phtitration']) SIM_SUBJECTS[ty] = 'chem';
for (const ty of ['motion', 'projectile', 'newtons', 'workenergy', 'collide', 'circular', 'shm', 'waves',
  'sound', 'optics', 'refraction', 'efield', 'circuits', 'ohmslaw', 'emi', 'magfield',
  'circbuild', 'lensmirror', 'mgraphs',
  'freefall', 'friction', 'reflect', 'rescolor', 'rc', 'transformer', 'econserv', 'screwgauge', 'potentiometer', 'verniercaliper', 'metrebridge',
  'pendulum', 'springshm', 'restube', 'gaspiston',
  'parallelogram', 'sonometer', 'lensuv', 'youngsmodulus',
  'rippletank', 'melde', 'statwaves', 'beats', 'quilltube', 'hare', 'utubeshm', 'archimedes']) SIM_SUBJECTS[ty] = 'phys';
for (const ty of ['cell', 'dna', 'heart', 'photosyn', 'transpire', 'micro', 'neuron', 'bloodflow', 'breath', 'mitosis', 'disease',
  'meiosis', 'natsel', 'popgrow', 'enzyme', 'respire', 'foodweb']) SIM_SUBJECTS[ty] = 'bio';
for (const ty of ['gplot', 'gtrans', 'deriv', 'integr', 'vector', 'trig', 'prob', 'stats' ,  'matrix', 'complexnum', 'cogo', 'seqser', 'projmath']) SIM_SUBJECTS[ty] = 'maths';
for (const ty of ['binary', 'logic', 'truthtab', 'cpu', 'network', 'ipaddr', 'sortvis', 'webplay',
  'sqlplay', 'flowchart', 'boolalg', 'memunits', 'progviz']) SIM_SUBJECTS[ty] = 'ict';
const SIM_ORD_HARD = new Set(['chemlab', 'titration', 'galvanic', 'emi', 'magfield', 'transpire', 'disease', 'deriv', 'integr', 'truthtab', 'cpu',
  'meiosis', 'natsel', 'equil', 'rc', 'transformer', 'matrix', 'complexnum', 'projmath', 'sqlplay', 'progviz']);
for (const c of [['memory', 'Memory Match', 'Flip cards and match A/L term pairs.'], ['scramble', 'Word Scramble', 'Unscramble the A/L word.'], ['quiz', 'Rapid GK Quiz', '5 quick general-knowledge questions.']]) {
  try { db.prepare('INSERT OR IGNORE INTO careers (gkey,name,descr) VALUES (?,?,?)').run(...c); } catch (_) { }
}
SIM_TYPES.forEach((ty, i) => {  // seed the DB-driven sim catalogue once; admin edits it afterwards
  try {
    db.prepare('INSERT OR IGNORE INTO sim_catalog (sim_type,subject,difficulty,ord) VALUES (?,?,?,?)')
      .run(ty, SIM_SUBJECTS[ty] || '', SIM_ORD_HARD.has(ty) ? 'hard' : (i % 3 === 0 ? 'easy' : 'medium'), i);
  } catch (_) { /* table created in db.js */ }
});
const SIM_AUTO = {
  1: { 1: 'atomic', 2: 'ionic', 3: 'stoich', 4: 'gaslaws', 5: 'energy', 8: 'energy', 9: 'ph' },
  3: { 1: 'cell', 2: 'heart' },
  4: { 2: 'motion', 3: 'waves', 4: 'gaslaws', 6: 'efield', 7: 'magfield', 8: 'circuits' },
};
// Physics lesson-title rules per unit_ord; first match wins; null = no sim for that topic.
// Patterns cover both English and Sinhala keywords from the actual catalogue.
const PHYS_RULES = {
  2: [['graph', 'mgraphs'], ['ප්‍රස්තාර', 'mgraphs'], ['suvat', 'mgraphs'],
  ['momentum', 'collide'], ['collision', 'collide'], ['impulse', 'collide'], ['ගැටීම', 'collide'], ['ආවේග', 'collide'],
  ['free fall', 'freefall'], ['freefall', 'freefall'], ['නිදහස් වැටීම', 'freefall'], ['falling', 'freefall'],
  ['projectile', 'projectile'], ['ප්‍රක්ෂිප්ත', 'projectile'],
  ['නිව්ටන්', 'newtons'], ['newton', 'newtons'], ['friction', 'newtons'], ['ඝර්ෂණ', 'newtons'], ['inclined', 'newtons'],
  ['circular', 'circular'], ['centripetal', 'circular'], ['වෘත්ත', 'circular'],
  ['කාර්යය', 'workenergy'], ['ශක්තිය', 'workenergy'], ['ක්ෂමතා', 'workenergy'],
  ['work', 'workenergy'], ['energy', 'workenergy'], ['power', 'workenergy'], ['kinetic', 'workenergy'], ['potential energy', 'workenergy'],
  ['moment', null], ['torque', null], ['couple', null], ['equilibrium', null], ['centre of gravity', null],
  ['බල සමතුලිත', null], ['භ්‍රමණ', null], ['තරල', null], ['ගුරුත්ව කේන්ද්‍රය', null], ['ද්‍රවස්ථිත', null], ['දැඟිලූ', null]],
  3: [['sound', 'sound'], ['ultra', 'sound'], ['echo', 'sound'], ['ශබ්ද', 'sound'],
  ['total internal', 'refraction'], ['අභ්‍යන්තර', 'refraction'], ['critical angle', 'refraction'],
  ['prism', 'refraction'], ['ප්‍රිස්ම', 'refraction'], ['වර්ණාවලි', 'refraction'],
  ['refraction', 'refraction'], ['refractive', 'refraction'], ['වර්තන', 'refraction'],
  ['lens', 'lensmirror'], ['කාච', 'lensmirror'], ['mirror', 'lensmirror'], ['කණ්ණාඩි', 'lensmirror'],
  ['eye', 'optics'], ['ඇස', 'optics'], ['optical', 'optics'], ['ප්‍රකාශ උපකරණ', 'optics'],
  ['light', 'optics'], ['ආලෝක', 'optics'],
  ['doppler', 'waves'], ['ඩොප්ලර්', 'waves'], ['ripple', 'waves'],
  ['interference', 'waves'], ['diffraction', 'waves'], ['stationary', 'waves'], ['superposition', 'waves'],
  ['harmonic', 'shm'], ['s.h.m', 'shm'], ['pendulum', 'shm'], ['සරල අවලම්බ', 'shm'], ['සමාවර්ත', 'shm'],
  ['wave', 'waves'], ['තරංග', 'waves'],
  ['oscillation', 'shm'], ['දෝලන', 'shm']],
  4: [['gas', 'gaslaws'], ['ideal', 'gaslaws'], ['boyle', 'gaslaws'], ['charles', 'gaslaws'], ['වායු', 'gaslaws']],
  6: [['field', 'efield'], ['ක්ෂේත්‍ර', 'efield'], ['charge', 'efield'], ['ආරෝපණ', 'efield'],
  ['coulomb', 'efield'], ['කුලෝම්', 'efield'], ['potential', 'efield'],
  ['capacit', 'rc'], ['discharging', 'rc'], ['time constant', 'rc']],
  7: [['induction', 'emi'], ['lenz', 'emi'], ['faraday', 'emi'], ['flux', 'emi'], ['alternating', 'emi'],
  ['transformer', 'transformer'], ['ට්‍රාන්ස්ෆෝමර්', 'transformer'],
  ['ප්‍රේරණ', 'emi'], ['ෆැරඩේ', 'emi'], ['torque', null], ['දෝලක', null]],
  8: [['ohm', 'ohmslaw'], ['resistance', 'ohmslaw'], ['resistivity', 'ohmslaw'], ['ප්‍රතිරෝද', 'ohmslaw'],
  ['i-v', 'ohmslaw'], ['iv characteristic', 'ohmslaw'],
  ['kirchhoff', 'circuits'], ['කර්චොෆ්', 'circuits'], ['potential divider', 'circuits'],
  ['පරිපථ', 'circbuild'], ['circuit', 'circbuild'], ['parallel', 'circuits'],
  ['cell', 'circuits'], ['කෝෂ', 'circuits'], ['internal resistance', 'circuits'], ['potentiometer', 'circuits']],
};
function resolveSim(l) {
  let stype = (l.simulation_type || '').trim();
  const enb = l.simulation_enabled;
  let auto = '';
  const subjMap = SIM_AUTO[l.subject_id] || {};
  if (l.subject_id === 4) {
    const rules = PHYS_RULES[l.unit_ord] || [];
    const title = (l.title || '').toLowerCase();
    let hit = '_nohit_';
    for (const [pat, sim] of rules) {
      if (title.includes(pat)) { hit = sim; break; }
    }
    if (hit === '_nohit_') auto = subjMap[l.unit_ord] || '';
    else if (hit) auto = hit;
    else auto = '';
  } else {
    auto = subjMap[l.unit_ord] || '';
  }
  if (!SIM_TYPES.includes(stype)) stype = '';
  if (enb === 0) return { type: '', auto, enabled: 0 };
  if (enb === 1 && stype) return { type: stype, auto, enabled: 1 };
  if (stype) return { type: stype, auto, enabled: 1 };
  if (auto) return { type: auto, auto, enabled: -1 };
  return { type: '', auto: '', enabled: -1 };
}

app.put('/api/admin/lessons/:id/sim', requireAdmin, ah((req, res) => {
  const l = db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id);
  if (!l) return bad(res, 'Lesson not found', 404);
  const b = req.body || {};
  let enb = b.enabled;
  if (enb === -1 || enb === '-1' || enb === 'auto' || enb == null) enb = null;
  else if (String(enb) === '1' || enb === 'on') enb = 1;
  else enb = 0;
  let stype = sv2(b.simulation_type, 30).trim();
  if (!SIM_TYPES.includes(stype)) stype = '';
  let cfg = (b.config && typeof b.config === 'object') ? b.config : {};
  const keep = {};
  for (const k of ['instructions_en', 'instructions_si', 'instructions_ta', 'concept']) if (cfg[k]) keep[k] = sv2(cfg[k], 4000);
  db.prepare('UPDATE lessons SET simulation_type=?, simulation_enabled=?, sim_config=? WHERE id=?')
    .run(stype, enb, JSON.stringify(keep), l.id);
  res.json({ ok: true });
}));

app.post('/api/lessons/:id/sim-event', requireAuth, ah((req, res) => {
  if (!db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id)) return bad(res, 'Lesson not found', 404);
  const b = req.body || {};
  const ev = sv2(b.event, 20);
  const uid = req.user.id;
  if (!['start', 'complete', 'score'].includes(ev)) return bad(res, 'Bad event');
  const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
  const st = sv2(b.sim_type, 30);
  db.prepare('INSERT INTO sim_progress (user_id,lesson_id,sim_type,updated_at) VALUES (?,?,?,?) ON CONFLICT(user_id,lesson_id) DO NOTHING').run(uid, req.params.id, st, now);
  if (ev === 'start') db.prepare('UPDATE sim_progress SET started=1, attempts=attempts+1, sim_type=?, updated_at=? WHERE user_id=? AND lesson_id=?').run(st, now, uid, req.params.id);
  else if (ev === 'complete') db.prepare('UPDATE sim_progress SET completed=1, sim_type=?, updated_at=? WHERE user_id=? AND lesson_id=?').run(st, now, uid, req.params.id);
  else {
    let sc = Math.max(0, parseInt(b.score, 10) || 0), tt = Math.max(1, parseInt(b.total, 10) || 1);
    sc = Math.min(sc, tt);
    const pct = Math.round((sc * 100) / tt);
    db.prepare('UPDATE sim_progress SET last_score=?, best_score=MAX(COALESCE(best_score,0),?), completed=1, updated_at=? WHERE user_id=? AND lesson_id=?').run(pct, pct, now, uid, req.params.id);
    db.prepare('INSERT INTO sim_events (user_id,sim_type,event,score,total,pct) VALUES (?,?,?,?,?,?)').run(uid, st, 'score', sc, tt, pct);
  }
  res.json(db.prepare('SELECT started,completed,attempts,best_score,last_score FROM sim_progress WHERE user_id=? AND lesson_id=?').get(uid, req.params.id));
}));

const DEFAULT_SETTINGS = { exam_date: '2027-08-09', weekly_target: '10', daily_goal: '2' };
function getSettings(uid) {
  const out = { ...DEFAULT_SETTINGS };
  db.prepare('SELECT key,value FROM user_settings WHERE user_id=?').all(uid).forEach((r) => { out[r.key] = r.value; });
  return out;
}
const todayStr = () => new Date().toISOString().slice(0, 10);

app.get('/api/search', ah((req, res) => {
  const q = sv2(req.query.q || '', 80).trim();
  if (q.length < 2) return res.json({ q, lessons: [], units: [], teachers: [], resources: [], subjects: [] });
  const like = '%' + q + '%';
  const lessons = db.prepare(`SELECT l.id, l.title, l.youtube_id, u.id AS unit_id, u.name AS unit_name,
      s.id AS subject_id, s.name AS subject_name, s.color1, s.color2, t.name AS teacher_name
      FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
      LEFT JOIN teachers t ON t.id=l.teacher_id
      WHERE l.title LIKE ? OR l.description LIKE ? ORDER BY l.id DESC LIMIT 12`).all(like, like);
  const units = db.prepare(`SELECT u.id, u.name, u.ord, s.id AS subject_id, s.name AS subject_name, s.color1, s.color2
      FROM units u JOIN subjects s ON s.id=u.subject_id WHERE u.name LIKE ? ORDER BY s.id, u.ord LIMIT 8`).all(like);
  const teachers = db.prepare(`SELECT id, name, bio, photo, subjects FROM teachers
      WHERE name LIKE ? OR bio LIKE ? OR subjects LIKE ? LIMIT 8`).all(like, like, like);
  const resources = db.prepare(`SELECT r.id, r.title, r.category, r.external_url, s2.name AS subject_name
      FROM resources r LEFT JOIN subjects s2 ON s2.id=r.subject_id
      WHERE r.status='approved' AND (r.title LIKE ? OR r.description LIKE ?) ORDER BY r.id DESC LIMIT 8`).all(like, like);
  const subjects = db.prepare(`SELECT id, name, name_si, name_ta, color1, color2, icon FROM subjects
      WHERE name LIKE ? OR name_si LIKE ? OR name_ta LIKE ? LIMIT 5`).all(like, like, like);
  res.json({ q, lessons, units, teachers, resources, subjects });
}));

app.get('/api/units/:id/practice', ah((req, res) => {
  const u = db.prepare('SELECT u.*, s.name AS subject_name, s.color1, s.color2 FROM units u JOIN subjects s ON s.id=u.subject_id WHERE u.id=?').get(req.params.id);
  if (!u) return bad(res, 'Unit not found', 404);
  const qs = db.prepare('SELECT * FROM practice_questions WHERE unit_id=? ORDER BY year DESC, ord, id').all(u.id);
  const marks = {};
  if (req.user) db.prepare('SELECT question_id, ok FROM practice_marks WHERE user_id=?').all(req.user.id).forEach((m) => { marks[m.question_id] = m.ok; });
  qs.forEach((x) => { x.my = marks[x.id] != null ? marks[x.id] : null; });
  res.json({ unit: u, questions: qs });
}));

app.post('/api/practice/:id/mark', requireAuth, ah((req, res) => {
  const ok = req.body && req.body.ok ? 1 : 0;
  if (!db.prepare('SELECT id FROM practice_questions WHERE id=?').get(req.params.id)) return bad(res, 'Question not found', 404);
  db.prepare(`INSERT INTO practice_marks (user_id,question_id,ok) VALUES (?,?,?)
    ON CONFLICT(user_id,question_id) DO UPDATE SET ok=excluded.ok`).run(req.user.id, req.params.id, ok);
  res.json({ ok: true });
}));

app.post('/api/admin/practice', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  if (!db.prepare('SELECT id FROM units WHERE id=?').get(b.unit_id)) return bad(res, 'Unit not found', 404);
  let qt = sv2(b.qtype, 20); if (!['structured', 'pastpaper'].includes(qt)) qt = 'structured';
  const q = sv2(b.question, 5000); if (!q) return bad(res, 'Question text required');
  const yr = parseInt(b.year, 10) || null, mk = parseInt(b.marks, 10) || 0;
  const mx = db.prepare('SELECT COALESCE(MAX(ord),0) m FROM practice_questions WHERE unit_id=?').get(b.unit_id).m;
  const r = db.prepare('INSERT INTO practice_questions (unit_id,qtype,year,title,question,answer,marks,ord) VALUES (?,?,?,?,?,?,?,?)')
    .run(b.unit_id, qt, yr, sv2(b.title, 200), q, sv2(b.answer, 8000), mk, mx + 1);
  res.json({ ok: true, id: r.lastInsertRowid });
}));

app.delete('/api/admin/practice/:id', requireAdmin, ah((req, res) => {
  db.prepare('DELETE FROM practice_questions WHERE id=?').run(req.params.id);
  res.json({ ok: true });
}));

app.post('/api/study/ping', requireAuth, ah((req, res) => {
  let sec = Math.max(0, Math.min(parseInt((req.body || {}).seconds, 10) || 0, 120));
  if (!sec) return res.json({ ok: true });
  db.prepare(`INSERT INTO study_events (user_id,day,seconds) VALUES (?,?,?)
    ON CONFLICT(user_id,day) DO UPDATE SET seconds=seconds+excluded.seconds`).run(req.user.id, todayStr(), sec);
  res.json({ ok: true });
}));

app.post('/api/lessons/:id/mcq-result', requireAuth, ah((req, res) => {
  if (!db.prepare('SELECT id FROM lessons WHERE id=?').get(req.params.id)) return bad(res, 'Lesson not found', 404);
  let score = Math.max(0, parseInt((req.body || {}).score, 10) || 0);
  let total = Math.max(1, parseInt((req.body || {}).total, 10) || 1);
  score = Math.min(score, total);
  db.prepare('INSERT INTO mcq_attempts (user_id,lesson_id,score,total) VALUES (?,?,?,?)').run(req.user.id, req.params.id, score, total);
  const best = db.prepare('SELECT MAX(score*1.0/total) b FROM mcq_attempts WHERE user_id=? AND lesson_id=?').get(req.user.id, req.params.id).b || 0;
  res.json({ ok: true, best_pct: Math.round(best * 100) });
}));

app.get('/api/settings', requireAuth, ah((req, res) => res.json({ settings: getSettings(req.user.id) })));

app.put('/api/settings', requireAuth, ah((req, res) => {
  const b = req.body || {};
  for (const k of Object.keys(DEFAULT_SETTINGS)) {
    if (!(k in b)) continue;
    let v = sv2(b[k], 30).trim();
    if (k === 'exam_date' && !/^\d{4}-\d{2}-\d{2}$/.test(v)) continue;
    if (k === 'weekly_target' || k === 'daily_goal') { v = String(Math.max(1, Math.min(parseInt(v, 10) || 0, 100))); }
    db.prepare(`INSERT INTO user_settings (user_id,key,value) VALUES (?,?,?)
      ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value`).run(req.user.id, k, v);
  }
  res.json({ settings: getSettings(req.user.id) });
}));

app.get('/api/planner', requireAuth, ah((req, res) => {
  const plans = db.prepare(`SELECT p.id, p.lesson_id, p.plan_date, p.done, l.title, l.youtube_id,
      u.name AS unit_name, s.name AS subject_name, s.id AS subject_id, s.color1, s.color2
      FROM study_plans p JOIN lessons l ON l.id=p.lesson_id
      JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
      WHERE p.user_id=? ORDER BY p.plan_date, p.done, p.id`).all(req.user.id);
  res.json({ plans, settings: getSettings(req.user.id) });
}));

app.post('/api/planner', requireAuth, ah((req, res) => {
  const b = req.body || {};
  const pdate = sv2(b.plan_date, 12) || todayStr();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(pdate)) return bad(res, 'Bad date');
  if (!db.prepare('SELECT id FROM lessons WHERE id=?').get(b.lesson_id)) return bad(res, 'Lesson not found', 404);
  try { db.prepare('INSERT INTO study_plans (user_id,lesson_id,plan_date) VALUES (?,?,?)').run(req.user.id, b.lesson_id, pdate); }
  catch (e) { return bad(res, 'Already planned for that day'); }
  res.json({ ok: true });
}));

app.post('/api/planner/:id/toggle', requireAuth, ah((req, res) => {
  const p = db.prepare('SELECT * FROM study_plans WHERE id=? AND user_id=?').get(req.params.id, req.user.id);
  if (!p) return bad(res, 'Not found', 404);
  db.prepare('UPDATE study_plans SET done=? WHERE id=?').run(p.done ? 0 : 1, p.id);
  res.json({ ok: true, done: p.done ? 0 : 1 });
}));

app.delete('/api/planner/:id', requireAuth, ah((req, res) => {
  db.prepare('DELETE FROM study_plans WHERE id=? AND user_id=?').run(req.params.id, req.user.id);
  res.json({ ok: true });
}));

app.get('/api/progress2', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  const units = db.prepare(`SELECT * FROM (SELECT u.id, u.name, u.ord, s.id AS subject_id, s.name AS subject_name, s.name_si, s.name_ta, s.color1, s.color2,
      (SELECT COUNT(*) FROM lessons l WHERE l.unit_id=u.id) AS total,
      (SELECT COUNT(*) FROM lessons l JOIN progress p ON p.lesson_id=l.id AND p.user_id=? AND p.completed=1 WHERE l.unit_id=u.id) AS done
      FROM units u JOIN subjects s ON s.id=u.subject_id) WHERE total>0 ORDER BY subject_id, ord`).all(uid);
  const days = []; for (let i = 6; i >= 0; i--) days.push(new Date(Date.now() - i * 864e5).toISOString().slice(0, 10));
  const emap = {};
  db.prepare('SELECT day, seconds FROM study_events WHERE user_id=? AND day>=?').all(uid, days[0]).forEach((r) => { emap[r.day] = r.seconds; });
  const week = days.map((d) => ({ day: d, seconds: emap[d] || 0 }));
  const weekTotal = week.reduce((a, w) => a + w.seconds, 0);
  const dayset = new Set();
  db.prepare('SELECT day FROM study_events WHERE user_id=? AND seconds>0').all(uid).forEach((r) => dayset.add(r.day));
  db.prepare('SELECT completed_at d1, watched_at d2 FROM progress WHERE user_id=?').all(uid).forEach((r) => {
    if (r.d1) dayset.add(r.d1.slice(0, 10)); if (r.d2) dayset.add(r.d2.slice(0, 10));
  });
  db.prepare('SELECT substr(created_at,1,10) d FROM exam_attempts WHERE user_id=?').all(uid).forEach((r) => { if (r.d) dayset.add(r.d); });
  let streak = 0, cur = todayStr();
  if (!dayset.has(cur)) cur = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
  while (dayset.has(cur)) { streak++; cur = new Date(new Date(cur + 'T00:00:00Z').getTime() - 864e5).toISOString().slice(0, 10); }
  const mcqAvg = db.prepare('SELECT AVG(b) a FROM (SELECT MAX(score*1.0/total) b FROM mcq_attempts WHERE user_id=? GROUP BY lesson_id)').get(uid).a;
  const mcqCount = db.prepare('SELECT COUNT(DISTINCT lesson_id) c FROM mcq_attempts WHERE user_id=?').get(uid).c;
  const prac = db.prepare('SELECT COUNT(*) c, COALESCE(SUM(ok),0) ok FROM practice_marks WHERE user_id=?').get(uid);
  const exs = db.prepare('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?').get(uid);
  const st = getSettings(uid);
  let daysLeft = null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(st.exam_date)) daysLeft = Math.floor((new Date(st.exam_date + 'T00:00:00Z').getTime() - Date.now()) / 864e5) + 1;
  const planToday = db.prepare('SELECT id, done FROM study_plans WHERE user_id=? AND plan_date=?').all(uid, todayStr());
  const simSubj = {};
  for (const [sid0] of Object.entries(SIM_AUTO)) {
    const sid = +sid0;
    const lrws = db.prepare(`SELECT l.title, l.simulation_type, l.simulation_enabled, u.subject_id, u.ord AS unit_ord
      FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?`).all(sid);
    const tot = lrws.filter((r) => resolveSim(r).type).length;
    const sqp = db.prepare(`SELECT COUNT(*) c, COALESCE(SUM(sp.completed),0) comp, AVG(sp.best_score) avg_best, COALESCE(SUM(sp.attempts),0) att
      FROM sim_progress sp JOIN lessons l ON l.id=sp.lesson_id JOIN units u ON u.id=l.unit_id
      WHERE sp.user_id=? AND u.subject_id=?`).get(uid, sid);
    if (tot) simSubj[sid] = { total: tot, tried: sqp.c || 0, completed: sqp.comp || 0, avg_score: Math.round(sqp.avg_best || 0), attempts: sqp.att || 0 };
  }
  const sp = db.prepare('SELECT COUNT(*) c, SUM(completed) comp, AVG(best_score) avg_best, SUM(attempts) att FROM sim_progress WHERE user_id=?').get(uid);
  const simTotal = Object.values(simSubj).reduce((a, v) => a + v.total, 0);
  const sims = { total: simTotal, tried: sp.c || 0, completed: sp.comp || 0, avg_score: Math.round(sp.avg_best || 0), attempts: sp.att || 0 };
  // XP (transparent points powering levels + leaderboard)
  const doneC = db.prepare('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1').get(uid).c;
  const watchOnly = db.prepare('SELECT COUNT(*) c FROM progress WHERE user_id=? AND watched=1 AND completed=0').get(uid).c;
  const minsAll = Math.floor((db.prepare('SELECT COALESCE(SUM(seconds),0) m FROM study_events WHERE user_id=?').get(uid).m || 0) / 60);
  const chalWins = db.prepare('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?').get(uid).c;
  const xpBy = { lessons: doneC * 20, videos: watchOnly * 5, mcq: mcqCount * 10 + Math.min(100, Math.round((mcqAvg || 0) * 100)), sims: (sp.c || 0) * 4 + (sp.comp || 0) * 10, challenges: chalWins * 15, careers: Math.min(300, db.prepare('SELECT COALESCE(SUM(xp),0) x FROM career_attempts WHERE user_id=?').get(uid).x || 0), exams: Math.min(exs.c, 20) * 10 + Math.round(exs.a / 2), study: minsAll, streak: streak * 10 };
  const xpTotal = Object.values(xpBy).reduce((a, b) => a + b, 0);
  res.json({ units, week, week_seconds: weekTotal, today_seconds: emap[todayStr()] || 0, streak,
    mcq_avg: Math.round((mcqAvg || 0) * 100), mcq_lessons: mcqCount,
    practice_done: prac.c, practice_ok: prac.ok, settings: st, days_left: daysLeft, today: todayStr(), sims, sims_subj: simSubj,
    exams: { taken: exs.c, avg: Math.round(exs.a), best: Math.round(exs.b) },
    xp: { total: xpTotal, by: xpBy },
    plan_today_total: planToday.length, plan_today_done: planToday.filter((p) => p.done).length });
}));

// ---------------- weekly leaderboard (rolling 7 days, real data only) ----------------
app.get('/api/leaderboard', requireAuth, ah((req, res) => {
  const uid = req.user.id;
  if (!sw('leaderboard_on')) return res.json({ enabled: false, top: [], me: null, players: 0 });
  const since = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10);
  const lb = db.prepare(`SELECT u.id, u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
    (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done
    FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
    WHERE u.role != 'admin' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id`).all(since);
  const rankIdx = lb.findIndex((r) => r.id === uid);
  const me2 = lb[rankIdx];
  res.json({
    top: lb.slice(0, 10).map((r) => ({ name: r.name.split(' ')[0], school: r.school || '', minutes: Math.floor(r.sec / 60), lessons: r.done, me: r.id === uid })),
    me: { rank: rankIdx >= 0 ? rankIdx + 1 : null, minutes: me2 ? Math.floor(me2.sec / 60) : 0, lessons: me2 ? me2.done : 0 },
    players: lb.length,
  });
}));

// ---------------- SIM LAB UPGRADE (2026-08-11q): simulator events + catalog ----------------
app.post('/api/sim/event', requireAuth, ah((req, res) => {
  const ty = str(req.body && req.body.sim_type, 30);
  if (!SIM_TYPES.includes(ty)) return bad(res, 'Unknown simulator', 404);
  const catRow = db.prepare('SELECT premium FROM sim_catalog WHERE sim_type=?').get(ty);
  if (catRow && catRow.premium && !(isPrem(req.user) || req.user.role === 'admin')) return res.status(403).json({ error: 'Premium simulator', premium: true });
  const ev = str(req.body && req.body.event, 12);
  const uid = req.user.id;
  if (ev === 'start') {
    const day = todayStr();
    db.prepare(`INSERT INTO sim_launches (user_id,sim_type,day,n) VALUES (?,?,?,1)
      ON CONFLICT(user_id,sim_type,day) DO UPDATE SET n=n+1`).run(uid, ty, day);
    return res.json({ ok: true });
  }
  if (ev === 'challenge') {
    const goal = str(req.body && req.body.goal, 160);
    if (!goal) return bad(res, 'Missing goal');
    const r = db.prepare('INSERT OR IGNORE INTO sim_challenge_wins (user_id,sim_type,goal) VALUES (?,?,?)').run(uid, ty, goal);
    const first = r.changes > 0;
    const total = db.prepare('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?').get(uid).c;
    return res.json({ ok: true, first, wins: total, xp: first ? 15 : 2 });
  }
  if (ev === 'score') {
    let sc = Math.max(0, parseInt(req.body && req.body.score, 10) || 0), tt = Math.max(1, parseInt(req.body && req.body.total, 10) || 1);
    sc = Math.min(sc, tt);
    const pct = Math.round((sc * 100) / tt);
    db.prepare('INSERT INTO sim_events (user_id,sim_type,event,score,total,pct) VALUES (?,?,?,?,?,?)').run(uid, ty, 'score', sc, tt, pct);
    return res.json({ ok: true, pct });
  }
  return bad(res, 'Bad event');
}));

/* ---------------- 🏆 Weekly sim leaderboard (v2026.08.12s) ---------------- */
app.get('/api/sims/leaderboard', ah((req, res) => {
  if (!sw('leaderboard_on')) return res.json({ enabled: false, rows: [], me: null, week_start: '', week_end: '' });
  const now = Date.now();
  const d = new Date(now);
  const daysSinceMonday = (d.getUTCDay() + 6) % 7;
  const monday = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - daysSinceMonday));
  const wstart = monday.toISOString().slice(0, 10) + ' 00:00:00';
  const wend = new Date(monday.getTime() + 7 * 86400000).toISOString().replace('T', ' ').slice(0, 19);
  // anti-farm: best score per sim per day per user; sum those
  const board = db.prepare(`SELECT u.id, u.name, SUM(q.sc) pts, COUNT(DISTINCT q.sim_type) sims
    FROM (SELECT user_id, sim_type, date(created_at) d, MAX(score) sc FROM sim_events
          WHERE event='score' AND created_at>=? GROUP BY user_id, sim_type, date(created_at)) q
    JOIN users u ON u.id=q.user_id AND u.status!='suspended'
    GROUP BY q.user_id ORDER BY pts DESC, sims DESC, u.id ASC`).all(wstart);
  const uid = req.user ? req.user.id : 0;
  const rows = board.slice(0, 50).map((r, i) => ({ rank: i + 1, name: r.name, points: r.pts, sims: r.sims, me: r.id === uid }));
  let me = null;
  board.forEach((r, i) => { if (r.id === uid) me = { rank: i + 1, points: r.pts, sims: r.sims }; });
  res.json({ week_start: wstart.slice(0, 10), week_end: wend, rows, me });
}));

app.get('/api/sims', ah((req, res) => {
  const pid = parseInt(req.query.lesson_id || '0', 10), uid2 = parseInt(req.query.unit_id || '0', 10);
  let sql = 'SELECT sim_type,subject,title,descr,difficulty,xp_reward,badge,unit_id,lesson_id,ord,premium FROM sim_catalog WHERE enabled=1';
  const par = [];
  if (pid) { sql += ' AND lesson_id=?'; par.push(pid); }
  else if (uid2) { sql += ' AND unit_id=?'; par.push(uid2); }
  sql += ' ORDER BY ord, id';
  const sims = db.prepare(sql).all(...par);
  if (pid || uid2) return res.json({ sims });
  const counts = {};
  for (const r of sims) if (r.subject) counts[r.subject] = (counts[r.subject] || 0) + 1;
  res.json({ sims, counts });
}));

app.get('/api/admin/sims', requireAdmin, ah((req, res) => {
  const cat = db.prepare('SELECT * FROM sim_catalog ORDER BY ord, id').all();
  const per = {};
  for (const r of db.prepare('SELECT sim_type, COALESCE(SUM(n),0) n, COUNT(DISTINCT user_id) u FROM sim_launches GROUP BY sim_type').all()) {
    per[r.sim_type] = per[r.sim_type] || {}; per[r.sim_type].launches = r.n; per[r.sim_type].students = r.u;
  }
  for (const r of db.prepare('SELECT sim_type, COUNT(*) c FROM sim_challenge_wins GROUP BY sim_type').all()) {
    per[r.sim_type] = per[r.sim_type] || {}; per[r.sim_type].wins = r.c;
  }
  for (const r of db.prepare('SELECT sim_type, COALESCE(SUM(completed),0) comp, COALESCE(SUM(attempts),0) att, AVG(best_score) bs FROM sim_progress GROUP BY sim_type').all()) {
    per[r.sim_type] = per[r.sim_type] || {};
    Object.assign(per[r.sim_type], { completed: r.comp, attempts: r.att, avg_best: Math.round(r.bs || 0) });
  }
  for (const row of cat) {
    const p2 = per[row.sim_type] || {};
    row.launches = p2.launches || 0; row.students = p2.students || 0; row.wins = p2.wins || 0;
    row.completed = p2.completed || 0; row.attempts = p2.attempts || 0; row.avg_best = p2.avg_best || 0;
  }
  const oneN = (q, ...p2) => db.prepare(q).get(...p2);
  const d7 = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10);
  const d30 = new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10);
  const series = [];
  for (let i = 7; i >= 0; i--) {
    const dd = new Date(Date.now() - i * 864e5).toISOString().slice(0, 10);
    series.push({ label: dd.slice(5), n: oneN('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day=?', dd).s });
  }
  const cards = {
    launches: oneN('SELECT COALESCE(SUM(n),0) s FROM sim_launches').s,
    students: oneN('SELECT COUNT(DISTINCT user_id) c FROM sim_launches').c,
    wins: oneN('SELECT COUNT(*) c FROM sim_challenge_wins').c,
    completed: oneN('SELECT COALESCE(SUM(completed),0) s FROM sim_progress').s,
    week: oneN('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day>=?', d7).s,
    month: oneN('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day>=?', d30).s,
    today: oneN('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day=?', todayStr()).s,
  };
  res.json({ sims: cat, cards, series });
}));

app.put('/api/admin/sims/:id', requireAdmin, ah((req, res) => {
  const row = db.prepare('SELECT * FROM sim_catalog WHERE id=?').get(req.params.id);
  if (!row) return bad(res, 'Not found', 404);
  const b = req.body || {};
  let diff = str(b.difficulty !== undefined ? b.difficulty : row.difficulty, 8);
  if (!['easy', 'medium', 'hard'].includes(diff)) diff = row.difficulty;
  let xp = row.xp_reward;
  if (b.xp_reward !== undefined) { const v = parseInt(b.xp_reward, 10); if (!isNaN(v)) xp = Math.max(0, Math.min(v, 500)); }
  const nvl = (k, old) => (b[k] === undefined) ? old : (b[k] === null ? null : Math.max(0, parseInt(b[k], 10) || 0));
  db.prepare(`UPDATE sim_catalog SET title=?, descr=?, difficulty=?, objectives=?, formulas=?, tips=?,
    xp_reward=?, badge=?, unit_id=?, lesson_id=?, enabled=?, premium=? WHERE id=?`)
    .run(str(b.title !== undefined ? b.title : row.title, 160), str(b.descr !== undefined ? b.descr : row.descr, 500), diff,
      str(b.objectives !== undefined ? b.objectives : row.objectives, 800), str(b.formulas !== undefined ? b.formulas : row.formulas, 400),
      str(b.tips !== undefined ? b.tips : row.tips, 500), xp, str(b.badge !== undefined ? b.badge : row.badge, 60),
      nvl('unit_id', row.unit_id), nvl('lesson_id', row.lesson_id),
      (b.enabled !== undefined ? b.enabled : row.enabled) ? 1 : 0,
      (b.premium !== undefined ? (b.premium ? 1 : 0) : row.premium), req.params.id);
  logAdmin(req, 'sim_update', row.sim_type);
  res.json({ ok: true });
}));

// ---------------- CAREER GAMES (2026-08-11q) ----------------
app.get('/api/careers', requireAuth, ah((req, res) => {
  if (!sw('careers_enabled')) return bad(res, 'Career Games are turned off by admin right now.', 403);
  const uid = req.user.id;
  const games = db.prepare('SELECT * FROM careers WHERE active=1 ORDER BY id').all().map((r) => {
    const att = db.prepare('SELECT COUNT(*) c, COALESCE(MAX(score),0) best FROM career_attempts WHERE user_id=? AND gkey=?').get(uid, r.gkey);
    const won = db.prepare('SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=? AND won=1').get(uid, r.gkey).c > 0;
    return { gkey: r.gkey, name: r.name, descr: r.descr, reward: !!r.reward_code && !(won && r.reward_once),
      attempts_used: att.c, max_attempts: r.max_attempts, best: att.best, won };
  });
  res.json({ games });
}));

app.post('/api/careers/finish', requireAuth, ah((req, res) => {
  if (!sw('careers_enabled')) return bad(res, 'Career Games are turned off by admin right now.', 403);
  const b = req.body || {};
  const gk = str(b.gkey, 30);
  const gme = db.prepare('SELECT * FROM careers WHERE gkey=? AND active=1').get(gk);
  if (!gme) return bad(res, 'Game not found or disabled', 403);
  const uid = req.user.id;
  let score = parseInt(b.score || 0, 10); if (isNaN(score)) score = 0; score = Math.max(0, Math.min(100, score));
  const used = db.prepare('SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=?').get(uid, gk).c;
  if (gme.max_attempts && used >= gme.max_attempts) return res.status(429).json({ error: 'Attempt limit reached for this game.' });
  const won = !!b.won && score >= 60;
  const xp = Math.min(50, Math.floor(score / 2));
  let coupon = '';
  if (won && gme.reward_code) {
    const got = db.prepare('SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=? AND won=1').get(uid, gk).c;
    if (!(got && gme.reward_once)) {
      const gcode = (gme.reward_code + '-S' + uid).slice(0, 40);
      if (!db.prepare('SELECT id FROM coupons WHERE code=?').get(gcode)) {
        const exp = new Date(Date.now() + 90 * 864e5).toISOString().slice(0, 10);
        db.prepare('INSERT INTO coupons (code,kind,value,expires,max_uses) VALUES (?,?,?,?,1)').run(gcode, 'percent', 15, exp);
      }
      coupon = gcode;
    }
  }
  db.prepare('INSERT INTO career_attempts (user_id,gkey,score,xp,won) VALUES (?,?,?,?,?)').run(uid, gk, score, xp, won ? 1 : 0);
  res.json({ ok: true, xp, won, coupon });
}));

app.get('/api/admin/careers', requireAdmin, ah((req, res) => {
  const out = db.prepare('SELECT * FROM careers ORDER BY id').all().map((r) => {
    const st = db.prepare('SELECT COUNT(*) c, COUNT(DISTINCT user_id) u, COALESCE(SUM(won),0) w, COALESCE(SUM(xp),0) x FROM career_attempts WHERE gkey=?').get(r.gkey);
    return { ...r, attempts: st.c, students: st.u, wins: st.w, xp_given: st.x };
  });
  res.json({ games: out });
}));

app.post('/api/admin/careers', requireAdmin, ah((req, res) => {
  const b = req.body || {};
  const gk = str(b.gkey, 30).toLowerCase().replace(/ /g, '_');
  if (!gk) return bad(res, 'gkey required');
  let cur;
  try {
    cur = db.prepare('INSERT INTO careers (gkey,name,descr) VALUES (?,?,?)').run(gk, str(b.name, 80) || gk, str(b.descr, 300));
  } catch (e) { return bad(res, 'gkey already exists'); }
  logAdmin(req, 'career_create', gk);
  res.json({ ok: true, id: cur.lastInsertRowid });
}));

app.put('/api/admin/careers/:id', requireAdmin, ah((req, res) => {
  const row = db.prepare('SELECT * FROM careers WHERE id=?').get(req.params.id);
  if (!row) return bad(res, 'Not found', 404);
  const b = req.body || {};
  let mx = row.max_attempts;
  if (b.max_attempts !== undefined) { const v = parseInt(b.max_attempts, 10); if (!isNaN(v)) mx = Math.max(0, Math.min(9999, v)); }
  db.prepare('UPDATE careers SET name=?, descr=?, reward_code=?, reward_once=?, max_attempts=?, active=? WHERE id=?')
    .run(str(b.name !== undefined ? b.name : row.name, 80), str(b.descr !== undefined ? b.descr : row.descr, 300),
      str(b.reward_code !== undefined ? b.reward_code : row.reward_code, 40).toUpperCase(),
      (b.reward_once !== undefined ? b.reward_once : row.reward_once) ? 1 : 0, mx,
      (b.active !== undefined ? b.active : row.active) ? 1 : 0, req.params.id);
  logAdmin(req, 'career_update', row.gkey);
  res.json({ ok: true });
}));

app.delete('/api/admin/careers/:id', requireAdmin, ah((req, res) => {
  const row = db.prepare('SELECT * FROM careers WHERE id=?').get(req.params.id);
  if (!row) return bad(res, 'Not found', 404);
  db.prepare('DELETE FROM careers WHERE id=?').run(req.params.id);
  db.prepare('DELETE FROM career_attempts WHERE gkey=?').run(row.gkey);
  logAdmin(req, 'career_delete', row.gkey);
  res.json({ ok: true });
}));

// ------------------------------------------------------------ STATIC (catch-all below)
app.use('/api', (req, res) => res.status(404).json({ error: 'Not found' }));

app.get('*', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));

app.listen(PORT, HOST, () => console.log(`AL Planner running at http://${HOST}:${PORT}`));
