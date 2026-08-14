#!/usr/bin/env node
/**
 * AL Planner — Physics video lesson pack (Node replacement for
 * add-physics-lessons.py). Data in content/physics-lessons.json.
 *
 * Makes sure the 11 bilingual Physics units exist (merging any duplicate
 * leftovers from older installs), then adds every video lesson, skipping
 * anything already present. Safe to run many times.
 *
 *   npm run content:physics
 */
'use strict';
const { openDb, loadContent, ensureTeacher, subjectId, lessonCount, existingVideoIds } = require('./_common');

const PHY_BIO = 'Popular G.C.E. A/L Physics teacher (video lessons).';

// old lesson titles that had made-up / typo Sinhala
const TITLE_FIX = {
  E7QbzysxmyE: 'Newton\u2019s Cradle',
  DZEfX4NFDLg: 'Flash Practicals 01 – වර්නියර් කැලිපරය (Vernier Caliper)',
};

const ekey = (nm) => nm.split(' – ')[0].trim().toLowerCase();

function main() {
  const db = openDb();
  const { units: UNITS, lessons } = loadContent('physics-lessons.json');

  const sid = subjectId(db, 'Physics');
  if (!sid) {
    console.log('ERROR: Physics subject not found. Run `npm run content:subjects` first.');
    return db.close();
  }

  // 1) merge duplicate/leftover units deterministically (older installs had
  //    English-name doubles; check by english-prefix, keep most-lessons unit)
  const allUnits = db.prepare('SELECT id,name FROM units WHERE subject_id=? ORDER BY id').all(sid);
  UNITS.forEach((canonName, i) => {
    const canonOrd = i + 1;
    const group = allUnits.filter((u) => ekey(u.name) === ekey(canonName));
    if (!group.length) return;
    const score = (u) => [lessonCount(db, u.id), u.name.includes('–') ? 1 : 0, -u.id];
    const keep = group.reduce((best, u) => {
      const [a1, a2, a3] = score(u);
      const [b1, b2, b3] = score(best);
      return a1 > b1 || (a1 === b1 && (a2 > b2 || (a2 === b2 && a3 > b3))) ? u : best;
    });
    for (const u of group) {
      if (u.id === keep.id) continue;
      db.prepare('UPDATE lessons SET unit_id=? WHERE unit_id=?').run(keep.id, u.id);
      db.prepare('UPDATE resources SET lesson_id=NULL WHERE lesson_id IN (SELECT id FROM lessons WHERE unit_id=?)').run(u.id);
      db.prepare('DELETE FROM units WHERE id=?').run(u.id);
      console.log(`   merged duplicate unit: "${u.name}"  ->  "${keep.name}"`);
    }
    db.prepare('UPDATE units SET name=?, ord=? WHERE id=?').run(canonName, canonOrd, keep.id);
  });

  // 2) Make sure all units exist + rename them to bilingual titles
  const unitId = new Map();
  UNITS.forEach((name, i) => {
    const ord = i + 1;
    const row = db.prepare('SELECT id,name FROM units WHERE subject_id=? AND ord=?').get(sid, ord);
    if (!row) {
      unitId.set(ord, db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)').run(sid, name, ord).lastInsertRowid);
    } else {
      if (row.name !== name) db.prepare('UPDATE units SET name=? WHERE id=?').run(name, row.id);
      unitId.set(ord, row.id);
    }
  });
  console.log(`OK Physics now has ${UNITS.length} bilingual units`);

  // 3) fix old lesson titles
  for (const [vid, t] of Object.entries(TITLE_FIX)) {
    db.prepare('UPDATE lessons SET title=? WHERE youtube_id=? AND title<>?').run(t, vid, t);
  }

  // 4) Teachers (create if missing) + add video lessons, skipping duplicates
  const teacherCache = new Map();
  const tidFor = (name) => {
    if (!teacherCache.has(name)) teacherCache.set(name, ensureTeacher(db, name, PHY_BIO, 'Physics'));
    return teacherCache.get(name);
  };

  const existing = existingVideoIds(db);
  const insert = db.prepare(
    'INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)'
  );
  let added = 0;
  let skipped = 0;

  const run = db.transaction(() => {
    for (const L of lessons) {
      if (existing.has(L.vid)) { skipped++; continue; }
      const uId = unitId.get(L.unitOrd);
      const count = lessonCount(db, uId);
      const unitName = UNITS[L.unitOrd - 1];
      const desc =
        `G.C.E. A/L Physics video lesson. Unit: ${unitName}. Taught by ${L.teacher}.\n` +
        `G.C.E. උ/පෙ භෞතික විද්‍යා වීඩියෝ පාඩම. ඒකකය: ${unitName}.`;
      insert.run(uId, tidFor(L.teacher), L.title, desc, L.vid, '', count + 1);
      existing.add(L.vid);
      added++;
    }
    // cosmetic: collapse double slashes left by teacher-name stripping in titles
    db.prepare("UPDATE lessons SET title = REPLACE(title, ' / / ', ' / ') WHERE title LIKE '%/ / %'").run();
  });
  run();

  console.log(`\nNew lessons added: ${added}   |   duplicates skipped: ${skipped}\n`);
  console.log('Physics units now:');
  UNITS.forEach((name, i) => {
    const c = lessonCount(db, unitId.get(i + 1));
    if (c) console.log('   ' + String(i + 1).padStart(2) + '. ' + name + '  ->  ' + c + ' lessons');
  });
  db.close();
  console.log('\nDONE! Start the website again and press Ctrl+F5:  http://localhost:3000/#/subject/4');
}

main();
