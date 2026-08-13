#!/usr/bin/env python3
"""
AL Planner - Chemistry video lesson pack (from the SMART AL STUDENT link list)
==============================================================================
What it does, all automatically:
  * Reorganises Chemistry into the official A/L unit structure
    (Atomic Structure, Chemical Bonding, Chemical Calculations, ... Industrial Chemistry)
  * Moves the old demo lessons into the correct new units
  * Adds every YouTube link from the list as a video lesson (~180 lessons)
  * Detects duplicate links (the list has some repeats) and adds them only once
  * Your accounts, uploads, progress and other subjects are NOT touched

Safe to run many times - already-added videos are skipped.

How to run:
  1. Stop the website (click its window, press Ctrl+C)
  2. python add-chemistry-lessons.py
     (on your PC:  & "C:\\Users\\Team Akoit\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" add-chemistry-lessons.py)
  3. Start the website again and press Ctrl+F5 in the browser
"""
import os
import re
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

RAW = r'''SMART AL STUDENT — ALL YOUTUBE LESSON LINKS

UNIT 1 — ATOMIC STRUCTURE — KALUM SENANAYAKA
1. https://youtu.be/_s7VV3u42H0
2. https://youtu.be/ehrgLl4zy_4
3. https://youtu.be/kWTPN5lk_aw
4. https://youtu.be/ggNQEyXBCqI
5. https://youtu.be/T2uVvKbX2dA
6. https://youtu.be/TyDEcBPzkEc
7. https://youtu.be/UJp-wYoZEZE
8. https://youtu.be/ht7TR3Qa2Zs
9. https://youtu.be/c8FYjU5XLck
10. https://youtu.be/Vtr1qazP7D0

UNIT 1 — OTHER LESSONS
https://youtu.be/yOOZi-DOp_Q
https://youtu.be/3A7G3bU10b4
https://youtu.be/UD8IwLo0ooc
https://youtu.be/GsbaYEJ0lyM
https://youtu.be/rhhPEYK-AHA
https://youtu.be/Vtr1qazP7D0

UNIT 2 — CHEMICAL BONDING — AMILA DASANAYAKA
https://www.youtube.com/live/D6gyAfIJ1uA
https://www.youtube.com/live/9WcBhOASpXM
https://www.youtube.com/live/eBbF4Dg2KuI
https://www.youtube.com/live/5wAPXqmBx8A
https://www.youtube.com/live/g6BCwdR0B2w
https://www.youtube.com/live/GXWUnY3q30w
https://www.youtube.com/live/W6LTBrXe1t0
https://www.youtube.com/live/cXwx-z1k6hw

UNIT 2 — CHEMICAL BONDING — NIPUN MADDUMAGE
https://www.youtube.com/live/nuMRKY49zkQ
https://www.youtube.com/live/MSEnHWVdPYI
https://www.youtube.com/live/3fpJ0GYvJjU
https://www.youtube.com/live/CubW-ivvhkY
https://www.youtube.com/live/0dSd1NX79PE
https://www.youtube.com/live/y-HEFHahZa8
https://www.youtube.com/live/lWSVCj97xAY
https://www.youtube.com/live/GDfheXiiEgo

UNIT 3 — CHEMISTRY CALCULATION — UJITH HEMACHANDRA
https://youtu.be/ivZhDjFeihM
https://youtu.be/znxjVK21MJQ
https://youtu.be/LQwdMiKZuz0
https://youtu.be/n81Cb9N2Np8
https://youtu.be/RJkZFOwKb5c
https://youtu.be/LizjRVxIOHQ
https://youtu.be/vgXIN0CuA6E
https://youtu.be/GfI4D3ZztE4
https://youtu.be/mZNlY079Y6Q
https://youtu.be/DxNvhuBoBlc
https://youtu.be/ZNhTbhroEEk
https://youtu.be/5Q4c4aNOOOw
https://youtu.be/PIA8EtfdtsQ
https://youtu.be/v8aFlLDm700
https://youtu.be/a1_jFc05u7o
https://youtu.be/Fly1Il05BXA

UNIT 3 — CHEMISTRY CALCULATION — NIPUN MADDUMAGE
https://www.youtube.com/live/O8UUZ1-7_98
https://www.youtube.com/live/vvk2YUfF1BA
https://youtu.be/svW4moYHs7c
https://www.youtube.com/live/R4dZwBOnaYU
https://www.youtube.com/live/50clkgAldSg
https://www.youtube.com/live/65LBLJdQI9w

UNIT 3 — CHEMISTRY CALCULATION — KALUM SENANAYAKA
https://youtu.be/ZOtnCNXDWjs
https://youtu.be/29NAOVDg4Uw
https://youtu.be/12pwNm0WmRY
https://youtu.be/AcvKaN06cys
https://youtu.be/M2VjV5ok9aI
https://youtu.be/XKWhZErn8bQ
https://youtu.be/-Uf4CGcRGt4
https://youtu.be/69HgyToh3fg
https://youtu.be/CDGKhU0AZt8
https://youtu.be/l0R0-VAa3rA

UNIT 3 — REDOX — AMILA / CHEMISTRY MADE EASY / UJITH
https://www.youtube.com/embed/Swwr_vNYU5s
https://www.youtube.com/live/e4SfZ533m9s
https://www.youtube.com/live/b0G3d9Z1bVQ
https://www.youtube.com/live/xH5I5nXmR0g
https://www.youtube.com/live/D2_26BqzYK0

UNIT 4 — MATTER AND ITS PROPERTIES
https://www.youtube.com/live/PsmE7MVo6Gc
https://www.youtube.com/live/re2dCpJCmUc
https://www.youtube.com/live/w7oVuHT85mc
https://www.youtube.com/live/tnH2TGLAyCg
https://www.youtube.com/live/vBKkMrLu-Kw
https://www.youtube.com/live/gQuteDAq4sI
https://www.youtube.com/live/ZNS3SiIw-qY
https://www.youtube.com/live/F1x0hTAPOpw

UNIT 4 — NIRANDIKA JAYAWARDANA
https://www.youtube.com/live/hd9W0e8c4pA
https://www.youtube.com/live/NRn5FGFetNI
https://www.youtube.com/live/FAvlBHqJujQ
https://www.youtube.com/live/7jCJr_YXWYk
https://www.youtube.com/live/Qp10EODVvkw
https://www.youtube.com/live/uA7CPGzC2ro
https://www.youtube.com/live/HKcNxwWXGso
https://www.youtube.com/live/12P9yn2n9jw
https://youtu.be/-WZ7KAYwcZE
https://youtu.be/uU_gP_MuQ04

UNIT 4 — 2024 REVISION — AMILA SIR
https://www.youtube.com/live/WrVc_wDN9C4
https://www.youtube.com/live/dFVksUk11QM
https://www.youtube.com/live/7I7nqMp0N1g
https://www.youtube.com/live/Nsos42wzTZE
https://www.youtube.com/live/Vvn37iw0_5A

UNIT 5 — ENERGETICS
https://www.youtube.com/live/F1x0hTAPOpw
https://www.youtube.com/live/5UUo1ZZEUVo
https://www.youtube.com/live/NA_1cVTxQAI
https://www.youtube.com/live/V1TpV6tO3Tw
https://www.youtube.com/live/Tn6cDNUY9uQ
https://youtu.be/EDDVXLeFDwU
https://youtu.be/OZIjLtbw5N0
https://www.youtube.com/live/Gh-22z0vIio
https://www.youtube.com/live/npPqywkX2xk
https://www.youtube.com/live/sNxb5gLx3MU
https://www.youtube.com/live/fPH1lKcGavA
https://www.youtube.com/live/Fpuq-LE9FBg
https://www.youtube.com/live/6dAgVs3LIuk
https://www.youtube.com/live/vBfqt2eQiOU
https://www.youtube.com/live/LLntj3RFmoA

UNIT 6 — INORGANIC CHEMISTRY
https://www.youtube.com/live/qirUq_fLetc
https://www.youtube.com/live/26EK1EbTykY
https://www.youtube.com/live/Nbme2eTwtas
https://www.youtube.com/live/HFEYn_HtYHk
https://www.youtube.com/live/avGPQbA7udg
https://www.youtube.com/live/cyMvFcPr3ts
https://www.youtube.com/live/zlsXa57UULc
https://youtu.be/FAIpXL-Oe6s
https://youtu.be/km9jyA31cU0
https://youtu.be/cWkJQXrZ4VY
https://youtu.be/Ddn_Gi-Qihs
https://youtu.be/UsuICKYVr_M
https://youtu.be/XAChgIY-1cM
https://youtu.be/O4uahQVUjfM
https://www.youtube-nocookie.com/embed/cBGTskrLn18?start=3

UNITS 7–10 — ORGANIC CHEMISTRY
https://www.youtube.com/live/uJWLCCZHgeo
https://www.youtube.com/live/2p7mT4-2KQc

UNIT 11 — CHEMICAL KINETICS
https://www.youtube.com/live/sxrPBaXDIxE
https://www.youtube.com/live/raueZj_rlG4
https://www.youtube.com/live/QTSSuO2DUDo
https://www.youtube.com/live/SZw6iNZ5N60
https://www.youtube.com/live/In-jbtFR6Bg
https://www.youtube.com/live/72GBVyGbJ5M
https://www.youtube.com/live/k5n2I6s_-D8
https://www.youtube.com/live/odiP40kF6Es
https://www.youtube.com/live/xKAQuWV1NyU
https://www.youtube.com/live/9s4mrkvwfGs
https://www.youtube.com/live/txDlupx3DyI
https://www.youtube.com/live/EgYY0I09TI8
https://youtu.be/UIRUpPdLzpg

UNIT 12 — EQUILIBRIUM / සමතුලිතතාවය
https://www.youtube.com/live/1Q9Gt2ZbxYw
https://www.youtube.com/live/-ueQn37phu8
https://www.youtube.com/live/fi7SmT292_I
https://www.youtube.com/live/VqbgZp-_X70
https://www.youtube.com/live/LZJFM-ZftlM
https://www.youtube.com/live/V8jQWc1mTPM
https://www.youtube.com/live/aj0Sq52OWqQ
https://youtu.be/hLafFibnA-I
https://youtu.be/6ByJ5o8xPZI
https://youtu.be/G7r5-aOiy9M
https://youtu.be/Sn6F-ReTeYM
https://youtu.be/Lt5PcCKGm4c

UNIT 13 — ELECTROCHEMISTRY
https://www.youtube.com/live/LZJFM-ZftlM
https://www.youtube.com/live/6hP1dEYx2dM
https://www.youtube.com/live/6AgJaTzzORA
https://www.youtube.com/live/DAS1XwSCexA
https://www.youtube.com/live/sxrPBaXDIxE
https://www.youtube.com/live/raueZj_rlG4
https://www.youtube.com/live/QTSSuO2DUDo
https://www.youtube.com/live/SZw6iNZ5N60
https://www.youtube.com/live/In-jbtFR6Bg

UNIT 14 — KARMANTHA RASAYANAYA
https://www.youtube.com/live/rPn_pzuTggU
https://www.youtube.com/live/jVnadv3UZpI
https://www.youtube.com/live/aUSHC_o4v3I
https://www.youtube.com/live/RnToDg0snHA
https://www.youtube.com/live/9A0LuJpY-lg
https://www.youtube.com/live/GoMoeVnCFME
https://www.youtube.com/live/r_aV8zEILhE
https://youtu.be/sFXs4ei3Wvo

UNIT 14 — NIPUN MADDUMAGE
https://www.youtube.com/live/kXVVlRGVnwo
https://www.youtube.com/live/B6eqK3NxIEQ
https://www.youtube.com/live/ERiuG4mYq_Y
https://www.youtube.com/live/r-YhqzoBN2k
https://www.youtube.com/live/dvsCKguOfX4
https://www.youtube.com/live/-DYH7yxz9-g
https://www.youtube.com/live/uS04wlOT4xU
https://www.youtube.com/live/virPGwPFzys
https://www.youtube.com/live/99ZKujmBnUI
https://www.youtube.com/live/JjqMCUWKnHo
https://www.youtube.com/live/6kVF1Cht8Jc
https://www.youtube.com/live/j6jP5_iCI3Q

UNIT 14 — UJITH HEMACHANDRA
https://www.youtube.com/live/DpDip4KEXfA
https://www.youtube.com/live/C0dhpTAuoa0
https://www.youtube.com/live/JAdbZlXh-88
https://www.youtube.com/live/MCE0wkPDOko
https://www.youtube.com/live/LCBB4uuPrKM
https://www.youtube.com/live/JPsxS5r1ucI
https://www.youtube.com/live/9QADi2OgKP8
https://www.youtube.com/live/yWviCQD13k0
https://www.youtube.com/live/oUyStKcoao0
'''

