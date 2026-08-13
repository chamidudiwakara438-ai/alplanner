#!/usr/bin/env python3
"""
AL Planner — Lesson CONTENT pack  (Theory tab + MCQ practice questions)
========================================================================
Every lesson page now has tabs under the video:
    Overview | Theory | MCQ Questions | Downloads

This file fills in STARTER content so you can see how it works:
  * Theory notes for 5 Chemistry lessons
  * 22 practice MCQs (with explanations) across 5 lessons

HOW TO ADD YOUR OWN CONTENT (2 easy ways)
-----------------------------------------
  WAY 1 — inside the website (easiest!):
      Sign in as admin (admin@alplanner.lk / admin123) -> open any lesson ->
      click the "Theory" tab  -> "Edit theory" -> type -> Save.
      click the "MCQ Questions" tab -> use the "Add a question" box at the bottom.

  WAY 2 — with this file (for many lessons at once):
      1. Scroll down to the CONTENT list below and copy one of the {...} blocks.
      2. Change  match  to the start of your lesson's title.
      3. Save this file, stop the website (Ctrl+C in the black window) and run:
             python add-lesson-tabs.py
         (on your PC if plain "python" misbehaves:
          & "C:\\Users\\Team Akoit\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" add-lesson-tabs.py)
      4. Start the website again and press Ctrl+F5 in the browser.

Safe to run many times: for each lesson listed below it REPLACES that lesson's
theory + questions with what's written here (nothing else is touched).
"""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

# ----------------------------------------------------------------------------
# CONTENT — one block per lesson.
#   match     : first words of the lesson title (must match ONE lesson)
#   theory    : text for the Theory tab (blank lines are fine)
#   questions : list of (question, optionA, optionB, optionC, optionD, correct, explanation)
#               correct = 1 for A, 2 for B, 3 for C, 4 for D
# ----------------------------------------------------------------------------
LETTERS = ('a', 'b', 'c', 'd')

