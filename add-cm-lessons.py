#!/usr/bin/env python3
"""AL Planner content pack: Combined Mathematics WhatsApp batch 1 (user-sent 2026-08-10, verified via yt-dlp).
Unit 5 (Series, Induction & Notations): 16 lessons
  - Ruwan Darshana: 2020 A/L Mathematical Induction EP 01-05 (playlist PL1NlDyWKZZADbyW92WqE9jBGCyB9G_h5J)
  - Thilina Welikala: Induction THEORY Part 01-05 + Past Paper Discussions 2019-2022 (playlist PLJJ5Ev35xYMHrnHHxGf19SgQ-hsUyJav0)
  - Janindu Rashmika: Induction sampurna padama (xiyzi8dnPg8, 4.4h)
  - Tharaka B Jayathilake: Induction siyalu getalu rata (fbC7V4YYxuU live, 2.3h)
Unit 1 (Real Numbers, Functions & Inequalities): 6 lessons
  - Ruwan Darshana: 2023 Revision Maapanka Asamanatha 1-6 (playlist PLuiSHx6XLn9SYJpORQeU7PgFwbkyTsc4v)
Teachers created if missing: Ruwan Darshana, Thilina Welikala, Janindu Rashmika, Tharaka B Jayathilake.
Idempotent: skips youtube_ids already present. Safe on every startup."""
import os, sqlite3