# Official G.C.E. A/L Chemistry unit structure. key = unit number in the link file.
UNIT_MAP = [
    ('1',    'Atomic Structure',           1),
    ('2',    'Chemical Bonding',           2),
    ('3',    'Chemical Calculations',      3),
    ('4',    'Matter and Its Properties',  4),
    ('5',    'Energetics',                 5),
    ('6',    'Inorganic Chemistry',        6),
    ('7-10', 'Organic Chemistry',          7),
    ('11',   'Chemical Kinetics',          8),
    ('12',   'Chemical Equilibrium',       9),
    ('13',   'Electrochemistry',           10),
    ('14',   'Industrial Chemistry',       11),
]
UNIT_NAME_BY_NO = {no: name for no, name, _ in UNIT_MAP}

TEACHER_NAMES = {
    'KALUM SENANAYAKA': 'Kalum Senanayaka',
    'AMILA DASANAYAKA': 'Amila Dasanayaka',
    'NIPUN MADDUMAGE': 'Nipun Maddumage',
    'UJITH HEMACHANDRA': 'Ujith Hemachandra',
    'NIRANDIKA JAYAWARDANA': 'Nirandika Jayawardana',
    'AMILA SIR': 'Amila Dasanayaka',
}

# Teacher photos removed on Team Akoit request (2026-08-11): placeholder portraits were
# not the real teachers. Keep this empty so fresh database builds do not link any photos;
# add real user-supplied photos here later if needed.
TEACHER_PHOTOS = {}