CONTENT = [
    {
        'match': 'Atomic Structure & Electronic Configuration',
        'theory': """ATOMIC STRUCTURE — KEY THEORY

The atom
- An atom has a tiny, dense, positively charged nucleus (protons + neutrons) surrounded by electrons in energy levels (shells).
- Proton: charge +1, mass ~1 u.   Neutron: charge 0, mass ~1 u.   Electron: charge -1, mass ~1/1836 u.

Atomic number and mass number
- Atomic number (Z) = number of protons = number of electrons in a neutral atom.
- Mass number (A) = protons + neutrons.
- Number of neutrons = A - Z.

Isotopes
- Isotopes are atoms of the same element (same Z) with different numbers of neutrons (different A).
- They have identical chemical properties (same electron arrangement) but slightly different physical properties.
- Example: 12C, 13C and 14C are isotopes of carbon.

Electronic configuration
- Maximum electrons in shell n = 2n^2  (K=2, L=8, M=18).
- Electrons fill shells from the lowest energy level outwards; the outer shell (valence electrons) controls chemical behaviour.

Exam tips
- Always show working for A - Z calculations.
- In ions, electrons change but protons stay the same (Z never changes).""",
        'questions': [
            ('The atomic number of an element is the number of…',
             'neutrons in the nucleus', 'protons in the nucleus', 'protons + neutrons', 'electrons in the outer shell only',
             2, 'Atomic number (Z) = number of protons. In a neutral atom it also equals the number of electrons.'),
            ('Isotopes of the same element have the same number of protons but different numbers of…',
             'electrons', 'neutrons', 'shells', 'valence electrons',
             2, 'Isotopes = same Z, different mass numbers, so the neutron count (A - Z) differs.'),
            ('The maximum number of electrons that can occupy the M shell (n = 3) is…',
             '2', '8', '18', '32',
             3, 'Maximum capacity = 2n^2 = 2 x 9 = 18.'),
            ('An atom of 23Na (mass number 23, atomic number 11) contains how many neutrons?',
             '11', '12', '23', '34',
             2, 'Neutrons = A - Z = 23 - 11 = 12.'),
            ('Which particle has a relative mass of about 1/1836 and a charge of -1?',
             'Proton', 'Neutron', 'Electron', 'Alpha particle',
             3, 'The electron is ~1836 times lighter than a proton and carries charge -1.'),
        ],
    },
    {
        'match': 'Chemical Bonding — Lesson 01',
        'theory': """CHEMICAL BONDING — KEY THEORY

Why atoms bond
- Atoms bond to achieve a stable (noble gas) electron arrangement — usually a full outer shell (octet / duplet).

Ionic bonding (metal + non-metal)
- Electrons are TRANSFERRED from metal to non-metal, forming cations (+) and anions (-).
- Held by strong electrostatic attraction. e.g. NaCl, MgO, CaCl2.
- Properties: high m.p., crystalline solids, conduct electricity when molten or in solution.

Covalent bonding (non-metal + non-metal)
- Electrons are SHARED in pairs. e.g. H2, Cl2, CH4, CO2.
- A single bond = 1 shared pair; double bond = 2 pairs (O=C=O); triple bond = 3 pairs.
- Simple molecules: low m.p., do not conduct. Giant covalent (diamond, SiO2): very hard, high m.p.

Metallic bonding
- Lattice of metal cations in a 'sea' of delocalised electrons -> conducts electricity and heat; malleable.

Exam tips
- Draw dot-and-cross diagrams with the full outer shell only.
- Remember: MgCl2 needs TWO Cl- ions per Mg2+.""",
        'questions': [
            ('Sodium chloride (NaCl) is best described as…',
             'a covalent molecule', 'an ionic compound', 'a metallic solid', 'a hydrogen-bonded liquid',
             2, 'A metal (Na) + non-metal (Cl) -> electron transfer -> ionic lattice.'),
            ('A covalent bond is formed when atoms…',
             'transfer electrons completely', 'share a pair of electrons', 'lose all valence electrons', 'attract by van der Waals forces only',
             2, 'Covalent = sharing of electron pairs between non-metal atoms.'),
            ('Carbon dioxide (CO2) contains which bonds between carbon and oxygen?',
             'Two single bonds', 'One single and one triple', 'Two double bonds', 'One ionic and one covalent',
             3, 'O=C=O : carbon forms a double bond with each oxygen atom.'),
            ('Which property is typical of an ionic compound?',
             'Low melting point', 'Conducts electricity when molten', 'Soft and easily bent', 'Does not dissolve in water',
             2, 'Ions are free to move when molten or in solution, so ionic compounds then conduct.'),
            ('Metals conduct electricity because they contain…',
             'ions free to move', 'delocalised electrons', 'shared electron pairs', 'protons free to move',
             2, "The 'sea' of delocalised electrons carries the current through the metal lattice."),
        ],
    },
    {
        'match': 'The Mole Concept & Stoichiometry',
        'theory': """CHEMICAL CALCULATIONS — THE MOLE TOOLKIT

The core formulas
- n = m / M        (moles = mass in grams / molar mass)
- c = n / V        (concentration in mol dm-3 = moles / volume in dm3)
- n = V / 22.4     (moles of gas = volume in dm3 / 22.4 dm3 mol-1 at STP)
- Number of particles = n x L   (L = Avogadro constant = 6.022 x 10^23 mol-1)

Molar mass
- M of a compound = sum of relative atomic masses. e.g. M(H2O) = 2(1) + 16 = 18 g mol-1.
- Worked example: moles in 36 g of water = m/M = 36/18 = 2 mol.

Concentration
- c = n/V with V in dm3  (1000 cm3 = 1 dm3).
- Worked example: 0.5 mol in 250 cm3 -> V = 0.25 dm3 -> c = 0.5/0.25 = 2 mol dm-3.

Stoichiometry (mole ratios)
- Read the ratio straight from the balanced equation.
- e.g. N2 + 3H2 -> 2NH3 : 1 mol N2 needs 3 mol H2 and gives 2 mol NH3.

Exam tips
- Convert cm3 to dm3 (divide by 1000) BEFORE using c = n/V.
- Keep 3 significant figures and always write the unit.""",
        'questions': [
            ('How many moles are there in 18 g of water? (H = 1, O = 16)',
             '0.5 mol', '1 mol', '2 mol', '18 mol',
             2, 'n = m/M = 18/18 = 1 mol.'),
            ('The volume occupied by 1 mole of any gas at STP is…',
             '1 dm3', '11.2 dm3', '22.4 dm3', '24 dm3',
             3, 'Molar gas volume at STP = 22.4 dm3 mol-1.'),
            ('A solution contains 0.25 mol of NaOH in 500 cm3. Its concentration is…',
             '0.125 mol dm-3', '0.25 mol dm-3', '0.5 mol dm-3', '2 mol dm-3',
             3, 'V = 500 cm3 = 0.5 dm3;  c = n/V = 0.25/0.5 = 0.5 mol dm-3.'),
            ('The Avogadro constant is…',
             '6.022 x 10^23 mol-1', '8.314 J K-1 mol-1', '22.4 dm3 mol-1', '1.6 x 10-19 C',
             1, 'L = 6.022 x 10^23 particles per mole.'),
            ('In the reaction N2 + 3H2 -> 2NH3, 1 mol of N2 reacts completely with…',
             '1 mol of H2', '2 mol of H2', '3 mol of H2', '6 mol of H2',
             3, 'The balanced equation shows the ratio N2 : H2 = 1 : 3.'),
        ],
    },
    {
        'match': 'Chemical Thermodynamics & Enthalpy',
        'theory': """ENERGETICS — KEY THEORY

Exothermic vs endothermic
- Exothermic: releases heat to the surroundings, DeltaH is NEGATIVE. e.g. combustion, neutralisation.
- Endothermic: absorbs heat, DeltaH is POSITIVE. e.g. thermal decomposition, photosynthesis.

Enthalpy change (DeltaH)
- DeltaH = H(products) - H(reactants).
- Exothermic pathway: reactants ABOVE products on the energy diagram.
- Activation energy (Ea) = energy from reactants up to the peak (must be supplied to start).

Bond breaking and making
- Breaking bonds ABSORBS energy; making bonds RELEASES energy.
- DeltaH ~ (energy to break bonds) - (energy released making bonds).
- If more energy is released making bonds than used breaking them, the reaction is exothermic.

Calorimetry
- q = mcDeltaT   (m = mass of solution, c = 4.2 J g-1 C-1 for water, DeltaT = temperature change).

Exam tips
- State the sign of DeltaH in every answer.
- A catalyst lowers Ea but does NOT change DeltaH.""",
        'questions': [
            ('An exothermic reaction…',
             'absorbs heat and has a positive DeltaH', 'releases heat and has a negative DeltaH',
             'always needs a catalyst', 'has products above reactants on the energy diagram',
             2, 'Exothermic = heat given out, so H(products) < H(reactants) and DeltaH < 0.'),
            ('Bond breaking is always…',
             'exothermic', 'endothermic', 'neutral', 'spontaneous',
             2, 'Energy must be supplied to break bonds, so bond breaking is endothermic.'),
            ('The activation energy of a reaction is…',
             'the energy of the products', 'the energy given out overall',
             'the energy needed to reach the top of the energy barrier', 'the energy in one mole of gas at STP',
             3, 'Ea is the gap from the reactants up to the peak of the energy profile.'),
            ('A catalyst speeds up a reaction by…',
             'increasing DeltaH', 'lowering the activation energy', 'increasing the temperature',
             'shifting the equilibrium to the right',
             2, 'A catalyst provides an alternative pathway of lower Ea; DeltaH is unchanged.'),
            ('50 g of water is heated and its temperature rises by 10 C. Heat absorbed is… (c = 4.2 J g-1 C-1)',
             '210 J', '420 J', '2100 J', '4200 J',
             3, 'q = mcDeltaT = 50 x 4.2 x 10 = 2100 J.'),
        ],
    },
    {
        'match': 'Chemical Equilibrium — Lesson 01',
        'theory': """CHEMICAL EQUILIBRIUM — KEY THEORY

Dynamic equilibrium
- In a closed system, forward and reverse reactions continue at EQUAL rates; concentrations stay constant.

Le Chatelier's principle
- If a constraint (change of concentration, pressure or temperature) is imposed on a system at equilibrium,
  the system adjusts so as to oppose that constraint.

Predicting the shift
- Concentration: add a reactant -> shifts to the RIGHT (uses it up).
- Pressure (gases only): increase pressure -> shifts to the side with FEWER moles of gas.
- Temperature: increase T -> shifts in the ENDOTHERMIC direction.

The equilibrium constant Kc
- For aA + bB <=> cC + dD :  Kc = [C]^c [D]^d / [A]^a [B]^b
- Kc changes ONLY with temperature.
- Big Kc -> products favoured; small Kc -> reactants favoured.

Industrial example — Haber process
- N2 + 3H2 <=> 2NH3, DeltaH < 0.
- High pressure (~200 atm): more NH3 (fewer gas moles on right).
- Low temperature favours yield but is slow -> compromise ~450 C plus iron catalyst.

Exam tips
- Catalyst does NOT change Kc or the position of equilibrium — it only speeds up attainment.
- Write Kc expressions without solids or pure liquids.""",
        'questions': [
            ('At dynamic equilibrium…',
             'both reactions stop', 'only the forward reaction continues',
             'forward and reverse reactions occur at equal rates', 'the products are all used up',
             3, 'Dynamic = both processes continue, at the same rate, so concentrations stay constant.'),
            ('For N2 + 3H2 <=> 2NH3, increasing the pressure shifts the equilibrium…',
             'to the left', 'to the right', 'no change', 'only if a catalyst is present',
             2, 'Right side has 2 moles of gas vs 4 on the left; higher pressure favours the side with fewer moles.'),
            ('Raising the temperature of an exothermic equilibrium shifts it…',
             'to the right', 'to the left (endothermic direction)', 'no change', 'completely to completion',
             2, 'The system opposes the rise by moving in the endothermic (heat-absorbing) direction.'),
            ('The value of Kc for a reaction is changed only by…',
             'adding a catalyst', 'changing the temperature', 'changing the pressure', 'adding more reactant',
             2, 'Kc depends only on temperature — concentration, pressure and catalysts do not alter it.'),
        ],
    },
]

