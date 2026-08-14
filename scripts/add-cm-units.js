#!/usr/bin/env node
/**
 * AL Planner content pack: Combined Mathematics real unit structure.
 * (Node replacement for add-cm-units.py)
 *
 * Replaces the two placeholder units (Pure / Applied Mathematics) with the 19
 * official-syllabus topic units (bilingual names). SAFE: runs only while every
 * CM unit has ZERO lessons; otherwise it leaves everything untouched. Idempotent.
 *
 *   npm run content:cm-units
 */
'use strict';
const { openDb, loadContent, subjectId } = require('./_common');

function main() {
  const db = openDb();
  const UNITS = loadContent('cm-units.json');

  const sid = subjectId(db, 'Combined Mathematics');
  if (!sid) {
    console.log('CM: subject not found — run content:subjects / start the server first.');
    return db.close();
  }

  const current = db.prepare('SELECT id,name FROM units WHERE subject_id=? ORDER BY ord').all(sid);
  const names = current.map((u) => u.name);
  if (names.length === UNITS.length && names.every((n, i) => n === UNITS[i])) {
    console.log(`CM: ${UNITS.length} topic units already in place — nothing to do.`);
    return db.close();
  }

  // safety: never delete units that hold lessons
  const busy = db
    .prepare('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?')
    .get(sid).c;
  if (busy) {
    console.log(`CM: has ${busy} lessons — unit restructure skipped (do it manually).`);
    return db.close();
  }

  const run = db.transaction(() => {
    db.prepare('DELETE FROM units WHERE subject_id=?').run(sid);
    const ins = db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)');
    UNITS.forEach((name, i) => ins.run(sid, name, i + 1));
  });
  run();

  console.log(`CM: placeholders replaced with ${UNITS.length} official topic units (bilingual).`);
  db.close();
}

main();
