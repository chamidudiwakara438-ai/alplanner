#!/usr/bin/env node
/**
 * AL Planner — apply the whole content library in the right order.
 * Replaces the old "run every add-*.py one by one" routine.
 *
 *   npm run content        (after the site has been started once)
 *
 * Every step is idempotent, so this is safe to run as often as you like.
 */
'use strict';
const path = require('path');
const { execFileSync } = require('child_process');

const STEPS = [
  // demo content first: its placeholder lessons otherwise block the Combined
  // Maths unit restructure below (that step refuses to touch units with lessons)
  ['remove-demo-content.js', 'Remove demo lessons, fake teachers and demo tutors'],
  ['add-subjects.js', 'Subjects + NIE unit lists (Physics, ICT)'],
  ['add-cm-units.js', 'Combined Maths official topic units'],
  ['add-chemistry-lessons.js', 'Chemistry video lesson pack'],
  ['add-cm-lessons.js', 'Combined Maths video lessons'],
  ['add-physics-lessons.js', 'Physics video lessons (main pack)'],
  ['add-physics-batch2.js', 'Physics video lessons (batch 2)'],
  ['add-physics-batch3.js', 'Physics video lessons (batch 3)'],
  ['add-lesson-tabs.js', 'Lesson Theory + MCQ tabs'],
  ['add-syllabus-links.js', 'Syllabus / past-paper external links'],
];

let failed = 0;
for (const [file, label] of STEPS) {
  console.log('\n' + '='.repeat(70));
  console.log('▶  ' + label + '   (' + file + ')');
  console.log('='.repeat(70));
  try {
    execFileSync(process.execPath, [path.join(__dirname, file)], { stdio: 'inherit' });
  } catch (e) {
    failed++;
    console.error('✖  step failed: ' + file);
  }
}

console.log('\n' + '='.repeat(70));
console.log(failed ? `Finished with ${failed} failed step(s).` : 'All content applied successfully. 🎉');
console.log('Start the website (npm start) and press Ctrl+F5 in the browser.');
process.exit(failed ? 1 : 0);
