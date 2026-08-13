#!/usr/bin/env python3
"""
AL Planner - Syllabus & official LINK pack
==========================================
Adds EXTERNAL LINK resources (no files are copied or hosted - we only link to
the original sources, with the credit captions you wrote).

Already included:
  1. A/L Chemistry Resource Book - 2019 Syllabus (mathsapi.com)
  2. A/L Chemistry Past Papers 2025-2013 (govdoc.lk)

HOW TO ADD MORE LINKS (e.g. Physics, ICT books):
  1. Scroll to LINKS below, copy one {...} block, paste under it,
     change title/category/subject/url/description.
  2. Save this file.
  3. Stop the website (Ctrl+C in the black window), then run:
         python add-syllabus-links.py
     (on your PC if plain "python" misbehaves:
      & "C:\\Users\\Team Akoit\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" add-syllabus-links.py)
  4. Start the website again -> Resources page -> they appear as blue link cards.

Safe to run many times - links already added are skipped.
Categories you may use: notes, short_notes, question_papers, past_papers, model_papers, study_material
Subjects must match the site names exactly: Chemistry, Combined Mathematics, Biology, Physics, ICT
"""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

LINKS = [
    {
        'title': 'A/L Chemistry Resource Book - 2019 Syllabus (Sinhala Medium)',
        'category': 'study_material',
        'subject': 'Chemistry',
        'url': 'https://www.mathsapi.com/2020/09/al-chemistry-resource-book-sinhala.html',
        'description': ('A/L Chemistry Resource Book (2019 Syllabus). Looking for the Chemistry Resource Book? '
                        'We have shared a link to the original resource for your convenience. '
                        'Credit belongs to the original publisher/source. We do not own or host this material.'),
    },
    {
        'title': 'A/L Chemistry Past Papers - 2025-2013 (Marking Schemes, all mediums)',
        'category': 'past_papers',
        'subject': 'Chemistry',
        'url': 'https://govdoc.lk/category/past-papers/gce-advance-level-exam',
        'description': ('A/L Chemistry Past Papers (2025-2013). Past papers and marking schemes are available through '
                        'the original source in English, Sinhala, and Tamil Medium. We do not own, host, or claim '
                        'copyright over these papers. We only provide links to the original source for educational '
                        'purposes. All credit belongs to the respective publishers and copyright holders.'),
    },
]

def main():
    if not os.path.exists(DB):
        print('ERROR: database not found at', DB)
        print('Start the website once first, then run this file again.')
        raise SystemExit(1)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    for col in ('external_url', 'description'):
        try:
            db.execute('ALTER TABLE resources ADD COLUMN %s TEXT DEFAULT \'\'' % col)
        except sqlite3.OperationalError:
            pass
    admin = db.execute('SELECT id FROM users WHERE role=\'admin\' ORDER BY id LIMIT 1').fetchone()
    admin_id = admin['id'] if admin else None
    added = skipped = 0
    for L in LINKS:
        subj = db.execute('SELECT id FROM subjects WHERE name=?', (L['subject'],)).fetchone()
        if not subj:
            print('  WARNING  subject not found:', L['subject'], '-> skipped')
            continue
        if db.execute('SELECT 1 FROM resources WHERE external_url=?', (L['url'],)).fetchone():
            print('  SKIP (already added):', L['title'][:60])
            skipped += 1
            continue
        db.execute('''INSERT INTO resources (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,
                      uploaded_by,status,external_url,description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (L['title'], L['category'], '', '', 0, '', subj['id'], None, admin_id, 'approved',
                    L['url'], L['description']))
        print('  ADDED:', L['title'][:60])
        added += 1
    db.commit()
    total = db.execute("SELECT COUNT(*) c FROM resources WHERE external_url != ''").fetchone()['c']
    db.close()
    print('-' * 60)
    print('Done! added: %d, already-present: %d, total external link resources: %d' % (added, skipped, total))
    print('Open  Resources  page -> they show as blue  "🔗 Open original source"  cards.')

if __name__ == '__main__':
    main()
