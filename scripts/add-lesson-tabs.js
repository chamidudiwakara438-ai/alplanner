#!/usr/bin/env node
/**
 * AL Planner — lesson Theory + MCQ tabs (Node replacement for add-lesson-tabs.py).
 * Content lives in content/lesson-tabs.json — one block per lesson:
 *   match     : first words of the lesson title (must match ONE lesson)
 *   theory    : text for the Theory tab
 *   questions : [{ q, a, b, c, d, answer: 'a'|'b'|'c'|'d', explanation }]
 *
 *   npm run content:tabs
 */
'use strict';
const { openDb, loadContent, tryAddColumn } = require('./_common');

function main() {
  const db = openDb();
  const CONTENT = loadContent('lesson-tabs.json');

  tryAddColumn(db, 'lessons', 'theory', "TEXT DEFAULT ''");
  db.exec(`CREATE TABLE IF NOT EXISTS lesson_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  q TEXT NOT NULL, a TEXT DEFAULT '', b TEXT DEFAULT '', c TEXT DEFAULT '', d TEXT DEFAULT '',
  answer TEXT DEFAULT 'a', explanation TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')))`);

  const insertQ = db.prepare(
    'INSERT INTO lesson_questions (lesson_id,q,a,b,c,d,answer,explanation,ord) VALUES (?,?,?,?,?,?,?,?,?)'
  );

  let doneT = 0;
  let doneQ = 0;
  const skipped = [];

  const run = db.transaction(() => {
    for (const blk of CONTENT) {
      const rows = db.prepare('SELECT id, title FROM lessons WHERE title LIKE ?').all(blk.match + '%');
      if (!rows.length) { skipped.push(blk.match); continue; }
      const lid = rows[0].id;
      db.prepare('UPDATE lessons SET theory=? WHERE id=?').run(blk.theory || '', lid);
      db.prepare('DELETE FROM lesson_questions WHERE lesson_id=?').run(lid);
      const qs = blk.questions || [];
      qs.forEach((q, i) =>
        insertQ.run(lid, q.q, q.a, q.b, q.c, q.d, q.answer, q.explanation || '', i + 1)
      );
      doneT++;
      doneQ += qs.length;
      console.log(`  OK  #${lid}  ${rows[0].title.slice(0, 52).padEnd(52)} theory + ${qs.length} questions`);
    }
  });
  run();

  for (const m of skipped) console.log(`  WARNING  no lesson starting with "${m}" — skipped.`);

  const qt = db.prepare('SELECT COUNT(*) c FROM lesson_questions').get().c;
  const th = db.prepare("SELECT COUNT(*) c FROM lessons WHERE theory != ''").get().c;
  db.close();
  console.log('-'.repeat(60));
  console.log(`Done! ${doneT} lessons got theory, ${doneQ} questions written this run.`);
  console.log(`Whole site now has: ${th} lessons with theory, ${qt} MCQ questions.`);
  console.log('Open any of those lessons -> Theory / MCQ Questions tabs.');
}

main();
