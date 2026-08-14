#!/usr/bin/env node
/**
 * AL Planner — Remove demo/seed content (Node replacement for
 * remove-demo-content.py).
 *
 * The website started with demo content so it never looked empty:
 *   * 24 demo video lessons (English, Khan Academy) with made-up teachers
 *   * 7 fake teacher profiles (Mr. Nimal Perera, etc.)
 *   * 6 demo tutors on the Tutors page
 *
 * Only REAL teacher packs should stay. Idempotent — safe to run on every start.
 *
 *   npm run content:clean-demo
 */
'use strict';
const fs = require('fs');
const { openDb, loadContent, DB_PATH } = require('./_common');

function main() {
  if (!fs.existsSync(DB_PATH)) return;
  const db = openDb();
  const FAKE_TEACHERS = loadContent('demo-teachers.json');

  let removedLessons = 0;
  let removedTeachers = 0;
  let removedTutors = 0;

  const run = db.transaction(() => {
    const marks = FAKE_TEACHERS.map(() => '?').join(',');
    const demoIds = db
      .prepare(`SELECT l.id FROM lessons l JOIN teachers t ON t.id=l.teacher_id WHERE t.name IN (${marks})`)
      .all(...FAKE_TEACHERS)
      .map((r) => r.id);

    if (demoIds.length) {
      const dm = demoIds.map(() => '?').join(',');
      db.prepare(`DELETE FROM lesson_questions WHERE lesson_id IN (${dm})`).run(...demoIds);
      db.prepare(`DELETE FROM progress WHERE lesson_id IN (${dm})`).run(...demoIds);
      db.prepare(`UPDATE resources SET lesson_id=NULL WHERE lesson_id IN (${dm})`).run(...demoIds);
      removedLessons = db.prepare(`DELETE FROM lessons WHERE id IN (${dm})`).run(...demoIds).changes;
    }

    for (const name of FAKE_TEACHERS) {
      const row = db.prepare('SELECT id FROM teachers WHERE name=?').get(name);
      if (!row) continue;
      const used = db.prepare('SELECT COUNT(*) c FROM lessons WHERE teacher_id=?').get(row.id).c;
      if (used === 0) {
        db.prepare('DELETE FROM teachers WHERE id=?').run(row.id);
        removedTeachers++;
      }
    }

    removedTutors = db.prepare('DELETE FROM tutors').run().changes;
    db.prepare('DELETE FROM tutor_messages').run();
  });
  run();
  db.close();

  if (removedLessons || removedTeachers || removedTutors) {
    console.log(
      `Demo content removed: ${removedLessons} lessons, ${removedTeachers} fake teachers, ${removedTutors} demo tutors.`
    );
  }
}

main();
