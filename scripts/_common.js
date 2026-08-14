'use strict';
// Shared helpers for the AL Planner content scripts (Node replacements for the
// old add-*.py / remove-demo-content.py helpers).
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const BASE = path.join(__dirname, '..');
const DATA_DIR = process.env.AL_DATA_DIR || path.join(BASE, 'data');
const DB_PATH = path.join(DATA_DIR, 'alplanner.db');
const CONTENT_DIR = path.join(BASE, 'content');

function openDb({ required = true } = {}) {
  if (required && !fs.existsSync(DB_PATH)) {
    console.error('ERROR: database not found at: ' + DB_PATH);
    console.error('Start the website once first (npm start), then run this file again.');
    process.exit(1);
  }
  fs.mkdirSync(DATA_DIR, { recursive: true });
  const db = new Database(DB_PATH);
  db.pragma('foreign_keys = ON');
  return db;
}

function loadContent(name) {
  return JSON.parse(fs.readFileSync(path.join(CONTENT_DIR, name), 'utf8'));
}

// ALTER TABLE ... ADD COLUMN that silently ignores "duplicate column" errors.
function tryAddColumn(db, table, column, decl) {
  try {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${decl}`);
  } catch (e) {
    if (!/duplicate column/i.test(e.message)) throw e;
  }
}

function ensureTeacher(db, name, bio, subjects) {
  const row = db.prepare('SELECT id FROM teachers WHERE name=?').get(name);
  if (row) return row.id;
  const info = db.prepare('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)').run(name, bio, subjects);
  return info.lastInsertRowid;
}

function subjectId(db, name) {
  const row = db.prepare('SELECT id FROM subjects WHERE lower(name)=lower(?)').get(name);
  return row ? row.id : null;
}

function lessonCount(db, unitId) {
  return db.prepare('SELECT COUNT(*) c FROM lessons WHERE unit_id=?').get(unitId).c;
}

function existingVideoIds(db) {
  const set = new Set();
  for (const r of db.prepare("SELECT youtube_id FROM lessons WHERE youtube_id IS NOT NULL AND youtube_id<>''").all()) {
    set.add(r.youtube_id);
  }
  return set;
}

/**
 * Shared "add a batch of YouTube lessons to units picked by unit ord" routine —
 * used by the Combined Maths and Physics batch packs.
 */
function addLessonBatch(db, { subjectName, teachers = [], lessons, descEn, descSi, label }) {
  const sid = subjectId(db, subjectName);
  if (!sid) {
    console.log(`${label}: subject "${subjectName}" not found — start the website once first.`);
    return;
  }
  for (const t of teachers) {
    if (!db.prepare('SELECT 1 FROM teachers WHERE name=?').get(t.name)) {
      ensureTeacher(db, t.name, t.bio, subjectName);
      console.log('  + teacher created:', t.name);
    }
  }
  const teacherIds = new Map(db.prepare('SELECT id,name FROM teachers').all().map((r) => [r.name, r.id]));
  const units = new Map(
    db.prepare('SELECT id,ord,name FROM units WHERE subject_id=?').all(sid).map((r) => [r.ord, r])
  );
  const existing = existingVideoIds(db);
  const insert = db.prepare(
    'INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)'
  );
  let added = 0;
  let skipped = 0;

  const run = db.transaction(() => {
    for (const L of lessons) {
      if (existing.has(L.vid)) { skipped++; continue; }
      const u = units.get(L.unitOrd);
      const tid = teacherIds.get(L.teacher);
      if (!u || !tid) {
        console.log('  WARN missing unit/teacher for', L.vid, L.unitOrd, L.teacher);
        continue;
      }
      const n = lessonCount(db, u.id);
      const desc = descEn(u.name, L.teacher) + '\n' + descSi(u.name, L.teacher);
      insert.run(u.id, tid, L.title, desc, L.vid, '', n + 1);
      existing.add(L.vid);
      added++;
    }
  });
  run();

  const total = db
    .prepare('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?')
    .get(sid).c;
  console.log(`${label}: added ${added}, skipped ${skipped} already-present. ${subjectName} lessons total: ${total}.`);
}

module.exports = {
  BASE, DATA_DIR, DB_PATH, CONTENT_DIR,
  openDb, loadContent, tryAddColumn, ensureTeacher, subjectId,
  lessonCount, existingVideoIds, addLessonBatch,
};
