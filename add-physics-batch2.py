#!/usr/bin/env python3
"""AL Planner content pack: Physics WhatsApp batch 2 (user-sent, verified via oEmbed/yt-dlp).
Adds ONLY the new videos from Chamidu's 09/08/2026 forward.
Idempotent: skips youtube_ids already present. Safe on every startup."""
import os, sqlite3

DATA = os.environ.get('AL_DATA_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB = os.path.join(DATA, 'alplanner.db')

import json
NEW = json.loads('[\n [\n  "8hMproLb1n8",\n  11,\n  "Ushan Gunasekara",\n  "Live 🔴 පදාර්ථ හා විකිරණ | අංශු භෞතික විද්\u200dයාව සම්පූර්ණයෙන්ම"\n ],\n [\n  "c4n9gpuJIlE",\n  10,\n  "Ushan Gunasekara",\n  "🔴 LIVE |  දුස්ස්\u200dරාවීතාව සහ ප්\u200dරත්\u200dයස්ථතාව සම්පූර්ණයෙන්ම"\n ],\n [\n  "GkDOGRJHReU",\n  3,\n  "Anuradha Perera",\n  "ආලෝකය Practical Day LIVE | Physics | Anuradha Perera"\n ],\n [\n  "AUqp4TDzL_0",\n  3,\n  "Anuradha Perera",\n  "🔴ආලෝකය PRACTICAL 2026 | PHYSICS | ANURADHA PERERA"\n ],\n [\n  "8m-PkrrQ_B8",\n  3,\n  "Nilantha Jayasuriya",\n  "A/L Physics | Nilantha Jayasuriya || 2026 Theory ආලෝකය Practical 01"\n ],\n [\n  "endTzqhHWf0",\n  3,\n  "Anuradha Perera",\n  "🔴 වර්ණාවලිමානය PRACTICAL 2026 | PHYSICS | ANURADHA PERERA"\n ],\n [\n  "ykDPlFAg8HQ",\n  4,\n  "Nirosh Malinga (Physics)",\n  "තාපය සම්පූර්ණ පාඩම AL Physics - Nirosh Malinga"\n ],\n [\n  "T-ZFMuBQaw0",\n  5,\n  "Ushan Gunasekara",\n  "🔴 LIVE | ගුරුත්වාකර්ශණ හා විද්\u200dයුත් ක්ෂේත්\u200dර සම්පූර්ණයෙන්ම"\n ],\n [\n  "YYWLIAKo3lA",\n  5,\n  "Aruna Pallekumbura",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර සම්පූර්ණ ඒකකයේ සාරාංශය - පැයෙන්"\n ],\n [\n  "PE-Q_9UexpY",\n  10,\n  "Samitha Rathnayake",\n  "පදාර්ථයේ යාන්ත්\u200dරික ගුණ ✨ | Mechanical Properties of Matter Speed Revision ❤️\u200d🔥 | Samitha Rathnayake"\n ],\n [\n  "vJ-nqTvONkI",\n  7,\n  "Samitha Rathnayake",\n  "චුම්භක ක්ෂේත්\u200dරය ✨ | Magnetic Field Speed Revision ❤️\u200d🔥 | Samitha Rathnayake"\n ],\n [\n  "H3onizMyNQo",\n  6,\n  "Samitha Rathnayake",\n  "විද්\u200dයුත් ක්ෂේත්\u200dරය ✨ | Electric Field Speed Revision ❤️\u200d🔥 | Samitha Rathnayake"\n ],\n [\n  "YYaq1ebMSTY",\n  5,\n  "Samitha Rathnayake",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dරය ✨️ | Gravitational Field  Spreed Revision ❤️\u200d🔥#Samitha_rathnayake #physics"\n ],\n [\n  "ZUdIxitTeoo",\n  5,\n  "Mahen Jecob",\n  "Mahen Jecob | ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | පසුගිය විභාග බහුවරණ විවරණය"\n ],\n [\n  "XgL_tY2jAoI",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන බහුවරණ විවරණය - 01"\n ],\n [\n  "8-Vw7LMCgoQ",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන බහුවරණ විවරණය - 02"\n ],\n [\n  "Cb44hUvpQjo",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන බහුවරණ විවරණය - 03"\n ],\n [\n  "-FuorCTv2aw",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන බහුවරණ විවරණය - 04"\n ],\n [\n  "wsLgXe2ofUc",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන බහුවරණ විවරණය - 05"\n ],\n [\n  "e9tusTr6vDU",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන මිශ්\u200dර අභ්\u200dයාස විවරණය - 01"\n ],\n [\n  "627Wjc22DzY",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන මිශ්\u200dර අභ්\u200dයාස විවරණය - 02"\n ],\n [\n  "_qTmFawxJMg",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන මිශ්\u200dර අභ්\u200dයාස විවරණය - 03"\n ],\n [\n  "rcAeYLwlnTQ",\n  5,\n  "Mahen Jecob",\n  "ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර නිබන්ධන මිශ්\u200dර අභ්\u200dයාස විවරණය - 04"\n ],\n [\n  "PK9cWqXFcLA",\n  5,\n  "Mahen Jecob",\n  "Jecob Sir & Pantaleon Sir | Episode 05 |  ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර"\n ]\n]')

DESC_EN = 'G.C.E. A/L Physics video lesson. Unit: %s. Taught by %s.'
DESC_SI = 'G.C.E. \u0d92/\u0dbd\u0dca \u0dad\u0dd9\u0dc0\u0dd2\u0dbd\u0dca \u0dc0\u0dd3\u0daf\u0dd2\u0dba\u0ddd \u0db4\u0dcf\u0da9\u0db8. \u0d92\u0d9a\u0d9a\u0dba: %s.'

def main():
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    teachers = {r['name']: r['id'] for r in db.execute('SELECT id,name FROM teachers')}
    units = {r['ord']: (r['id'], r['name']) for r in db.execute('SELECT id,ord,name FROM units WHERE subject_id=4')}
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
        desc = DESC_EN % (uname, teacher) + '\n' + DESC_SI % uname
        db.execute('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)',
                   (u_id, tid, title, desc, vid, '', cnt + 1))
        existing.add(vid); added += 1
    db.commit()
    tot = db.execute('SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=4').fetchone()[0]
    print('Batch2 physics: added %d, skipped %d already-present. Physics lessons total: %d.' % (added, skipped, tot))
    db.close()

if __name__ == '__main__':
    main()
