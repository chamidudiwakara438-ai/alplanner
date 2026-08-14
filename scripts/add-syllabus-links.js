#!/usr/bin/env node
/**
 * AL Planner — Syllabus & official LINK pack (Node replacement for
 * add-syllabus-links.py).
 *
 * Adds EXTERNAL LINK resources — no files are copied or hosted, we only link
 * to the original sources with their credit captions.
 *
 * HOW TO ADD MORE LINKS: edit content/syllabus-links.json (copy one object,
 * change title/category/subject/url/description), then run:
 *
 *   npm run content:links
 *
 * Safe to run many times — links already added are skipped.
 * Categories: notes, short_notes, question_papers, past_papers, model_papers, study_material
 * Subjects must match the site names exactly: Chemistry, Combined Mathematics, Biology, Physics, ICT
 */
'use strict';
const { openDb, loadContent, tryAddColumn } = require('./_common');

function main() {
  const db = openDb();
  const LINKS = loadContent('syllabus-links.json');

  for (const col of ['external_url', 'description']) tryAddColumn(db, 'resources', col, "TEXT DEFAULT ''");

  const admin = db.prepare("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").get();
  const adminId = admin ? admin.id : null;

  const insert = db.prepare(`INSERT INTO resources
    (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,uploaded_by,status,external_url,description)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`);

  let added = 0;
  let skipped = 0;
  for (const L of LINKS) {
    const subj = db.prepare('SELECT id FROM subjects WHERE name=?').get(L.subject);
    if (!subj) {
      console.log('  WARNING  subject not found:', L.subject, '-> skipped');
      continue;
    }
    if (db.prepare('SELECT 1 FROM resources WHERE external_url=?').get(L.url)) {
      console.log('  SKIP (already added):', L.title.slice(0, 60));
      skipped++;
      continue;
    }
    insert.run(L.title, L.category, '', '', 0, '', subj.id, null, adminId, 'approved', L.url, L.description);
    console.log('  ADDED:', L.title.slice(0, 60));
    added++;
  }

  const total = db.prepare("SELECT COUNT(*) c FROM resources WHERE external_url != ''").get().c;
  db.close();
  console.log('-'.repeat(60));
  console.log(`Done! added: ${added}, already-present: ${skipped}, total external link resources: ${total}`);
  console.log('Open the Resources page -> they show as blue "🔗 Open original source" cards.');
}

main();
