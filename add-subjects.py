#!/usr/bin/env python3
"""
AL Planner - one-time helper
============================
Adds TWO new A/L subjects (Physics + ICT) with their official NIE unit lists
into your website's database. Your existing data (accounts, uploads,
progress) is NOT touched.

Safe to run again and again - anything that already exists is skipped.

How to run:
  1. Stop the website  (click its window, press Ctrl+C)  [not strictly needed]
  2. In the same folder type:   python add-subjects.py
     (on your PC use the full command:)
     & "C:\\Users\\Team Akoit\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" add-subjects.py
  3. Start the website again and refresh the browser.
"""
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

# Official NIE G.C.E. A/L syllabuses - unit lists
SUBJECTS = [
    {
        'name': 'Physics',
        'si': '\u0db7\u0ddc\u0dad\u0dd2\u0d9a \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf',   # Bhauthika Vidyava
        'ta': '\u0b87\u0baf\u0bb1\u0bcd\u0baa\u0bbf\u0baf\u0bb2\u0bcd',                     # Iyarpiyal
        'code': 'PHY', 'icon': 'book', 'c1': '#f97316', 'c2': '#e11d48',
        'units': [
            'Measurement', 'Mechanics', 'Oscillations and Waves', 'Thermal Physics',
            'Gravitational Field', 'Electrostatic Field', 'Magnetic Field',
            'Current Electricity', 'Electronics', 'Mechanical Properties of Matter',
            'Matter and Radiation',
        ],
    },
    {
        'name': 'ICT',
        'si': '\u0dad\u0ddc\u0dbb\u0dad\u0dd4\u0dbb\u0dd4 \u0dc4\u0dcf \u0dc3\u0db1\u0dca\u0db1\u0dd2\u0dc0\u0dda\u0daf\u0db1 \u0dad\u0dcf\u0d9a\u0dca\u0dc2\u0dab\u0dba',  # Thorathuru ha Sanniwedana Thakshanaya
        'ta': '\u0ba4\u0b95\u0bb5\u0bb2\u0bcd \u0ba4\u0bca\u0bb4\u0bbf\u0bb2\u0bcd\u0ba8\u0bc1\u0b9f\u0bcd\u0baa\u0bae\u0bcd',  # Thakaval Thozhilnutpam
        'code': 'ICT', 'icon': 'cap', 'c1': '#06b6d4', 'c2': '#3b82f6',
        'units': [
            'Concept of ICT', 'Introduction to Computer', 'Data Representation',
            'Fundamentals of Digital Circuits', 'Computer Operating Systems',
            'Data Communication and Networking', 'System Analysis and Design',
            'Database Management', 'Programming', 'Web Development',
            'Internet of Things', 'ICT in Business',
            'New Trends and Future Directions of ICT', 'Project',
        ],
    },
]


def main():
    if not os.path.exists(DB):
        print('ERROR: database not found at: ' + DB)
        print('Start the website once first (run server.py), then run this file again.')
        sys.exit(1)

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    for subj in SUBJECTS:
        row = db.execute('SELECT id FROM subjects WHERE lower(name)=lower(?)', (subj['name'],)).fetchone()
        if row:
            sid = row['id']
            print('-- ' + subj['name'] + ' already exists - checking its units...')
        else:
            cur = db.execute(
                'INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)',
                (subj['name'], subj['si'], subj['ta'], subj['code'], subj['icon'], subj['c1'], subj['c2']))
            sid = cur.lastrowid
            print('OK ' + subj['name'] + ' subject added')

        added = 0
        for i, uname in enumerate(subj['units'], 1):
            # check by ORD (not name): bilingual renames must not cause reinserts of empty English units
            exists = db.execute('SELECT id FROM units WHERE subject_id=? AND ord=?', (sid, i)).fetchone()
            if not exists:
                db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', (sid, uname, i))
                added += 1

        total = db.execute('SELECT COUNT(*) c FROM units WHERE subject_id=?', (sid,)).fetchone()['c']
        print('   ' + subj['name'] + ': ' + str(total) + ' units ready (' + str(added) + ' new)')

    db.commit()
    db.close()

    print('')
    print('DONE! Now:')
    print('  1. Start the website again   (same command as before, or double-click RUN-ME.bat)')
    print('  2. Refresh your browser      http://localhost:3000/#/subjects')
    print('  3. To add lesson videos: log in as admin -> Admin panel -> Lessons ->')
    print('     pick the subject/unit and paste any YouTube link.')


if __name__ == '__main__':
    main()
