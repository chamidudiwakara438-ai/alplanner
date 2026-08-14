#!/usr/bin/env node
/**
 * AL Planner content pack: Combined Mathematics video lessons (batch 1).
 * Node replacement for add-cm-lessons.py — data in content/cm-lessons.json.
 *
 *   npm run content:cm-lessons
 */
'use strict';
const { openDb, loadContent, addLessonBatch } = require('./_common');

function main() {
  const db = openDb();
  const { teachers, lessons } = loadContent('cm-lessons.json');
  addLessonBatch(db, {
    subjectName: 'Combined Mathematics',
    teachers,
    lessons,
    descEn: (unit, teacher) =>
      `G.C.E. A/L Combined Mathematics video lesson. Unit: ${unit}. Taught by ${teacher}.`,
    descSi: (unit, teacher) =>
      `G.C.E. උසස් පෙළ සංයුක්ත ගණිතය වීඩියෝ පාඩම. ඒකකය: ${unit}. ගුරුවරයා: ${teacher}.`,
    label: 'CM batch1',
  });
  db.close();
}

main();