URL_RE = re.compile(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:live/|embed/|shorts/|watch\?v=))([A-Za-z0-9_-]{6,20})')


def parse_sections():
    """Returns list of (unit_name, teacher, tag, [youtube_ids])."""
    sections = []
    cur = None
    for line in RAW.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith('UNIT'):
            parts = [p.strip() for p in line.split('\u2014')]  # em dash
            m = re.search(r'(\d+)(?:\u2013\s*(\d+))?', parts[0])  # 'UNIT 3' or 'UNITS 7-10'
            if not m:
                cur = None
                continue
            key = m.group(1) + ('-' + m.group(2) if m.group(2) else '')
            unit_name = UNIT_NAME_BY_NO.get(key)
            if unit_name is None:
                sys.exit('Unknown unit number in line: ' + line)
            teacher = None
            tag = None
            for extra in parts[1:]:  # unit label AND/OR teacher/tag, in any position
                u = extra.upper()
                if u in TEACHER_NAMES:
                    teacher = TEACHER_NAMES[u]
                elif 'REVISION' in u:
                    tag = '2024 Revision'
                # anything else is the unit label (already known from the unit number)
            cur = [unit_name, teacher, tag, []]
            sections.append(cur)
        else:
            m = URL_RE.search(line)
            if m and cur is not None:
                cur[3].append(m.group(1))
    return sections


