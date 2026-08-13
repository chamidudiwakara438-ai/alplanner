'use strict';
const path = require('path');
const Database = require('better-sqlite3');

const DATA_DIR = path.join(__dirname, 'data');
const UPLOAD_DIR = path.join(__dirname, 'uploads');
const fs = require('fs');
for (const d of [DATA_DIR, UPLOAD_DIR]) fs.mkdirSync(d, { recursive: true });

const db = new Database(path.join(DATA_DIR, 'alplanner.db'));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student',
  school TEXT DEFAULT '',
  district TEXT DEFAULT '',
  al_year TEXT DEFAULT '',
  medium TEXT DEFAULT 'en',
  stream TEXT DEFAULT '',
  subjects TEXT DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS al_years (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT UNIQUE NOT NULL,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS subjects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  name_si TEXT DEFAULT '',
  name_ta TEXT DEFAULT '',
  code TEXT DEFAULT '',
  icon TEXT DEFAULT 'book',
  color1 TEXT DEFAULT '#6366f1',
  color2 TEXT DEFAULT '#22d3ee',
  medium TEXT DEFAULT 'en',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS units (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  ord INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS teachers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  bio TEXT DEFAULT '',
  subjects TEXT DEFAULT '',
  photo TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  youtube_id TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  theory TEXT DEFAULT '',
  ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS resources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'study_material',
  file_path TEXT NOT NULL,
  orig_name TEXT DEFAULT '',
  size INTEGER DEFAULT 0,
  mime TEXT DEFAULT '',
  subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
  lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
  uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  downloads INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tutors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  photo TEXT DEFAULT '',
  subjects TEXT DEFAULT '[]',
  experience TEXT DEFAULT '',
  classes TEXT DEFAULT '[]',
  location TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  whatsapp TEXT DEFAULT '',
  email TEXT DEFAULT '',
  bio TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tutor_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tutor_id INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tutor_comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tutor_id INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  keep INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS site_settings (
  key TEXT PRIMARY KEY,
  value TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS contact_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT DEFAULT '',
  message TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  completed INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT,
  watched INTEGER NOT NULL DEFAULT 0,
  watched_at TEXT,
  favourite INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS saved_resources (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, resource_id)
);
`);

// ---- Shared metadata -------------------------------------------------
const DISTRICTS = [
  'Ampara', 'Anuradhapura', 'Badulla', 'Batticaloa', 'Colombo', 'Galle',
  'Gampaha', 'Hambantota', 'Jaffna', 'Kalutara', 'Kandy', 'Kegalle',
  'Kilinochchi', 'Kurunegala', 'Mannar', 'Matale', 'Matara', 'Monaragala',
  'Mullaitivu', 'Nuwara Eliya', 'Polonnaruwa', 'Puttalam', 'Ratnapura',
  'Trincomalee', 'Vavuniya'
];

const STREAMS = [
  'Physical Science',
  'Biological Science',
  'Commerce',
  'Arts',
  'Engineering Technology',
  'Bio Systems Technology'
];

const MEDIUMS = ['en', 'si', 'ta'];

const RESOURCE_CATEGORIES = [
  { id: 'notes',           label: 'Notes' },
  { id: 'short_notes',     label: 'Short Notes' },
  { id: 'question_papers', label: 'Question Papers' },
  { id: 'past_papers',     label: 'Past Papers' },
  { id: 'model_papers',    label: 'Model Papers' },
  { id: 'study_material',  label: 'Study Materials' }
];

// migration for older databases: teacher photos
try { db.exec("ALTER TABLE teachers ADD COLUMN photo TEXT DEFAULT ''"); } catch (e) { /* already exists */ }
// migration: per-lesson theory tab + MCQ practice questions
try { db.exec("ALTER TABLE lessons ADD COLUMN theory TEXT DEFAULT ''"); } catch (e) { /* already exists */ }
for (const col of ['external_url', 'description']) { // migration: external link resources w/ credit captions
  try { db.exec("ALTER TABLE resources ADD COLUMN " + col + " TEXT DEFAULT ''"); } catch (e) { /* already exists */ }
}
db.exec(`CREATE TABLE IF NOT EXISTS lesson_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  q TEXT NOT NULL, a TEXT DEFAULT '', b TEXT DEFAULT '', c TEXT DEFAULT '', d TEXT DEFAULT '',
  answer TEXT DEFAULT 'a', explanation TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')))`);

// smart features v2: search/practice/study-time/planner/settings/progress+
db.exec(`CREATE TABLE IF NOT EXISTS user_settings (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key TEXT NOT NULL, value TEXT DEFAULT '', PRIMARY KEY (user_id, key))`);
db.exec(`CREATE TABLE IF NOT EXISTS study_events (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day TEXT NOT NULL, seconds INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, day))`);
db.exec(`CREATE TABLE IF NOT EXISTS study_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  plan_date TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')), UNIQUE (user_id, lesson_id, plan_date))`);
db.exec(`CREATE TABLE IF NOT EXISTS practice_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  qtype TEXT NOT NULL DEFAULT 'structured', year INTEGER,
  title TEXT DEFAULT '', question TEXT NOT NULL, answer TEXT DEFAULT '', marks INTEGER DEFAULT 0,
  ord INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS practice_marks (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL REFERENCES practice_questions(id) ON DELETE CASCADE,
  ok INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, question_id))`);
db.exec(`CREATE TABLE IF NOT EXISTS mcq_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')))`);

// interactive simulations: lesson attach fields + progress
for (const col of ["simulation_type TEXT DEFAULT ''", 'simulation_enabled INTEGER DEFAULT NULL', "sim_config TEXT DEFAULT ''"]) {
  try { db.exec('ALTER TABLE lessons ADD COLUMN ' + col); } catch (e) { /* already exists */ }
}
// richer resource filters + tutor marketplace fields
for (const col of ["medium TEXT DEFAULT ''", "year TEXT DEFAULT ''", 'unit_id INTEGER DEFAULT NULL', "valid_until TEXT DEFAULT ''"]) {
  try { db.exec('ALTER TABLE resources ADD COLUMN ' + col); } catch (e) { /* already exists */ }
}
for (const col of ["district TEXT DEFAULT ''", "mode TEXT DEFAULT ''", "medium TEXT DEFAULT ''", "level TEXT DEFAULT ''", 'featured INTEGER NOT NULL DEFAULT 0']) {
  try { db.exec('ALTER TABLE tutors ADD COLUMN ' + col); } catch (e) { /* already exists */ }
}
db.exec(`CREATE TABLE IF NOT EXISTS sim_progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL DEFAULT '', started INTEGER NOT NULL DEFAULT 0,
  completed INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
  best_score INTEGER, last_score INTEGER, updated_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, lesson_id))`);
db.exec(`CREATE TABLE IF NOT EXISTS lab_notes (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  prac TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (user_id, prac))`);
db.exec(`CREATE TABLE IF NOT EXISTS lab_progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  prac TEXT NOT NULL, best INTEGER NOT NULL DEFAULT 0, done INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (user_id, prac))`);
db.exec(`CREATE TABLE IF NOT EXISTS exam_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject TEXT NOT NULL DEFAULT '', mode TEXT NOT NULL DEFAULT '',
  qcount INTEGER NOT NULL DEFAULT 0, score INTEGER NOT NULL DEFAULT 0,
  seconds INTEGER NOT NULL DEFAULT 0, topics TEXT NOT NULL DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS ai_usage (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, day))`);
db.exec(`CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file TEXT NOT NULL DEFAULT '', amount INTEGER NOT NULL DEFAULT 0, note TEXT DEFAULT '',
  method TEXT NOT NULL DEFAULT 'slip', txn_id TEXT NOT NULL DEFAULT '', mobile TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending', reason TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')), decided_at TEXT DEFAULT '')`);
try { db.exec("ALTER TABLE payments ADD COLUMN method TEXT NOT NULL DEFAULT 'slip'"); } catch (e) { /* already exists */ }
try { db.exec("ALTER TABLE payments ADD COLUMN txn_id TEXT NOT NULL DEFAULT ''"); } catch (e) { /* already exists */ }
try { db.exec("ALTER TABLE payments ADD COLUMN mobile TEXT NOT NULL DEFAULT ''"); } catch (e) { /* already exists */ }
try { db.exec("ALTER TABLE users ADD COLUMN premium_until TEXT DEFAULT ''"); } catch (e) { /* already exists */ }

// ---------------- admin spec pack (2026-08-11p) ----------------
db.exec(`CREATE TABLE IF NOT EXISTS admin_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, admin TEXT DEFAULT '',
  action TEXT NOT NULL, target TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS coupons (
  id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
  kind TEXT NOT NULL DEFAULT 'percent', value INTEGER NOT NULL DEFAULT 0,
  expires TEXT DEFAULT '', max_uses INTEGER NOT NULL DEFAULT 0, uses INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS ai_knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS ai_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question TEXT DEFAULT '', answer TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS challenges (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT 'mixed',
  mode TEXT NOT NULL DEFAULT 'm1', start TEXT NOT NULL DEFAULT '', end TEXT NOT NULL DEFAULT '',
  prize1 TEXT DEFAULT '', prize2 TEXT DEFAULT '', prize3 TEXT DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS challenge_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 0, qcount INTEGER NOT NULL DEFAULT 0, seconds INTEGER NOT NULL DEFAULT 0,
  prize_status TEXT NOT NULL DEFAULT '', created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (challenge_id, user_id))`);
try { db.exec("ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"); } catch (e) { /* already exists */ }
try { db.exec("ALTER TABLE payments ADD COLUMN coupon TEXT DEFAULT ''"); } catch (e) { /* already exists */ }

// ---------------- sim lab upgrade (2026-08-11q): DB-driven simulator catalog + events ----------------
db.exec(`CREATE TABLE IF NOT EXISTS sim_catalog (
  id INTEGER PRIMARY KEY AUTOINCREMENT, sim_type TEXT UNIQUE NOT NULL,
  subject TEXT NOT NULL DEFAULT '', title TEXT DEFAULT '', descr TEXT DEFAULT '',
  difficulty TEXT NOT NULL DEFAULT 'medium', objectives TEXT DEFAULT '', formulas TEXT DEFAULT '',
  tips TEXT DEFAULT '', xp_reward INTEGER NOT NULL DEFAULT 15, badge TEXT DEFAULT '',
  unit_id INTEGER DEFAULT NULL, lesson_id INTEGER DEFAULT NULL,
  enabled INTEGER NOT NULL DEFAULT 1, ord INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS sim_launches (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, sim_type, day))`);
db.exec(`CREATE TABLE IF NOT EXISTS sim_challenge_wins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL, goal TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (user_id, sim_type, goal))`);
db.exec(`CREATE TABLE IF NOT EXISTS sim_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL DEFAULT '', event TEXT NOT NULL DEFAULT 'score',
  score INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 1, pct INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')))`);
db.exec('CREATE INDEX IF NOT EXISTS ix_sim_events_week ON sim_events(created_at)');
try { db.exec('ALTER TABLE sim_catalog ADD COLUMN premium INTEGER NOT NULL DEFAULT 0'); } catch (_) { /* exists */ }
try { db.exec('ALTER TABLE resources ADD COLUMN premium INTEGER NOT NULL DEFAULT 0'); } catch (_) { /* exists */ }
db.exec(`CREATE TABLE IF NOT EXISTS careers (
  id INTEGER PRIMARY KEY AUTOINCREMENT, gkey TEXT UNIQUE NOT NULL, name TEXT NOT NULL DEFAULT '',
  descr TEXT DEFAULT '', reward_code TEXT DEFAULT '', reward_once INTEGER NOT NULL DEFAULT 1,
  max_attempts INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')))`);
db.exec(`CREATE TABLE IF NOT EXISTS career_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  gkey TEXT NOT NULL, score INTEGER NOT NULL DEFAULT 0, xp INTEGER NOT NULL DEFAULT 0,
  won INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))`);


// ---------------- Virtual Lab & NIE Practicals Database (Part 1) ----------------
db.exec(`CREATE TABLE IF NOT EXISTS practicals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '',
  practical_title_en TEXT NOT NULL DEFAULT '',
  practical_title_si TEXT NOT NULL DEFAULT '',
  unit_lesson TEXT NOT NULL DEFAULT '',
  objective TEXT NOT NULL DEFAULT '',
  theory_principle TEXT NOT NULL DEFAULT '',
  apparatus_materials TEXT NOT NULL DEFAULT '',
  chemicals TEXT DEFAULT NULL,
  diagram_setup_url TEXT DEFAULT NULL,
  procedure TEXT NOT NULL DEFAULT '',
  observation_table_format TEXT NOT NULL DEFAULT '',
  formulae TEXT NOT NULL DEFAULT '',
  calculations TEXT NOT NULL DEFAULT '',
  graph_details TEXT NOT NULL DEFAULT '',
  result_conclusion TEXT NOT NULL DEFAULT '',
  precautions_safety TEXT NOT NULL DEFAULT '',
  common_errors TEXT NOT NULL DEFAULT '',
  viva_questions TEXT NOT NULL DEFAULT '[]',
  past_paper_questions TEXT NOT NULL DEFAULT '[]',
  seed_key TEXT UNIQUE NOT NULL)`);
db.exec('CREATE INDEX IF NOT EXISTS idx_prac_subject ON practicals(subject)');
db.exec('CREATE INDEX IF NOT EXISTS idx_prac_category ON practicals(category)');

const PRAC_KEYMAP = { s: 'subject', c: 'category', en: 'practical_title_en', si: 'practical_title_si',
  u: 'unit_lesson', o: 'objective', th: 'theory_principle', ap: 'apparatus_materials',
  ch: 'chemicals', dg: 'diagram_setup_url', pr: 'procedure', ob: 'observation_table_format',
  f: 'formulae', ca: 'calculations', g: 'graph_details', r: 'result_conclusion',
  pc: 'precautions_safety', er: 'common_errors', vq: 'viva_questions', pp: 'past_paper_questions' };
const PRAC_COLS = ['subject', 'category', 'practical_title_en', 'practical_title_si', 'unit_lesson', 'objective',
  'theory_principle', 'apparatus_materials', 'chemicals', 'diagram_setup_url', 'procedure',
  'observation_table_format', 'formulae', 'calculations', 'graph_details', 'result_conclusion',
  'precautions_safety', 'common_errors', 'viva_questions', 'past_paper_questions', 'seed_key'];

function seedPracticals() {
  const dir = path.join(__dirname, 'practicals');
  if (!fs.existsSync(dir)) return 0;
  const recs = [];
  for (const fp of fs.readdirSync(dir).filter((f) => f.endsWith('.json')).sort()) {
    for (const rec of JSON.parse(fs.readFileSync(path.join(dir, fp), 'utf8'))) {
      const row = {};
      for (const c of PRAC_COLS) row[c] = null;
      for (const [sk, col] of Object.entries(PRAC_KEYMAP)) if (rec[sk] != null) row[col] = rec[sk];
      row.practical_title_si = rec.si || rec.en || '';
      row.viva_questions = JSON.stringify(rec.vq || []);
      row.past_paper_questions = JSON.stringify(rec.pp || []);
      row.seed_key = (row.subject || '') + ' | ' + (row.practical_title_en || '');
      recs.push(row);
    }
  }
  const keys = recs.map((r) => r.seed_key);
  const seedTx = db.transaction(() => {
    if (keys.length) db.prepare(`DELETE FROM practicals WHERE seed_key NOT IN (${keys.map(() => '?').join(',')})`).run(...keys);
    const upd = PRAC_COLS.filter((c) => c !== 'seed_key').map((c) => `${c}=excluded.${c}`).join(', ');
    const ins = db.prepare(`INSERT INTO practicals (${PRAC_COLS.join(',')}) VALUES (${PRAC_COLS.map(() => '?').join(',')}) ON CONFLICT(seed_key) DO UPDATE SET ${upd}`);
    for (const row of recs) ins.run(...PRAC_COLS.map((c) => row[c]));
  });
  seedTx();
  return recs.length;
}
try { console.log('NIE Practicals seeded:', seedPracticals(), 'records (Physics 43 / Chemistry 45)'); }
catch (e) { console.log('Practicals seed warning:', e.message); }

module.exports = { db, DATA_DIR, UPLOAD_DIR, DISTRICTS, STREAMS, MEDIUMS, RESOURCE_CATEGORIES, seedPracticals };
