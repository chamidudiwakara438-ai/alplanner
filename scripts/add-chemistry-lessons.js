#!/usr/bin/env node
/**
 * AL Planner — Chemistry video lesson pack (Node replacement for
 * add-chemistry-lessons.py). The parsed link list lives in
 * content/chemistry-lessons.json.
 *
 * What it does, all automatically:
 *   * Reorganises Chemistry into the official A/L unit structure
 *   * Moves the old demo lessons into the correct new units
 *   * Adds every YouTube link from the list as a video lesson
 *   * Detects duplicate links and adds them only once
 *   * Accounts, uploads, progress and other subjects are NOT touched
 *
 * Safe to run many times — already-added videos are skipped.
 *
 *   npm run content:chemistry
 */
'use strict';
const { openDb, loadContent, tryAddColumn, ensureTeacher, lessonCount } = require('./_common');

const CHEM_BIO = 'Popular G.C.E. A/L Chemistry teacher (video lessons).';

function main() {
  const db = openDb();
  const { unitMap, moveRules, fallbackUnit, sections } = loadContent('chemistry-lessons.json');

  // teacher-photo column, for databases created before this feature
  tryAddColumn(db, 'teachers', 'photo', "TEXT DEFAULT ''");

  let subjId;
  const subj = db.prepare("SELECT id FROM subjects WHERE lower(name)='chemistry'").get();
  if (!subj) {
    subjId = db
      .prepare('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)')
      .run('Chemistry', 'රසායන විද්‍යා', 'வேதியியல்', 'CHEM', 'flask', '#8b5cf6', '#22d3ee').lastInsertRowid;
    console.log('OK Chemistry subject created');
  } else {
    subjId = subj.id;
  }

  const unitCache = new Map();
  const ensureUnit = (name, ord) => {
    if (unitCache.has(name)) return unitCache.get(name);
    const row = db.prepare('SELECT id FROM units WHERE subject_id=? AND name=?').get(subjId, name);
    let uid;
    if (row) {
      uid = row.id;
      db.prepare('UPDATE units SET ord=? WHERE id=?').run(ord, uid);
    } else {
      uid = db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)').run(subjId, name, ord).lastInsertRowid;
    }
    unitCache.set(name, uid);
    return uid;
  };

  // 1) Move old demo lessons out of 'General/Physical Chemistry' into the new units
  let moved = 0;
  for (const old of ['General Chemistry', 'Physical Chemistry']) {
    const row = db.prepare('SELECT id FROM units WHERE subject_id=? AND name=?').get(subjId, old);
    if (!row) continue;
    for (const les of db.prepare('SELECT id,title FROM lessons WHERE unit_id=?').all(row.id)) {
      const t = (les.title || '').toLowerCase();
      const rule = moveRules.find((r) => t.includes(r.kw));
      const target = rule ? rule.unit : fallbackUnit;
      let tid = db.prepare('SELECT id FROM units WHERE subject_id=? AND name=?').get(subjId, target);
      if (!tid) {
        tid = { id: db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,0)').run(subjId, target).lastInsertRowid };
      }
      db.prepare('UPDATE lessons SET unit_id=? WHERE id=?').run(tid.id, les.id);
      moved++;
    }
    db.prepare('DELETE FROM units WHERE id=?').run(row.id);
  }
  if (moved) console.log(`OK moved ${moved} old demo lessons into the new units`);

  // 2) Create / reorder the official unit structure
  const unitIds = new Map();
  for (const u of unitMap) unitIds.set(u.name, ensureUnit(u.name, u.ord));
  console.log(`OK Chemistry now has ${unitIds.size} official units`);

  // 3) Add the video lessons (skip duplicates — inside the file and against the DB)
  const teacherCache = new Map();
  const existing = new Set(
    db.prepare('SELECT youtube_id FROM lessons').all().map((r) => r.youtube_id).filter(Boolean)
  );
  const seen = new Set();
  let added = 0;
  let skippedDup = 0;
  const insert = db.prepare(
    'INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)'
  );

  const run = db.transaction(() => {
    for (const sec of sections) {
      for (const vid of sec.videos) {
        if (seen.has(vid) || existing.has(vid)) { skippedDup++; continue; }
        seen.add(vid);
        const unitId = unitIds.get(sec.unit);
        const count = lessonCount(db, unitId);
        const num = String(count + 1).padStart(2, '0');
        let title = sec.unit + ' — ' + (sec.tag ? sec.tag + ' ' : 'Lesson ') + num;
        let tid = null;
        let desc = 'G.C.E. A/L Chemistry video lesson. Unit: ' + sec.unit + '.';
        if (sec.teacher) {
          title += ' (' + sec.teacher + ')';
          if (!teacherCache.has(sec.teacher)) {
            teacherCache.set(sec.teacher, ensureTeacher(db, sec.teacher, CHEM_BIO, 'Chemistry'));
          }
          tid = teacherCache.get(sec.teacher);
          desc = 'G.C.E. A/L Chemistry video lesson. Unit: ' + sec.unit + '. Taught by ' + sec.teacher + '.';
        }
        insert.run(unitId, tid, title, desc, vid, '', count + 1);
        existing.add(vid);
        added++;
      }
    }
  });
  run();

  console.log('\nSummary:');
  for (const u of unitMap) {
    const id = unitIds.get(u.name);
    const c = lessonCount(db, id);
    const vids = db.prepare("SELECT COUNT(*) c FROM lessons WHERE unit_id=? AND youtube_id<>''").get(id).c;
    console.log('   ' + u.name.padEnd(28) + c + ' lessons (' + vids + ' videos)');
  }
  const total = db
    .prepare('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?')
    .get(subjId).c;
  db.close();
  console.log(`\n   TOTAL Chemistry lessons: ${total}  |  added now: ${added}  |  duplicate links skipped: ${skippedDup}`);
  console.log('\nDONE! Start the website again and press Ctrl+F5:  http://localhost:3000/#/subject/1');
}

main();
