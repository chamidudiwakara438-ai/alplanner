#!/usr/bin/env node
/**
 * AL Planner content pack: Physics video lessons — batch 2.
 * Node replacement for add-physics-batch2.py (data in
 * content/physics-lessons-batch2.json).
 *
 *   npm run content:physics2
 */
'use strict';
const { openDb, loadContent, addLessonBatch } = require('./_common');

function main() {
  const db = openDb();
  const { teachers, lessons } = loadContent('physics-lessons-batch2.json');
  addLessonBatch(db, {
    subjectName: 'Physics',
    teachers,
    lessons,
    descEn: (unit, teacher) => `G.C.E. A/L Physics video lesson. Unit: ${unit}. Taught by ${teacher}.`,
    descSi: (unit) => `G.C.E. උ/පෙ භෞතික විද්‍යා වීඩියෝ පාඩම. ඒකකය: ${unit}.`,
    label: 'Batch2 physics',
  });
  db.close();
}

main();