def qrow(lesson_id, item, ord_):
    q, a, b, c, d, correct, exp = item
    exp = exp if len(item) > 6 else ''
    return (lesson_id, q, a, b, c, d, LETTERS[correct - 1], exp, ord_)

def main():
    if not os.path.exists(DB):
        print('ERROR: database not found at', DB)
        print('Start the website once first, then run this file again.')
        raise SystemExit(1)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    try:
        db.execute("ALTER TABLE lessons ADD COLUMN theory TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    db.execute("""CREATE TABLE IF NOT EXISTS lesson_questions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
      q TEXT NOT NULL, a TEXT DEFAULT '', b TEXT DEFAULT '', c TEXT DEFAULT '', d TEXT DEFAULT '',
      answer TEXT DEFAULT 'a', explanation TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')))""")

    done_t, done_q, skipped = 0, 0, []
    for blk in CONTENT:
        m = blk['match']
        rows = db.execute('SELECT id, title FROM lessons WHERE title LIKE ?', (m + '%',)).fetchall()
        if not rows:
            skipped.append(m)
            continue
        lid = rows[0]['id']
        db.execute('UPDATE lessons SET theory=? WHERE id=?', (blk.get('theory', ''), lid))
        db.execute('DELETE FROM lesson_questions WHERE lesson_id=?', (lid,))
        for i, item in enumerate(blk.get('questions', []), 1):
            db.execute('INSERT INTO lesson_questions (lesson_id,q,a,b,c,d,answer,explanation,ord) VALUES (?,?,?,?,?,?,?,?,?)',
                       qrow(lid, item, i))
        done_t += 1
        done_q += len(blk.get('questions', []))
        print('  OK  #%d  %-52s theory + %d questions' % (lid, rows[0]['title'][:52], len(blk.get('questions', []))))
    for m in skipped:
        print('  WARNING  no lesson starting with "%s" — skipped.' % m)
    db.commit()
    qt = db.execute('SELECT COUNT(*) c FROM lesson_questions').fetchone()['c']
    th = db.execute("SELECT COUNT(*) c FROM lessons WHERE theory != ''").fetchone()['c']
    db.close()
    print('-' * 60)
    print('Done! %d lessons got theory, %d questions written this run.' % (done_t, done_q))
    print('Whole site now has: %d lessons with theory, %d MCQ questions.' % (th, qt))
    print('Open any of those lessons -> Theory / MCQ Questions tabs.')

if __name__ == '__main__':
    main()
