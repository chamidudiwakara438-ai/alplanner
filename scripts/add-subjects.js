#!/usr/bin/env node
/**
 * AL Planner — one-time helper (Node replacement for add-subjects.py)
 * ===================================================================
 * Adds the extra A/L subjects (Physics + ICT) with their official NIE unit
 * lists into the website's database. Existing data (accounts, uploads,
 * progress) is NOT touched. Safe to run again and again.
 *
 *   npm run content:subjects
 */
'use strict';
const { openDb, loadContent } = require('./_common');

function main() {
  const db = openDb();
  const SUBJECTS = loadContent('subjects.json');

  for (const subj of SUBJECTS) {
    let sid;
    const row = db.prepare('SELECT id FROM subjects WHERE lower(name)=lower(?)').get(subj.name);
    if (row) {
      sid = row.id;
      console.log('-- ' + subj.name + ' already exists — checking its units...');
    } else {
      sid = db
        .prepare('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)')
        .run(subj.name, subj.si, subj.ta, subj.code, subj.icon, subj.c1, subj.c2).lastInsertRowid;
      console.log('OK ' + subj.name + ' subject added');
    }

    let added = 0;
    subj.units.forEach((uname, i) => {
      const ord = i + 1;
      // check by ORD (not name): bilingual renames must not cause reinserts
      const exists = db.prepare('SELECT id FROM units WHERE subject_id=? AND ord=?').get(sid, ord);
      if (!exists) {
        db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)').run(sid, uname, ord);
        added++;
      }
    });

    const total = db.prepare('SELECT COUNT(*) c FROM units WHERE subject_id=?').get(sid).c;
    console.log(`   ${subj.name}: ${total} units ready (${added} new)`);
  }

  db.close();
  console.log('\nDONE! Start the website again (npm start) and refresh http://localhost:3000/#/subjects');
}

main();
