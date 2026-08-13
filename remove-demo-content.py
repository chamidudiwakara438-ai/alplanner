#!/usr/bin/env python3
"""
AL Planner - Remove demo/seed content
=====================================
The website started with demo content so it never looked empty:
  * 24 demo video lessons (English, Khan Academy) with made-up teachers
  * 7 fake teacher profiles (Mr. Nimal Perera, etc.)
  * 6 demo tutors on the Tutors page

Users asked to remove them - only REAL teacher packs should stay.
This script is idempotent: safe to run on every site start.

Run:  python remove-demo-content.py
"""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

FAKE_TEACHERS = ['Mr. Nimal Perera', 'Prof. Anura Jayasuriya', 'Ms. Sanduni Fernando',
                 'Mr. Kasun Bandara', 'Ms. Dilani Wickramasinghe', 'Dr. Tharushi Jayasinghe',
                 'Mr. Ruwan Gunasekara']


def main():
    if not os.path.exists(DB):
        return 0
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    marks = ','.join('?' * len(FAKE_TEACHERS))
    demo = db.execute(
        'SELECT l.id FROM lessons l JOIN teachers t ON t.id=l.teacher_id WHERE t.name IN (%s)' % marks,
        FAKE_TEACHERS).fetchall()
    demo_ids = [r['id'] for r in demo]

    removed_lessons = 0
    if demo_ids:
        dmarks = ','.join('?' * len(demo_ids))
        db.execute('DELETE FROM lesson_questions WHERE lesson_id IN (%s)' % dmarks, demo_ids)
        db.execute('DELETE FROM progress WHERE lesson_id IN (%s)' % dmarks, demo_ids)
        db.execute('UPDATE resources SET lesson_id=NULL WHERE lesson_id IN (%s)' % dmarks, demo_ids)
        cur = db.execute('DELETE FROM lessons WHERE id IN (%s)' % dmarks, demo_ids)
        removed_lessons = cur.rowcount

    removed_teachers = 0
    for name in FAKE_TEACHERS:
        row = db.execute('SELECT id FROM teachers WHERE name=?', (name,)).fetchone()
        if not row:
            continue
        used = db.execute('SELECT COUNT(*) c FROM lessons WHERE teacher_id=?', (row['id'],)).fetchone()['c']
        if used == 0:
            db.execute('DELETE FROM teachers WHERE id=?', (row['id'],))
            removed_teachers += 1

    cur = db.execute('DELETE FROM tutors')
    removed_tutors = cur.rowcount
    db.execute('DELETE FROM tutor_messages')

    db.commit()
    db.close()

    if removed_lessons or removed_teachers or removed_tutors:
        print('Demo content removed: %d lessons, %d fake teachers, %d demo tutors.'
              % (removed_lessons, removed_teachers, removed_tutors))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