def teacher_id(db, name):
    row = db.execute('SELECT id FROM teachers WHERE name=?', (name,)).fetchone()
    if row:
        return row['id']
    cur = db.execute('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)',
                     (name, 'Popular G.C.E. A/L Chemistry teacher (video lessons).', 'Chemistry'))
    return cur.lastrowid


# Rules to move old demo lessons into the correct new unit, by title keyword
MOVE_RULES = [
    ('atomic', 'Atomic Structure'), ('mole', 'Chemical Calculations'),
    ('stoichiometr', 'Chemical Calculations'), ('bond', 'Chemical Bonding'),
    ('matter', 'Matter and Its Properties'), ('gas', 'Matter and Its Properties'),
    ('thermo', 'Energetics'), ('enthalp', 'Energetics'), ('energ', 'Energetics'),
    ('kinetic', 'Chemical Kinetics'), ('rate of', 'Chemical Kinetics'),
    ('equilibrium', 'Chemical Equilibrium'), ('acid', 'Chemical Equilibrium'),
    ('electro', 'Electrochemistry'), ('organic', 'Organic Chemistry'),
    ('inorganic', 'Inorganic Chemistry'), ('periodic', 'Inorganic Chemistry'),
]
FALLBACK_UNIT = 'Energetics'


def main():
    if not os.path.exists(DB):
        print('ERROR: database not found at: ' + DB)
        print('Start the website once first (run server.py), then run this file again.')
        sys.exit(1)

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    try:  # teacher-photo column, for databases created before this feature
        db.execute("ALTER TABLE teachers ADD COLUMN photo TEXT DEFAULT ''")
        db.commit()
    except sqlite3.OperationalError:
        pass

    subj = db.execute("SELECT id FROM subjects WHERE lower(name)='chemistry'").fetchone()
    if not subj:
        cur = db.execute('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)',
                         ('Chemistry', '\u0dbb\u0dc3\u0dcf\u0dba\u0db1 \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf',
                          '\u0bb5\u0bc7\u0ba4\u0bbf\u0baf\u0bbf\u0baf\u0bb2\u0bcd', 'CHEM', 'flask', '#8b5cf6', '#22d3ee'))
        subj_id = cur.lastrowid
        print('OK Chemistry subject created')
    else:
        subj_id = subj['id']

    # 1) Move old demo lessons out of 'General Chemistry' / 'Physical Chemistry' into the new units
    unit_cache = {}

    def ensure_unit(name, ord_val):
        if name in unit_cache:
            return unit_cache[name]
        row = db.execute('SELECT id FROM units WHERE subject_id=? AND name=?', (subj_id, name)).fetchone()
        if row:
            uid = row['id']
            db.execute('UPDATE units SET ord=? WHERE id=?', (ord_val, uid))
        else:
            uid = db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', (subj_id, name, ord_val)).lastrowid
        unit_cache[name] = uid
        return uid

    moved = 0
    for old in ('General Chemistry', 'Physical Chemistry'):
        row = db.execute('SELECT id FROM units WHERE subject_id=? AND name=?', (subj_id, old)).fetchone()
        if not row:
            continue
        for les in db.execute('SELECT id,title FROM lessons WHERE unit_id=?', (row['id'],)).fetchall():
            t = les['title'].lower()
            target = next((un for kw, un in MOVE_RULES if kw in t), FALLBACK_UNIT)
            tid = db.execute('SELECT id FROM units WHERE subject_id=? AND name=?', (subj_id, target)).fetchone()
            if not tid:
                tid_row = db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,0)', (subj_id, target))
                tid = {'id': tid_row.lastrowid}
            db.execute('UPDATE lessons SET unit_id=? WHERE id=?', (tid['id'], les['id']))
            moved += 1
        db.execute('DELETE FROM units WHERE id=?', (row['id'],))
    if moved:
        print('OK moved ' + str(moved) + ' old demo lessons into the new units')

    # 2) Create / reorder the official unit structure
    unit_ids = {}
    for _no, name, ord_val in UNIT_MAP:
        unit_ids[name] = ensure_unit(name, ord_val)
    print('OK Chemistry now has ' + str(len(unit_ids)) + ' official units')

    # 3) Add the video lessons (skip duplicates - inside the file and against the DB)
    teacher_cache = {}
    existing = {r['youtube_id'] for r in db.execute('SELECT youtube_id FROM lessons').fetchall() if r['youtube_id']}
    seen = set()
    added = 0
    skipped_dup = 0

    for unit_name, teacher, tag, ids in parse_sections():
        for vid in ids:
            if vid in seen or vid in existing:
                skipped_dup += 1
                continue
            seen.add(vid)
            count = db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (unit_ids[unit_name],)).fetchone()['c']
            num = '%02d' % (count + 1)
            title = unit_name + ' \u2014 ' + (tag + ' ' if tag else 'Lesson ') + num
            if teacher:
                title += ' (' + teacher + ')'
            if teacher:
                tid = teacher_cache.get(teacher) or teacher_id(db, teacher)
                teacher_cache[teacher] = tid
                desc = 'G.C.E. A/L Chemistry video lesson. Unit: ' + unit_name + '. Taught by ' + teacher + '.'
            else:
                tid = None
                desc = 'G.C.E. A/L Chemistry video lesson. Unit: ' + unit_name + '.'
            db.execute('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)',
                       (unit_ids[unit_name], tid, title, desc, vid, '', count + 1))
            existing.add(vid)
            added += 1

    # Link teacher photos (create any missing teacher rows too)
    photos_set = 0
    for _name, _path in TEACHER_PHOTOS.items():
        if not db.execute('SELECT id FROM teachers WHERE name=?', (_name,)).fetchone():
            db.execute('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)',
                       (_name, 'Popular G.C.E. A/L Chemistry teacher (video lessons).', 'Chemistry'))
        db.execute('UPDATE teachers SET photo=? WHERE name=?', (_path, _name))
        photos_set += 1

    db.commit()

    print('OK teacher photos linked (' + str(photos_set) + ' teachers)')
    print('')
    print('Summary:')
    for _no, name, _ord in UNIT_MAP:
        c = db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (unit_ids[name],)).fetchone()['c']
        vids = db.execute("SELECT COUNT(*) c FROM lessons WHERE unit_id=? AND youtube_id<>''", (unit_ids[name],)).fetchone()['c']
        print('   ' + name.ljust(28) + str(c) + ' lessons (' + str(vids) + ' videos)')
    total = db.execute('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?', (subj_id,)).fetchone()['c']
    db.close()
    print('')
    print('   TOTAL Chemistry lessons: ' + str(total) + '  |  added now: ' + str(added) + '  |  duplicate links skipped: ' + str(skipped_dup))
    print('')
    print('DONE! Start the website again and press Ctrl+F5 in the browser:')
    print('   http://localhost:3000/#/subject/1')


if __name__ == '__main__':
    main()
