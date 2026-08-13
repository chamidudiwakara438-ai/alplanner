#!/usr/bin/env python3
"""AL Planner content pack: Combined Mathematics real unit structure.
Replaces the two placeholder units (Pure Mathematics / Applied Mathematics)
with the 19 official-syllabus topic units (bilingual names, matched to the
student's past-paper analysis sheet). SAFE: runs only while every CM unit
has ZERO lessons; otherwise it leaves everything untouched. Idempotent."""
import os
import sqlite3

DATA = os.environ.get('AL_DATA_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB = os.path.join(DATA, 'alplanner.db')

UNITS = [
    # ---- Pure (Paper I) ----
    'Real Numbers, Functions & Inequalities – සංඛ්‍යා, ශ්‍රිත හා අසමානතා',
    'Quadratics & Polynomials – බහුපද ශ්‍රිත සහ වර්ගජ සමීකරණ',
    'Indices, Logarithms & Rational Functions – දර්ශක, ලඝුගණක හා පරිමේය ශ්‍රිත',
    'Binomial Expansion – ද්විපද ප්‍රසාරණය',
    'Series, Induction & Notations – ශ්‍රේණි, ගණිත අභ්‍යුහනය හා ආගන්ඩ් සටහන්',
    'Trigonometry – ත්‍රිකෝණමිතිය',
    'Limits & Continuity – සීමා හා අඛණ්ඩතාව',
    'Differentiation & Applications – අවකලනය හා භාවිතය',
    'Integration & Applications – අනුකලනය හා භාවිතය',
    'Complex Numbers – සංකීර්ණ සංඛ්‍යා සහ න්‍යාස',
    'Matrices – මාත්‍රිකා',
    'Straight Line & Circle – සරල රේඛාව හා වෘත්තය',
    'Permutations & Combinations – පරිවර්තන හා සංයෝජන',
    'Probability & Statistics – සම්භාවිතාව හා සංඛ්‍යානය',
    # ---- Applied (Paper II) ----
    'Vectors – දෛශික',
    'Forces, Equilibrium & Friction – බල සමතුලිතතාවය හා ඝර්ෂණය',
    'Motion: Straight Line, Relative & Projectiles – චලනය: සෘජු, සාපේක්ෂ හා ප්‍රක්ෂිප්තය',
    'Work, Energy, Power, Impulse & Collision – ජවය, ශක්තිය, ක්ෂමතාව, ආවේගය හා ගැටීම්',
    'Circular Motion, SHM & Centre of Mass – වෘත්තීය චලනය, SHM හා Centre of Mass',
]

def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT id FROM subjects WHERE lower(name)='combined mathematics'").fetchone()
    if not row:
        print('CM: subject not found - run add-subjects / start server first.')
        return
    sid = row['id']
    cur = db.execute('SELECT id,name FROM units WHERE subject_id=? ORDER BY ord', (sid,)).fetchall()
    names = [u['name'] for u in cur]
    if names == UNITS:
        print('CM: 19 topic units already in place - nothing to do.')
        return
    # safety: never delete units that hold lessons
    busy = db.execute('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?', (sid,)).fetchone()['c']
    if busy:
        print('CM: has %d lessons - unit restructure skipped (do it manually).' % busy)
        return
    db.execute('DELETE FROM units WHERE subject_id=?', (sid,))
    for i, name in enumerate(UNITS, 1):
        db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', (sid, name, i))
    db.commit()
    print('CM: placeholders replaced with %d official topic units (bilingual).' % len(UNITS))

if __name__ == '__main__':
    main()