DATA = os.environ.get('AL_DATA_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB = os.path.join(DATA, 'alplanner.db')

NEW_TEACHERS = [
    ["Ruwan Darshana", "Popular G.C.E. A/L Combined Mathematics teacher (Combined Maths Ruwan Darshana YouTube channel)."],
    ["Thilina Welikala", "G.C.E. A/L Combined Mathematics teacher (Thilina Welikala - Combined Maths)."],
    ["Janindu Rashmika", "G.C.E. A/L Combined Mathematics teacher (Combined Maths | Janindu Rashmika)."],
    ["Tharaka B Jayathilake", "G.C.E. A/L Combined Mathematics teacher (Tharaka B Jayathilake - Combined Maths)."],
]

# [youtube_id, unit_ord, teacher, title]
NEW = [
    # --- Unit 5: Induction (Ruwan Darshana 2020 A/L series) ---
    ["rI0LD5Ij_OU", 5, "Ruwan Darshana", "2020 A/L Mathematical Induction | ගණිත අභ්‍යුහනය Episode 01"],
    ["4Cyt3BGdfiY", 5, "Ruwan Darshana", "2020 A/L Mathematical Induction | ගණිත අභ්‍යුහනය Episode 02"],
    ["tTeVjJg0Ylg", 5, "Ruwan Darshana", "2020 A/L Mathematical Induction | ගණිත අභ්‍යුහනය Episode 03"],
    ["pnZeuIykYZY", 5, "Ruwan Darshana", "2020 A/L Mathematical Induction | ගණිත අභ්‍යුහනය Episode 04"],
    ["dleoymSx7jc", 5, "Ruwan Darshana", "2020 A/L Mathematical Induction | ගණිත අභ්‍යුහනය Episode 05"],
    # --- Unit 5: Induction (Thilina Welikala theory + past papers) ---
    ["dJDo7HRt-fE", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Part 01 | THEORY | Combined Maths"],
    ["Tkh_drSqXyo", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Part 02 | THEORY | Combined Maths"],
    ["nhkM80EljrY", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Part 03 | THEORY | Combined Maths"],
    ["9aEsjRXZp-o", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Part 04 | THEORY | Combined Maths"],
    ["WT1JjtdAzwc", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Part 05 | THEORY | Combined Maths"],
    ["DhwQUqzlmpg", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Past Paper Discussion | 2019 | Combined Maths"],
    ["ZW4AD_FhpzQ", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Past Paper Discussion | 2020 | Combined Maths"],
    ["zHGDl5Gbfmc", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Past Paper Discussion | 2021 | Combined Maths"],
    ["y3Tdy_dfIVE", 5, "Thilina Welikala", "ගණිත අභ්‍යුහනය | Mathematical Induction | Past Paper Discussion | 2022 | Combined Maths"],
    # --- Unit 5: Induction full-lesson one-shots ---
    ["xiyzi8dnPg8", 5, "Janindu Rashmika", "Combined Maths 2023 A/L | Mathematical Induction | ගණිත අභ්‍යුහනය | සම්පූර්ණ පාඩම | Janindu Rashmika"],
    ["fbC7V4YYxuU", 5, "Tharaka B Jayathilake", "ගණිත අභ්‍යූහණය සියලු ගැටළු රටා ✅ | Tharaka B Jayathilake"],
    # --- Unit 1: Maapanka Asamanatha (Ruwan Darshana 2023 Revision) ---
    ["IiUq-pbD1-A", 1, "Ruwan Darshana", "2023 Revision - Day 01 - මාපාංක අසමානතා 1 | Combined Maths"],
    ["Ruq1WGd0HHA", 1, "Ruwan Darshana", "2023 Revision - Day 01 - මාපාංක අසමානතා 2 | Combined Maths"],
    ["abdpO40Op60", 1, "Ruwan Darshana", "2023 Revision - Day 02 - මාපාංක අසමානතා 3 | Combined Maths"],
    ["ST6WrUGq8xQ", 1, "Ruwan Darshana", "2023 Revision - Day 03 - මාපාංක අසමානතා 4 | Combined Maths"],
    ["7Yr4XoDqk7Q", 1, "Ruwan Darshana", "2023 Revision - Day 04 - මාපාංක අසමානතා 5 | Combined Maths"],
    ["XLLUGPEWKB0", 1, "Ruwan Darshana", "2023 Revision - Day 05 - මාපාංක අසමානතා 6 (මාපාංක ප්‍රස්තාර) | Combined Maths"],
]

DESC_EN = 'G.C.E. A/L Combined Mathematics video lesson. Unit: %s. Taught by %s.'
DESC_SI = 'G.C.E. උසස් පෙළ සංයුක්ත ගණිතය වීඩියෝ පාඩම. ඒකකය: %s. ගුරුවරයා: %s.'

def main():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    for name, bio in NEW_TEACHERS:
        if not db.execute('SELECT 1 FROM teachers WHERE name=?', (name,)).fetchone():
            db.execute('INSERT INTO teachers (name,bio,subjects,photo) VALUES (?,?,?,?)',
                       (name, bio, 'Combined Mathematics', ''))
            db.commit()
            print('  + teacher created:', name)
    teachers = {r['name']: r['id'] for r in db.execute('SELECT id,name FROM teachers')}
    units = {r['ord']: (r['id'], r['name']) for r in db.execute('SELECT id,ord,name FROM units WHERE subject_id=2')}
    existing = {r[0] for r in db.execute("SELECT youtube_id FROM lessons WHERE youtube_id<>''")}
    added = skipped = 0
    for vid, ord_unit, teacher, title in NEW:
        if vid in existing:
            skipped += 1
            continue
        u = units.get(ord_unit); tid = teachers.get(teacher)
        if not u or not tid:
            print('  WARN missing unit/teacher for', vid, ord_unit, teacher); continue
        u_id, uname = u
        cnt = db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (u_id,)).fetchone()['c']
        desc = DESC_EN % (uname, teacher) + '\n' + DESC_SI % (uname, teacher)
        db.execute('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)',
                   (u_id, tid, title, desc, vid, '', cnt + 1))
        existing.add(vid); added += 1
    db.commit()
    tot = db.execute('SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=2').fetchone()[0]
    print('CM batch1: added %d, skipped %d already-present. CM lessons total: %d.' % (added, skipped, tot))
    db.close()

if __name__ == '__main__':
    main()
