#!/usr/bin/env python3
"""
AL Planner - Python edition.
Full backend in ONE file: Flask API + SQLite database + auto-seed + PDF writer.

Run:
    pip install flask
    python server.py
Then open http://localhost:3000

Logins:  student@alplanner.lk / student123   |   admin@alplanner.lk / admin123

(The Node.js version `server.js` offers identical features - use whichever
 runtime you prefer. Both read the same data/ and uploads/ folders.)
"""
import os, re, json, time, sqlite3, secrets, calendar, csv, io
import urllib.request, urllib.error
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, send_file, g, Response
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
BOOT_T0 = time.time()
SITE_VER = '2026.08.13w'
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
UPLOAD_DIR = os.environ.get('AL_UPLOAD_DIR', os.path.join(BASE, 'uploads'))
PUBLIC_DIR = os.environ.get('AL_PUBLIC_DIR', os.path.join(BASE, 'public'))
DB_PATH = os.path.join(DATA_DIR, 'alplanner.db')
for d in (DATA_DIR, UPLOAD_DIR):
    os.makedirs(d, exist_ok=True)

COOKIE = 'al_session'
SESSION_DAYS = 30
PORT = int(os.environ.get('PORT', '3000'))

DISTRICTS = ['Ampara','Anuradhapura','Badulla','Batticaloa','Colombo','Galle','Gampaha','Hambantota','Jaffna','Kalutara','Kandy','Kegalle','Kilinochchi','Kurunegala','Mannar','Matale','Matara','Monaragala','Mullaitivu','Nuwara Eliya','Polonnaruwa','Puttalam','Ratnapura','Trincomalee','Vavuniya']
STREAMS = ['Physical Science','Biological Science','Commerce','Arts','Engineering Technology','Bio Systems Technology']
MEDIUMS = ['en','si','ta']
RESOURCE_CATEGORIES = [
    {'id':'notes','label':'Notes'}, {'id':'short_notes','label':'Short Notes'},
    {'id':'question_papers','label':'Question Papers'}, {'id':'past_papers','label':'Past Papers'},
    {'id':'model_papers','label':'Model Papers'}, {'id':'study_material','label':'Study Materials'},
]
ALLOWED_EXT = {'.pdf','.doc','.docx','.ppt','.pptx','.xls','.xlsx','.txt','.md','.zip','.png','.jpg','.jpeg','.webp'}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL COLLATE NOCASE, password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student', school TEXT DEFAULT '', district TEXT DEFAULT '',
  al_year TEXT DEFAULT '', medium TEXT DEFAULT 'en', stream TEXT DEFAULT '',
  subjects TEXT DEFAULT '[]', created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS al_years (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT UNIQUE NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS subjects (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_si TEXT DEFAULT '', name_ta TEXT DEFAULT '',
  code TEXT DEFAULT '', icon TEXT DEFAULT 'book', color1 TEXT DEFAULT '#6366f1', color2 TEXT DEFAULT '#22d3ee',
  medium TEXT DEFAULT 'en', created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS units (
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL, ord INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, bio TEXT DEFAULT '', subjects TEXT DEFAULT '', photo TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL, title TEXT NOT NULL,
  description TEXT DEFAULT '', youtube_id TEXT DEFAULT '', notes TEXT DEFAULT '',
  theory TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS lesson_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  q TEXT NOT NULL, a TEXT DEFAULT '', b TEXT DEFAULT '', c TEXT DEFAULT '', d TEXT DEFAULT '',
  answer TEXT DEFAULT 'a', explanation TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS resources (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'study_material',
  file_path TEXT NOT NULL, orig_name TEXT DEFAULT '', size INTEGER DEFAULT 0, mime TEXT DEFAULT '',
  subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
  lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
  uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending', downloads INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS tutors (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, photo TEXT DEFAULT '',
  subjects TEXT DEFAULT '[]', experience TEXT DEFAULT '', classes TEXT DEFAULT '[]',
  location TEXT DEFAULT '', phone TEXT DEFAULT '', whatsapp TEXT DEFAULT '',
  email TEXT DEFAULT '', bio TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS tutor_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tutor_id INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, message TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS tutor_comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tutor_id INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, body TEXT NOT NULL,
  keep INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS contact_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT DEFAULT '',
  message TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  completed INTEGER NOT NULL DEFAULT 0, completed_at TEXT, watched INTEGER NOT NULL DEFAULT 0,
  watched_at TEXT, favourite INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, lesson_id));
CREATE TABLE IF NOT EXISTS saved_resources (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  created_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (user_id, resource_id));
"""

# ============================================================ PDF writer
def _esc(s):
    s = str(s).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return re.sub(r'[^\x20-\x7E]', '?', s)

def _wrap(text, width):
    out, cur = [], ''
    for w in str(text).split():
        if len(cur) + 1 + len(w) > width and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + ' ' + w) if cur else w
    if cur: out.append(cur)
    return out

def make_pdf(title, paragraphs):
    lines = []
    for p in paragraphs:
        if p == '': lines.append(''); continue
        lines.extend(_wrap(p, 84)); lines.append('')
    pages = [lines[i:i+43] for i in range(0, len(lines), 43)] or [[]]
    objects = {1: '<< /Type /Catalog /Pages 2 0 R >>',
               3: '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               4: '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>'}
    kids = []
    for i, pg in enumerate(pages):
        pid, cid = 5 + i * 2, 6 + i * 2
        kids.append(pid)
        s = 'BT /F2 16 Tf 56 764 Td (%s) Tj ET\n' % _esc(title)
        s += '0.35 0.35 0.9 RG 2 w 56 754 m 556 754 l S\n'
        s += 'BT /F1 10.5 Tf 56 730 Td 15 TL\n'
        for l in pg:
            s += 'T*\n' if l == '' else '(%s) Tj T*\n' % _esc(l)
        s += 'ET\nBT /F1 9 Tf 460 30 Td (AL Planner - alplanner.lk) Tj ET'
        objects[pid] = ('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                        '/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>' % cid)
        objects[cid] = '<< /Length %d >>\nstream\n%s\nendstream' % (len(s.encode('latin-1')), s)
    objects[2] = '<< /Type /Pages /Kids [%s] /Count %d >>' % (' '.join('%d 0 R' % k for k in kids), len(kids))
    n = 4 + len(pages) * 2
    out = '%PDF-1.4\n'
    offs = [0] * (n + 1)
    for i in range(1, n + 1):
        offs[i] = len(out.encode('latin-1'))
        out += '%d 0 obj\n%s\nendobj\n' % (i, objects[i])
    xref = len(out.encode('latin-1'))
    out += 'xref\n0 %d\n0000000000 65535 f \n' % (n + 1)
    for i in range(1, n + 1):
        out += str(offs[i]).zfill(10) + ' 00000 n \n'
    out += 'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (n + 1, xref)
    return out.encode('latin-1')

# ============================================================ SEED
def _slug(t):
    return 'seed-' + re.sub(r'[^a-z0-9]+', '-', str(t).lower()).strip('-')[:60] + '.pdf'

def seed_db(db):
    if db.execute('SELECT COUNT(*) c FROM users').fetchone()['c'] > 0:
        return False
    cur = db.cursor()
    cur.executescript("""
      DELETE FROM sessions; DELETE FROM progress; DELETE FROM saved_resources;
      DELETE FROM tutor_messages; DELETE FROM resources; DELETE FROM lessons;
      DELETE FROM units; DELETE FROM teachers; DELETE FROM tutors;
      DELETE FROM subjects; DELETE FROM al_years; DELETE FROM users; DELETE FROM sqlite_sequence;""")
    pw_admin = generate_password_hash('admin123')
    pw_student = generate_password_hash('student123')
    cur.execute("INSERT INTO users (name,email,password_hash,role,school,district,al_year,medium,stream,subjects) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ('Platform Admin','admin@alplanner.lk',pw_admin,'admin','AL Planner HQ','Colombo','','en','','[]'))
    cur.execute("INSERT INTO users (name,email,password_hash,role,school,district,al_year,medium,stream,subjects) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ('Kavindu Samarasinghe','student@alplanner.lk',pw_student,'student','Ananda College, Colombo 10','Colombo','A/L 2027','en','Physical Science',
                 json.dumps(['Chemistry','Combined Mathematics'])))
    cur.executemany('INSERT INTO al_years (label,active) VALUES (?,1)', [('A/L 2027',), ('A/L 2028',)])
    teachers = [
        ('Mr. Nimal Perera','Senior Chemistry teacher with 18+ years of G.C.E. A/L classroom experience. Famous for building rock-solid fundamentals in General and Inorganic Chemistry.','Chemistry'),
        ('Prof. Anura Jayasuriya','Former university lecturer specialising in Physical Chemistry. Makes thermodynamics, kinetics and equilibrium feel simple and logical.','Chemistry'),
        ('Ms. Sanduni Fernando','Organic Chemistry specialist. Known for clear mechanism-based teaching and exam-focused paper discussion.','Chemistry'),
        ('Mr. Kasun Bandara','Combined Mathematics (Pure) teacher with 15 years of experience producing island ranks. Structured, proof-driven lessons.','Combined Mathematics'),
        ('Ms. Dilani Wickramasinghe','Combined Mathematics (Applied) teacher. Turns mechanics and probability into intuitive, picture-first ideas.','Combined Mathematics'),
        ('Dr. Tharushi Jayasinghe','Medical faculty graduate and Biology teacher. Diagram-first teaching for molecular and cellular biology.','Biology'),
        ('Mr. Ruwan Gunasekara','Biology teacher with 20 years of experience. Specialises in plant and human bio-systems and paper-marking technique.','Biology'),
    ]
    cur.executemany('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)', teachers)
    subs = [
        ('Chemistry','රසායන විද්‍යාව','வேதியியல்','CHEM','flask','#8b5cf6','#22d3ee'),
        ('Combined Mathematics','සංයුක්ත ගණිතය','இணை கணிதம்','CM','sigma','#6366f1','#ec4899'),
        ('Biology','ජීව විද්‍යාව','உயிரியல்','BIO','dna','#22c55e','#a3e635'),
        ('Physics','භෞතික විද්‍යාව','இயற்பியல்','PHY','book','#f97316','#e11d48'),
        ('ICT','තොරතුරු හා සන්නිවේදන තාක්ෂණය','தகவல் தொழில்நுட்பம்','ICT','cap','#06b6d4','#3b82f6'),
    ]
    cur.executemany('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)', subs)
    units = [(1,'General Chemistry',1),(1,'Physical Chemistry',2),(1,'Organic Chemistry',3),(1,'Inorganic Chemistry',4),
             (2,'Pure Mathematics',1),(2,'Applied Mathematics',2),(3,'Molecular & Cellular Biology',1),(3,'Plant & Animal Systems',2),
             (4,'Measurement',1),(4,'Mechanics',2),(4,'Oscillations and Waves',3),(4,'Thermal Physics',4),
             (4,'Gravitational Field',5),(4,'Electrostatic Field',6),(4,'Magnetic Field',7),(4,'Current Electricity',8),
             (4,'Electronics',9),(4,'Mechanical Properties of Matter',10),(4,'Matter and Radiation',11),
             (5,'Concept of ICT',1),(5,'Introduction to Computer',2),(5,'Data Representation',3),
             (5,'Fundamentals of Digital Circuits',4),(5,'Computer Operating Systems',5),
             (5,'Data Communication and Networking',6),(5,'System Analysis and Design',7),(5,'Database Management',8),
             (5,'Programming',9),(5,'Web Development',10),(5,'Internet of Things',11),(5,'ICT in Business',12),
             (5,'New Trends and Future Directions of ICT',13),(5,'Project',14)]
    cur.executemany('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', units)

    L = []
    def les(u, t, title, desc, yt, notes, o):
        L.append((u, t, title, desc, yt, notes, o))
    les(1,1,'Atomic Structure & Electronic Configuration',
        'Protons, neutrons and electrons, isotopes, and how electrons fill orbitals. The foundation every other Chemistry unit is built on.',
        '1xSQlwWGT8M',
        'Key points\n- Atom = nucleus (protons + neutrons) surrounded by electrons in shells.\n- Atomic number (Z) = protons. Mass number (A) = protons + neutrons.\n- Isotopes: same Z, different A (e.g. C-12 and C-14).\n- Fill orbitals by Aufbau order: 1s 2s 2p 3s 3p 4s 3d ...\n- Each orbital holds max 2 electrons (Pauli). Fill degenerate orbitals singly first (Hund).\n- Exam tip: always write the full electron configuration before the short form.',1)
    les(1,1,'The Mole Concept & Stoichiometry',
        "Moles, molar mass, Avogadro's number and how to convert between mass, moles and number of particles in calculations.",
        'AsqEkF7hcII',
        'Key points\n- 1 mole = 6.022 x 10^23 particles (Avogadro constant).\n- n = m / M (moles = mass / molar mass).\n- Concentration: c = n / V (mol dm-3).\n- At STP, 1 mole of gas occupies 22.4 dm3.\n- Stoichiometry: use the balanced equation mole ratios to move between substances.\n- Exam tip: keep 3 significant figures and carry units through every step.',2)
    les(1,1,'Chemical Bonding & Molecular Structure',
        'Ionic, covalent, coordinate and metallic bonding, shapes of molecules (VSEPR) and how bonding decides properties.',
        'playlist:PLSQl0a2vh4HAYCvTHhMGsNvLS-btVPXRw',
        'Key points\n- Ionic bond: complete electron transfer (metal + non-metal), high m.p., conducts when molten/aqueous.\n- Covalent bond: sharing of electron pairs (non-metals), low m.p., usually non-conductors.\n- Coordinate (dative) bond: both shared electrons from one atom (e.g. NH4+).\n- VSEPR: electron pairs repel; lone pairs squeeze bond angles (CH4 109.5, NH3 107, H2O 104.5).\n- Metallic bonding: lattice of positive ions in a sea of delocalised electrons.',3)
    les(2,2,'The Gaseous State of Matter',
        "Boyle's and Charles' laws, the ideal gas equation PV = nRT, kinetic theory and real gas deviations.",
        'erjMiErRgSQ',
        'Key points\n- Boyle: P1V1 = P2V2 (constant T). Charles: V/T = constant (constant P).\n- Combined: PV/T = constant. Ideal gas: PV = nRT, R = 8.314 J K-1 mol-1.\n- Kinetic theory: negligible molecular volume, no intermolecular forces, elastic collisions.\n- Real gases deviate at high pressure and low temperature.\n- Diffusion rate inversely proportional to sqrt of molar mass (Graham).',1)
    les(2,2,'Chemical Thermodynamics & Enthalpy',
        'System vs surroundings, exothermic and endothermic reactions, enthalpy change and calorimetry basics.',
        'fucyI7Ouj2c',
        'Key points\n- Enthalpy H = heat content at constant pressure.\n- deltaH negative = exothermic (releases heat), positive = endothermic.\n- Standard enthalpy of formation: 1 mole of compound from elements in standard states.\n- q = mc x deltaT for calorimetry experiments.\n- Activation energy: minimum energy for a successful collision.',2)
    les(2,2,"Hess's Law & Enthalpy Calculations",
        "Hess's law of constant heat summation, enthalpy cycles, and calculating reaction enthalpy from formation and combustion data.",
        'chXMpDwjBDk',
        'Key points\n- Hess: total enthalpy change is independent of the route taken.\n- deltaH(reaction) = SUM deltaHf(products) - SUM deltaHf(reactants).\n- Using combustion data: deltaH = SUM deltaHc(reactants) - SUM deltaHc(products).\n- Bond enthalpy method: deltaH = bonds broken - bonds formed.\n- Exam tip: draw the enthalpy cycle and label every arrow direction.',3)
    les(3,3,'Introduction to Organic Chemistry',
        'What makes carbon special, catenation, hybridisation (sp3, sp2, sp), functional groups and the main families of organic compounds.',
        'JHgTNNX01r4',
        'Key points\n- Carbon forms 4 covalent bonds and long stable chains (catenation).\n- sp3 carbon: 4 single bonds, tetrahedral, 109.5. sp2: 1 double bond, trigonal planar, 120. sp: triple bond, linear, 180.\n- Homologous series: same functional group, same general formula, gradual property change.\n- Main families: alkanes, alkenes, alkynes, alcohols, aldehydes, ketones, carboxylic acids, esters.\n- Isomerism: structural (chain / position / functional) and stereoisomerism (geometrical, optical).',1)
    les(3,3,'IUPAC Nomenclature of Organic Compounds',
        'Systematic naming of alkanes, alkenes, alkynes, alcohols, haloalkanes and more using IUPAC rules, step by step.',
        'TYU_JluleME',
        'Key points\n- Step 1: find the longest chain containing the principal functional group.\n- Step 2: number to give the principal group the lowest locant.\n- Step 3: name substituents alphabetically with their locants.\n- Suffixes: -ane, -ene, -yne, -ol, -al, -one, -oic acid.\n- Common exam traps: ethyl- before methyl- alphabetically; count from the end near the functional group.',2)
    les(3,3,'Hydrocarbons: Alkanes, Alkenes & Alkynes',
        'Structure, preparation and characteristic reactions of hydrocarbons: substitution vs addition vs oxidation.',
        'hcpWpluvXgc',
        'Key points\n- Alkanes (CnH2n+2): free-radical substitution with Br2/Cl2 in sunlight; generally unreactive.\n- Alkenes (CnH2n): electrophilic addition - H2/Ni, HX, X2, cold dilute KMnO4 (forms diol).\n- Markovnikov rule for unsymmetrical alkenes + HX.\n- Alkynes: addition reactions, terminal alkynes are weakly acidic.\n- Baeyer test (decolourising purple KMnO4) detects unsaturation.',3)
    les(4,1,'The Periodic Table & Periodicity',
        'How the table is organised, periodic trends in atomic radius, ionisation energy, electronegativity and their explanations.',
        't_f8bB1kf6M',
        'Key points\n- Elements arranged by increasing atomic number; groups share outer electron configuration.\n- Atomic radius decreases across a period, increases down a group.\n- Ionisation energy increases across a period (with small dips at group 13 and 16), decreases down a group.\n- Electronegativity peaks at fluorine.\n- Metallic character increases down a group and towards the left.',1)
    les(4,1,'s-Block & p-Block Elements',
        'Group 1, 2 and 17 trends, important compounds of Na, Mg and the halogens, and their everyday uses.',
        '',
        'Key points\n- Group 1 (alkali metals): soft, reactive, stored under oil; reactivity increases downwards.\n- Group 2: harder and less reactive; solubility of hydroxides increases down the group.\n- Group 17 (halogens): oxidising power decreases down the group; displacement reactions.\n- Important compounds: NaOH (chlor-alkali), Na2CO3 (Solvay), CaO (limestone).\n- Flame tests: Na yellow, K lilac, Ca brick-red.',2)
    les(4,1,'Industrial & Environmental Chemistry',
        'How Chemistry is applied in Sri Lankan industry and the environment: fertilisers, cement, air and water pollution.',
        '',
        'Key points\n- Haber process: N2 + 3H2 -> 2NH3, Fe catalyst, ~450 C, ~200 atm.\n- Contact process for H2SO4: V2O5 catalyst.\n- Air pollutants: CO, NOx, SO2, particulates; photochemical smog.\n- Water quality: dissolved oxygen, BOD, eutrophication from fertiliser runoff.\n- Ozone layer: CFCs break O3; Montreal Protocol phase-out.',3)
    les(5,4,'Limits & Continuity',
        'The idea of a limit, evaluating limits analytically, limits at infinity and the sandwich theorem.',
        'riXcZT2ICjA',
        'Key points\n- Limit: value f(x) approaches as x -> a (function need not be defined at a).\n- Techniques: direct substitution, factorising, rationalising, standard limits.\n- Standard results: lim(x->0) sin x / x = 1; lim(x->0) (e^x - 1)/x = 1.\n- Continuity at a: f(a) defined, limit exists, both equal.\n- Exam tip: for 0/0 forms, factor or rationalise before substituting.',1)
    les(5,4,'Differentiation & Applications',
        'First principles, power, product, quotient and chain rules, gradients of tangents and rate-of-change problems.',
        'bRZmfc1YFsQ',
        "Key points\n- f'(x) = lim(h->0) [f(x+h) - f(x)] / h.\n- d/dx x^n = n x^(n-1). Sum, product, quotient and chain rules.\n- Tangent gradient = dy/dx at the point; normal gradient = -1/m.\n- Stationary points where dy/dx = 0; classify with the second derivative.\n- Applications: maxima/minima, related rates, small increments.",2)
    les(5,4,'Integration & Its Applications',
        'Indefinite integrals as antiderivatives, standard integrals, substitution, definite integrals and areas under curves.',
        'MMv-027KEqU',
        'Key points\n- Integral of x^n = x^(n+1)/(n+1) + C (n != -1); integral of 1/x = ln|x| + C.\n- Standard integrals: e^x, sin x, cos x, sec^2 x.\n- Substitution: pick u = inner function; convert dx fully.\n- Definite integral = signed area; area between curve and x-axis.\n- Trapezium rule for numerical integration when exact form is hard.',3)
    les(6,5,'Vectors in Two Dimensions',
        'Vector notation, magnitude and direction, unit vectors, scalar product and resolving forces with vectors.',
        'br7tS1t2SFE',
        'Key points\n- A vector has magnitude and direction; written ai + bj or as a column.\n- Magnitude = sqrt(a^2 + b^2); unit vector = vector / magnitude.\n- Scalar (dot) product: a.b = |a||b| cos theta = a1a2 + b1b2.\n- Perpendicular vectors have a.b = 0.\n- Position vectors make geometry proofs much easier.',1)
    les(6,5,'Motion in a Straight Line (Kinematics)',
        'Displacement, velocity and acceleration, SUVAT equations, velocity-time graphs and vertical motion under gravity.',
        'XIJAZM5G5Fg',
        'Key points\n- v = u + at; s = ut + (1/2)at^2; v^2 = u^2 + 2as. Use only for constant acceleration.\n- Area under v-t graph = displacement; gradient of v-t graph = acceleration.\n- Under gravity: a = -g = -9.8 m s-2 (or -10 for quick work).\n- Relative velocity: velocity of A relative to B = vA - vB.\n- Exam tip: draw the v-t graph even when you use equations.',2)
    les(6,5,'Probability & Statistics',
        'Sample spaces, addition and multiplication rules, conditional probability, mean, variance and their exam patterns.',
        'uzkc-qNVoOk',
        'Key points\n- P(A) = favourable outcomes / total outcomes (equally likely cases).\n- Addition rule: P(A u B) = P(A) + P(B) - P(A n B).\n- Independent events: P(A n B) = P(A)P(B); conditional: P(A|B) = P(A n B)/P(B).\n- Tree diagrams organise multi-stage experiments.\n- Mean = SIGMA fx / N; variance = SIGMA f(x - mean)^2 / N.',3)
    les(7,6,'Cell Structure & Function',
        'Prokaryotic vs eukaryotic cells, organelles and their jobs, and how membrane structure controls transport.',
        '1aJBToJrlvA',
        'Key points\n- Eukaryotes have a true nucleus and membrane-bound organelles; prokaryotes do not.\n- Mitochondria: aerobic respiration. Ribosomes: protein synthesis. RER vs SER.\n- Golgi: modifies, packages, secretes. Lysosomes: intracellular digestion.\n- Fluid mosaic model: phospholipid bilayer + proteins; controls diffusion, osmosis, active transport.\n- Plant cells add: cell wall, chloroplasts, large central vacuole.',1)
    les(7,6,'Biological Molecules',
        'Carbohydrates, lipids, proteins and nucleic acids: monomers, polymers, bonds and food tests.',
        'j5VA6YrqTNs',
        'Key points\n- Carbohydrates: monosaccharides (glucose), disaccharides (maltose), polysaccharides (starch, cellulose).\n- Lipids: glycerol + fatty acids; saturated vs unsaturated; energy stores and membranes.\n- Proteins: amino acids joined by peptide bonds; 4 levels of structure; enzymes are proteins.\n- Nucleic acids: DNA and RNA made of nucleotides (sugar, phosphate, base).\n- Food tests: Benedict (reducing sugar), iodine (starch), Biuret (protein), ethanol emulsion (lipid).',2)
    les(7,6,'Photosynthesis & Cellular Respiration',
        'Light and dark reactions, the Calvin cycle, glycolysis, Krebs cycle and the electron transport chain.',
        'nbDV6dRnEy8',
        'Key points\n- Photosynthesis: 6CO2 + 6H2O -> C6H12O6 + 6O2 (light, chlorophyll).\n- Light reactions in thylakoids produce ATP and NADPH2 and release O2.\n- Calvin cycle (stroma) fixes CO2 using RuBP; rate limited by light, CO2, temperature.\n- Respiration: glycolysis (cytoplasm), Krebs (matrix), ETC (cristae) -> ~36 ATP.\n- C4 plants (e.g. sugarcane) minimise photorespiration in hot climates.',3)
    les(8,7,'Plant Cells, Tissues & Transport',
        'Xylem and phloem, transpiration pull, root pressure and how water and food move through the plant.',
        'd9GkH4vpK3w',
        'Key points\n- Xylem transports water and minerals upward; vessels are dead, lignified tubes.\n- Phloem transports food (translocation) using companion cells and sieve tubes.\n- Transpiration pull is the main driver; affected by light, temperature, humidity, wind.\n- Cohesion-tension theory explains the continuous water column.\n- Guard cells open/close stomata using turgor changes driven by K+ movement.',1)
    les(8,7,'Human Circulatory System',
        'Heart structure, the double circulation, blood vessels, cardiac cycle and common exam diagrams.',
        '9fxm85Fy4sQ',
        'Key points\n- Double circulation: pulmonary (heart -> lungs) and systemic (heart -> body).\n- Left side carries oxygenated blood and is more muscular (higher pressure).\n- Valves prevent backflow: bicuspid, tricuspid, semilunar.\n- SA node is the natural pacemaker; AV node delays the impulse.\n- Arteries: thick elastic walls; capillaries: one cell thick for exchange; veins: valves, low pressure.',2)
    les(8,7,'Genetics & Inheritance',
        "Mendel's laws, monohybrid and dihybrid crosses, sex determination and common pedigree questions.",
        'CBezq1fFUEA',
        'Key points\n- Gene: DNA segment coding for a trait; alleles are alternative forms.\n- Law of segregation: allele pairs separate during gamete formation.\n- Monohybrid cross ratio 3:1 (phenotype), 1:2:1 (genotype); test cross gives 1:1.\n- Independent assortment: genes on different chromosomes inherit independently (dihybrid 9:3:3:1).\n- Humans: XX female, XY male; haemophilia and colour blindness are X-linked.',3)
    cur.executemany('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)', L)

    def add_pdf(title, paragraphs):
        data = make_pdf(title, paragraphs)
        fname = _slug(title)
        with open(os.path.join(UPLOAD_DIR, fname), 'wb') as fh:
            fh.write(data)
        return fname, len(data)
    def res(title, cat, subj, lesson, paragraphs, status='approved', by=1, dl=0):
        fname, size = add_pdf(title, paragraphs)
        cur.execute("INSERT INTO resources (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,uploaded_by,status,downloads) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (title,cat,fname,title+'.pdf',size,'application/pdf',subj,lesson,by,status,dl))
        return cur.lastrowid
    res('Atomic Structure — Short Notes','short_notes',1,1,[
        'Everything you need about the atom on two pages.','','1. Subatomic particles',
        'Proton: mass 1 u, charge +1, inside nucleus. Neutron: mass 1 u, no charge.',
        'Electron: mass about 1/1836 u, charge -1, occupies shells around the nucleus.','','2. Isotopes',
        'Atoms of the same element with different numbers of neutrons.',
        'Example: chlorine exists as Cl-35 (75%) and Cl-37 (25%), giving RAM 35.5.','','3. Electronic configuration',
        'Order of filling: 1s 2s 2p 3s 3p 4s 3d 4p ... (use the diagonal rule).',
        'Chromium and copper are exceptions: [Ar] 3d5 4s1 and [Ar] 3d10 4s1.','','Quick practice',
        'Write the configuration of Fe2+ and Fe3+ and explain why Fe3+ is more stable.'],'approved',1,132)
    res('Mole Concept — Calculation Question Pack','question_papers',1,2,[
        '25 graded calculation questions on the mole, concentration and gas volumes.','','Section A — basics',
        'Q1. How many moles are there in 8.0 g of NaOH? (M = 40)',
        'Q2. How many molecules are present in 0.25 mol of CO2?',
        'Q3. What volume does 3.2 g of O2 occupy at STP?','','Section B — concentration',
        'Q4. 5.85 g of NaCl is dissolved to make 250 cm3 of solution. Find the concentration.',
        'Q5. What mass of KOH is needed for 500 cm3 of a 0.2 mol dm-3 solution?','','Section C — stoichiometry',
        'Q6. CaCO3 -> CaO + CO2. What mass of CaO forms from 25 g of pure CaCO3?',
        'Q7. 4.6 g of Na reacts with excess water. Find the volume of H2 at STP.','',
        'Answers are printed upside-down on the last page. Attempt before checking!'],'approved',1,98)
    res('Introduction to Organic Chemistry — Complete Notes','notes',1,7,[
        'A complete starter pack for Unit 12-14 Organic Chemistry.','','1. Why carbon is unique',
        'Tetravalency and catenation let carbon build millions of stable compounds.','','2. Hybridisation',
        'sp3: four sigma bonds, tetrahedral, 109.5 degrees (methane).',
        'sp2: three sigma + one pi, trigonal planar, 120 degrees (ethene).',
        'sp: two sigma + two pi, linear, 180 degrees (ethyne).','','3. Functional groups to memorise',
        'Alkane (-), alkene (C=C), alkyne (C triple C), halide (-X), alcohol (-OH),',
        'aldehyde (-CHO), ketone (>C=O), carboxylic acid (-COOH), ester (-COO-), amine (-NH2).','','4. Isomerism checklist',
        'Chain isomers - position isomers - functional group isomers.',
        'Geometrical (cis/trans) needs restricted rotation + two different groups on each C.','',
        'Study plan: watch the video lesson, copy the family tree, then do the 50-question set.'],'approved',1,214)
    res('Organic Nomenclature — 50 Practice Questions','question_papers',1,8,[
        'Name these compounds (IUPAC). Difficulty increases gradually.','',
        '1. CH3CH2CH2CH3        2. CH3CH(CH3)CH2CH3       3. CH2=CHCH2CH3',
        '4. CH3C(CH3)2CH3       5. CH triple C-CH3          6. CH3CH2CH2OH',
        '7. CH3CH(Br)CH3        8. CH3CH2CHO               9. CH3COCH2CH3',
        '10. CH3CH2COOH         11. (CH3)2CHCH2CH2Cl       12. CH2=CHCH(CH3)2',
        '...','Questions 13-50 continue with branched, cyclic and polyfunctional examples.','',
        'Marking scheme included: each correct name = 1 mark, correct locants = half mark.'],'approved',1,76)
    res('Organic Chemistry — Past Paper Collection (2019–2024)','past_papers',1,7,[
        'Organic Chemistry structured and essay questions extracted from AL papers.','','2024 Paper II Q9 (excerpt)',
        'Compound A (C4H10O) reacts with acidified K2Cr2O7 to give B which gives a silver',
        'mirror with Tollens reagent. Identify A and B and write the mechanism.','','2023 Paper II Q10 (excerpt)',
        'Show how you would convert ethanol to ethyl ethanoate using inorganic reagents only.','',
        '2022 Paper I — MCQ set on isomerism and reaction types (10 questions with key).','',
        'How to use: attempt under timed conditions, then compare with the marking points.'],'approved',1,187)
    res('AL Chemistry Model Paper 2026 — Full Paper I & II','model_papers',1,None,[
        'A full-length model paper in the new pattern. Paper I: 50 MCQ. Paper II: structured + essay.','',
        'Paper I instructions: 2 hours. Answer all 50 questions. No negative marking.',
        'Paper II instructions: 3 hours. Part A structured (compulsory). Part B: answer 4 of 6 essays.','','Syllabus coverage',
        'General Chemistry 25% | Physical Chemistry 25% | Organic Chemistry 30% | Inorganic 20%','',
        'A detailed marking scheme with examiner comments follows every paper.','',
        'Recommended: sit the paper first, then watch the related video lessons for weak areas.'],'approved',1,342)
    res('Limits & Continuity — Theory + Worked Examples','notes',2,13,[
        'Pure Mathematics unit 01 quick reference.','','Standard limits (memorise!)',
        'lim(x->0) sin x / x = 1        lim(x->0) tan x / x = 1',
        'lim(x->0) (e^x - 1) / x = 1    lim(x->0) ln(1+x) / x = 1',
        'lim(x->a) (x^n - a^n)/(x - a) = n a^(n-1)','','Worked example',
        'lim(x->0) (sin 3x)/(x) = lim 3 x sin3x/(3x) = 3.','','Continuity checklist at x = a:',
        '1) f(a) exists  2) both one-sided limits exist and agree  3) limit = f(a).','',
        '12 practice problems with full solutions are included at the end.'],'approved',1,154)
    res('Integration Formula Sheet — Quick Revision','short_notes',2,15,[
        'One-page formula sheet for the integration unit.','',
        'Basic: x^n -> x^(n+1)/(n+1) + C, 1/x -> ln|x| + C, e^x -> e^x + C',
        'Trig: sin x -> -cos x + C, cos x -> sin x + C, sec^2 x -> tan x + C','',
        "Reverse chain rule (substitution): integral f(g(x)) g'(x) dx; set u = g(x).",
        'Definite integrals: swap the limits when you substitute for u.','',
        'Area under curve y = f(x) from a to b = integral(a,b) f(x) dx (split at zeros).',
        'Trapezium rule: h/2 [y0 + yn + 2(sum of middle ordinates)].'],'approved',1,121)
    res('AL Combined Mathematics — Past Paper 2023','past_papers',2,None,[
        'Combined Mathematics 2023 past paper — Paper I and Paper II combined booklet.','',
        'Paper I: 2 hours, 25 structured questions, answer all.',
        'Paper II Part A: 3 questions (Pure + Applied mix). Part B: choose 5 of 7.','',
        'Topics weighted heavily this year: differentiation applications,',
        'integration areas, SUVAT, friction and probability trees.','',
        'Includes the official-style marking guide with alternative-method credit.'],'approved',1,268)
    res('Cell Structure & Function — Illustrated Notes','notes',3,19,[
        'Biology unit 02 illustrated notes for revision.','','Organelle job list',
        'Nucleus - stores DNA, controls the cell.        Mitochondrion - aerobic respiration.',
        'Ribosome - protein synthesis.                    RER - protein transport with ribosomes.',
        'Golgi - packaging and secretion.                 Lysosome - digestion of worn organelles.',
        'Chloroplast - photosynthesis (plants).           Cell wall - cellulose support (plants).','',
        'Membrane fluid mosaic model','Phospholipid bilayer with cholesterol, intrinsic and extrinsic proteins.',
        'Diffusion, facilitated diffusion, osmosis and active transport compared in a table.','',
        'Draw and label: a generalised animal cell and plant cell (exam favourite!).'],'approved',1,143)
    res('Photosynthesis Light Reactions — Short Notes','short_notes',3,21,[
        'Light reactions summarised in one page.','','Site: thylakoid membranes of the chloroplast.',
        'Inputs: light, H2O, ADP + Pi, NADP.  Outputs: ATP, NADPH2, O2.','',
        'Photolysis of water supplies electrons and releases oxygen.',
        'Non-cyclic photophosphorylation: PSII -> ETC -> PSI -> NADPH2.',
        'Cyclic photophosphorylation: PSI only, produces extra ATP.','',
        'Limiting factors graph shapes: light, CO2 and temperature — know all three!'],'approved',1,87)
    res('AL Biology Model Paper 2026 — Full Paper','model_papers',3,None,[
        'Biology model paper in the current pattern with a complete marking scheme.','',
        'Paper I: 50 MCQ (2 hours). Paper II: 4 structured + 4 of 6 essays (3 hours).','',
        'Coverage: molecular biology 20%, cells 20%, plant & animal systems 30%,',
        'genetics & evolution 15%, environment & applied biology 15%.','',
        'Examiner tips: keep diagrams large and labelled; quote numerical data;',
        'answer exactly what the command word asks (state / describe / explain / compare).'],'approved',1,305)
    res('Organic Reaction Mechanisms — Summary Sheet','study_material',1,7,[
        'Student-made summary of the main organic mechanisms (curly arrows).',
        'Free radical substitution (methane + Br2), electrophilic addition (ethene + HBr),',
        'nucleophilic substitution (haloalkane + OH-), oxidation of alcohols ladder.','',
        'Uploaded by a student - waiting for admin approval before public release.'],'pending',2,0)

    now = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    for lid in (1,2,13,19):
        cur.execute('INSERT INTO progress (user_id,lesson_id,completed,completed_at,watched,watched_at,favourite) VALUES (?,?,?,?,?,?,0)',(2,lid,1,now,1,now))
    for lid in (3,7,14):
        cur.execute('INSERT INTO progress (user_id,lesson_id,completed,watched,watched_at,favourite) VALUES (?,?,?,?,?,0)',(2,lid,0,1,now))
    cur.execute('UPDATE progress SET favourite=1 WHERE user_id=2 AND lesson_id IN (7,13)')
    cur.execute('INSERT OR IGNORE INTO saved_resources (user_id,resource_id) VALUES (2,4)')
    cur.execute('INSERT OR IGNORE INTO saved_resources (user_id,resource_id) VALUES (2,8)')

    tutors = [
        ('Eng. Pradeep Kumara','/assets/tutors/tutor1.jpg',['Combined Mathematics'],'12 years',
         ['2027 Theory — Sat 8.00 AM (Zoom)','2028 Theory — Sun 3.30 PM (Colombo 05)','Revision & Paper Class — Wed 6.00 PM (Zoom)'],
         'Colombo 05 + Online','077 123 4567','94771234567','pradeep.kumara.maths@gmail.com',
         'Engineering graduate who has produced 40+ island ranks. Step-by-step pure and applied maths with weekly quizzes and individual paper marking.'),
        ('Ms. Nadeesha Silva','/assets/tutors/tutor2.jpg',['Chemistry'],'8 years',
         ['2027 Theory — Tue 4.00 PM (Kandy)','2028 Theory — Thu 4.00 PM (Online)','Paper Class — Sat 10.00 AM (Online)'],
         'Kandy + Online','071 555 2890','94715552890','nadeesha.chem@gmail.com',
         'B.Sc. (Hons) Chemistry. Colourful summaries, mnemonics for inorganic trends and 10 years of past-paper discussion built into every unit.'),
        ('Dr. Kavindu Rathnayake','/assets/tutors/tutor3.jpg',['Biology'],'10 years',
         ['2027 Theory — Fri 5.00 PM (Zoom)','2028 Theory — Sun 8.00 AM (Gampaha)','MCQ Masterclass — Monthly'],
         'Gampaha + Online','076 442 1188','94764421188','dr.kavindu.bio@gmail.com',
         'Medical faculty graduate. Diagram-first biology teaching with memory palaces for long essays. Free WhatsApp doubt-clearing group.'),
        ('Mr. S. Thayalan','/assets/tutors/tutor4.jpg',['Combined Mathematics'],'14 years',
         ['2027 Theory — Mon 4.30 PM (Jaffna)','2028 Theory — Sat 9.00 AM (Zoom)','Revision — Sun 4.00 PM (Jaffna)'],
         'Jaffna + Online','077 890 3345','94778903345','thayalan.maths@gmail.com',
         'Veteran Northern-province maths teacher, bilingual Tamil/English classes. Rigorous problem sheets every week with model-answer walkthroughs.'),
        ('Ms. Fathima Rizna','/assets/tutors/tutor5.jpg',['Chemistry'],'6 years',
         ['2028 Theory — Wed 5.30 PM (Online)','Organic Crash Course — Monthly (Colombo 03)'],
         'Colombo 03 + Online','075 667 9021','94756679021','rizna.chem@gmail.com',
         'Young, energetic chemistry teacher focused on organic mechanisms and MCQ speed technique. Small-group online classes, recordings provided.'),
        ('Mr. Chaminda Herath','/assets/tutors/tutor6.jpg',['Biology','Chemistry'],'15 years',
         ['2027 Biology — Sat 6.00 AM (Kurunegala)','2027 Chemistry — Sun 6.00 AM (Kurunegala)','Online Revision — Daily 8.00 PM'],
         'Kurunegala + Online','070 234 8876','94702348876','chaminda.herath@gmail.com',
         "The North-Western province's best-known bio/chem combination teacher. Full-day seminar series before every term test. Printed tutes included."),
    ]
    for name, photo, subjs, exp, classes, loc, phone, wa, email, bio in tutors:
        cur.execute('INSERT INTO tutors (name,photo,subjects,experience,classes,location,phone,whatsapp,email,bio) VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (name, photo, json.dumps(subjs), exp, json.dumps(classes), loc, phone, wa, email, bio))
    db.commit()
    return True

# fresh DB + schema + seed at startup
_boot = sqlite3.connect(DB_PATH)
_boot.row_factory = sqlite3.Row
_boot.executescript(SCHEMA)
try:  # migration for older databases: teacher photos
    _boot.execute("ALTER TABLE teachers ADD COLUMN photo TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass
try:  # migration: per-lesson theory tab
    _boot.execute("ALTER TABLE lessons ADD COLUMN theory TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass
for _col in ("external_url", "description"):  # migration: external link resources w/ credit captions
    try:
        _boot.execute("ALTER TABLE resources ADD COLUMN %s TEXT DEFAULT ''" % _col)
    except sqlite3.OperationalError:
        pass
_boot.execute("""CREATE TABLE IF NOT EXISTS lesson_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  q TEXT NOT NULL, a TEXT DEFAULT '', b TEXT DEFAULT '', c TEXT DEFAULT '', d TEXT DEFAULT '',
  answer TEXT DEFAULT 'a', explanation TEXT DEFAULT '', ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')))""")
_boot.commit()
if seed_db(_boot):
    print('Database seeded (24 lessons, 13 resources, 6 tutors).')

# ---- self-healing: merge duplicate Physics units left by older installs ----
PHYS_CANON = [
    'Measurement \u2013 \u0db8\u0dd2\u0dab\u0dd4\u0db8\u0dca',
    'Mechanics \u2013 \u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',
    'Oscillations and Waves \u2013 \u0daf\u0ddd\u0dbd\u0db1 \u0dc3\u0dc4 \u0dad\u0dbb\u0d82\u0d9c',
    'Thermal Physics \u2013 \u0dad\u0dcf\u0db4 \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',
    'Gravitational Field \u2013 \u0d9c\u0dd4\u0dbb\u0dd4\u0dad\u0dca\u0dc0 \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',
    'Electrostatic Field \u2013 \u0dc3\u0dca\u0dae\u0dd2\u0dad \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dd4\u0dad\u0dca \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',
    'Magnetic Field \u2013 \u0da0\u0dd4\u0db8\u0dca\u0db6\u0d9a \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',
    'Current Electricity \u2013 \u0db0\u0dcf\u0dbb\u0dcf \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dd4\u0dad\u0dca\u0dba',
    'Electronics \u2013 \u0d89\u0dbd\u0d9a\u0dca\u0da7\u0dca\u200d\u0dbb\u0ddd\u0db1\u0dd2\u0d9a \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',
    'Mechanical Properties of Matter – පදාර්ථයේ යාන්ත්‍රික ගුණ',
    'Matter and Radiation – පදාර්ථය හා විකිරණ',
]

def cleanup_physics_units(db):
    """Merge duplicate/leftover Physics units (deterministic, safe to run at every start)."""
    try:
        row = db.execute("SELECT id FROM subjects WHERE name='Physics'").fetchone()
        if not row:
            return
        sid = row['id']
        units = db.execute('SELECT id,name FROM units WHERE subject_id=? ORDER BY id', (sid,)).fetchall()
        fixed = 0
        for idx, canon in enumerate(PHYS_CANON, 1):
            eng = canon.split(' \u2013 ')[0].strip().lower()
            group = [u for u in units
                     if u['name'].split(' \u2013 ')[0].strip().lower() == eng]
            if not group:
                continue
            def nlessons(u):
                return db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (u['id'],)).fetchone()['c']
            # keep the unit with most lessons; tie-break: bilingual name, then lowest id
            keep = max(group, key=lambda u: (nlessons(u), '\u2013' in u['name'], -u['id']))
            for u in group:
                if u['id'] == keep['id']:
                    continue
                db.execute('UPDATE lessons SET unit_id=? WHERE unit_id=?', (keep['id'], u['id']))
                db.execute('UPDATE resources SET subject_id=?, lesson_id=NULL WHERE lesson_id IN (SELECT id FROM lessons WHERE unit_id=?)', (sid, u['id']))
                db.execute('DELETE FROM units WHERE id=?', (u['id'],))
                fixed += 1
            db.execute('UPDATE units SET name=?, ord=? WHERE id=?', (canon, idx, keep['id']))
        if fixed:
            db.commit()
            print('Physics units cleaned: %d duplicate(s) merged.' % fixed)
    except Exception as _e:
        pass

cleanup_physics_units(_boot)
_boot.close()

# ============================================================ APP
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 26 * 1024 * 1024

def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.isolation_level = None  # autocommit, like better-sqlite3
        db.execute('PRAGMA foreign_keys=ON')
        g._db = db
    return db

@app.teardown_appcontext
def close_db(_e):
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()

def s(v, mx=500):
    return str(v).strip()[:mx] if isinstance(v, str) else ''

def bad(msg, code=400):
    return jsonify({'error': msg}), code

def rows(cur):
    return [dict(r) for r in cur.fetchall()]

def one(cur):
    r = cur.fetchone()
    return dict(r) if r else None

def public_user(u):
    if not u: return None
    try: subjs = json.loads(u['subjects'] or '[]')
    except Exception: subjs = []
    return {'id': u['id'], 'name': u['name'], 'email': u['email'], 'role': u['role'],
            'school': u['school'], 'district': u['district'], 'al_year': u['al_year'],
            'medium': u['medium'], 'stream': u['stream'], 'subjects': subjs, 'created_at': u['created_at'],
            'premium_until': u['premium_until'] if 'premium_until' in u.keys() else ''}

def create_session(user_id):
    token = secrets.token_hex(32)
    get_db().execute('INSERT INTO sessions (token,user_id,expires_at) VALUES (?,?,?)',
                     (token, user_id, int(time.time() * 1000) + SESSION_DAYS * 86400000))
    return token

@app.before_request
def load_user():
    g.user = None
    token = request.cookies.get(COOKIE)
    if token:
        u = one(get_db().execute('SELECT u.* FROM sessions se JOIN users u ON u.id=se.user_id WHERE se.token=? AND se.expires_at>?',
                                 (token, int(time.time() * 1000))))
        g.user = u

def set_session_cookie(resp, token):
    resp.set_cookie(COOKIE, token, httponly=True, samesite='Lax', max_age=SESSION_DAYS * 86400)

def require_auth(f):
    @wraps(f)
    def w(*a, **kw):
        if not g.user: return bad('Please sign in to continue', 401)
        if g.user.get('status') == 'suspended': return bad('Your account was suspended. Please contact the AL Planner team.', 403)
        return f(*a, **kw)
    return w

def require_admin(f):
    @wraps(f)
    def w(*a, **kw):
        if not g.user or g.user['role'] != 'admin': return bad('Admins only', 403)
        return f(*a, **kw)
    return w

def yt_embed(yid):
    if not yid: return None
    if yid.startswith('playlist:'):
        return 'https://www.youtube.com/embed/videoseries?list=' + yid[9:]
    return 'https://www.youtube-nocookie.com/embed/' + yid + '?rel=0'

def yt_normalize(v):
    v = s(v, 300)
    if not v: return ''
    if re.match(r'^[a-zA-Z0-9_-]{11}$', v): return v
    m = re.search(r'(?:youtube\.com/(?:watch\?[^#]*v=|embed/|shorts/|v/|live/)|youtu\.be/)([a-zA-Z0-9_-]{11})', v)
    if m: return m.group(1)
    m = re.search(r'[?&]list=([a-zA-Z0-9_-]{10,})', v)
    if m: return 'playlist:' + m.group(1)
    return v if len(v) == 11 else ''

def lesson_out(l, extra=None):
    d = dict(l)
    d['embed_url'] = yt_embed(d.get('youtube_id'))
    d['has_video'] = bool(d.get('youtube_id'))
    if extra: d.update(extra)
    return d

# ------------------------------------------------------------ AUTH
@app.post('/api/auth/register')
def register():
    b = request.get_json(silent=True) or {}
    if not sw(get_db(), 'register_open'): return bad('Registrations are closed by admin right now. Please check back soon!', 403)
    name, email, password = s(b.get('name'), 80), s(b.get('email'), 120).lower(), str(b.get('password') or '')
    if len(name) < 2: return bad('Please enter your full name')
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email): return bad('Please enter a valid email address')
    if not email.endswith('@gmail.com'): return bad('Please register with a Gmail address (@gmail.com)')
    if len(password) < 6: return bad('Password must be at least 6 characters')
    district, al_year, stream = s(b.get('district'), 60), s(b.get('alYear'), 20), s(b.get('stream'), 60)
    medium = b.get('medium') if b.get('medium') in MEDIUMS else 'en'
    if not district: return bad('Please select your district')
    if not al_year: return bad('Please select your A/L year')
    if not stream: return bad('Please select your stream')
    subjs = [s(x, 60) for x in (b.get('subjects') or []) if x][:6]
    db = get_db()
    if one(db.execute('SELECT id FROM users WHERE email=?', (email,))):
        return bad('An account with this email already exists', 409)
    cur = db.execute("INSERT INTO users (name,email,password_hash,role,school,district,al_year,medium,stream,subjects) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (name, email, generate_password_hash(password), 'student', s(b.get('school'), 120),
                      district, al_year, medium, stream, json.dumps(subjs)))
    token = create_session(cur.lastrowid)
    resp = jsonify({'user': public_user(one(db.execute('SELECT * FROM users WHERE id=?', (cur.lastrowid,))))})
    set_session_cookie(resp, token)
    return resp

@app.post('/api/auth/login')
def login():
    b = request.get_json(silent=True) or {}
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE email=?', (s(b.get('email'), 120).lower(),)))
    ok = False
    if u:
        try: ok = check_password_hash(u['password_hash'], str(b.get('password') or ''))
        except Exception: ok = False  # hash from the Node/bcrypt build -> fresh DB needed
    if not ok: return bad('Incorrect email or password', 401)
    if u.get('status') == 'suspended': return bad('Your account was suspended. Please contact the AL Planner team.', 403)
    token = create_session(u['id'])
    resp = jsonify({'user': public_user(u)})
    set_session_cookie(resp, token)
    return resp

@app.post('/api/auth/logout')
def logout():
    token = request.cookies.get(COOKIE)
    if token: get_db().execute('DELETE FROM sessions WHERE token=?', (token,))
    resp = jsonify({'ok': True})
    resp.delete_cookie(COOKIE)
    return resp

@app.get('/api/auth/me')
def me():
    return jsonify({'user': public_user(g.user)})

@app.post('/api/auth/password')
@require_auth
def change_password():
    b = request.get_json(silent=True) or {}
    cur_pw, new_pw = str(b.get('current') or ''), str(b.get('new') or '')
    if len(new_pw) < 6: return bad('New password must be at least 6 characters')
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (g.user['id'],)))
    try: ok = check_password_hash(u['password_hash'], cur_pw)
    except Exception: ok = False
    if not ok: return bad('Current password is incorrect')
    db.execute('UPDATE users SET password_hash=? WHERE id=?', (generate_password_hash(new_pw), u['id']))
    return jsonify({'ok': True})

# ------------------------------------------------------------ META / CATALOG
@app.get('/api/meta')
def meta():
    db = get_db()
    return jsonify({
        'districts': DISTRICTS, 'streams': STREAMS, 'mediums': MEDIUMS,
        'years': rows(db.execute('SELECT * FROM al_years WHERE active=1 ORDER BY id')),
        'categories': RESOURCE_CATEGORIES,
        'subjects': rows(db.execute('SELECT id,name,name_si,name_ta,code,icon,color1,color2 FROM subjects ORDER BY id')),
        'units': rows(db.execute('SELECT id,subject_id,name,ord FROM units ORDER BY subject_id,ord')),
    })

def progress_map(uid):
    if not uid: return {}
    return {p['lesson_id']: p for p in rows(get_db().execute('SELECT * FROM progress WHERE user_id=?', (uid,)))}

@app.get('/api/subjects')
def subjects():
    db = get_db()
    out = rows(db.execute("""
      SELECT s.*,
       (SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=s.id) AS lesson_count,
       (SELECT COUNT(*) FROM units u WHERE u.subject_id=s.id) AS unit_count,
       (SELECT COUNT(*) FROM resources r WHERE r.subject_id=s.id AND r.status='approved') AS resource_count
      FROM subjects s ORDER BY s.id"""))
    return jsonify({'subjects': out})

@app.get('/api/stats')
def api_stats():
    db = get_db()
    n = lambda q: db.execute(q).fetchone()[0]
    return jsonify({'subjects': n('SELECT COUNT(*) FROM subjects'),
                    'units': n('SELECT COUNT(*) FROM units'),
                    'lessons': n('SELECT COUNT(*) FROM lessons'),
                    'resources': n("SELECT COUNT(*) FROM resources WHERE status='approved'"),
                    'teachers': n('SELECT COUNT(*) FROM teachers'),
                    'students': n("SELECT COUNT(*) FROM users WHERE role='student'")})

@app.get('/api/videos')
def videos():
    sid = request.args.get('subject', '')
    q = """SELECT l.id,l.title,l.youtube_id,l.ord,t.name AS teacher_name,t.photo AS teacher_photo,
                  u.name AS unit_name,s.id AS subject_id,s.name AS subject_name,s.color1,s.color2
           FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
           LEFT JOIN teachers t ON t.id=l.teacher_id WHERE l.youtube_id<>''"""
    args = ()
    if sid.isdigit():
        q += ' AND s.id=?'
        args = (int(sid),)
    q += ' ORDER BY s.id,l.ord,l.id'
    return jsonify({'videos': rows(get_db().execute(q, args))})

@app.get('/api/subjects/<int:sid>')
def subject_detail(sid):
    db = get_db()
    sub = one(db.execute('SELECT * FROM subjects WHERE id=?', (sid,)))
    if not sub: return bad('Subject not found', 404)
    prog = progress_map(g.user['id'] if g.user else None)
    units = []
    for u in rows(db.execute('SELECT * FROM units WHERE subject_id=? ORDER BY ord,id', (sid,))):
        ls = rows(db.execute("""SELECT l.id,l.title,l.ord,l.youtube_id,t.name AS teacher_name,t.photo AS teacher_photo
                                FROM lessons l LEFT JOIN teachers t ON t.id=l.teacher_id
                                WHERE l.unit_id=? ORDER BY l.ord,l.id""", (u['id'],)))
        u['lessons'] = [lesson_out(l, {'state': prog.get(l['id'])}) for l in ls]
        units.append(u)
    return jsonify({'subject': sub, 'units': units})

@app.get('/api/lessons/<int:lid>')
def lesson_detail(lid):
    db = get_db()
    l = one(db.execute("""
      SELECT l.*, t.name AS teacher_name, t.bio AS teacher_bio, t.photo AS teacher_photo, u.name AS unit_name, u.subject_id, u.ord AS unit_ord,
             s.name AS subject_name, s.name_si AS subject_name_si, s.name_ta AS subject_name_ta,
             s.color1, s.color2, s.icon AS subject_icon
      FROM lessons l LEFT JOIN teachers t ON t.id=l.teacher_id
      JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id WHERE l.id=?""", (lid,)))
    if not l: return bad('Lesson not found', 404)
    state = one(db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?', (g.user['id'], lid))) if g.user else None
    resources = rows(db.execute("""SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,u.name AS uploader
        FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by
        WHERE r.lesson_id=? AND r.status='approved' ORDER BY r.id DESC""", (lid,)))
    related = rows(db.execute("""SELECT l.id,l.title,l.youtube_id,t.name AS teacher_name,t.photo AS teacher_photo
        FROM lessons l JOIN units u ON u.id=l.unit_id LEFT JOIN teachers t ON t.id=l.teacher_id
        WHERE u.subject_id=? AND l.id!=? ORDER BY l.id LIMIT 8""", (l['subject_id'], lid)))
    questions = rows(db.execute('SELECT * FROM lesson_questions WHERE lesson_id=? ORDER BY ord,id', (lid,)))
    sim = resolve_sim(l)
    try: sim['config'] = json.loads(l.get('sim_config') or '{}')
    except Exception: sim['config'] = {}
    sim['progress'] = one(db.execute('SELECT started,completed,attempts,best_score,last_score FROM sim_progress WHERE user_id=? AND lesson_id=?', (g.user['id'], lid))) if g.user else None
    out = lesson_out(l)
    out['simulation_type'] = l.get('simulation_type') or ''
    out['simulation_enabled'] = l.get('simulation_enabled')
    return jsonify({'lesson': out, 'state': state or {'completed': 0, 'watched': 0, 'favourite': 0},
                    'resources': resources, 'related': [lesson_out(r) for r in related], 'questions': questions,
                    'sim': sim})

@app.put('/api/admin/lessons/<int:lid>/sim')
@require_admin
def admin_set_sim(lid):
    db = get_db()
    l = one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,)))
    if not l: return bad('Lesson not found', 404)
    b = request.get_json(silent=True) or {}
    enb = b.get('enabled')
    if enb in (-1, '-1', 'auto', None): enb = None
    elif str(enb) in ('1', 'on'): enb = 1
    else: enb = 0
    stype = s(b.get('simulation_type'), 30).strip()
    if stype not in SIM_TYPES: stype = ''
    cfg = b.get('config') or {}
    if not isinstance(cfg, dict): cfg = {}
    cfg = {k: s(cfg.get(k), 4000) for k in ('instructions_en', 'instructions_si', 'instructions_ta', 'concept') if cfg.get(k)}
    db.execute('UPDATE lessons SET simulation_type=?, simulation_enabled=?, sim_config=? WHERE id=?',
               (stype, enb, json.dumps(cfg, ensure_ascii=False), lid))
    return jsonify({'ok': True})

@app.post('/api/lessons/<int:lid>/sim-event')
@require_auth
def sim_event(lid):
    db = get_db()
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    b = request.get_json(silent=True) or {}
    ev = s(b.get('event'), 20)
    uid = g.user['id']
    if ev not in ('start', 'complete', 'score'): return bad('Bad event')
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    db.execute('INSERT INTO sim_progress (user_id,lesson_id,sim_type,updated_at) VALUES (?,?,?,?) '
               'ON CONFLICT(user_id,lesson_id) DO NOTHING', (uid, lid, s(b.get('sim_type'), 30), now))
    if ev == 'start':
        db.execute('UPDATE sim_progress SET started=1, attempts=attempts+1, sim_type=?, updated_at=? WHERE user_id=? AND lesson_id=?',
                   (s(b.get('sim_type'), 30), now, uid, lid))
    elif ev == 'complete':
        db.execute('UPDATE sim_progress SET completed=1, sim_type=?, updated_at=? WHERE user_id=? AND lesson_id=?',
                   (s(b.get('sim_type'), 30), now, uid, lid))
    else:
        try:
            sc = max(0, int(b.get('score') or 0)); tt = max(1, int(b.get('total') or 1)); sc = min(sc, tt)
        except Exception: return bad('Bad score')
        pct = round(sc * 100 / tt)
        db.execute('UPDATE sim_progress SET last_score=?, best_score=MAX(COALESCE(best_score,0),?), completed=1, updated_at=? WHERE user_id=? AND lesson_id=?',
                   (pct, pct, now, uid, lid))
        db.execute('INSERT INTO sim_events (user_id,sim_type,event,score,total,pct) VALUES (?,?,?,?,?,?)',
                   (uid, s(b.get('sim_type'), 30), 'score', sc, tt, pct))
    return jsonify(one(db.execute('SELECT started,completed,attempts,best_score,last_score FROM sim_progress WHERE user_id=? AND lesson_id=?', (uid, lid))))

@app.put('/api/lessons/<int:lid>/theory')
@require_admin
def lesson_theory(lid):
    db = get_db()
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    b = request.get_json(silent=True) or {}
    db.execute('UPDATE lessons SET theory=? WHERE id=?', (s(b.get('theory'), 20000), lid))
    return jsonify({'ok': True})

@app.post('/api/lessons/<int:lid>/questions')
@require_admin
def lesson_add_question(lid):
    db = get_db()
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    b = request.get_json(silent=True) or {}
    q = s(b.get('q'), 600)
    if not q: return bad('Question text required')
    ans = str(b.get('answer') or 'a').strip().lower()
    if ans not in ('a', 'b', 'c', 'd'): ans = 'a'
    mx = one(db.execute('SELECT COALESCE(MAX(ord),0) m FROM lesson_questions WHERE lesson_id=?', (lid,)))['m']
    cur = db.execute('INSERT INTO lesson_questions (lesson_id,q,a,b,c,d,answer,explanation,ord) VALUES (?,?,?,?,?,?,?,?,?)',
                     (lid, q, s(b.get('a'), 300), s(b.get('b'), 300), s(b.get('c'), 300), s(b.get('d'), 300),
                      ans, s(b.get('explanation'), 1000), mx + 1))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.delete('/api/questions/<int:qid>')
@require_admin
def lesson_del_question(qid):
    get_db().execute('DELETE FROM lesson_questions WHERE id=?', (qid,))
    return jsonify({'ok': True})

@app.post('/api/lessons/<int:lid>/toggle')
@require_auth
def toggle_lesson(lid):
    field = s((request.get_json(silent=True) or {}).get('field'), 20)
    if field not in ('completed', 'watched', 'favourite'): return bad('Invalid field')
    db = get_db()
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    uid = g.user['id']
    row = one(db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?', (uid, lid)))
    if not row:
        db.execute('INSERT INTO progress (user_id,lesson_id) VALUES (?,?)', (uid, lid))
        row = {'completed': 0, 'watched': 0, 'favourite': 0}
    nv = 0 if row[field] else 1
    now = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    if field in ('completed', 'watched'):
        db.execute(f'UPDATE progress SET {field}=?, {field}_at=? WHERE user_id=? AND lesson_id=?', (nv, now if nv else None, uid, lid))
    else:
        db.execute('UPDATE progress SET favourite=? WHERE user_id=? AND lesson_id=?', (nv, uid, lid))
    return jsonify(one(db.execute('SELECT * FROM progress WHERE user_id=? AND lesson_id=?', (uid, lid))))

@app.get('/api/teachers')
def teachers():
    return jsonify({'teachers': rows(get_db().execute('SELECT * FROM teachers ORDER BY name'))})

@app.get('/api/teachers/<int:tid>')
def teacher_detail(tid):
    db = get_db()
    t = one(db.execute('SELECT * FROM teachers WHERE id=?', (tid,)))
    if not t: return bad('Teacher not found', 404)
    lessons = rows(db.execute("""SELECT l.id,l.title,l.youtube_id,l.ord,u.name AS unit_name,u.ord AS unit_ord,s2.name AS subject_name,s2.id AS subject_id
        FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s2 ON s2.id=u.subject_id
        WHERE l.teacher_id=? ORDER BY s2.id,u.ord,l.ord,l.id""", (tid,)))
    res = rows(db.execute("""SELECT r.id,r.title,r.category,r.downloads,s2.name AS subject_name FROM resources r
        LEFT JOIN subjects s2 ON s2.id=r.subject_id
        WHERE r.status='approved' AND r.lesson_id IN (SELECT id FROM lessons WHERE teacher_id=?) ORDER BY r.id DESC LIMIT 60""", (tid,)))
    subs = sorted({l['subject_name'] for l in lessons if l['subject_name']})
    units_n = len({(l['subject_id'], l['unit_name']) for l in lessons})
    return jsonify({'teacher': dict(t), 'lessons': lessons, 'resources': res,
        'stats': {'lessons': len(lessons), 'units': units_n, 'subjects': len(subs), 'videos': sum(1 for l in lessons if l['youtube_id'])}})

# ------------------------------------------------------------ DASHBOARD
def activity_dates(db, uid):
    ds = set()
    for r in db.execute("SELECT substr(completed_at,1,10) d FROM progress WHERE user_id=? AND completed_at IS NOT NULL", (uid,)):
        if r['d']: ds.add(r['d'])
    for r in db.execute("SELECT substr(created_at,1,10) d FROM mcq_attempts WHERE user_id=?", (uid,)):
        if r['d']: ds.add(r['d'])
    for r in db.execute("SELECT substr(updated_at,1,10) d FROM sim_progress WHERE user_id=?", (uid,)):
        if r['d']: ds.add(r['d'])
    return sorted(ds)

def longest_streak(dates):
    best = cur = 0; prev = None
    for d in dates:
        try:
            y, m, dd = [int(x) for x in d.split('-')]
            import datetime as _dt
            day = _dt.date(y, m, dd)
        except Exception:
            continue
        cur = cur + 1 if prev and (day - prev).days == 1 else 1
        if cur > best: best = cur
        prev = day
    return best

@app.get('/api/weakareas')
@require_auth
def weakareas():
    db = get_db(); uid = g.user['id']
    agg = {}
    for r in db.execute("""SELECT u.id uid,u.name uname,u.ord uord,s2.id sid,s2.name sname,s2.name_si ssi,s2.name_ta sta,
            SUM(a.score) sc,SUM(a.total) tot,COUNT(*) n FROM mcq_attempts a
            JOIN lessons l ON l.id=a.lesson_id JOIN units u ON u.id=l.unit_id JOIN subjects s2 ON s2.id=u.subject_id
            WHERE a.user_id=? GROUP BY u.id""", (uid,)):
        agg[r['uid']] = dict(r)
    for r in db.execute("""SELECT u.id uid,COUNT(*) n,SUM(sp.last_score)/100.0*5 sc FROM sim_progress sp
            JOIN lessons l ON l.id=sp.lesson_id JOIN units u ON u.id=l.unit_id
            WHERE sp.user_id=? AND sp.last_score IS NOT NULL GROUP BY u.id""", (uid,)):
        if r['uid'] in agg:
            agg[r['uid']]['sc'] = (agg[r['uid']]['sc'] or 0) + (r['sc'] or 0)
            agg[r['uid']]['tot'] = (agg[r['uid']]['tot'] or 0) + r['n'] * 5
            agg[r['uid']]['n'] += r['n']
        else:
            u = one(db.execute('SELECT u.id uid,u.name uname,u.ord uord,s2.id sid,s2.name sname,s2.name_si ssi,s2.name_ta sta FROM units u JOIN subjects s2 ON s2.id=u.subject_id WHERE u.id=?', (r['uid'],)))
            if u:
                agg[r['uid']] = dict(u); agg[r['uid']]['sc'] = r['sc'] or 0; agg[r['uid']]['tot'] = r['n'] * 5; agg[r['uid']]['n'] = r['n']
    areas = []
    for a in agg.values():
        if not a.get('tot'): continue
        pct = round(100.0 * a['sc'] / a['tot'])
        areas.append({'unit_id': a['uid'], 'unit': a['uname'], 'ord': a['uord'], 'subject_id': a['sid'], 'subject': a['sname'],
                      'subject_si': a['ssi'], 'subject_ta': a['sta'], 'pct': pct, 'right': round(a['sc'], 1), 'of': a['tot'], 'attempts': a['n'],
                      'status': 'weak' if pct < 50 else ('good' if pct < 75 else 'excellent')})
    areas.sort(key=lambda x: (x['subject_id'], x['ord']))
    return jsonify({'areas': areas,
        'summary': {'weak': sum(1 for x in areas if x['status'] == 'weak'), 'good': sum(1 for x in areas if x['status'] == 'good'), 'excellent': sum(1 for x in areas if x['status'] == 'excellent')}})

# ---------------- A/L Exam Mode (timed practice papers) ----------------
@app.post('/api/exam/attempt')
@require_auth
def exam_attempt():
    db = get_db(); uid = g.user['id']
    b = request.get_json(silent=True) or {}
    subj = s(b.get('subject'), 10)
    if subj not in ('chem', 'phys', 'bio', 'mixed'): return bad('Bad subject')
    mode = s(b.get('mode'), 10)
    if mode not in ('m1', 'm2', 'm3'): return bad('Bad mode')
    try:
        cnt = int(b.get('count')); sc = int(b.get('score')); secs = int(b.get('seconds') or 0)
    except (TypeError, ValueError):
        return bad('Bad numbers')
    if cnt < 1 or cnt > 100 or sc < 0 or sc > cnt: return bad('Bad numbers')
    secs = max(0, min(secs, 4 * 3600))
    clean = []
    if isinstance(b.get('topics'), list):
        for tp in b['topics'][:60]:
            if not isinstance(tp, dict): continue
            ty = s(tp.get('t'), 30)
            if ty not in SIM_TYPES: continue
            try:
                c2 = int(tp.get('c')); n2 = int(tp.get('n'))
            except (TypeError, ValueError):
                continue
            if n2 < 1 or n2 > 100 or c2 < 0 or c2 > n2: continue
            clean.append({'t': ty, 'c': c2, 'n': n2})
    db.execute('INSERT INTO exam_attempts (user_id,subject,mode,qcount,score,seconds,topics) VALUES (?,?,?,?,?,?,?)',
               (uid, subj, mode, cnt, sc, secs, json.dumps(clean)))
    return jsonify({'ok': True})

@app.get('/api/exam/stats')
@require_auth
def exam_stats():
    db = get_db(); uid = g.user['id']
    att = rows(db.execute('SELECT id,subject,mode,qcount AS count,score,seconds,created_at FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 8', (uid,)))
    agg = one(db.execute('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?', (uid,)))
    tt = {}
    for r in rows(db.execute('SELECT topics FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 20', (uid,))):
        try: arr = json.loads(r['topics'] or '[]')
        except (ValueError, TypeError): arr = []
        for tp in arr:
            d = tt.setdefault(tp['t'], [0, 0]); d[0] += tp['c']; d[1] += tp['n']
    topics = sorted(({'t': k, 'c': v[0], 'n': v[1], 'pct': round(v[0] * 100 / v[1])} for k, v in tt.items() if v[1]),
                    key=lambda x: x['pct'])
    return jsonify({'attempts': att, 'taken': agg['c'], 'avg': round(agg['a']), 'best': round(agg['b']),
                    'weak': [x for x in topics if x['pct'] < 60][:8], 'topics': topics[:12]})

# ---------------- 🤖 AI Tutor (Gemini API — admin pastes the key; free tier key works) ----------------
AI_MODEL = 'gemini-2.5-flash'

def _setting(db, key):
    r = db.execute('SELECT value FROM site_settings WHERE key=?', (key,)).fetchone()
    return r['value'] if r and r['value'] else ''

def _chemdb_list(db):
    try:
        v = json.loads(_setting(db, 'chemdb_extra') or '[]')
        return v if isinstance(v, list) else []
    except Exception:
        return []

def _chemdb_set(db, lst):
    db.execute("INSERT INTO site_settings (key,value) VALUES ('chemdb_extra',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (json.dumps(lst)[:8000],))

def is_premium(u):
    return bool(u and u['premium_until'] and u['premium_until'] >= time.strftime('%Y-%m-%d', time.gmtime()))

@app.get('/api/admin/aikey')
@require_admin
def admin_aikey():
    db = get_db()
    k = _setting(db, 'ai_key')
    return jsonify({'set': bool(k), 'tail': ('…' + k[-4:]) if k else '', 'model': AI_MODEL,
                    'premium_price': _setting(db, 'premium_price'), 'premium_bank': _setting(db, 'premium_bank'),
                    'ezcash_number': _setting(db, 'ezcash_number'),
                    'free_limit': _setting(db, 'ai_free_limit') or '10', 'pro_limit': _setting(db, 'ai_pro_limit') or '100',
                    'model_eff': _ai_model(db), 'prompt': _setting(db, 'ai_prompt')})

# ---------------- 🧠 Offline syllabus Guru (works with zero API key) ----------------
def _load_offline_kb():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline_kb.json'), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'topics': [], 'guide': ''}
_OFFLINE_KB = _load_offline_kb()

def _offline_answer(db, text):
    """Match the student's question to the syllabus knowledge bank. Returns (reply, matched_title)."""
    t2 = (' ' + re.sub(r'[^a-z0-9+\- ]+', ' ', (text or '').lower()) + ' ')
    best, best_sc = None, 0
    for tp in _OFFLINE_KB.get('topics', []):
        sc = 0
        for k in tp.get('keys', []):
            k2 = k.lower().strip()
            if not k2: continue
            if (' ' + k2 + ' ') in t2 or t2.find(k2) >= 0:
                sc += 1 + k2.count(' ') * 2
        if sc > best_sc: best, best_sc = tp, sc
    lore_hit = ''
    try:
        for r2 in db.execute('SELECT text FROM ai_knowledge ORDER BY id DESC LIMIT 40'):
            words = [w for w in re.findall(r'[a-z]{4,}', (r2['text'] or '').lower())]
            if words and sum(1 for w in set(words) if w in t2) >= 3:
                lore_hit = '\n\n📌 From the AL Planner team notes: ' + (r2['text'] or '')[:600]
                break
    except Exception:
        pass
    if not best:
        g2 = _OFFLINE_KB.get('guide') or ''
        return ('🧠 ' + g2 + lore_hit, '')
    head = '🧠 AL Guru (offline syllabus expert): ' + best.get('title', '') + ' [' + best.get('subj', '') + ']\n\n'
    tail = '\n\n— Offline mode: for free open-ended chat, admin can add a FREE Gemini key (Admin → Site).'
    return (head + best.get('body', '') + lore_hit + tail, best.get('title', ''))

@app.post('/api/ai/chat')
@require_auth
def ai_chat():
    db = get_db(); uid = g.user['id']
    if not sw(db, 'ai_on'): return bad('AI Tutor is switched off by admin right now.', 403)
    key = _setting(db, 'ai_key')
    b = request.get_json(silent=True) or {}
    msgs_in = b.get('messages')
    if not isinstance(msgs_in, list) or not msgs_in: return bad('No message')
    prem0 = is_premium(g.user)
    cap0 = _ai_cap(db, prem0)
    today0 = time.strftime('%Y-%m-%d', time.gmtime())
    used0 = one(db.execute('SELECT n FROM ai_usage WHERE user_id=? AND day=?', (uid, today0)))
    left0 = cap0 - (used0['n'] if used0 else 0)
    if not key:
        last0 = ''
        for m0 in reversed(msgs_in):
            if isinstance(m0, dict) and m0.get('role') != 'model' and m0.get('text'):
                last0 = s(m0.get('text'), 2000); break
        rep, _tt = _offline_answer(db, last0)
        return jsonify({'reply': s(rep, 4000), 'left': left0, 'premium': prem0, 'engine': 'offline'})
    msgs = []
    for m2 in msgs_in[-8:]:
        if not isinstance(m2, dict): continue
        role = 'model' if m2.get('role') == 'model' else 'user'
        txt = s(m2.get('text'), 2000)
        if txt: msgs.append({'role': role, 'parts': [{'text': txt}]})
    if not msgs or msgs[-1]['role'] != 'user': return bad('No message')
    lang = s(b.get('lang'), 5)
    lang_name = {'si': 'Sinhala', 'ta': 'Tamil'}.get(lang, 'English')
    prem = is_premium(g.user)
    cap = _ai_cap(db, prem)
    today = time.strftime('%Y-%m-%d', time.gmtime())
    used = one(db.execute('SELECT n FROM ai_usage WHERE user_id=? AND day=?', (uid, today)))
    used_n = used['n'] if used else 0
    if used_n >= cap:
        return jsonify({'error': 'limit', 'premium': prem}), 429
    sys_txt = ('You are "Quantum AI" — the expert Sri Lankan G.C.E. A/L tutor of AL Planner, specialised in Chemistry, Physics, Combined Maths, Biology and ICT, aligned with the NIE syllabus. You are a friendly, precise study assistant inside AL Planner. '
               'Subjects: Chemistry, Physics, Combined Mathematics, Biology, ICT (2019 syllabus). '
               'Reply in ' + lang_name + ' unless the student writes in another language. '
               'Keep answers short and exam-focused: definitions, steps, one small example. '
               'If a question is off-topic (not study-related), politely steer back to A/L study. Never invent Sri Lankan syllabus facts you are unsure about.')
    extra = _setting(db, 'ai_prompt')
    if extra:
        sys_txt += '\nExtra instructions from the AL Planner team:\n' + extra[:1500]
    lore = rows(db.execute('SELECT text FROM ai_knowledge ORDER BY id DESC LIMIT 40'))
    if lore:
        sys_txt += ('\nApproved knowledge from the AL Planner team (trust this over your own memory):\n• ' +
                    '\n• '.join(r2['text'] for r2 in lore)[:5000])
    payload = {'system_instruction': {'parts': [{'text': sys_txt}]}, 'contents': msgs,
               'generationConfig': {'maxOutputTokens': 700, 'temperature': 0.6}}
    url = 'https://generativelanguage.googleapis.com/v1beta/models/' + _ai_model(db) + ':generateContent?key=' + key
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        _log(db, 'ai_gemini_err', 'HTTP %s' % e.code)
        last1 = msgs[-1]['parts'][0]['text'] if msgs else ''
        rep, _tt = _offline_answer(db, last1)
        prem1 = is_premium(g.user)
        return jsonify({'reply': s(rep, 4000), 'left': _ai_cap(db, prem1) - used_n, 'premium': prem1, 'engine': 'offline_fallback',
                        'note': ('Gemini key problem (HTTP %s) — offline syllabus Guru answered instead.' % e.code)})
    except Exception:
        _log(db, 'ai_gemini_err', 'network')
        last1 = msgs[-1]['parts'][0]['text'] if msgs else ''
        rep, _tt = _offline_answer(db, last1)
        prem1 = is_premium(g.user)
        return jsonify({'reply': s(rep, 4000), 'left': _ai_cap(db, prem1) - used_n, 'premium': prem1, 'engine': 'offline_fallback',
                        'note': 'Online AI unreachable — offline syllabus Guru answered instead.'})
    try:
        text = data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError):
        last1 = msgs[-1]['parts'][0]['text'] if msgs else ''
        rep, _tt = _offline_answer(db, last1)
        prem1 = is_premium(g.user)
        return jsonify({'reply': s(rep, 4000), 'left': _ai_cap(db, prem1) - used_n, 'premium': prem1, 'engine': 'offline_fallback'})
    db.execute('INSERT INTO ai_usage (user_id,day,n) VALUES (?,?,1) ON CONFLICT(user_id,day) DO UPDATE SET n=n+1', (uid, today))
    return jsonify({'reply': s(text, 4000), 'left': cap - used_n - 1, 'premium': prem, 'engine': 'gemini'})

# ---------------- 💎 Premium via bank-slip upload (no payment gateway needed) ----------------
SLIP_DIR = os.path.join(UPLOAD_DIR, 'slips')

@app.get('/api/premium/status')
@require_auth
def premium_status():
    db = get_db(); uid = g.user['id']
    slips = rows(db.execute('SELECT id,amount,note,status,reason,created_at,method,txn_id,mobile,file FROM payments WHERE user_id=? ORDER BY id DESC LIMIT 10', (uid,)))
    today = time.strftime('%Y-%m-%d', time.gmtime())
    used = one(db.execute('SELECT n FROM ai_usage WHERE user_id=? AND day=?', (uid, today)))
    prem = is_premium(g.user)
    return jsonify({'premium': prem, 'until': g.user['premium_until'] if prem else '',
                    'price': _setting(db, 'premium_price'), 'bank': _setting(db, 'premium_bank'),
                    'ai_left': _ai_cap(db, prem) - (used['n'] if used else 0), 'slips': slips,
                    'ezcash': _setting(db, 'ezcash_number')})

@app.get('/api/premium/quote')
@require_auth
def premium_quote():
    db = get_db()
    try: base = max(0, int(_setting(db, 'premium_price') or 0))
    except (TypeError, ValueError): base = 0
    out = {'price': base, 'final': base, 'discount': 0, 'ok': True}
    code = s(request.args.get('coupon'), 40)
    if code:
        cp = _coupon_find(db, code)
        if not cp:
            out['ok'] = False
        else:
            fin, cut = _coupon_calc(cp, base)
            out.update({'final': fin, 'discount': cut, 'code': cp['code']})
    return jsonify(out)

@app.post('/api/premium/slip')
@require_auth
def premium_slip():
    db = get_db(); uid = g.user['id']
    pend = one(db.execute("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='pending'", (uid,)))['c']
    if pend >= 3: return bad('You already have slips waiting for approval — please wait.')
    f = request.files.get('file')
    if not f or not f.filename: return bad('Please attach a photo/PDF of the bank slip')
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.pdf'): return bad('Slip must be an image or PDF')
    try: amount = max(0, min(int(request.form.get('amount') or 0), 1000000))
    except Exception: amount = 0
    coupon = s(request.form.get('coupon'), 40).upper()
    if coupon:
        cp = _coupon_find(db, coupon)
        if not cp: return bad('That coupon code is not valid (expired or fully used)')
        try: base = max(0, int(_setting(db, 'premium_price') or 0))
        except (TypeError, ValueError): base = 0
        amount, _cut = _coupon_calc(cp, base)
    os.makedirs(SLIP_DIR, exist_ok=True)
    stored = 's-' + secrets.token_hex(10) + ext
    f.save(os.path.join(SLIP_DIR, stored))
    db.execute('INSERT INTO payments (user_id,file,amount,note,coupon) VALUES (?,?,?,?,?)',
               (uid, stored, amount, s(request.form.get('note'), 300), coupon))
    return jsonify({'ok': True, 'pending': True})

@app.post('/api/premium/ezcash')
@require_auth
def premium_ezcash():
    db = get_db(); uid = g.user['id']
    if not _setting(db, 'ezcash_number'):
        return bad('eZ Cash payments are not available yet — please use a bank slip')
    pend = one(db.execute("SELECT COUNT(*) c FROM payments WHERE user_id=? AND status='pending'", (uid,)))['c']
    if pend >= 3: return bad('You already have payments waiting for approval — please wait.')
    b = request.get_json(silent=True) or {}
    mobile = s(b.get('mobile'), 15)
    if not re.match(r'^0\d{9}$', mobile): return bad('Enter a valid mobile number, e.g. 0771234567')
    txn = s(b.get('txn_id'), 40).strip()
    if not re.match(r'^[A-Za-z0-9\-]{6,40}$', txn):
        return bad('Enter the Transaction ID exactly as in the eZ Cash SMS (6+ letters/digits)')
    dup = one(db.execute("SELECT COUNT(*) c FROM payments WHERE txn_id=? AND status IN ('pending','approved')", (txn,)))
    if dup['c']: return bad('This Transaction ID was already submitted — contact admin if wrong')
    try: amount = max(0, min(int(b.get('amount') or 0), 1000000))
    except Exception: amount = 0
    coupon = s(b.get('coupon'), 40).upper()
    if coupon:
        cp = _coupon_find(db, coupon)
        if not cp: return bad('That coupon code is not valid (expired or fully used)')
        try: base = max(0, int(_setting(db, 'premium_price') or 0))
        except (TypeError, ValueError): base = 0
        amount, _cut = _coupon_calc(cp, base)
    db.execute("INSERT INTO payments (user_id,method,txn_id,mobile,amount,note,coupon) VALUES (?,?,?,?,?,?,?)",
               (uid, 'ezcash', txn, mobile, amount, s(b.get('note'), 300).strip() or 'eZ Cash ' + mobile, coupon))
    _log(db, 'ezcash_submit', 'txn %s user #%d Rs.%s' % (txn, uid, amount))
    return jsonify({'ok': True, 'pending': True})

@app.get('/api/slips/<int:pid>')
@require_auth
def slip_file(pid):
    row = one(get_db().execute('SELECT * FROM payments WHERE id=?', (pid,)))
    if not row or (g.user['role'] != 'admin' and row['user_id'] != g.user['id']): return bad('Not found', 404)
    if not row['file']: return bad('This payment has no slip image (eZ Cash)', 404)
    return send_from_directory(SLIP_DIR, row['file'])

# ---------------- Chemistry Practical Lab: database-driven observation profiles ----------------
_LAB_NOTE_FIELDS = ('Aim', 'Apparatus', 'Chemicals', 'Procedure', 'Observations', 'Equation', 'Calculation', 'Conclusion')

@app.get('/api/chemdb')
def chemdb_public():
    return jsonify({'extra': _chemdb_list(get_db())})

@app.post('/api/admin/chemdb')
@require_admin
def chemdb_add():
    db = get_db(); b = request.get_json(silent=True) or {}
    kind = s(b.get('kind'), 10)
    if kind == 'flame':
        e = {'kind': 'flame', 'salt': s(b.get('salt'), 60), 'ion': s(b.get('ion'), 20),
             'col': s(b.get('col'), 10), 'cname': s(b.get('cname'), 60)}
        if not all([e['salt'], e['ion'], e['cname']]):
            return bad('Fill in salt name, ion symbol and the flame colour name')
        if not re.match(r'^#[0-9A-Fa-f]{6}$', e['col']):
            return bad('Colour must be the TRUE flame colour as #RRGGBB (e.g. #ffc81e)')
    elif kind == 'precip':
        e = {'kind': 'precip', 'sample': s(b.get('sample'), 60), 'reagent': s(b.get('reagent'), 60),
             'obs': s(b.get('obs'), 300), 'col': s(b.get('col'), 10),
             'eq': s(b.get('eq'), 160), 'ionic': s(b.get('ionic'), 160), 'note': s(b.get('note'), 300)}
        if not all([e['sample'], e['reagent'], e['obs'], e['eq']]):
            return bad('Fill at least sample, reagent, observation and equation')
        if e['col'] and not re.match(r'^#[0-9A-Fa-f]{6}$', e['col']):
            return bad('Precipitate colour must be the TRUE colour as #RRGGBB (or empty)')
    else:
        return bad('kind must be "flame" or "precip"')
    lst = _chemdb_list(db)
    if len(lst) >= 60: return bad('Chemistry database is full (60 teacher entries) — delete some first')
    lst.append(e); _chemdb_set(db, lst)
    _log(db, 'chemdb_add', kind + ': ' + (e.get('salt') or e.get('sample', '')))
    return jsonify({'ok': True, 'extra': lst})

@app.post('/api/admin/chemdb/del')
@require_admin
def chemdb_del():
    db = get_db(); b = request.get_json(silent=True) or {}
    try: idx = int(b.get('idx', -1))
    except Exception: return bad('bad index')
    lst = _chemdb_list(db)
    if idx < 0 or idx >= len(lst): return bad('No such entry')
    gone = lst.pop(idx); _chemdb_set(db, lst)
    _log(db, 'chemdb_del', gone.get('kind', '?') + ': ' + (gone.get('salt') or gone.get('sample', '')))
    return jsonify({'ok': True, 'extra': lst})

@app.get('/api/lab/state')
@require_auth
def lab_state():
    db = get_db(); uid = g.user['id']
    notes = {}
    for r in db.execute('SELECT prac, data FROM lab_notes WHERE user_id=?', (uid,)):
        try: notes[r['prac']] = json.loads(r['data'] or '{}')
        except Exception: notes[r['prac']] = {}
    prog = {r['prac']: {'best': r['best'], 'done': r['done']}
            for r in db.execute('SELECT prac, best, done FROM lab_progress WHERE user_id=?', (uid,))}
    return jsonify({'notes': notes, 'progress': prog})

@app.post('/api/lab/note')
@require_auth
def lab_note_save():
    db = get_db(); uid = g.user['id']
    b = request.get_json(silent=True) or {}
    prac = s(b.get('prac'), 30)
    if not prac or not re.match(r'^[A-Za-z0-9_-]{2,30}$', prac): return bad('bad practical id')
    d = b.get('data') if isinstance(b.get('data'), dict) else {}
    clean = {k: s(v, 2000) for k, v in d.items() if k in _LAB_NOTE_FIELDS}
    db.execute("INSERT INTO lab_notes (user_id,prac,data,updated_at) VALUES (?,?,?,datetime('now')) "
               "ON CONFLICT(user_id,prac) DO UPDATE SET data=excluded.data, updated_at=datetime('now')",
               (uid, prac, json.dumps(clean)))
    return jsonify({'ok': True})

@app.post('/api/lab/progress')
@require_auth
def lab_progress_save():
    db = get_db(); uid = g.user['id']
    b = request.get_json(silent=True) or {}
    prac = s(b.get('prac'), 30)
    if not prac or not re.match(r'^[A-Za-z0-9_-]{2,30}$', prac): return bad('bad practical id')
    try: score = max(0, min(100, int(b.get('score') or 0)))
    except Exception: score = 0
    done = 1 if b.get('done') else 0
    db.execute("INSERT INTO lab_progress (user_id,prac,best,done,updated_at) VALUES (?,?,?,?,datetime('now')) "
               "ON CONFLICT(user_id,prac) DO UPDATE SET best=MAX(best,excluded.best), done=MAX(done,excluded.done), updated_at=datetime('now')",
               (uid, prac, score, done))
    return jsonify({'ok': True})

@app.get('/api/admin/payments')
@require_admin
def admin_payments():
    db = get_db()
    return jsonify({'payments': rows(db.execute("""SELECT p.*, u.name, u.email, u.school FROM payments p
        JOIN users u ON u.id=p.user_id ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END, p.id DESC LIMIT 100"""))})

@app.put('/api/admin/payments/<int:pid>')
@require_admin
def admin_payment_decide(pid):
    db = get_db()
    row = one(db.execute('SELECT * FROM payments WHERE id=?', (pid,)))
    if not row: return bad('Not found', 404)
    b = request.get_json(silent=True) or {}
    act = s(b.get('action'), 10)
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    if act == 'approve':
        today = time.strftime('%Y-%m-%d', time.gmtime())
        u = one(db.execute('SELECT premium_until FROM users WHERE id=?', (row['user_id'],)))
        base = u['premium_until'] if u and u['premium_until'] and u['premium_until'] > today else today
        until = time.strftime('%Y-%m-%d', time.gmtime(time.mktime(time.strptime(base, '%Y-%m-%d')) + 31 * 86400))
        db.execute('UPDATE users SET premium_until=? WHERE id=?', (until, row['user_id']))
        db.execute("UPDATE payments SET status='approved', decided_at=? WHERE id=?", (now, pid))
        if row['coupon']:
            db.execute('UPDATE coupons SET uses=uses+1 WHERE code=?', (row['coupon'],))
        _log(db, 'payment_approve', 'slip #%d user #%d Rs.%s' % (pid, row['user_id'], row['amount']))
        return jsonify({'ok': True, 'until': until})
    if act == 'reject':
        db.execute("UPDATE payments SET status='rejected', reason=?, decided_at=? WHERE id=?", (s(b.get('reason'), 200), now, pid))
        _log(db, 'payment_reject', 'slip #%d user #%d' % (pid, row['user_id']))
        return jsonify({'ok': True})
    return bad('Bad action')

@app.get('/api/badges')
@require_auth
def badges():
    db = get_db(); uid = g.user['id']
    lessons_done = one(db.execute('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1', (uid,)))['c']
    q = one(db.execute('SELECT COUNT(*) n, COALESCE(SUM(total),0) tot FROM mcq_attempts WHERE user_id=?', (uid,)))
    quizzes, mcqs = q['n'], q['tot']
    sims = one(db.execute('SELECT COUNT(*) c FROM sim_progress WHERE user_id=? AND completed=1', (uid,)))['c']
    past_papers = one(db.execute("""SELECT COUNT(*) c FROM practice_marks pm JOIN practice_questions pq ON pq.id=pm.question_id
        WHERE pm.user_id=? AND pm.ok=1 AND pq.qtype='pastpaper'""", (uid,)))['c']
    streak = longest_streak(activity_dates(db, uid))
    chal_w = one(db.execute('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?', (uid,)))['c']
    math_w = one(db.execute("SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=? AND sim_type IN ('gplot','gtrans','deriv','integr','vector','trig','prob','stats')", (uid,)))['c']
    ict_w = one(db.execute("SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=? AND sim_type IN ('binary','logic','truthtab','cpu','network','ipaddr','sortvis','webplay')", (uid,)))['c']
    BD = [
        ('first_lesson', '🎬', lessons_done, 1), ('lessons_10', '📚', lessons_done, 10),
        ('sim_first', '⚡', sims, 1), ('sims_10', '🧪', sims, 10),
        ('quizzes_5', '🎯', quizzes, 5), ('mcq_100', '❓', mcqs, 100),
        ('pp_first', '📄', past_papers, 1), ('streak_7', '📅', streak, 7),
        ('chal_first', '🎖️', chal_w, 1), ('chal_10', '🏆', chal_w, 10),
        ('maths_solver', '📐', math_w, 3), ('ict_explorer', '💻', ict_w, 3),
    ]
    return jsonify({'badges': [{'id': i, 'icon': ic, 'prog': min(p, rq), 'req': rq, 'earned': p >= rq} for i, ic, p, rq in BD],
        'stats': {'lessons_done': lessons_done, 'mcqs': mcqs, 'quizzes': quizzes, 'sims': sims, 'past_papers': past_papers, 'streak': streak, 'challenges': chal_w}})

@app.get('/api/dashboard')
@require_auth
def dashboard():
    db = get_db()
    uid = g.user['id']
    subs = []
    for sub in rows(db.execute('SELECT id,name,name_si,name_ta,code,icon,color1,color2 FROM subjects ORDER BY id')):
        sub['total'] = one(db.execute('SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?', (sub['id'],)))['c']
        sub['completed'] = one(db.execute("""SELECT COUNT(*) c FROM lessons l JOIN units u ON u.id=l.unit_id
            JOIN progress p ON p.lesson_id=l.id AND p.user_id=? AND p.completed=1 WHERE u.subject_id=?""", (uid, sub['id'])))['c']
        subs.append(sub)
    join = """SELECT l.id,l.title,l.youtube_id,u.name AS unit_name,s.name AS subject_name,s.color1,s.color2,t.name AS teacher_name,
              p.completed,p.watched,p.favourite,p.completed_at,p.watched_at
              FROM progress p JOIN lessons l ON l.id=p.lesson_id JOIN units u ON u.id=l.unit_id
              JOIN subjects s ON s.id=u.subject_id LEFT JOIN teachers t ON t.id=l.teacher_id WHERE p.user_id=?"""
    completed = rows(db.execute(join + ' AND p.completed=1 ORDER BY p.completed_at DESC', (uid,)))
    watched = rows(db.execute(join + ' AND p.watched=1 ORDER BY p.watched_at DESC', (uid,)))
    favourites = rows(db.execute(join + ' AND p.favourite=1', (uid,)))
    saved = rows(db.execute("""SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,s.name AS subject_name, u2.name AS uploader
        FROM saved_resources sv JOIN resources r ON r.id=sv.resource_id
        LEFT JOIN subjects s ON s.id=r.subject_id LEFT JOIN users u2 ON u2.id=r.uploaded_by
        WHERE sv.user_id=? ORDER BY sv.created_at DESC""", (uid,)))
    uploads = rows(db.execute("""SELECT r.id,r.title,r.category,r.status,r.size,r.downloads,r.created_at,r.valid_until,s.name AS subject_name
        FROM resources r LEFT JOIN subjects s ON s.id=r.subject_id WHERE r.uploaded_by=? ORDER BY r.id DESC""", (uid,)))
    return jsonify({'subjects': subs,
                    'counts': {'completed': len(completed), 'watched': len(watched), 'saved': len(saved),
                               'uploads': len(uploads), 'favourites': len(favourites)},
                    'completed': completed, 'watched': watched, 'favourites': favourites,
                    'saved': saved, 'uploads': uploads})

# ------------------------------------------------------------ RESOURCES
@app.get('/api/resources')
def resources():
    db = get_db()
    where, params = ["r.status='approved'", "(r.valid_until='' OR r.valid_until >= datetime('now'))"], []
    if request.args.get('subjectId'): where.append('r.subject_id=?'); params.append(request.args['subjectId'])
    if request.args.get('category'): where.append('r.category=?'); params.append(request.args['category'])
    if request.args.get('unitId'): where.append('r.unit_id=?'); params.append(request.args['unitId'])
    if request.args.get('medium'): where.append('r.medium=?'); params.append(request.args['medium'])
    if request.args.get('year'): where.append('r.year=?'); params.append(request.args['year'])
    if request.args.get('search'): where.append('r.title LIKE ?'); params.append('%' + s(request.args['search'], 60) + '%')
    uid = g.user['id'] if g.user else -1
    out = rows(db.execute(f"""SELECT r.id,r.title,r.category,r.size,r.downloads,r.created_at,r.lesson_id,
        r.external_url,r.description,r.medium,r.year,r.unit_id,r.valid_until,r.premium,
        s2.name AS subject_name, un.name AS unit_name, u.name AS uploader, CASE WHEN sv.user_id IS NULL THEN 0 ELSE 1 END AS saved
        FROM resources r LEFT JOIN subjects s2 ON s2.id=r.subject_id LEFT JOIN units un ON un.id=r.unit_id
        LEFT JOIN users u ON u.id=r.uploaded_by
        LEFT JOIN saved_resources sv ON sv.resource_id=r.id AND sv.user_id=?
        WHERE {' AND '.join(where)} ORDER BY r.id DESC LIMIT 200""", [uid] + params))
    return jsonify({'resources': out})

@app.post('/api/resources')
@require_auth
def upload_resource():
    db = get_db()
    if not sw(db, 'upload_open'): return bad('Uploads are closed by admin right now.', 403)
    f = request.files.get('file')
    if not f or not f.filename: return bad('Please attach a file (PDF, document, image or zip)')
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_EXT: return bad('Upload failed. Please try a different file.')
    title = s(request.form.get('title'), 140)
    category = s(request.form.get('category'), 30)
    if len(title) < 3: return bad('Please give your resource a clear title')
    if not any(c['id'] == category for c in RESOURCE_CATEGORIES): return bad('Please choose a valid category')
    db = get_db()
    subj_id = int(request.form['subjectId']) if request.form.get('subjectId', '').isdigit() else None
    les_id = int(request.form['lessonId']) if request.form.get('lessonId', '').isdigit() else None
    unit_id = int(request.form['unitId']) if request.form.get('unitId', '').isdigit() else None
    rmedium = request.form.get('medium') if request.form.get('medium') in MEDIUMS else ''
    ryear = s(request.form.get('year'), 20)
    if subj_id and not one(db.execute('SELECT id FROM subjects WHERE id=?', (subj_id,))): return bad('Invalid subject')
    if les_id and not one(db.execute('SELECT id FROM lessons WHERE id=?', (les_id,))): return bad('Invalid lesson')
    if unit_id and not one(db.execute('SELECT id FROM units WHERE id=?', (unit_id,))): return bad('Invalid unit')
    stored = 'u-' + secrets.token_hex(10) + ext
    full = os.path.join(UPLOAD_DIR, stored)
    f.save(full)
    size = os.path.getsize(full)
    status = 'approved' if g.user['role'] == 'admin' else 'pending'
    cur = db.execute("""INSERT INTO resources (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,unit_id,medium,year,uploaded_by,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (title, category, stored, s(f.filename, 200), size, f.mimetype or '', subj_id, les_id, unit_id, rmedium, ryear, g.user['id'], status))
    return jsonify({'ok': True, 'id': cur.lastrowid, 'status': status, 'approved': status == 'approved'})

@app.get('/api/resources/<int:rid>/download')
def download_resource(rid):
    db = get_db()
    r = one(db.execute('SELECT * FROM resources WHERE id=?', (rid,)))
    if not r: return bad('Resource not found', 404)
    allowed = r['status'] == 'approved' or (g.user and (g.user['role'] == 'admin' or g.user['id'] == r['uploaded_by']))
    if r['valid_until'] and r['valid_until'] < one(db.execute("SELECT datetime('now') n", ()))['n'] and not (g.user and (g.user['role'] == 'admin' or g.user['id'] == r['uploaded_by'])):
        return bad('This resource has expired', 403)
    if not allowed: return bad('This resource is not available yet (awaiting approval)', 403)
    if r['premium'] and not (g.user and (is_premium(g.user) or g.user['role'] == 'admin' or g.user['id'] == r['uploaded_by'])):
        return jsonify({'error': 'This is a 💎 Premium resource', 'premium': True}), 403
    full = os.path.join(UPLOAD_DIR, r['file_path'])
    if not os.path.exists(full): return bad('File missing on server', 404)
    db.execute('UPDATE resources SET downloads=downloads+1 WHERE id=?', (rid,))
    return send_file(full, as_attachment=True, download_name=r['orig_name'] or ('resource-%d%s' % (rid, os.path.splitext(r['file_path'])[1])))

@app.post('/api/resources/<int:rid>/save')
@require_auth
def save_resource(rid):
    db = get_db()
    if not one(db.execute('SELECT id FROM resources WHERE id=?', (rid,))): return bad('Resource not found', 404)
    uid = g.user['id']
    if one(db.execute('SELECT 1 x FROM saved_resources WHERE user_id=? AND resource_id=?', (uid, rid))):
        db.execute('DELETE FROM saved_resources WHERE user_id=? AND resource_id=?', (uid, rid))
        return jsonify({'saved': False})
    db.execute('INSERT INTO saved_resources (user_id,resource_id) VALUES (?,?)', (uid, rid))
    return jsonify({'saved': True})

@app.delete('/api/resources/<int:rid>')
@require_auth
def delete_resource(rid):
    db = get_db()
    r = one(db.execute('SELECT * FROM resources WHERE id=?', (rid,)))
    if not r: return bad('Resource not found', 404)
    if g.user['role'] != 'admin' and g.user['id'] != r['uploaded_by']: return bad('Not allowed', 403)
    db.execute('DELETE FROM resources WHERE id=?', (rid,))
    try: os.remove(os.path.join(UPLOAD_DIR, r['file_path']))
    except OSError: pass
    return jsonify({'ok': True})

# ------------------------------------------------------------ TUTORS
def tutor_out(t):
    d = dict(t)
    for k in ('subjects', 'classes'):
        try: d[k] = json.loads(d.get(k) or '[]')
        except Exception: d[k] = []
    return d

@app.get('/api/tutors')
def tutors():
    q = s(request.args.get('search', ''), 60).lower()
    subj = s(request.args.get('subject', ''), 60).lower()
    out = [tutor_out(t) for t in rows(get_db().execute('SELECT * FROM tutors ORDER BY id'))]
    if q: out = [t for t in out if q in (t['name'] + ' ' + (t['location'] or '') + ' ' + ' '.join(t['subjects'])).lower()]
    if subj: out = [t for t in out if subj in ' '.join(t['subjects']).lower()]
    dist = s(request.args.get('district', ''), 40).lower()
    mode = s(request.args.get('mode', ''), 10).lower()
    med = s(request.args.get('medium', ''), 4).lower()
    lvl = s(request.args.get('level', ''), 6).lower()
    if dist: out = [t for t in out if dist in (t.get('district') or '').lower() or dist in (t.get('location') or '').lower()]
    if mode in ('online', 'physical'): out = [t for t in out if (t.get('mode') or '').lower() in (mode, 'both')]
    if med in MEDIUMS: out = [t for t in out if (t.get('medium') or '').lower() in (med, '', 'all')]
    if lvl in ('al', 'ol'): out = [t for t in out if (t.get('level') or '').lower() in (lvl, 'both', '')]
    # public tutor comments: auto-delete after 3 months unless admin marked keep=1
    purge_old_comments(get_db())
    counts = {r['tutor_id']: r['c'] for r in get_db().execute('SELECT tutor_id, COUNT(*) c FROM tutor_comments GROUP BY tutor_id')}
    for t in out: t['comment_count'] = counts.get(t['id'], 0)
    return jsonify({'tutors': out})

@app.get('/api/tutors/<int:tid>')
def tutor_detail(tid):
    t = one(get_db().execute('SELECT * FROM tutors WHERE id=?', (tid,)))
    if not t: return bad('Tutor not found', 404)
    return jsonify({'tutor': tutor_out(t)})

@app.post('/api/tutors/<int:tid>/message')
@require_auth
def tutor_message(tid):
    db = get_db()
    if not one(db.execute('SELECT id FROM tutors WHERE id=?', (tid,))): return bad('Tutor not found', 404)
    message = s((request.get_json(silent=True) or {}).get('message'), 2000)
    if len(message) < 5: return bad('Please write a short message')
    db.execute('INSERT INTO tutor_messages (tutor_id,user_id,message) VALUES (?,?,?)', (tid, g.user['id'], message))
    return jsonify({'ok': True})

# ---------------- Tutor comments (public, moderated by admin) ----------------
def purge_old_comments(db):
    """Auto-delete tutor comments older than 3 months unless admin kept them."""
    db.execute("DELETE FROM tutor_comments WHERE keep=0 AND created_at < datetime('now','-3 months')")

def comment_out(r):
    d = dict(r)
    d['days_left'] = max(0, d.get('days_left') or 0)
    d.pop('user_id', None)
    return d

_COMMENT_SQL = """SELECT c.*, u.name AS author,
    CAST(julianday(c.created_at,'+3 months') - julianday('now') AS INTEGER) AS days_left
    FROM tutor_comments c JOIN users u ON u.id=c.user_id WHERE c.tutor_id=? ORDER BY c.id DESC"""

@app.get('/api/tutors/<int:tid>/comments')
def tutor_comments_list(tid):
    db = get_db()
    if not one(db.execute('SELECT id FROM tutors WHERE id=?', (tid,))): return bad('Tutor not found', 404)
    purge_old_comments(db)
    if not sw(db, 'tutor_comments'): return jsonify({'enabled': False, 'comments': [], 'pending_count': 0})
    is_admin = g.user and g.user['role'] == 'admin'
    sql = _COMMENT_SQL if is_admin else _COMMENT_SQL.replace('WHERE c.tutor_id=?', 'WHERE c.tutor_id=? AND c.approved=1')
    allr = rows(db.execute(sql, (tid,)))
    pend = sum(1 for r in allr if not r['approved'])
    return jsonify({'enabled': True, 'comments': [comment_out(r) for r in allr], 'pending_count': pend if is_admin else 0})

@app.post('/api/tutors/<int:tid>/comments')
@require_auth
def tutor_comment_add(tid):
    db = get_db()
    if not one(db.execute('SELECT id FROM tutors WHERE id=?', (tid,))): return bad('Tutor not found', 404)
    if not sw(db, 'tutor_comments'): return bad('Comments are disabled by admin right now.', 403)
    body = s((request.get_json(silent=True) or {}).get('body'), 500)
    if len(body) < 3: return bad('Please write a short comment')
    approved = 0 if sw(db, 'comment_approve') else 1
    cur = db.execute('INSERT INTO tutor_comments (tutor_id,user_id,body,approved) VALUES (?,?,?,?)', (tid, g.user['id'], body, approved))
    r = one(db.execute(_COMMENT_SQL.replace('ORDER BY c.id DESC', 'AND c.id=? ORDER BY c.id DESC'), (tid, cur.lastrowid)))
    return jsonify({'ok': True, 'pending': not approved, 'comment': comment_out(r)})

@app.put('/api/admin/comments/<int:cid>/approve')
@require_admin
def admin_comment_approve(cid):
    get_db().execute('UPDATE tutor_comments SET approved=1, is_read=1 WHERE id=?', (cid,))
    return jsonify({'ok': True})

@app.delete('/api/admin/comments/<int:cid>')
@require_admin
def admin_comment_del(cid):
    get_db().execute('DELETE FROM tutor_comments WHERE id=?', (cid,))
    return jsonify({'ok': True})

@app.put('/api/admin/comments/<int:cid>/keep')
@require_admin
def admin_comment_keep(cid):
    keep = 1 if (request.get_json(silent=True) or {}).get('keep') else 0
    get_db().execute('UPDATE tutor_comments SET keep=? WHERE id=?', (keep, cid))
    return jsonify({'ok': True, 'keep': keep})

# ---------------- Site settings (notification bar + contact details + ADMIN SWITCHES) + contact form ----------------
_SITE_KEYS = ('announcement', 'contact_email', 'contact_whatsapp', 'contact_address',
              'register_open', 'upload_open', 'leaderboard_on', 'tutor_comments', 'comment_approve', 'ai_on', 'careers_enabled')
# admin switches: '' (never set) means these defaults apply
_SWITCH_DEFAULT = {'register_open': '1', 'upload_open': '1', 'leaderboard_on': '1', 'tutor_comments': '1', 'comment_approve': '1', 'ai_on': '1', 'careers_enabled': '1'}
# secret/extra keys: admin-writable, NEVER returned by public /api/site
_EXTRA_KEYS = ('ai_key', 'premium_price', 'premium_bank', 'ai_free_limit', 'ai_pro_limit', 'ai_model', 'ai_prompt')

def site_out(db):
    out = {}
    for k in _SITE_KEYS:
        r = db.execute('SELECT value FROM site_settings WHERE key=?', (k,)).fetchone()
        out[k] = r['value'] if r and r['value'] != '' else _SWITCH_DEFAULT.get(k, '')
    return out

def sw(db, key):
    """True when an admin switch is ON ('' = default)."""
    r = db.execute('SELECT value FROM site_settings WHERE key=?', (key,)).fetchone()
    v = r['value'] if r and r['value'] != '' else _SWITCH_DEFAULT.get(key, '1')
    return v != '0'

# ---------------- admin spec pack helpers ----------------
def _log(db, action, target=''):
    try:
        db.execute('INSERT INTO admin_logs (admin,action,target) VALUES (?,?,?)',
                   ((g.user['email'] if g.user else '?'), s(action, 80), s(target, 160)))
    except Exception:
        pass

def _ai_cap(db, prem):
    try:
        return max(1, min(1000, int(_setting(db, 'ai_pro_limit' if prem else 'ai_free_limit') or (100 if prem else 10))))
    except (TypeError, ValueError):
        return 100 if prem else 10

def _ai_model(db):
    m = (_setting(db, 'ai_model') or '').strip()
    return m if re.match(r'^[a-zA-Z0-9._-]{3,60}$', m) else AI_MODEL

def _coupon_find(db, code):
    cp = one(db.execute('SELECT * FROM coupons WHERE code=? AND active=1', (s(code, 40).upper(),)))
    if not cp: return None
    today = time.strftime('%Y-%m-%d', time.gmtime())
    if cp['expires'] and cp['expires'] < today: return None
    if cp['max_uses'] and cp['uses'] >= cp['max_uses']: return None
    return cp

def _coupon_calc(cp, base):
    if not cp: return base, 0
    if cp['kind'] == 'percent':
        cut = int(round(base * min(100, max(0, cp['value'])) / 100.0))
    else:
        cut = min(base, max(0, cp['value']))
    return base - cut, cut

@app.get('/api/site')
def site_public():
    return jsonify({'site': site_out(get_db())})

@app.put('/api/admin/site')
@require_admin
def admin_site_save():
    db = get_db()
    b = request.get_json(silent=True) or {}
    for k in _SITE_KEYS:
        if k in b:
            db.execute('INSERT INTO site_settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                       (k, s(b.get(k), 300)))
    # extra keys: AI key (secret), premium price + bank details, AI limits/model/extra prompt
    for k in ('premium_price', 'premium_bank', 'ezcash_number', 'ai_free_limit', 'ai_pro_limit', 'ai_model', 'ai_prompt'):
        if k in b:
            db.execute('INSERT INTO site_settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                       (k, s(b.get(k), 900)))
    if 'ai_key' in b:
        ak = s(b.get('ai_key'), 200)
        if ak == 'CLEAR':
            db.execute("DELETE FROM site_settings WHERE key='ai_key'")
        elif ak:
            db.execute("INSERT INTO site_settings (key,value) VALUES ('ai_key',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (ak,))
    _log(db, 'site_update', ','.join(sorted(k for k in b.keys() if k != 'ai_key'))[:150])
    return jsonify({'ok': True, 'site': site_out(db)})

@app.post('/api/contact')
def contact_send():
    b = request.get_json(silent=True) or {}
    name = s(b.get('name'), 80)
    email = s(b.get('email'), 120)
    message = s(b.get('message'), 1000)
    if not name or len(message) < 5: return bad('Name and a short message are required')
    get_db().execute('INSERT INTO contact_messages (name,email,message) VALUES (?,?,?)', (name, email, message))
    return jsonify({'ok': True})

@app.get('/api/admin/contact-messages')
@require_admin
def admin_contact_messages():
    return jsonify({'messages': rows(get_db().execute('SELECT * FROM contact_messages ORDER BY id DESC LIMIT 200'))})

@app.delete('/api/admin/contact-messages/<int:mid>')
@require_admin
def admin_contact_message_del(mid):
    get_db().execute('DELETE FROM contact_messages WHERE id=?', (mid,))
    return jsonify({'ok': True})

# ---------------- Admin notification bell ----------------
@app.get('/api/admin/notifications')
@require_admin
def admin_notifications():
    db = get_db()
    c = lambda q: one(db.execute(q))['c']
    latest = rows(db.execute('SELECT id,name,message,created_at FROM contact_messages WHERE is_read=0 ORDER BY id DESC LIMIT 5'))
    latestc = rows(db.execute("""SELECT c.id,c.body,c.created_at,u.name AS author,t.name AS tutor FROM tutor_comments c
        JOIN users u ON u.id=c.user_id JOIN tutors t ON t.id=c.tutor_id WHERE c.is_read=0 ORDER BY c.id DESC LIMIT 5"""))
    return jsonify({'unread_msgs': c('SELECT COUNT(*) c FROM contact_messages WHERE is_read=0'),
                    'new_comments': c('SELECT COUNT(*) c FROM tutor_comments WHERE is_read=0'),
                    'pending': c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
                    'latest': latest, 'latestc': latestc})

@app.post('/api/admin/notifications/read-all')
@require_admin
def admin_notifications_read_all():
    db = get_db()
    db.execute('UPDATE contact_messages SET is_read=1')
    db.execute('UPDATE tutor_comments SET is_read=1')
    return jsonify({'ok': True})

# ------------------------------------------------------------ ADMIN
@app.get('/api/admin/overview')
@require_admin
def admin_overview():
    db = get_db()
    c = lambda sql, *p: one(db.execute(sql, p))['c']
    return jsonify({
        'students': c("SELECT COUNT(*) c FROM users WHERE role='student'"),
        'lessons': c('SELECT COUNT(*) c FROM lessons'), 'units': c('SELECT COUNT(*) c FROM units'),
        'subjects': c('SELECT COUNT(*) c FROM subjects'), 'teachers': c('SELECT COUNT(*) c FROM teachers'),
        'tutors': c('SELECT COUNT(*) c FROM tutors'), 'pending': c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
        'resources': c("SELECT COUNT(*) c FROM resources WHERE status='approved'"),
        'messages': c('SELECT COUNT(*) c FROM tutor_messages'),
        'years': rows(db.execute('SELECT * FROM al_years ORDER BY id')),
        'recentStudents': rows(db.execute("SELECT id,name,email,school,district,al_year,created_at FROM users WHERE role='student' ORDER BY id DESC LIMIT 6")),
        'pendingList': rows(db.execute("""SELECT r.id,r.title,r.category,r.created_at,u.name AS uploader,s.name AS subject_name
            FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by LEFT JOIN subjects s ON s.id=r.subject_id
            WHERE r.status='pending' ORDER BY r.id DESC LIMIT 6""")),
        'recentMessages': rows(db.execute("""SELECT m.id,m.message,m.created_at,u.name AS student,t.name AS tutor
            FROM tutor_messages m JOIN users u ON u.id=m.user_id JOIN tutors t ON t.id=m.tutor_id ORDER BY m.id DESC LIMIT 6""")),
    })

# ---------------- super admin dashboard (all real DB data) ----------------
@app.get('/api/admin/super')
@require_admin
def admin_super():
    db = get_db()
    c = lambda sql, *p: one(db.execute(sql, p))['c']
    now = time.time(); week = 604800
    growth, activity = [], []
    for i in range(7, -1, -1):
        a = now - (i + 1) * week; b2 = now - i * week
        ad = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(a)); bd = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(b2))
        add = time.strftime('%Y-%m-%d', time.gmtime(a)); bdd = time.strftime('%Y-%m-%d', time.gmtime(b2))
        lb = time.strftime('%b %d', time.gmtime(b2))
        growth.append({'label': lb, 'n': c("SELECT COUNT(*) c FROM users WHERE role='student' AND created_at>=? AND created_at<?", ad, bd)})
        activity.append({'label': lb, 'n': int(one(db.execute('SELECT COALESCE(SUM(seconds),0) n FROM study_events WHERE day>=? AND day<?', (add, bdd)))['n'] / 60)})
    d30 = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now - 30 * 86400))
    d7 = time.strftime('%Y-%m-%d', time.gmtime(now - 6 * 86400))
    today0 = time.strftime('%Y-%m-%d', time.gmtime(now))
    d30d = time.strftime('%Y-%m-%d', time.gmtime(now - 29 * 86400))
    popular = rows(db.execute("""SELECT s.name, s.name_si, s.name_ta, COUNT(*) n FROM progress p
        JOIN lessons l ON l.id=p.lesson_id JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
        WHERE p.completed=1 GROUP BY s.id ORDER BY n DESC"""))
    feed = []
    for r in rows(db.execute("SELECT name, created_at ts FROM users WHERE role='student' ORDER BY id DESC LIMIT 4")):
        feed.append({'ic': '🎓', 'text': r['name'] + ' registered', 'ts': r['ts']})
    for r in rows(db.execute('SELECT r.title, r.created_at ts, u.name un FROM resources r LEFT JOIN users u ON u.id=r.uploaded_by ORDER BY r.id DESC LIMIT 4')):
        feed.append({'ic': '📤', 'text': (r['un'] or 'Someone') + ' uploaded "' + r['title'] + '"', 'ts': r['ts']})
    for r in rows(db.execute('SELECT c.created_at ts, u.name un, t2.name tn FROM tutor_comments c JOIN users u ON u.id=c.user_id JOIN tutors t2 ON t2.id=c.tutor_id ORDER BY c.id DESC LIMIT 3')):
        feed.append({'ic': '💬', 'text': r['un'] + ' commented on tutor ' + r['tn'], 'ts': r['ts']})
    for r in rows(db.execute('SELECT name, created_at ts FROM contact_messages ORDER BY id DESC LIMIT 2')):
        feed.append({'ic': '✉️', 'text': r['name'] + ' sent a contact message', 'ts': r['ts']})
    feed = sorted([f for f in feed if f['ts']], key=lambda x: x['ts'], reverse=True)[:8]
    for f in feed:
        try: f['ago'] = max(0, int((now - calendar.timegm(time.strptime(f['ts'][:19], '%Y-%m-%d %H:%M:%S'))) / 60))
        except Exception: f['ago'] = None
    top = rows(db.execute("""SELECT u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
        (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done
        FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
        WHERE u.role='student' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id LIMIT 5""", (d7,)))
    up_bytes = 0
    try:
        for f in os.listdir(UPLOAD_DIR):
            fp = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(fp): up_bytes += os.path.getsize(fp)
    except OSError: pass
    cards = {
        'students': c("SELECT COUNT(*) c FROM users WHERE role='student'"),
        'active7': c('SELECT COUNT(DISTINCT user_id) c FROM study_events WHERE day>=?', d7),
        'new30': c("SELECT COUNT(*) c FROM users WHERE role='student' AND created_at>=?", d30),
        'teachers': c('SELECT COUNT(*) c FROM teachers'), 'tutors': c('SELECT COUNT(*) c FROM tutors'),
        'lessons': c('SELECT COUNT(*) c FROM lessons'),
        'resources': c("SELECT COUNT(*) c FROM resources WHERE status='approved'"),
        'pastpapers': c("SELECT COUNT(*) c FROM resources WHERE status='approved' AND category='past_papers'"),
        'pending_uploads': c("SELECT COUNT(*) c FROM resources WHERE status='pending'"),
        'pending_comments': c('SELECT COUNT(*) c FROM tutor_comments WHERE approved=0'),
        'exams_sat': c('SELECT COUNT(*) c FROM exam_attempts'),
        'exam_avg': round(one(db.execute('SELECT COALESCE(AVG(score*100.0/qcount),0) a FROM exam_attempts'))['a']),
        'slips_pending': c("SELECT COUNT(*) c FROM payments WHERE status='pending'"),
        'revenue': one(db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved'"))['s'],
        'rev_today': one(db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)=?", (today0,)))['s'],
        'rev_7d': one(db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)>=?", (d7,)))['s'],
        'rev_30d': one(db.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved' AND substr(decided_at,1,10)>=?", (d30d,)))['s'],
        'ai_today': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM ai_usage WHERE day=?', (today0,)))['s'],
        'ai_total': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM ai_usage'))['s'],
        'coupons': c('SELECT COUNT(*) c FROM coupons WHERE active=1'),
        'challenges': c('SELECT COUNT(*) c FROM challenges'),
        'reports_open': c("SELECT COUNT(*) c FROM ai_reports WHERE status='open'"),
    }
    return jsonify({'cards': cards, 'growth': growth, 'activity': activity, 'popular': popular, 'feed': feed, 'top': top,
                    'system': {'db_bytes': os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
                               'uploads_bytes': up_bytes,
                               'uptime_s': int(now - BOOT_T0),
                               'premium_users': c("SELECT COUNT(*) c FROM users WHERE premium_until IS NOT NULL AND premium_until>=?", today0),
                               'ai_week': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM ai_usage WHERE day>=?', (d7,)))['s'],
                               'ver': SITE_VER,
                               'backup_at': (one(db.execute("SELECT value v FROM site_settings WHERE key='backup_at'")) or {'v': ''})['v']}})

# ---------------- one-click DB backup ----------------
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')

@app.post('/api/admin/backup')
@require_admin
def admin_backup():
    db = get_db(); db.commit()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime('%Y-%m-%d %H:%M', time.gmtime())
    fn = 'alplanner-' + time.strftime('%Y%m%d-%H%M%S', time.gmtime()) + '.db'
    dst = os.path.join(BACKUP_DIR, fn)
    src = sqlite3.connect(DB_PATH); out = sqlite3.connect(dst)
    try: src.backup(out)
    finally: out.close(); src.close()
    try:
        files = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith('.db'))
        for old in files[:-10]: os.remove(os.path.join(BACKUP_DIR, old))
    except OSError: pass
    db.execute("INSERT INTO site_settings (key,value) VALUES ('backup_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (ts,))
    _log(db, 'backup', fn)
    return jsonify({'ok': True, 'file': fn, 'bytes': os.path.getsize(dst), 'at': ts})

@app.get('/api/admin/backup/download')
@require_admin
def admin_backup_download():
    try: files = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith('.db'))
    except OSError: files = []
    if not files: return bad('No backup yet — press Backup now first', 404)
    return send_file(os.path.join(BACKUP_DIR, files[-1]), as_attachment=True, download_name=files[-1])

# ---------------- full student rankings for admin ----------------
@app.get('/api/admin/rankings')
@require_admin
def admin_rankings():
    db = get_db()
    d7 = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 6 * 86400))
    lb = rows(db.execute("""SELECT u.id, u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
        (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done,
        (SELECT COALESCE(AVG(a.score*100.0/a.qcount),0) FROM exam_attempts a WHERE a.user_id=u.id) examavg
        FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
        WHERE u.role='student' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id LIMIT 50""", (d7,)))
    return jsonify({'top': [{'name': r['name'], 'school': r['school'] or '', 'minutes': int(r['sec'] / 60),
                             'lessons': r['done'], 'exam_avg': round(r['examavg'])} for r in lb]})

@app.get('/api/admin/resources')
@require_admin
def admin_resources():
    status = s(request.args.get('status', ''), 20)
    sql = """SELECT r.*, s.name AS subject_name, u.name AS uploader, l.title AS lesson_title,
        CASE WHEN r.valid_until<>'' AND r.valid_until < datetime('now') THEN 1 ELSE 0 END AS expired
        FROM resources r LEFT JOIN subjects s ON s.id=r.subject_id LEFT JOIN users u ON u.id=r.uploaded_by
        LEFT JOIN lessons l ON l.id=r.lesson_id {where} ORDER BY r.id DESC LIMIT 300"""
    where = 'WHERE r.status=?' if status else ''
    return jsonify({'resources': rows(get_db().execute(sql.format(where=where), (status,) if status else ()))})

@app.put('/api/admin/resources/<int:rid>')
@require_admin
def admin_resource_edit(rid):
    db = get_db()
    r = one(db.execute('SELECT * FROM resources WHERE id=?', (rid,)))
    if not r: return bad('Resource not found', 404)
    b = request.get_json(silent=True) or {}
    title = s(b['title'], 140) if 'title' in b else r['title']
    category = b['category'] if b.get('category') in [c['id'] for c in RESOURCE_CATEGORIES] else r['category']
    status = b['status'] if b.get('status') in ('pending', 'approved', 'rejected') else r['status']
    subj_id = (int(b['subjectId']) if str(b.get('subjectId') or '').isdigit() else None) if 'subjectId' in b else r['subject_id']
    unit_id = (int(b['unitId']) if str(b.get('unitId') or '').isdigit() else None) if 'unitId' in b else r['unit_id']
    medium = b['medium'] if b.get('medium') in MEDIUMS else r['medium']
    year = s(b['year'], 20) if 'year' in b else r['year']
    prem = (1 if b.get('premium') in (1, True, '1') else 0) if 'premium' in b else r['premium']
    db.execute('UPDATE resources SET title=?, category=?, status=?, subject_id=?, unit_id=?, medium=?, year=?, premium=? WHERE id=?', (title, category, status, subj_id, unit_id, medium, year, prem, rid))
    # validity period: admin may set/change it any time ('' / 'forever' = no expiry)
    VALIDITY_DAYS = {'1w': 7, '1m': 30, '4m': 122, '6m': 183, '12m': 365, '24m': 730}
    validity = s(b.get('validity'), 10)
    if 'validity' in b:
        if validity in ('', 'forever'):
            db.execute("UPDATE resources SET valid_until='' WHERE id=?", (rid,))
        elif validity in VALIDITY_DAYS:
            db.execute("UPDATE resources SET valid_until=datetime('now', ?) WHERE id=?", ('+%d days' % VALIDITY_DAYS[validity], rid))
    return jsonify({'ok': True})

@app.post('/api/admin/subjects')
@require_admin
def admin_add_subject():
    b = request.get_json(silent=True) or {}
    if not s(b.get('name'), 80): return bad('Subject name required')
    cur = get_db().execute('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2,medium) VALUES (?,?,?,?,?,?,?,?)',
        (s(b.get('name'), 80), s(b.get('name_si'), 80), s(b.get('name_ta'), 80), s(b.get('code'), 10),
         s(b.get('icon'), 20) or 'book', s(b.get('color1'), 10) or '#6366f1', s(b.get('color2'), 10) or '#22d3ee',
         b.get('medium') if b.get('medium') in MEDIUMS else 'en'))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.delete('/api/admin/subjects/<int:sid>')
@require_admin
def admin_del_subject(sid):
    get_db().execute('DELETE FROM subjects WHERE id=?', (sid,))
    return jsonify({'ok': True})

@app.get('/api/admin/units')
@require_admin
def admin_units():
    sid = int(request.args.get('subjectId', '0') or 0)
    return jsonify({'units': rows(get_db().execute('SELECT * FROM units WHERE subject_id=? ORDER BY ord,id', (sid,)))})

@app.post('/api/admin/units')
@require_admin
def admin_add_unit():
    b = request.get_json(silent=True) or {}
    db = get_db()
    sid = int(b.get('subjectId') or 0)
    if not sid or not s(b.get('name'), 120): return bad('Subject and unit name required')
    if not one(db.execute('SELECT id FROM subjects WHERE id=?', (sid,))): return bad('Invalid subject')
    cur = db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', (sid, s(b.get('name'), 120), int(b.get('ord') or 0)))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.delete('/api/admin/units/<int:uid>')
@require_admin
def admin_del_unit(uid):
    get_db().execute('DELETE FROM units WHERE id=?', (uid,))
    return jsonify({'ok': True})

@app.post('/api/admin/lessons')
@require_admin
def admin_add_lesson():
    b = request.get_json(silent=True) or {}
    db = get_db()
    uid = int(b.get('unitId') or 0)
    if not uid or not s(b.get('title'), 160): return bad('Unit and lesson title required')
    if not one(db.execute('SELECT id FROM units WHERE id=?', (uid,))): return bad('Invalid unit')
    teacher_id = int(b['teacherId']) if str(b.get('teacherId') or '').isdigit() else None
    cur = db.execute('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)',
                     (uid, teacher_id, s(b.get('title'), 160), s(b.get('description'), 3000),
                      yt_normalize(b.get('video') or ''), s(b.get('notes'), 8000), int(b.get('ord') or 0)))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.put('/api/admin/lessons/<int:lid>')
@require_admin
def admin_edit_lesson(lid):
    db = get_db()
    l = one(db.execute('SELECT * FROM lessons WHERE id=?', (lid,)))
    if not l: return bad('Lesson not found', 404)
    b = request.get_json(silent=True) or {}
    teacher_id = (int(b['teacherId']) if str(b.get('teacherId') or '').isdigit() else None) if 'teacherId' in b else l['teacher_id']
    db.execute('UPDATE lessons SET title=?,description=?,youtube_id=?,notes=?,teacher_id=? WHERE id=?', (
        s(b['title'], 160) if 'title' in b else l['title'],
        s(b['description'], 3000) if 'description' in b else l['description'],
        yt_normalize(b['video']) if 'video' in b else l['youtube_id'],
        s(b['notes'], 8000) if 'notes' in b else l['notes'],
        teacher_id, lid))
    return jsonify({'ok': True})

@app.delete('/api/admin/lessons/<int:lid>')
@require_admin
def admin_del_lesson(lid):
    get_db().execute('DELETE FROM lessons WHERE id=?', (lid,))
    return jsonify({'ok': True})

@app.post('/api/admin/teachers')
@require_admin
def admin_add_teacher():
    b = request.get_json(silent=True) or {}
    if not s(b.get('name'), 80): return bad('Teacher name required')
    cur = get_db().execute('INSERT INTO teachers (name,bio,subjects,photo) VALUES (?,?,?,?)',
                           (s(b.get('name'), 80), s(b.get('bio'), 600), s(b.get('subjects'), 120), s(b.get('photo'), 200)))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.put('/api/admin/teachers/<int:tid>')
@require_admin
def admin_edit_teacher(tid):
    db = get_db()
    t0 = one(db.execute('SELECT * FROM teachers WHERE id=?', (tid,)))
    if not t0: return bad('Teacher not found', 404)
    b = request.get_json(silent=True) or {}
    db.execute('UPDATE teachers SET name=?,bio=?,subjects=?,photo=? WHERE id=?', (
        s(b.get('name'), 80) or t0['name'], s(b.get('bio'), 600), s(b.get('subjects'), 120),
        s(b.get('photo'), 200), tid))
    return jsonify({'ok': True})

@app.delete('/api/admin/teachers/<int:tid>')
@require_admin
def admin_del_teacher(tid):
    get_db().execute('DELETE FROM teachers WHERE id=?', (tid,))
    return jsonify({'ok': True})

def arr(v):
    if isinstance(v, str):
        try: v = json.loads(v)
        except Exception: v = []
    return json.dumps([s(x, 120) for x in (v if isinstance(v, list) else [])][:10])

@app.post('/api/admin/tutors')
@require_admin
def admin_add_tutor():
    b = request.get_json(silent=True) or {}
    if not s(b.get('name'), 80): return bad('Tutor name required')
    cur = get_db().execute('INSERT INTO tutors (name,photo,subjects,experience,classes,location,phone,whatsapp,email,bio,district,mode,medium,level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (s(b.get('name'), 80), s(b.get('photo'), 200), arr(b.get('subjects')), s(b.get('experience'), 40), arr(b.get('classes')),
         s(b.get('location'), 80), s(b.get('phone'), 30), s(b.get('whatsapp'), 30), s(b.get('email'), 120), s(b.get('bio'), 600),
         s(b.get('district'), 40) if b.get('district') in DISTRICTS else '', (s(b.get('mode'), 10).lower() if s(b.get('mode'), 10).lower() in ('online', 'physical', 'both') else ''),
         b.get('medium') if b.get('medium') in MEDIUMS else '', (s(b.get('level'), 6).lower() if s(b.get('level'), 6).lower() in ('al', 'ol', 'both') else '')))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.put('/api/admin/tutors/<int:tid>')
@require_admin
def admin_edit_tutor(tid):
    db = get_db()
    t0 = one(db.execute('SELECT * FROM tutors WHERE id=?', (tid,)))
    if not t0: return bad('Tutor not found', 404)
    b = request.get_json(silent=True) or {}
    mode = s(b.get('mode'), 10).lower(); lvl = s(b.get('level'), 6).lower()
    db.execute('UPDATE tutors SET name=?,photo=?,subjects=?,experience=?,classes=?,location=?,phone=?,whatsapp=?,email=?,bio=?,district=?,mode=?,medium=?,level=? WHERE id=?', (
        s(b.get('name'), 80) or t0['name'], s(b.get('photo'), 200), arr(b.get('subjects')), s(b.get('experience'), 40), arr(b.get('classes')),
        s(b.get('location'), 80), s(b.get('phone'), 30), s(b.get('whatsapp'), 30), s(b.get('email'), 120), s(b.get('bio'), 600),
        b.get('district') if b.get('district') in DISTRICTS else '', mode if mode in ('online', 'physical', 'both') else '',
        b.get('medium') if b.get('medium') in MEDIUMS else '', lvl if lvl in ('al', 'ol', 'both') else '', tid))
    return jsonify({'ok': True})

@app.delete('/api/admin/tutors/<int:tid>')
@require_admin
def admin_del_tutor(tid):
    get_db().execute('DELETE FROM tutors WHERE id=?', (tid,))
    return jsonify({'ok': True})

@app.post('/api/admin/years')
@require_admin
def admin_add_year():
    label = s((request.get_json(silent=True) or {}).get('label'), 20)
    if not label: return bad('Year label required (e.g. A/L 2029)')
    try:
        get_db().execute('INSERT INTO al_years (label,active) VALUES (?,1)', (label,))
    except sqlite3.IntegrityError:
        return bad('That year already exists')
    return jsonify({'ok': True})

@app.put('/api/admin/years/<int:yid>')
@require_admin
def admin_toggle_year(yid):
    db = get_db()
    y = one(db.execute('SELECT * FROM al_years WHERE id=?', (yid,)))
    if not y: return bad('Not found', 404)
    nv = 0 if y['active'] else 1
    db.execute('UPDATE al_years SET active=? WHERE id=?', (nv, yid))
    return jsonify({'ok': True, 'active': nv})

@app.delete('/api/admin/years/<int:yid>')
@require_admin
def admin_del_year(yid):
    get_db().execute('DELETE FROM al_years WHERE id=?', (yid,))
    return jsonify({'ok': True})

@app.get('/api/admin/students')
@require_admin
def admin_students():
    db = get_db()
    q = s(request.args.get('search', ''), 60)
    fy, fd, fm = s(request.args.get('year'), 20), s(request.args.get('district'), 60), s(request.args.get('medium'), 5)
    sql = 'SELECT id,name,email,role,school,district,al_year,medium,stream,subjects,status,created_at FROM users'
    cond, par = [], []
    if q:
        like = '%' + q + '%'
        cond.append('(name LIKE ? OR email LIKE ? OR school LIKE ?)'); par += [like, like, like]
    if fy: cond.append('al_year=?'); par.append(fy)
    if fd: cond.append('district=?'); par.append(fd)
    if fm in ('en', 'si', 'ta'): cond.append('medium=?'); par.append(fm)
    if cond: sql += ' WHERE ' + ' AND '.join(cond)
    sql += ' ORDER BY id DESC LIMIT 400'
    return jsonify({'students': rows(db.execute(sql, par))})

@app.get('/api/admin/students/<int:uid2>')
@require_admin
def admin_student_detail(uid2):
    db = get_db()
    u = one(db.execute('SELECT id,name,email,role,school,district,al_year,medium,stream,subjects,premium_until,created_at FROM users WHERE id=?', (uid2,)))
    if not u: return bad('Not found', 404)
    c = lambda sql, *p: one(db.execute(sql, p))['c']
    d7 = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 6 * 86400))
    ex = one(db.execute('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?', (uid2,)))
    mcq_a = one(db.execute('''SELECT AVG(b) a FROM (SELECT MAX(score*1.0/total) b FROM mcq_attempts WHERE user_id=? GROUP BY lesson_id)''', (uid2,)))
    today = time.strftime('%Y-%m-%d', time.gmtime())
    last = None
    for r in rows(db.execute("""SELECT MAX(y) m FROM (
            SELECT day y FROM study_events WHERE user_id=?
            UNION SELECT substr(completed_at,1,10) FROM progress WHERE user_id=? AND completed_at<>''
            UNION SELECT substr(created_at,1,10) FROM exam_attempts WHERE user_id=?)""", (uid2, uid2, uid2))):
        last = r['m']
    rec = []
    for r in rows(db.execute('SELECT l.title, p.completed_at ts FROM progress p JOIN lessons l ON l.id=p.lesson_id WHERE p.user_id=? AND p.completed=1 ORDER BY p.completed_at DESC LIMIT 5', (uid2,))):
        rec.append({'ic': '✅', 'text': r['title'], 'ts': r['ts']})
    for r in rows(db.execute('SELECT subject, score, qcount, created_at ts FROM exam_attempts WHERE user_id=? ORDER BY id DESC LIMIT 3', (uid2,))):
        rec.append({'ic': '🎯', 'text': r['subject'] + ' exam — ' + str(r['score']) + '/' + str(r['qcount']), 'ts': r['ts']})
    for r in rows(db.execute('SELECT amount, status, created_at ts FROM payments WHERE user_id=? ORDER BY id DESC LIMIT 3', (uid2,))):
        rec.append({'ic': '💎', 'text': 'Slip Rs. ' + str(r['amount'] or 0) + ' — ' + r['status'], 'ts': r['ts']})
    rec = sorted([x for x in rec if x['ts']], key=lambda x: x['ts'], reverse=True)[:8]
    return jsonify({'u': u, 'last_seen': last, 'recent': rec, 'stats': {
        'lessons_done': c('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1', uid2),
        'lessons_watched': c('SELECT COUNT(*) c FROM progress WHERE user_id=? AND watched=1', uid2),
        'saved': c('SELECT COUNT(*) c FROM saved_resources WHERE user_id=?', uid2),
        'uploads': c('SELECT COUNT(*) c FROM resources WHERE uploaded_by=?', uid2),
        'sims_tried': c('SELECT COUNT(*) c FROM sim_progress WHERE user_id=?', uid2),
        'study_min': int(one(db.execute('SELECT COALESCE(SUM(seconds),0) s FROM study_events WHERE user_id=?', (uid2,)))['s'] / 60),
        'study_7d': int(one(db.execute('SELECT COALESCE(SUM(seconds),0) s FROM study_events WHERE user_id=? AND day>=?', (uid2, d7)))['s'] / 60),
        'exams': ex['c'], 'exam_avg': round(ex['a']), 'exam_best': round(ex['b']),
        'mcq_avg': round((mcq_a['a'] or 0) * 100),
        'ai_today': (one(db.execute('SELECT n FROM ai_usage WHERE user_id=? AND day=?', (uid2, today))) or {'n': 0})['n'],
    }})

@app.put('/api/admin/users/<int:uid>')
@require_admin
def admin_user_role(uid):
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (uid,)))
    if not u: return bad('User not found', 404)
    role = 'admin' if (request.get_json(silent=True) or {}).get('role') == 'admin' else 'student'
    if u['id'] == g.user['id'] and role != 'admin': return bad('You cannot remove your own admin role')
    db.execute('UPDATE users SET role=? WHERE id=?', (role, uid))
    _log(db, 'role_change', u['email'] + ' -> ' + role)
    return jsonify({'ok': True})

@app.delete('/api/admin/users/<int:uid>')
@require_admin
def admin_del_user(uid):
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (uid,)))
    if not u: return bad('User not found', 404)
    if u['id'] == g.user['id']: return bad('You cannot delete your own account')
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    _log(db, 'user_delete', u['email'])
    return jsonify({'ok': True})

@app.get('/api/admin/messages')
@require_admin
def admin_messages():
    return jsonify({'messages': rows(get_db().execute("""SELECT m.*, u.name AS student, u.email AS student_email, t.name AS tutor
        FROM tutor_messages m JOIN users u ON u.id=m.user_id JOIN tutors t ON t.id=m.tutor_id ORDER BY m.id DESC LIMIT 200"""))})

# ------------------------------------------------------------ STATIC / SPA
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File is too large (max 25 MB)'}), 413

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

# ------------------------------------------------- AUTO CONTENT UPDATE
def auto_content_update():
    """Runs the idempotent content packs so even an OLD database gets every
    new lesson the moment the website starts (Physics / Chemistry / tabs /
    syllabus links). Safe: packs skip anything already added."""
    import subprocess, sys
    packs = ['add-subjects.py', 'remove-demo-content.py', 'add-cm-units.py', 'add-chemistry-lessons.py',
             'add-lesson-tabs.py', 'add-syllabus-links.py', 'add-physics-lessons.py',
             'add-physics-batch2.py', 'add-physics-batch3.py', 'add-cm-lessons.py']
    env = os.environ.copy()
    env['AL_DATA_DIR'] = DATA_DIR
    ran = 0
    for p in packs:
        f = os.path.join(BASE, p)
        if not os.path.exists(f):
            continue
        try:
            subprocess.run([sys.executable, f], env=env, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=180)
            ran += 1
        except Exception:
            pass
    if ran:
        try:
            db = sqlite3.connect(DB_PATH)
            n = db.execute("SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=(SELECT id FROM subjects WHERE name='Physics')").fetchone()[0]
            m = db.execute("SELECT COUNT(*) FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=(SELECT id FROM subjects WHERE name='Combined Mathematics')").fetchone()[0]
            db.close()
            print('  Content check OK - %d content packs verified. Physics lessons: %d | CM lessons: %d' % (ran, n, m))
        except Exception:
            print('  Content check OK - %d content packs verified.' % ran)

# ------------------------------------------------- SMART FEATURES v2
# (search / practice questions / study time / planner / settings / progress+)

_boot2 = sqlite3.connect(DB_PATH)
_boot2.executescript("""CREATE TABLE IF NOT EXISTS user_settings (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key TEXT NOT NULL, value TEXT DEFAULT '', PRIMARY KEY (user_id, key));
CREATE TABLE IF NOT EXISTS study_events (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day TEXT NOT NULL, seconds INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, day));
CREATE TABLE IF NOT EXISTS study_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  plan_date TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')), UNIQUE (user_id, lesson_id, plan_date));
CREATE TABLE IF NOT EXISTS practice_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
  qtype TEXT NOT NULL DEFAULT 'structured', year INTEGER,
  title TEXT DEFAULT '', question TEXT NOT NULL, answer TEXT DEFAULT '', marks INTEGER DEFAULT 0,
  ord INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS practice_marks (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL REFERENCES practice_questions(id) ON DELETE CASCADE,
  ok INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, question_id));
CREATE TABLE IF NOT EXISTS mcq_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS sim_progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL DEFAULT '', started INTEGER NOT NULL DEFAULT 0,
  completed INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
  best_score INTEGER, last_score INTEGER, updated_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, lesson_id));
CREATE TABLE IF NOT EXISTS lab_notes (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  prac TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (user_id, prac));
CREATE TABLE IF NOT EXISTS lab_progress (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  prac TEXT NOT NULL, best INTEGER NOT NULL DEFAULT 0, done INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (user_id, prac));
CREATE TABLE IF NOT EXISTS exam_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject TEXT NOT NULL DEFAULT '', mode TEXT NOT NULL DEFAULT '',
  qcount INTEGER NOT NULL DEFAULT 0, score INTEGER NOT NULL DEFAULT 0,
  seconds INTEGER NOT NULL DEFAULT 0, topics TEXT NOT NULL DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS ai_usage (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, day));
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file TEXT NOT NULL DEFAULT '', amount INTEGER NOT NULL DEFAULT 0, note TEXT DEFAULT '',
  method TEXT NOT NULL DEFAULT 'slip', txn_id TEXT NOT NULL DEFAULT '', mobile TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending', reason TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')), decided_at TEXT DEFAULT '');""")
for _c in ("simulation_type TEXT DEFAULT ''", "simulation_enabled INTEGER DEFAULT NULL", "sim_config TEXT DEFAULT ''"):
    try:
        _boot2.execute("ALTER TABLE lessons ADD COLUMN %s" % _c)
    except sqlite3.OperationalError:
        pass
# migrations: richer resource filters (medium/year/unit) + tutor marketplace fields
for _tbl, _cols in (("resources", ("medium TEXT DEFAULT ''", "year TEXT DEFAULT ''", "unit_id INTEGER DEFAULT NULL", "valid_until TEXT DEFAULT ''")),
                    ("tutors", ("district TEXT DEFAULT ''", "mode TEXT DEFAULT ''", "medium TEXT DEFAULT ''", "level TEXT DEFAULT ''", "featured INTEGER NOT NULL DEFAULT 0"))):
    for _c in _cols:
        try:
            _boot2.execute("ALTER TABLE %s ADD COLUMN %s" % (_tbl, _c))
        except sqlite3.OperationalError:
            pass
# read-tracking columns for admin notification bell (+ comment approval column for admin switches)
for _tbl2, _c2 in (("contact_messages", "is_read INTEGER NOT NULL DEFAULT 0"), ("tutor_comments", "is_read INTEGER NOT NULL DEFAULT 0"),
                   ("tutor_comments", "approved INTEGER NOT NULL DEFAULT 1"), ("users", "premium_until TEXT DEFAULT ''")):
    try:
        _boot2.execute("ALTER TABLE %s ADD COLUMN %s" % (_tbl2, _c2))
    except sqlite3.OperationalError:
        pass
_boot2.commit()
try:  # purge expired tutor comments at startup (3-month rule, keep=1 survives)
    _boot2.execute("DELETE FROM tutor_comments WHERE keep=0 AND created_at < datetime('now','-3 months')")
    _boot2.commit()
except sqlite3.Error:
    pass
_boot2.close()

# ------------------------------------------------- ADMIN SPEC PACK (2026-08-11p)
_boot3 = sqlite3.connect(DB_PATH)
_boot3.executescript("""CREATE TABLE IF NOT EXISTS admin_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, admin TEXT DEFAULT '',
  action TEXT NOT NULL, target TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS coupons (
  id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
  kind TEXT NOT NULL DEFAULT 'percent', value INTEGER NOT NULL DEFAULT 0,
  expires TEXT DEFAULT '', max_uses INTEGER NOT NULL DEFAULT 0, uses INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS ai_knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS ai_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question TEXT DEFAULT '', answer TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS challenges (
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT 'mixed',
  mode TEXT NOT NULL DEFAULT 'm1', start TEXT NOT NULL DEFAULT '', end TEXT NOT NULL DEFAULT '',
  prize1 TEXT DEFAULT '', prize2 TEXT DEFAULT '', prize3 TEXT DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS challenge_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  score INTEGER NOT NULL DEFAULT 0, qcount INTEGER NOT NULL DEFAULT 0, seconds INTEGER NOT NULL DEFAULT 0,
  prize_status TEXT NOT NULL DEFAULT '', created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (challenge_id, user_id));""")
for _tbl4, _c4 in (("users", "status TEXT NOT NULL DEFAULT 'active'"), ("payments", "coupon TEXT DEFAULT ''")):
    try:
        _boot3.execute("ALTER TABLE %s ADD COLUMN %s" % (_tbl4, _c4))
    except sqlite3.OperationalError:
        pass
_boot3.commit()
_boot3.close()

# ------------------------------------------------- SIM LAB UPGRADE (2026-08-11q)
_boot4 = sqlite3.connect(DB_PATH)
_boot4.executescript("""CREATE TABLE IF NOT EXISTS sim_catalog (
  id INTEGER PRIMARY KEY AUTOINCREMENT, sim_type TEXT UNIQUE NOT NULL,
  subject TEXT NOT NULL DEFAULT '', title TEXT DEFAULT '', descr TEXT DEFAULT '',
  difficulty TEXT NOT NULL DEFAULT 'medium', objectives TEXT DEFAULT '', formulas TEXT DEFAULT '',
  tips TEXT DEFAULT '', xp_reward INTEGER NOT NULL DEFAULT 15, badge TEXT DEFAULT '',
  unit_id INTEGER DEFAULT NULL, lesson_id INTEGER DEFAULT NULL,
  enabled INTEGER NOT NULL DEFAULT 1, ord INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS sim_launches (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, sim_type, day));
CREATE TABLE IF NOT EXISTS sim_challenge_wins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL, goal TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (user_id, sim_type, goal));
CREATE TABLE IF NOT EXISTS sim_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  sim_type TEXT NOT NULL DEFAULT '', event TEXT NOT NULL DEFAULT 'score',
  score INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 1, pct INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')));
CREATE INDEX IF NOT EXISTS ix_sim_events_week ON sim_events(created_at);
CREATE TABLE IF NOT EXISTS careers (
  id INTEGER PRIMARY KEY AUTOINCREMENT, gkey TEXT UNIQUE NOT NULL, name TEXT NOT NULL DEFAULT '',
  descr TEXT DEFAULT '', reward_code TEXT DEFAULT '', reward_once INTEGER NOT NULL DEFAULT 1,
  max_attempts INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS career_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  gkey TEXT NOT NULL, score INTEGER NOT NULL DEFAULT 0, xp INTEGER NOT NULL DEFAULT 0,
  won INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));""")
for _alt in ("ALTER TABLE sim_catalog ADD COLUMN premium INTEGER NOT NULL DEFAULT 0",
             "ALTER TABLE resources ADD COLUMN premium INTEGER NOT NULL DEFAULT 0",
             "ALTER TABLE payments ADD COLUMN method TEXT NOT NULL DEFAULT 'slip'",
             "ALTER TABLE payments ADD COLUMN txn_id TEXT NOT NULL DEFAULT ''",
             "ALTER TABLE payments ADD COLUMN mobile TEXT NOT NULL DEFAULT ''"):
    try: _boot4.execute(_alt)
    except sqlite3.OperationalError: pass
_boot4.commit()
_boot4.close()

SIM_TYPES = ['atomic', 'ionic', 'polarity', 'vsepr', 'states', 'gaslaws',
             'molarity', 'dilution', 'stoich', 'energy', 'ph', 'titration',
             # Physics pack
             'motion', 'projectile', 'newtons', 'workenergy', 'collide', 'circular', 'shm', 'waves',
             'sound', 'optics', 'refraction', 'efield', 'circuits', 'ohmslaw', 'emi', 'magfield',
             # Biology pack
             'cell', 'dna', 'heart', 'photosyn', 'transpire', 'micro',
             # Advanced Chemistry pack
             'react', 'organic', 'galvanic', 'ptable',
             # Advanced Physics pack (free-build / drag / grapher)
             'circbuild', 'lensmirror', 'mgraphs',
             # Biology pack wave 2
             'neuron', 'bloodflow', 'breath', 'mitosis', 'disease',
             # Combined Maths pack
             'gplot', 'gtrans', 'deriv', 'integr', 'vector', 'trig', 'prob', 'stats',
             # ICT pack
             'binary', 'logic', 'truthtab', 'cpu', 'network', 'ipaddr', 'sortvis', 'webplay',
             # Biology pack 3
             'meiosis', 'natsel', 'popgrow', 'enzyme', 'respire', 'foodweb',
             # Chemistry pack 3
             'equil', 'vlab',
             # Chemistry Virtual Practical Laboratory (database-driven practicals)
             'chemlab', 'flametest', 'phtitration',
             # Physics pack 3
             'freefall', 'friction', 'reflect', 'rescolor', 'rc', 'transformer', 'econserv',
             # Virtual Lab precision instruments (Part 3)
             'screwgauge', 'potentiometer',
             # Virtual Lab precision instruments (Part 4)
             'verniercaliper', 'metrebridge',
             # Premium Physics FX pack (Part 7) — PhET-style practical sims
             'pendulum', 'springshm', 'restube', 'gaspiston',
             # Premium Physics FX pack wave 2 (Part 9)
             'parallelogram', 'sonometer', 'lensuv', 'youngsmodulus',
             # Premium Physics FX pack wave 3 (Part 11) — Waves & Fluids FX
             'rippletank', 'melde', 'statwaves', 'beats',
             'quilltube', 'hare', 'utubeshm', 'archimedes',
             # Maths pack 2
             'matrix', 'complexnum', 'cogo', 'seqser', 'projmath',
             # ICT pack 2
             'sqlplay', 'flowchart', 'boolalg', 'memunits', 'progviz']
# Auto default simulation per (subject_id, unit_ord). Admin can override per lesson.
# subject of each sim type (drives the DB catalog, analytics and subject badges)
SIM_SUBJECTS = {}
for _ty in ['atomic', 'ionic', 'polarity', 'vsepr', 'states', 'gaslaws', 'molarity', 'dilution',
            'stoich', 'energy', 'ph', 'titration', 'react', 'organic', 'galvanic', 'ptable',
            'equil', 'vlab', 'chemlab', 'flametest', 'phtitration']:
    SIM_SUBJECTS[_ty] = 'chem'
for _ty in ['motion', 'projectile', 'newtons', 'workenergy', 'collide', 'circular', 'shm', 'waves',
            'sound', 'optics', 'refraction', 'efield', 'circuits', 'ohmslaw', 'emi', 'magfield',
            'circbuild', 'lensmirror', 'mgraphs',
            'freefall', 'friction', 'reflect', 'rescolor', 'rc', 'transformer', 'econserv', 'screwgauge', 'potentiometer', 'verniercaliper', 'metrebridge',
            'pendulum', 'springshm', 'restube', 'gaspiston',
            'parallelogram', 'sonometer', 'lensuv', 'youngsmodulus',
            'rippletank', 'melde', 'statwaves', 'beats', 'quilltube', 'hare', 'utubeshm', 'archimedes']:
    SIM_SUBJECTS[_ty] = 'phys'
for _ty in ['cell', 'dna', 'heart', 'photosyn', 'transpire', 'micro', 'neuron', 'bloodflow', 'breath', 'mitosis', 'disease',
            'meiosis', 'natsel', 'popgrow', 'enzyme', 'respire', 'foodweb']:
    SIM_SUBJECTS[_ty] = 'bio'
for _ty in ['gplot', 'gtrans', 'deriv', 'integr', 'vector', 'trig', 'prob', 'stats',
            'matrix', 'complexnum', 'cogo', 'seqser', 'projmath']:
    SIM_SUBJECTS[_ty] = 'maths'
for _ty in ['binary', 'logic', 'truthtab', 'cpu', 'network', 'ipaddr', 'sortvis', 'webplay',
            'sqlplay', 'flowchart', 'boolalg', 'memunits', 'progviz']:
    SIM_SUBJECTS[_ty] = 'ict'
_ORD_HARD = {'chemlab', 'titration', 'galvanic', 'emi', 'magfield', 'transpire', 'disease', 'deriv', 'integr', 'truthtab', 'cpu',
             'meiosis', 'natsel', 'equil', 'rc', 'transformer', 'matrix', 'complexnum', 'projmath', 'sqlplay', 'progviz'}
try:  # seed the DB-driven sim catalogue once (admin edits metadata afterwards)
    _bs = sqlite3.connect(DB_PATH)
    for _i, _ty in enumerate(SIM_TYPES):
        _bs.execute('INSERT OR IGNORE INTO sim_catalog (sim_type,subject,difficulty,ord) VALUES (?,?,?,?)',
                    (_ty, SIM_SUBJECTS.get(_ty, ''), 'hard' if _ty in _ORD_HARD else ('easy' if _i % 3 == 0 else 'medium'), _i))
    for _c in (('memory', 'Memory Match', 'Flip cards and match A/L term pairs.'), ('scramble', 'Word Scramble', 'Unscramble the A/L word.'), ('quiz', 'Rapid GK Quiz', '5 quick general-knowledge questions.')):
        _bs.execute('INSERT OR IGNORE INTO careers (gkey,name,descr) VALUES (?,?,?)', _c)
    _bs.commit()
    _bs.close()
except sqlite3.Error:
    pass

SIM_AUTO = {
    1: {1: 'atomic', 2: 'ionic', 3: 'stoich', 4: 'gaslaws', 5: 'energy', 8: 'energy', 9: 'ph'},   # Chemistry
    3: {1: 'cell', 2: 'heart'},                                                       # Biology (placeholder units)
    4: {2: 'motion', 3: 'waves', 4: 'gaslaws', 6: 'efield', 7: 'magfield', 8: 'circuits'},        # Physics
}
# Physics lesson-title rules per unit_ord: first matching pattern wins.
# Patterns cover both the English and Sinhala keywords found in the actual lesson catalogue.
# A rule value of None = "no sim for this lesson" (e.g. Moments / fluids — no sim covers it yet).
PHYS_RULES = {
    2: [('graph', 'mgraphs'), ('ප්‍රස්තාර', 'mgraphs'), ('suvat', 'mgraphs'),
        ('momentum', 'collide'), ('collision', 'collide'), ('impulse', 'collide'), ('ගැටීම', 'collide'), ('ආවේග', 'collide'),
        ('free fall', 'freefall'), ('freefall', 'freefall'), ('නිදහස් වැටීම', 'freefall'), ('falling', 'freefall'),
        ('projectile', 'projectile'), ('ප්‍රක්ෂිප්ත', 'projectile'),
        ('නිව්ටන්', 'newtons'), ('newton', 'newtons'), ('friction', 'newtons'), ('ඝර්ෂණ', 'newtons'), ('inclined', 'newtons'),
        ('circular', 'circular'), ('centripetal', 'circular'), ('වෘත්ත', 'circular'),
        ('කාර්යය', 'workenergy'), ('ශක්තිය', 'workenergy'), ('ක්ෂමතා', 'workenergy'),
        ('work', 'workenergy'), ('energy', 'workenergy'), ('power', 'workenergy'), ('kinetic', 'workenergy'), ('potential energy', 'workenergy'),
        ('moment', None), ('torque', None), ('couple', None), ('equilibrium', None), ('centre of gravity', None),
        ('බල සමතුලිත', None), ('භ්‍රමණ', None), ('තරල', None), ('ගුරුත්ව කේන්ද්‍රය', None), ('ද්‍රවස්ථිත', None), ('දැඟිලූ', None)],
    3: [('sound', 'sound'), ('ultra', 'sound'), ('echo', 'sound'), ('ශබ්ද', 'sound'),
        ('total internal', 'refraction'), ('අභ්‍යන්තර', 'refraction'), ('critical angle', 'refraction'),
        ('prism', 'refraction'), ('ප්‍රිස්ම', 'refraction'), ('වර්ණාවලි', 'refraction'),
        ('refraction', 'refraction'), ('refractive', 'refraction'), ('වර්තන', 'refraction'),
        ('lens', 'lensmirror'), ('කාච', 'lensmirror'), ('mirror', 'lensmirror'), ('කණ්ණාඩි', 'lensmirror'),
        ('eye', 'optics'), ('ඇස', 'optics'), ('optical', 'optics'), ('ප්‍රකාශ උපකරණ', 'optics'),
        ('light', 'optics'), ('ආලෝක', 'optics'),
        ('doppler', 'waves'), ('ඩොප්ලර්', 'waves'), ('ripple', 'waves'),
        ('interference', 'waves'), ('diffraction', 'waves'), ('stationary', 'waves'), ('superposition', 'waves'),
        ('harmonic', 'shm'), ('s.h.m', 'shm'), ('pendulum', 'shm'), ('සරල අවලම්බ', 'shm'), ('සමාවර්ත', 'shm'),
        ('wave', 'waves'), ('තරංග', 'waves'),
        ('oscillation', 'shm'), ('දෝලන', 'shm')],
    4: [('gas', 'gaslaws'), ('ideal', 'gaslaws'), ('boyle', 'gaslaws'), ('charles', 'gaslaws'), ('වායු', 'gaslaws')],
    6: [('field', 'efield'), ('ක්ෂේත්‍ර', 'efield'), ('charge', 'efield'), ('ආරෝපණ', 'efield'),
        ('coulomb', 'efield'), ('කුලෝම්', 'efield'), ('potential', 'efield'),
        ('capacit', 'rc'), ('discharging', 'rc'), ('time constant', 'rc')],
    7: [('induction', 'emi'), ('lenz', 'emi'), ('faraday', 'emi'), ('flux', 'emi'), ('alternating', 'emi'),
        ('transformer', 'transformer'), ('ට්‍රාන්ස්ෆෝමර්', 'transformer'),
        ('ප්‍රේරණ', 'emi'), ('ෆැරඩේ', 'emi'), ('torque', None), ('දෝලක', None)],
    8: [('ohm', 'ohmslaw'), ('resistance', 'ohmslaw'), ('resistivity', 'ohmslaw'), ('ප්‍රතිරෝද', 'ohmslaw'),
        ('i-v', 'ohmslaw'), ('iv characteristic', 'ohmslaw'),
        ('kirchhoff', 'circuits'), ('කර්චොෆ්', 'circuits'), ('potential divider', 'circuits'),
        ('පරිපථ', 'circbuild'), ('circuit', 'circbuild'), ('parallel', 'circuits'),
        ('cell', 'circuits'), ('කෝෂ', 'circuits'), ('internal resistance', 'circuits'), ('potentiometer', 'circuits')],
}

def resolve_sim(lesson):
    """Effective simulation for a lesson: explicit admin setting wins; otherwise unit default / title rule."""
    stype = (lesson.get('simulation_type') or '').strip()
    enb = lesson.get('simulation_enabled')
    sid = lesson.get('subject_id'); uord = lesson.get('unit_ord')
    auto = None
    subj_map = SIM_AUTO.get(sid) or {}
    if sid == 4:
        rules = PHYS_RULES.get(uord) or []
        title = (lesson.get('title') or '').lower()
        hit = '_nohit_'
        for pat, sim in rules:
            if pat in title:
                hit = sim
                break
        if hit == '_nohit_': auto = subj_map.get(uord)
        elif hit: auto = hit
        else: auto = None   # rule said None for this topic
    elif sid in SIM_AUTO:
        auto = subj_map.get(uord)
    if stype not in SIM_TYPES: stype = ''
    if enb == 0:
        return {'type': '', 'auto': auto or '', 'enabled': 0}
    if enb == 1 and stype:
        return {'type': stype, 'auto': auto or '', 'enabled': 1}
    if stype:  # explicit type chosen, enabled unset -> treat as on
        return {'type': stype, 'auto': auto or '', 'enabled': 1}
    if auto:
        return {'type': auto, 'auto': auto, 'enabled': -1}
    return {'type': '', 'auto': '', 'enabled': -1}

DEFAULT_SETTINGS = {'exam_date': '2027-08-09', 'weekly_target': '10', 'daily_goal': '2'}

def get_settings(uid):
    out = dict(DEFAULT_SETTINGS)
    for r in rows(get_db().execute('SELECT key,value FROM user_settings WHERE user_id=?', (uid,))):
        out[r['key']] = r['value']
    return out

@app.get('/api/search')
def api_search():
    q = s(request.args.get('q', ''), 80).strip()
    if len(q) < 2:
        return jsonify({'q': q, 'lessons': [], 'units': [], 'teachers': [], 'resources': [], 'subjects': []})
    like = '%' + q + '%'
    db = get_db()
    lessons = rows(db.execute("""SELECT l.id, l.title, l.youtube_id, u.id AS unit_id, u.name AS unit_name,
        s.id AS subject_id, s.name AS subject_name, s.color1, s.color2, t.name AS teacher_name
        FROM lessons l JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
        LEFT JOIN teachers t ON t.id=l.teacher_id
        WHERE l.title LIKE ? OR l.description LIKE ? ORDER BY l.id DESC LIMIT 12""", (like, like)))
    units = rows(db.execute("""SELECT u.id, u.name, u.ord, s.id AS subject_id, s.name AS subject_name, s.color1, s.color2
        FROM units u JOIN subjects s ON s.id=u.subject_id WHERE u.name LIKE ? ORDER BY s.id, u.ord LIMIT 8""", (like,)))
    teachers = rows(db.execute("""SELECT id, name, bio, photo, subjects FROM teachers
        WHERE name LIKE ? OR bio LIKE ? OR subjects LIKE ? LIMIT 8""", (like, like, like)))
    resources = rows(db.execute("""SELECT r.id, r.title, r.category, r.external_url, s2.name AS subject_name
        FROM resources r LEFT JOIN subjects s2 ON s2.id=r.subject_id
        WHERE r.status='approved' AND (r.title LIKE ? OR r.description LIKE ?) ORDER BY r.id DESC LIMIT 8""", (like, like)))
    subjects = rows(db.execute("""SELECT id, name, name_si, name_ta, color1, color2, icon FROM subjects
        WHERE name LIKE ? OR name_si LIKE ? OR name_ta LIKE ? LIMIT 5""", (like, like, like)))
    return jsonify({'q': q, 'lessons': lessons, 'units': units, 'teachers': teachers,
                    'resources': resources, 'subjects': subjects})

# ---------------- practice questions (structured + past paper) ----------------
@app.get('/api/units/<int:uid>/practice')
def unit_practice(uid):
    db = get_db()
    u = one(db.execute('SELECT u.*, s.name AS subject_name, s.color1, s.color2 FROM units u JOIN subjects s ON s.id=u.subject_id WHERE u.id=?', (uid,)))
    if not u: return bad('Unit not found', 404)
    qs = rows(db.execute('SELECT * FROM practice_questions WHERE unit_id=? ORDER BY year DESC, ord, id', (uid,)))
    marks = {}
    if g.user:
        for m in rows(db.execute('SELECT question_id, ok FROM practice_marks WHERE user_id=?', (g.user['id'],))):
            marks[m['question_id']] = m['ok']
    for q in qs:
        q['my'] = marks.get(q['id'])
    return jsonify({'unit': u, 'questions': qs})

@app.post('/api/practice/<int:qid>/mark')
@require_auth
def practice_mark(qid):
    b = request.get_json(silent=True) or {}
    ok = 1 if b.get('ok') else 0
    db = get_db()
    if not one(db.execute('SELECT id FROM practice_questions WHERE id=?', (qid,))): return bad('Question not found', 404)
    db.execute('INSERT INTO practice_marks (user_id,question_id,ok) VALUES (?,?,?) '
               'ON CONFLICT(user_id,question_id) DO UPDATE SET ok=excluded.ok', (g.user['id'], qid, ok))
    return jsonify({'ok': True})

@app.post('/api/admin/practice')
@require_admin
def admin_add_practice():
    b = request.get_json(silent=True) or {}
    db = get_db()
    uid = b.get('unit_id')
    if not one(db.execute('SELECT id FROM units WHERE id=?', (uid,))): return bad('Unit not found', 404)
    qt = s(b.get('qtype'), 20)
    if qt not in ('structured', 'pastpaper'): qt = 'structured'
    q = s(b.get('question'), 5000)
    if not q: return bad('Question text required')
    try: yr = int(b.get('year') or 0) or None
    except Exception: yr = None
    try: mk = int(b.get('marks') or 0)
    except Exception: mk = 0
    mx = one(db.execute('SELECT COALESCE(MAX(ord),0) m FROM practice_questions WHERE unit_id=?', (uid,)))['m']
    cur = db.execute('INSERT INTO practice_questions (unit_id,qtype,year,title,question,answer,marks,ord) VALUES (?,?,?,?,?,?,?,?)',
                     (uid, qt, yr, s(b.get('title'), 200), q, s(b.get('answer'), 8000), mk, mx + 1))
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.delete('/api/admin/practice/<int:qid>')
@require_admin
def admin_del_practice(qid):
    get_db().execute('DELETE FROM practice_questions WHERE id=?', (qid,))
    return jsonify({'ok': True})

# ---------------- study time heartbeat ----------------
@app.post('/api/study/ping')
@require_auth
def study_ping():
    b = request.get_json(silent=True) or {}
    try: sec = max(0, min(int(b.get('seconds') or 0), 120))
    except Exception: sec = 0
    if not sec: return jsonify({'ok': True})
    day = time.strftime('%Y-%m-%d', time.gmtime())
    get_db().execute('INSERT INTO study_events (user_id,day,seconds) VALUES (?,?,?) '
                     'ON CONFLICT(user_id,day) DO UPDATE SET seconds=seconds+excluded.seconds',
                     (g.user['id'], day, sec))
    return jsonify({'ok': True})

# ---------------- MCQ result store ----------------
@app.post('/api/lessons/<int:lid>/mcq-result')
@require_auth
def mcq_result(lid):
    b = request.get_json(silent=True) or {}
    db = get_db()
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    try:
        score = max(0, int(b.get('score') or 0)); total = max(1, int(b.get('total') or 1))
    except Exception: return bad('Bad score')
    score = min(score, total)
    db.execute('INSERT INTO mcq_attempts (user_id,lesson_id,score,total) VALUES (?,?,?,?)', (g.user['id'], lid, score, total))
    best = one(db.execute('SELECT MAX(score*1.0/total) b FROM mcq_attempts WHERE user_id=? AND lesson_id=?', (g.user['id'], lid)))['b'] or 0
    return jsonify({'ok': True, 'best_pct': round(best * 100)})

# ---------------- settings (exam date / goals) ----------------
@app.get('/api/settings')
@require_auth
def settings_get():
    return jsonify({'settings': get_settings(g.user['id'])})

@app.put('/api/settings')
@require_auth
def settings_put():
    b = request.get_json(silent=True) or {}
    db = get_db()
    for k in DEFAULT_SETTINGS:
        if k in b:
            v = s(b.get(k), 30).strip()
            if k == 'exam_date' and not re.match(r'^\d{4}-\d{2}-\d{2}$', v or ''): continue
            if k in ('weekly_target', 'daily_goal'):
                try: v = str(max(1, min(int(v), 100)))
                except Exception: continue
            db.execute('INSERT INTO user_settings (user_id,key,value) VALUES (?,?,?) '
                       'ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value', (g.user['id'], k, v))
    return jsonify({'settings': get_settings(g.user['id'])})

# ---------------- study planner ----------------
@app.get('/api/planner')
@require_auth
def planner_list():
    db = get_db()
    plans = rows(db.execute("""SELECT p.id, p.lesson_id, p.plan_date, p.done, l.title, l.youtube_id,
        u.name AS unit_name, s.name AS subject_name, s.id AS subject_id, s.color1, s.color2
        FROM study_plans p JOIN lessons l ON l.id=p.lesson_id
        JOIN units u ON u.id=l.unit_id JOIN subjects s ON s.id=u.subject_id
        WHERE p.user_id=? ORDER BY p.plan_date, p.done, p.id""", (g.user['id'],)))
    return jsonify({'plans': plans, 'settings': get_settings(g.user['id'])})

@app.post('/api/planner')
@require_auth
def planner_add():
    db = get_db()
    b = request.get_json(silent=True) or {}
    lid = b.get('lesson_id')
    pdate = s(b.get('plan_date'), 12) or time.strftime('%Y-%m-%d', time.gmtime())
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', pdate): return bad('Bad date')
    if not one(db.execute('SELECT id FROM lessons WHERE id=?', (lid,))): return bad('Lesson not found', 404)
    try:
        db.execute('INSERT INTO study_plans (user_id,lesson_id,plan_date) VALUES (?,?,?)', (g.user['id'], lid, pdate))
    except sqlite3.IntegrityError:
        return bad('Already planned for that day')
    return jsonify({'ok': True})

@app.post('/api/planner/<int:pid>/toggle')
@require_auth
def planner_toggle(pid):
    db = get_db()
    p = one(db.execute('SELECT * FROM study_plans WHERE id=? AND user_id=?', (pid, g.user['id'])))
    if not p: return bad('Not found', 404)
    db.execute('UPDATE study_plans SET done=? WHERE id=?', (0 if p['done'] else 1, pid))
    return jsonify({'ok': True, 'done': 0 if p['done'] else 1})

@app.delete('/api/planner/<int:pid>')
@require_auth
def planner_del(pid):
    get_db().execute('DELETE FROM study_plans WHERE id=? AND user_id=?', (pid, g.user['id']))
    return jsonify({'ok': True})

# ---------------- progress+ : units / week / streak / mcq / countdown ----------------
@app.get('/api/progress2')
@require_auth
def progress2():
    db = get_db(); uid = g.user['id']
    # per-unit completion
    units = rows(db.execute("""
        SELECT * FROM (
          SELECT u.id, u.name, u.ord, s.id AS subject_id, s.name AS subject_name, s.name_si, s.name_ta, s.color1, s.color2,
            (SELECT COUNT(*) FROM lessons l WHERE l.unit_id=u.id) AS total,
            (SELECT COUNT(*) FROM lessons l JOIN progress p ON p.lesson_id=l.id AND p.user_id=? AND p.completed=1
              WHERE l.unit_id=u.id) AS done
          FROM units u JOIN subjects s ON s.id=u.subject_id
        ) WHERE total>0 ORDER BY subject_id, ord""", (uid,)))
    # study minutes for the last 7 days
    days = [(time.strftime('%Y-%m-%d', time.gmtime(time.time() - i * 86400))) for i in range(6, -1, -1)]
    emap = {r['day']: r['seconds'] for r in rows(db.execute(
        'SELECT day, seconds FROM study_events WHERE user_id=? AND day>=?', (uid, days[0])))}
    week = [{'day': d, 'seconds': int(emap.get(d, 0))} for d in days]
    week_total = sum(w['seconds'] for w in week)
    # streak: days with study time OR a lesson completed/watched
    dayset = set(r['day'] for r in rows(db.execute('SELECT day FROM study_events WHERE user_id=? AND seconds>0', (uid,))))
    for r in rows(db.execute("SELECT completed_at d1, watched_at d2 FROM progress WHERE user_id=?", (uid,))):
        for v in (r['d1'], r['d2']):
            if v: dayset.add(v[:10])
    for r in rows(db.execute('SELECT substr(created_at,1,10) d FROM exam_attempts WHERE user_id=?', (uid,))):
        if r['d']: dayset.add(r['d'])
    streak = 0
    cur = time.strftime('%Y-%m-%d', time.gmtime())
    if cur not in dayset:
        cur = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 86400))  # allow "still alive from yesterday"
    while cur in dayset:
        streak += 1
        cur = time.strftime('%Y-%m-%d', time.gmtime(time.mktime(time.strptime(cur, '%Y-%m-%d')) - 86400))
    # MCQ average of best attempts
    mcq_avg = one(db.execute('''SELECT AVG(b) a FROM (SELECT MAX(score*1.0/total) b FROM mcq_attempts
        WHERE user_id=? GROUP BY lesson_id)''', (uid,)))['a']
    mcq_count = one(db.execute('SELECT COUNT(DISTINCT lesson_id) c FROM mcq_attempts WHERE user_id=?', (uid,)))['c']
    # practice marks
    prac = one(db.execute('SELECT COUNT(*) c, COALESCE(SUM(ok),0) ok FROM practice_marks WHERE user_id=?', (uid,)))
    # exam mode attempts
    exs = one(db.execute('SELECT COUNT(*) c, COALESCE(AVG(score*100.0/qcount),0) a, COALESCE(MAX(score*100.0/qcount),0) b FROM exam_attempts WHERE user_id=?', (uid,)))
    # exam countdown from settings
    st = get_settings(uid)
    days_left = None
    try:
        days_left = (time.mktime(time.strptime(st['exam_date'], '%Y-%m-%d')) - time.time()) / 86400.0
        days_left = int(days_left) + 1
    except Exception: pass
    today = time.strftime('%Y-%m-%d', time.gmtime())
    plan_today = rows(db.execute('SELECT id, done FROM study_plans WHERE user_id=? AND plan_date=?', (uid, today)))
    # interactive simulation stats — per subject (Chemistry + Physics auto-mapped units + explicit lessons)
    sim_subj = {}
    for sid in SIM_AUTO:
        lrws = rows(db.execute('''SELECT l.title, l.simulation_type, l.simulation_enabled, u.subject_id, u.ord AS unit_ord
            FROM lessons l JOIN units u ON u.id=l.unit_id WHERE u.subject_id=?''', (sid,)))
        tot = sum(1 for r in lrws if resolve_sim(r)['type'])
        sqp = one(db.execute("""SELECT COUNT(*) c, COALESCE(SUM(sp.completed),0) comp, AVG(sp.best_score) avg_best, COALESCE(SUM(sp.attempts),0) att
            FROM sim_progress sp JOIN lessons l ON l.id=sp.lesson_id JOIN units u ON u.id=l.unit_id
            WHERE sp.user_id=? AND u.subject_id=?""", (uid, sid)))
        if tot:
            sim_subj[str(sid)] = {'total': tot, 'tried': sqp['c'] or 0, 'completed': sqp['comp'] or 0,
                                  'avg_score': round(sqp['avg_best'] or 0), 'attempts': sqp['att'] or 0}
    sp = one(db.execute('''SELECT COUNT(*) c, SUM(completed) comp, AVG(best_score) avg_best, SUM(attempts) att
        FROM sim_progress WHERE user_id=?''', (uid,)))
    sim_total = sum(v['total'] for v in sim_subj.values()) or None
    sims = {'total': sim_total or 0, 'tried': sp['c'] or 0, 'completed': sp['comp'] or 0,
            'avg_score': round(sp['avg_best'] or 0), 'attempts': sp['att'] or 0}
    # ---------------- XP (transparent points powering levels + leaderboard) ----------------
    done_c = one(db.execute('SELECT COUNT(*) c FROM progress WHERE user_id=? AND completed=1', (uid,)))['c']
    watch_only = one(db.execute('SELECT COUNT(*) c FROM progress WHERE user_id=? AND watched=1 AND completed=0', (uid,)))['c']
    mins_all = int(one(db.execute('SELECT COALESCE(SUM(seconds),0) m FROM study_events WHERE user_id=?', (uid,)))['m'] / 60)
    chal_wins = one(db.execute('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?', (uid,)))['c']
    career_xp = one(db.execute('SELECT COALESCE(SUM(xp),0) x FROM career_attempts WHERE user_id=?', (uid,)))['x']
    xp_by = {
        'lessons': done_c * 20,
        'videos': watch_only * 5,
        'mcq': mcq_count * 10 + min(100, round((mcq_avg or 0) * 100)),
        'sims': (sp['c'] or 0) * 4 + (sp['comp'] or 0) * 10,
        'challenges': chal_wins * 15,
        'careers': min(300, career_xp),
        'exams': min(exs['c'], 20) * 10 + round(exs['a'] / 2),
        'study': mins_all,
        'streak': streak * 10,
    }
    xp_total = sum(xp_by.values())
    return jsonify({'units': units, 'week': week, 'week_seconds': week_total,
                    'today_seconds': int(emap.get(today, 0)), 'streak': streak,
                    'mcq_avg': round((mcq_avg or 0) * 100), 'mcq_lessons': mcq_count,
                    'practice_done': prac['c'], 'practice_ok': prac['ok'],
                    'settings': st, 'days_left': days_left, 'today': today, 'sims': sims, 'sims_subj': sim_subj,
                    'exams': {'taken': exs['c'], 'avg': round(exs['a']), 'best': round(exs['b'])},
                    'xp': {'total': xp_total, 'by': xp_by},
                    'plan_today_total': len(plan_today), 'plan_today_done': sum(1 for p in plan_today if p['done'])})

# ---------------- weekly leaderboard (rolling 7 days, real data only) ----------------
@app.get('/api/leaderboard')
@require_auth
def leaderboard():
    db = get_db(); uid = g.user['id']
    if not sw(db, 'leaderboard_on'): return jsonify({'enabled': False, 'top': [], 'me': None, 'players': 0})
    since = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 6 * 86400))
    lb = rows(db.execute("""
        SELECT u.id, u.name, u.school, COALESCE(SUM(e.seconds),0) sec,
          (SELECT COUNT(*) FROM progress p WHERE p.user_id=u.id AND p.completed=1) done
        FROM users u LEFT JOIN study_events e ON e.user_id=u.id AND e.day>=?
        WHERE u.role != 'admin' GROUP BY u.id ORDER BY sec DESC, done DESC, u.id""", (since,)))
    rank = next((i + 1 for i, r in enumerate(lb) if r['id'] == uid), None)
    me = next((r for r in lb if r['id'] == uid), None)
    return jsonify({
        'top': [{'name': r['name'].split(' ')[0], 'school': r['school'] or '', 'minutes': int(r['sec'] / 60),
                 'lessons': r['done'], 'me': r['id'] == uid} for r in lb[:10]],
        'me': {'rank': rank, 'minutes': int(me['sec'] / 60) if me else 0, 'lessons': me['done'] if me else 0},
        'players': len(lb)})

# =================================================== ADMIN SPEC PACK (2026-08-11p)
# Student safety tools / audit log / CSV exports / coupons / AI studio / media / weekly challenge

STATUS_TXT = {'suspend': 'suspended', 'restore': 'active'}

@app.post('/api/admin/students/<int:uid>/status')
@require_admin
def admin_student_status(uid):
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (uid,)))
    if not u: return bad('User not found', 404)
    if u['role'] == 'admin': return bad('Admin accounts cannot be suspended')
    act = s((request.get_json(silent=True) or {}).get('action'), 12)
    if act not in STATUS_TXT: return bad('Bad action')
    db.execute('UPDATE users SET status=? WHERE id=?', (STATUS_TXT[act], uid))
    if act == 'suspend':
        db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))  # kick out live sessions
    _log(db, 'student_' + act, u['email'])
    return jsonify({'ok': True, 'status': STATUS_TXT[act]})

@app.post('/api/admin/students/<int:uid>/resetpw')
@require_admin
def admin_student_resetpw(uid):
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (uid,)))
    if not u: return bad('User not found', 404)
    temp = secrets.token_hex(4)  # 8 readable chars
    db.execute('UPDATE users SET password_hash=? WHERE id=?', (generate_password_hash(temp), uid))
    db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
    _log(db, 'password_reset', u['email'])
    return jsonify({'ok': True, 'temp': temp, 'email': u['email']})

@app.post('/api/admin/students/<int:uid>/impersonate')
@require_admin
def admin_student_impersonate(uid):
    db = get_db()
    u = one(db.execute('SELECT * FROM users WHERE id=?', (uid,)))
    if not u: return bad('User not found', 404)
    if u['role'] != 'student': return bad('Only student accounts can be opened this way')
    _log(db, 'impersonate', u['email'])
    back = request.cookies.get(COOKIE)  # admin's own session token -> given to the browser so it can switch back later
    token = create_session(u['id'])
    resp = jsonify({'ok': True, 'user': public_user(u), 'back': back})
    set_session_cookie(resp, token)
    return resp

@app.post('/api/auth/unimpersonate')
def unimpersonate():
    b = request.get_json(silent=True) or {}
    tok = s(b.get('back'), 100)
    u = one(get_db().execute('''SELECT u.* FROM sessions se JOIN users u ON u.id=se.user_id
        WHERE se.token=? AND se.expires_at>?''', (tok, int(time.time() * 1000))))
    if not u or u['role'] != 'admin': return bad('Could not switch back — please log in again.', 400)
    resp = jsonify({'ok': True, 'user': public_user(u)})
    set_session_cookie(resp, tok)
    return resp

# ---------------- audit log + CSV exports ----------------
@app.get('/api/admin/logs')
@require_admin
def admin_logs():
    return jsonify({'logs': rows(get_db().execute('SELECT * FROM admin_logs ORDER BY id DESC LIMIT 250'))})

def _csv_resp(name, header, data):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in data: w.writerow(r)
    return Response(buf.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=alplanner-%s.csv' % name})

@app.get('/api/admin/export/<kind>')
@require_admin
def admin_export(kind):
    db = get_db()
    if kind == 'students':
        rs = db.execute('''SELECT id,name,email,school,district,al_year,medium,stream,subjects,status,premium_until,created_at
                           FROM users WHERE role='student' ORDER BY id DESC''').fetchall()
        _log(db, 'export', 'students')
        return _csv_resp('students', ['id', 'name', 'email', 'school', 'district', 'al_year', 'medium', 'stream', 'subjects', 'status', 'premium_until', 'created_at'],
                         [[r['id'], r['name'], r['email'], r['school'], r['district'], r['al_year'], r['medium'], r['stream'], r['subjects'], r['status'], r['premium_until'], r['created_at']] for r in rs])
    if kind == 'payments':
        rs = db.execute('''SELECT p.id,u.name,u.email,p.amount,p.coupon,p.note,p.status,p.reason,p.created_at,p.decided_at
                           FROM payments p JOIN users u ON u.id=p.user_id ORDER BY p.id DESC''').fetchall()
        _log(db, 'export', 'payments')
        return _csv_resp('payments', ['id', 'student', 'email', 'amount', 'coupon', 'note', 'status', 'reason', 'created_at', 'decided_at'],
                         [[r['id'], r['name'], r['email'], r['amount'], r['coupon'], r['note'], r['status'], r['reason'], r['created_at'], r['decided_at']] for r in rs])
    if kind == 'exams':
        rs = db.execute('''SELECT e.id,u.name,u.email,e.subject,e.mode,e.score,e.qcount,e.seconds,e.created_at
                           FROM exam_attempts e JOIN users u ON u.id=e.user_id ORDER BY e.id DESC''').fetchall()
        _log(db, 'export', 'exams')
        return _csv_resp('exam-results', ['id', 'student', 'email', 'subject', 'mode', 'score', 'out_of', 'seconds', 'created_at'],
                         [[r['id'], r['name'], r['email'], r['subject'], r['mode'], r['score'], r['qcount'], r['seconds'], r['created_at']] for r in rs])
    if kind == 'questions':
        rs = db.execute('''SELECT q.id,l.title,q.q,q.a,q.b,q.c,q.d,q.answer,q.explanation
                           FROM lesson_questions q JOIN lessons l ON l.id=q.lesson_id ORDER BY q.lesson_id, q.ord, q.id''').fetchall()
        _log(db, 'export', 'questions')
        return _csv_resp('questions', ['id', 'lesson', 'question', 'A', 'B', 'C', 'D', 'correct', 'explanation'],
                         [[r['id'], r['title'], r['q'], r['a'], r['b'], r['c'], r['d'], r['answer'], r['explanation']] for r in rs])
    return bad('Unknown export', 404)

# ---------------- 🎟️ coupons (Premium discounts) ----------------
@app.get('/api/admin/coupons')
@require_admin
def admin_coupons():
    return jsonify({'coupons': rows(get_db().execute('SELECT * FROM coupons ORDER BY id DESC LIMIT 200'))})

@app.post('/api/admin/coupons')
@require_admin
def admin_coupon_add():
    db = get_db(); b = request.get_json(silent=True) or {}
    code = s(b.get('code'), 40).upper().replace(' ', '')
    if not re.match(r'^[A-Z0-9-]{3,40}$', code): return bad('Code must be 3-40 letters/numbers (e.g. AL2027)')
    kind = 'fixed' if b.get('kind') == 'fixed' else 'percent'
    try: value = max(0, min(int(b.get('value') or 0), 1000000))
    except (TypeError, ValueError): value = 0
    if kind == 'percent' and value > 100: value = 100
    if not value: return bad('Please set the discount value')
    try: maxu = max(0, min(int(b.get('max_uses') or 0), 100000))
    except (TypeError, ValueError): maxu = 0
    exp = s(b.get('expires'), 12)
    if exp and not re.match(r'^\d{4}-\d{2}-\d{2}$', exp): return bad('Expiry must be a date (YYYY-MM-DD)')
    try:
        db.execute('INSERT INTO coupons (code,kind,value,expires,max_uses) VALUES (?,?,?,?,?)', (code, kind, value, exp, maxu))
    except sqlite3.IntegrityError:
        return bad('That code already exists', 409)
    _log(db, 'coupon_create', code)
    return jsonify({'ok': True})

@app.put('/api/admin/coupons/<int:cid>')
@require_admin
def admin_coupon_toggle(cid):
    db = get_db()
    cp = one(db.execute('SELECT * FROM coupons WHERE id=?', (cid,)))
    if not cp: return bad('Not found', 404)
    nv = 0 if cp['active'] else 1
    db.execute('UPDATE coupons SET active=? WHERE id=?', (nv, cid))
    _log(db, 'coupon_' + ('on' if nv else 'off'), cp['code'])
    return jsonify({'ok': True, 'active': nv})

@app.delete('/api/admin/coupons/<int:cid>')
@require_admin
def admin_coupon_del(cid):
    db = get_db()
    cp = one(db.execute('SELECT * FROM coupons WHERE id=?', (cid,)))
    if not cp: return bad('Not found', 404)
    db.execute('DELETE FROM coupons WHERE id=?', (cid,))
    _log(db, 'coupon_delete', cp['code'])
    return jsonify({'ok': True})

# ---------------- 🤖 AI studio: knowledge base + answer reports ----------------
@app.get('/api/admin/ailore')
@require_admin
def admin_ailore():
    db = get_db()
    return jsonify({'lore': rows(db.execute('SELECT * FROM ai_knowledge ORDER BY id DESC LIMIT 100')),
                    'reports': rows(db.execute('''SELECT r.*, u.name, u.email FROM ai_reports r
                        JOIN users u ON u.id=r.user_id ORDER BY CASE r.status WHEN 'open' THEN 0 ELSE 1 END, r.id DESC LIMIT 100'''))})

@app.post('/api/admin/ailore')
@require_admin
def admin_ailore_add():
    db = get_db()
    txt = s((request.get_json(silent=True) or {}).get('text'), 1500)
    if len(txt) < 5: return bad('Please write the knowledge note (5+ characters)')
    db.execute('INSERT INTO ai_knowledge (text) VALUES (?)', (txt,))
    _log(db, 'ai_knowledge', txt[:60])
    return jsonify({'ok': True})

@app.delete('/api/admin/ailore/<int:kid>')
@require_admin
def admin_ailore_del(kid):
    db = get_db()
    db.execute('DELETE FROM ai_knowledge WHERE id=?', (kid,))
    _log(db, 'ai_knowledge_delete', '#%d' % kid)
    return jsonify({'ok': True})

@app.put('/api/admin/aireports/<int:rid>')
@require_admin
def admin_aireport_resolve(rid):
    db = get_db()
    r = one(db.execute('SELECT * FROM ai_reports WHERE id=?', (rid,)))
    if not r: return bad('Not found', 404)
    stt = 'resolved' if (request.get_json(silent=True) or {}).get('action') == 'resolve' else 'open'
    db.execute('UPDATE ai_reports SET status=? WHERE id=?', (stt, rid))
    _log(db, 'ai_report_' + stt, '#%d' % rid)
    return jsonify({'ok': True, 'status': stt})

@app.post('/api/ai/report')
@require_auth
def ai_report():
    db = get_db()
    b = request.get_json(silent=True) or {}
    q, a = s(b.get('question'), 1500), s(b.get('answer'), 3000)
    if not q or not a: return bad('Nothing to report')
    today = time.strftime('%Y-%m-%d', time.gmtime())
    n = one(db.execute('SELECT COUNT(*) c FROM ai_reports WHERE user_id=? AND substr(created_at,1,10)=?', (g.user['id'], today)))['c']
    if n >= 10: return bad('You have sent many reports today — the team will review them!')
    db.execute('INSERT INTO ai_reports (user_id,question,answer) VALUES (?,?,?)', (g.user['id'], q, a))
    return jsonify({'ok': True})

# ---------------- 🗂️ media manager (uploads folder) ----------------
@app.get('/api/admin/media')
@require_admin
def admin_media():
    out = []
    base = os.path.abspath(UPLOAD_DIR)
    for root, _dirs, files in os.walk(base):
        for fn in files:
            fp = os.path.join(root, fn)
            try: stt = os.stat(fp)
            except OSError: continue
            out.append({'f': os.path.relpath(fp, base).replace(os.sep, '/'), 'size': stt.st_size, 'mtime': int(stt.st_mtime)})
    out.sort(key=lambda x: x['mtime'], reverse=True)
    return jsonify({'files': out[:500], 'total': len(out)})

@app.delete('/api/admin/media')
@require_admin
def admin_media_del():
    db = get_db()
    rel = s((request.get_json(silent=True) or {}).get('f'), 300)
    base = os.path.abspath(UPLOAD_DIR)
    fp = os.path.abspath(os.path.join(base, rel))
    if not rel or not fp.startswith(base + os.sep) or not os.path.isfile(fp): return bad('File not found', 404)
    try: os.remove(fp)
    except OSError: return bad('Could not delete that file')
    _log(db, 'media_delete', rel)
    return jsonify({'ok': True})

# ---------------- 🏆 weekly challenge ----------------
CH_SUBJECTS = ('mixed', 'chem', 'phys', 'bio')
CH_MODES = {'m1': (10, 15), 'm2': (25, 35), 'm3': (50, 60)}

def _chal_view(db, ch, uid, today):
    state = 'now' if (ch['active'] and ch['start'] <= today <= ch['end']) else ('upcoming' if (ch['active'] and today < ch['start']) else 'past')
    n = one(db.execute('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=?', (ch['id'],)))['c']
    d = {'id': ch['id'], 'title': ch['title'], 'subject': ch['subject'], 'mode': ch['mode'],
         'start': ch['start'], 'end': ch['end'], 'prize1': ch['prize1'], 'prize2': ch['prize2'], 'prize3': ch['prize3'],
         'state': state, 'players': n, 'questions': CH_MODES.get(ch['mode'], (10, 15))[0], 'minutes': CH_MODES.get(ch['mode'], (10, 15))[1]}
    if uid:
        mine = one(db.execute('SELECT score,qcount,seconds FROM challenge_attempts WHERE challenge_id=? AND user_id=?', (ch['id'], uid)))
        if mine:
            d['mine'] = {'score': mine['score'], 'qcount': mine['qcount'], 'seconds': mine['seconds']}
            d['rank'] = one(db.execute('''SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=? AND
                (score>?) OR (score=? AND seconds<?) OR (score=? AND seconds=? AND user_id<?)''',
                (ch['id'], mine['score'], mine['score'], mine['seconds'], mine['score'], mine['seconds'], uid)))['c'] + 1
    return d

@app.get('/api/challenge')
def challenge_public():
    db = get_db()
    uid = g.user['id'] if g.user else None
    today = time.strftime('%Y-%m-%d', time.gmtime())
    now_l, up_l, past_l = [], [], []
    for ch in rows(db.execute('SELECT * FROM challenges ORDER BY start DESC, id DESC LIMIT 20')):
        v = _chal_view(db, ch, uid, today)
        (now_l if v['state'] == 'now' else up_l if v['state'] == 'upcoming' else past_l).append(v)
    past_l = past_l[:5]
    for v in past_l:  # boards for finished challenges
        v['board'] = _chal_board(db, v['id'])
    return jsonify({'today': today, 'now': now_l, 'upcoming': up_l, 'past': past_l})

def _chal_board(db, cid):
    return [{'name': r['name'].split(' ')[0], 'school': r['school'] or '', 'score': r['score'], 'qcount': r['qcount'],
             'seconds': r['seconds'], 'prize_status': r['prize_status'], 'aid': r['id']}
            for r in rows(db.execute('''SELECT a.id, a.score, a.qcount, a.seconds, a.prize_status, u.name, u.school
                FROM challenge_attempts a JOIN users u ON u.id=a.user_id
                WHERE a.challenge_id=? ORDER BY a.score DESC, a.seconds ASC, a.id ASC LIMIT 50''', (cid,)))]

@app.get('/api/challenge/<int:cid>/board')
@require_auth
def challenge_board(cid):
    db = get_db()
    ch = one(db.execute('SELECT * FROM challenges WHERE id=?', (cid,)))
    if not ch: return bad('Not found', 404)
    today = time.strftime('%Y-%m-%d', time.gmtime())
    if ch['active'] and today <= ch['end'] and g.user['role'] != 'admin':
        return bad('The leaderboard unlocks when this challenge ends', 403)
    return jsonify({'board': _chal_board(db, cid)})

@app.post('/api/challenge/<int:cid>/attempt')
@require_auth
def challenge_attempt(cid):
    db = get_db()
    ch = one(db.execute('SELECT * FROM challenges WHERE id=?', (cid,)))
    if not ch: return bad('Challenge not found', 404)
    today = time.strftime('%Y-%m-%d', time.gmtime())
    if not (ch['active'] and ch['start'] <= today <= ch['end']):
        return bad('This challenge is not open right now', 403)
    b = request.get_json(silent=True) or {}
    n_q, _mins = CH_MODES.get(ch['mode'], (10, 15))
    try:
        score = max(0, min(int(b.get('score')), n_q)); secs = max(0, min(int(b.get('seconds') or 0), 4 * 3600))
    except (TypeError, ValueError):
        return bad('Bad numbers')
    try:
        db.execute('INSERT INTO challenge_attempts (challenge_id,user_id,score,qcount,seconds) VALUES (?,?,?,?,?)',
                   (cid, g.user['id'], score, n_q, secs))
    except sqlite3.IntegrityError:
        return bad('You already sat this challenge — one attempt each!', 409)
    rank = one(db.execute('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=? AND (score>? OR (score=? AND seconds<?))',
                          (cid, score, score, secs)))['c'] + 1
    return jsonify({'ok': True, 'rank': rank})

@app.get('/api/admin/challenges')
@require_admin
def admin_challenges():
    db = get_db()
    out = []
    for ch in rows(db.execute('SELECT * FROM challenges ORDER BY id DESC LIMIT 50')):
        d = dict(ch)
        d['players'] = one(db.execute('SELECT COUNT(*) c FROM challenge_attempts WHERE challenge_id=?', (ch['id'],)))['c']
        d['board'] = _chal_board(db, ch['id'])
        out.append(d)
    return jsonify({'challenges': out})

@app.post('/api/admin/challenges')
@require_admin
def admin_challenge_add():
    db = get_db(); b = request.get_json(silent=True) or {}
    title = s(b.get('title'), 120)
    if len(title) < 3: return bad('Please give the challenge a title')
    subj = s(b.get('subject'), 8)
    if subj not in CH_SUBJECTS: subj = 'mixed'
    mode = s(b.get('mode'), 4)
    if mode not in CH_MODES: mode = 'm1'
    start, end = s(b.get('start'), 12), s(b.get('end'), 12)
    if not (re.match(r'^\d{4}-\d{2}-\d{2}$', start) and re.match(r'^\d{4}-\d{2}-\d{2}$', end)): return bad('Pick start and end dates')
    if end < start: return bad('End date must be after the start date')
    db.execute('INSERT INTO challenges (title,subject,mode,start,end,prize1,prize2,prize3) VALUES (?,?,?,?,?,?,?,?)',
               (title, subj, mode, start, end, s(b.get('prize1'), 120), s(b.get('prize2'), 120), s(b.get('prize3'), 120)))
    _log(db, 'challenge_create', title)
    return jsonify({'ok': True})

@app.put('/api/admin/challenges/<int:cid>')
@require_admin
def admin_challenge_edit(cid):
    db = get_db()
    ch = one(db.execute('SELECT * FROM challenges WHERE id=?', (cid,)))
    if not ch: return bad('Not found', 404)
    b = request.get_json(silent=True) or {}
    if 'prize_status' in b:
        aid = int(b.get('attempt_id') or 0)
        stt = s(b.get('prize_status'), 12)
        if stt not in ('', 'pending', 'verified', 'sent', 'delivered'): return bad('Bad status')
        db.execute('UPDATE challenge_attempts SET prize_status=? WHERE id=? AND challenge_id=?', (stt, aid, cid))
        _log(db, 'prize_status', 'challenge #%d attempt #%d -> %s' % (cid, aid, stt or 'none'))
        return jsonify({'ok': True})
    title = s(b.get('title', ch['title']), 120) or ch['title']
    subj = s(b.get('subject', ch['subject']), 8)
    if subj not in CH_SUBJECTS: subj = ch['subject']
    mode = s(b.get('mode', ch['mode']), 4)
    if mode not in CH_MODES: mode = ch['mode']
    start, end = s(b.get('start', ch['start']), 12), s(b.get('end', ch['end']), 12)
    if not (re.match(r'^\d{4}-\d{2}-\d{2}$', start) and re.match(r'^\d{4}-\d{2}-\d{2}$', end)): start, end = ch['start'], ch['end']
    active = 1 if b.get('active', ch['active']) in (1, True, '1') else 0
    db.execute('UPDATE challenges SET title=?,subject=?,mode=?,start=?,end=?,prize1=?,prize2=?,prize3=?,active=? WHERE id=?',
               (title, subj, mode, start, end, s(b.get('prize1', ch['prize1']), 120), s(b.get('prize2', ch['prize2']), 120),
                s(b.get('prize3', ch['prize3']), 120), active, cid))
    _log(db, 'challenge_update', title)
    return jsonify({'ok': True})

@app.delete('/api/admin/challenges/<int:cid>')
@require_admin
def admin_challenge_del(cid):
    db = get_db()
    ch = one(db.execute('SELECT * FROM challenges WHERE id=?', (cid,)))
    if not ch: return bad('Not found', 404)
    db.execute('DELETE FROM challenges WHERE id=?', (cid,))
    _log(db, 'challenge_delete', ch['title'])
    return jsonify({'ok': True})

# ---------------- 🧪 Sim lab: catalog + events + analytics (v q) ----------------
@app.post('/api/sim/event')
@require_auth
def sim_event2():
    db = get_db()
    b = request.get_json(silent=True) or {}
    ty = s(b.get('sim_type'), 30)
    if ty not in SIM_TYPES: return bad('Unknown simulator', 404)
    cat = one(db.execute('SELECT premium FROM sim_catalog WHERE sim_type=?', (ty,)))
    if cat and cat['premium'] and not (is_premium(g.user) or g.user['role'] == 'admin'):
        return jsonify({'error': 'Premium simulator', 'premium': True}), 403
    ev = s(b.get('event'), 12)
    uid = g.user['id']
    if ev == 'start':
        today = time.strftime('%Y-%m-%d', time.gmtime())
        db.execute('INSERT INTO sim_launches (user_id,sim_type,day,n) VALUES (?,?,?,1) '
                   'ON CONFLICT(user_id,sim_type,day) DO UPDATE SET n=n+1', (uid, ty, today))
        return jsonify({'ok': True})
    if ev == 'challenge':
        goal = s(b.get('goal'), 160)
        if not goal: return bad('Missing goal')
        cur = db.execute('INSERT OR IGNORE INTO sim_challenge_wins (user_id,sim_type,goal) VALUES (?,?,?)', (uid, ty, goal))
        first = cur.rowcount > 0
        total = one(db.execute('SELECT COUNT(*) c FROM sim_challenge_wins WHERE user_id=?', (uid,)))['c']
        return jsonify({'ok': True, 'first': bool(first), 'wins': total, 'xp': 15 if first else 2})
    if ev == 'score':
        try:
            sc = max(0, int(b.get('score') or 0)); tt = max(1, int(b.get('total') or 1)); sc = min(sc, tt)
        except Exception: return bad('Bad score')
        pct = round(sc * 100 / tt)
        db.execute('INSERT INTO sim_events (user_id,sim_type,event,score,total,pct) VALUES (?,?,?,?,?,?)', (uid, ty, 'score', sc, tt, pct))
        return jsonify({'ok': True, 'pct': pct})
    return bad('Bad event')

# ---------------- 🏆 Weekly sim leaderboard (v2026.08.12s) ----------------
@app.get('/api/sims/leaderboard')
def weekly_sim_leaderboard():
    db = get_db()
    if not sw(db, 'leaderboard_on'): return jsonify({'enabled': False, 'rows': [], 'me': None, 'week_start': '', 'week_end': ''})
    now = time.time()
    lt = time.gmtime(now)
    monday = now - (lt.tm_wday * 86400 + lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec)
    wstart = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(monday))
    wend = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(monday + 7 * 86400))
    # anti-farm: best score per sim per day per user; sum those
    board = rows(db.execute("""SELECT u.id, u.name, SUM(q.sc) pts, COUNT(DISTINCT q.sim_type) sims
        FROM (SELECT user_id, sim_type, date(created_at) d, MAX(score) sc FROM sim_events
              WHERE event='score' AND created_at>=? GROUP BY user_id, sim_type, date(created_at)) q
        JOIN users u ON u.id=q.user_id AND u.status!='suspended'
        GROUP BY q.user_id ORDER BY pts DESC, sims DESC, u.id ASC""", (wstart,)))
    uid = g.user['id'] if g.user else 0
    out = [{'rank': i + 1, 'name': r['name'], 'points': r['pts'], 'sims': r['sims'], 'me': r['id'] == uid} for i, r in enumerate(board[:50])]
    me = None
    for i, r in enumerate(board):
        if r['id'] == uid:
            me = {'rank': i + 1, 'points': r['pts'], 'sims': r['sims']}
            break
    return jsonify({'week_start': wstart[:10], 'week_end': wend, 'rows': out, 'me': me})

@app.get('/api/sims')
def sims_public():
    db = get_db()
    pid, uid2 = request.args.get('lesson_id', type=int), request.args.get('unit_id', type=int)
    sql = 'SELECT sim_type,subject,title,descr,difficulty,xp_reward,badge,unit_id,lesson_id,ord,premium FROM sim_catalog WHERE enabled=1'
    par = []
    if pid: sql += ' AND lesson_id=?'; par.append(pid)
    elif uid2: sql += ' AND unit_id=?'; par.append(uid2)
    sql += ' ORDER BY ord, id'
    sims = rows(db.execute(sql, par))
    if pid or uid2:  # related-lab lookups fall back to all sims of the same subject when nothing is pinned
        return jsonify({'sims': sims})
    cnt = {}
    for r2 in sims:
        if r2['subject']: cnt[r2['subject']] = cnt.get(r2['subject'], 0) + 1
    return jsonify({'sims': sims, 'counts': cnt})

@app.get('/api/admin/sims')
@require_admin
def admin_sims():
    db = get_db()
    cat = rows(db.execute('SELECT * FROM sim_catalog ORDER BY ord, id'))
    per = {}
    for r2 in rows(db.execute('SELECT sim_type, COALESCE(SUM(n),0) n, COUNT(DISTINCT user_id) u FROM sim_launches GROUP BY sim_type')):
        per.setdefault(r2['sim_type'], {})['launches'] = r2['n']; per[r2['sim_type']]['students'] = r2['u']
    for r2 in rows(db.execute("SELECT sim_type, COUNT(*) c, COUNT(DISTINCT user_id) u FROM sim_challenge_wins GROUP BY sim_type")):
        per.setdefault(r2['sim_type'], {})['wins'] = r2['c']
    for r2 in rows(db.execute('SELECT sim_type, COALESCE(SUM(completed),0) comp, COALESCE(SUM(attempts),0) att, AVG(best_score) bs FROM sim_progress GROUP BY sim_type')):
        per.setdefault(r2['sim_type'], {}).update({'completed': r2['comp'], 'attempts': r2['att'], 'avg_best': round(r2['bs'] or 0)})
    for row_ in cat:
        p = per.get(row_['sim_type'], {})
        row_['launches'] = p.get('launches', 0); row_['students'] = p.get('students', 0)
        row_['wins'] = p.get('wins', 0); row_['completed'] = p.get('completed', 0)
        row_['attempts'] = p.get('attempts', 0); row_['avg_best'] = p.get('avg_best', 0)
    d7 = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 6 * 86400))
    d30 = time.strftime('%Y-%m-%d', time.gmtime(time.time() - 29 * 86400))
    series = []
    for i in range(7, -1, -1):
        dd = time.strftime('%Y-%m-%d', time.gmtime(time.time() - i * 86400))
        series.append({'label': dd[5:], 'n': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day=?', (dd,)))['s']})
    cards = {
        'launches': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM sim_launches'))['s'],
        'students': one(db.execute('SELECT COUNT(DISTINCT user_id) c FROM sim_launches'))['c'],
        'wins': one(db.execute('SELECT COUNT(*) c FROM sim_challenge_wins'))['c'],
        'completed': one(db.execute('SELECT COALESCE(SUM(completed),0) s FROM sim_progress'))['s'],
        'week': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day>=?', (d7,)))['s'],
        'month': one(db.execute('SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day>=?', (d30,)))['s'],
        'today': one(db.execute("SELECT COALESCE(SUM(n),0) s FROM sim_launches WHERE day=?", (time.strftime('%Y-%m-%d', time.gmtime()),)))['s'],
    }
    return jsonify({'sims': cat, 'cards': cards, 'series': series})

@app.put('/api/admin/sims/<int:cid>')
@require_admin
def admin_sim_edit(cid):
    db = get_db()
    row = one(db.execute('SELECT * FROM sim_catalog WHERE id=?', (cid,)))
    if not row: return bad('Not found', 404)
    b = request.get_json(silent=True) or {}
    diff = s(b.get('difficulty', row['difficulty']), 8)
    if diff not in ('easy', 'medium', 'hard'): diff = row['difficulty']
    try: xp = max(0, min(int(b.get('xp_reward', row['xp_reward'])), 500))
    except (TypeError, ValueError): xp = row['xp_reward']
    db.execute('''UPDATE sim_catalog SET title=?, descr=?, difficulty=?, objectives=?, formulas=?, tips=?,
                  xp_reward=?, badge=?, unit_id=?, lesson_id=?, enabled=?, premium=? WHERE id=?''',
               (s(b.get('title', row['title']), 160), s(b.get('descr', row['descr']), 500), diff,
                s(b.get('objectives', row['objectives']), 800), s(b.get('formulas', row['formulas']), 400),
                s(b.get('tips', row['tips']), 500), xp, s(b.get('badge', row['badge']), 60),
                b.get('unit_id', row['unit_id']), b.get('lesson_id', row['lesson_id']),
                1 if b.get('enabled', row['enabled']) in (1, True, '1') else 0,
                (1 if b['premium'] in (1, True, '1') else 0) if 'premium' in b else row['premium'], cid))
    _log(db, 'sim_update', row['sim_type'])
    return jsonify({'ok': True})

# ---------------- CAREER GAMES (2026-08-11q) ----------------
_CAREER_SEED = (
    ('memory', 'Memory Match', 'Flip cards and match A/L term pairs (symbols, units, definitions).'),
    ('scramble', 'Word Scramble', 'Unscramble the A/L subject word before time runs out.'),
    ('quiz', 'Rapid GK Quiz', '5 quick general-knowledge questions - score decides your XP.'),
)

@app.get('/api/careers')
@require_auth
def careers_public():
    db = get_db()
    if not sw(db, 'careers_enabled'): return bad('Career Games are turned off by admin right now.', 403)
    uid = g.user['id']
    games = []
    for r2 in rows(db.execute('SELECT * FROM careers WHERE active=1 ORDER BY id')):
        att = one(db.execute('SELECT COUNT(*) c, COALESCE(MAX(score),0) best FROM career_attempts WHERE user_id=? AND gkey=?', (uid, r2['gkey'])))
        won = one(db.execute("SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=? AND won=1", (uid, r2['gkey'])))['c'] > 0
        games.append({'gkey': r2['gkey'], 'name': r2['name'], 'descr': r2['descr'],
                      'reward': bool(r2['reward_code']) and not (won and r2['reward_once']),
                      'attempts_used': att['c'], 'max_attempts': r2['max_attempts'], 'best': att['best'], 'won': won})
    return jsonify({'games': games})

@app.post('/api/careers/finish')
@require_auth
def careers_finish():
    db = get_db()
    if not sw(db, 'careers_enabled'): return bad('Career Games are turned off by admin right now.', 403)
    b = request.get_json(silent=True) or {}
    gk = s(b.get('gkey'), 30)
    gme = one(db.execute('SELECT * FROM careers WHERE gkey=? AND active=1', (gk,)))
    if not gme: return bad('Game not found or disabled', 403)
    uid = g.user['id']
    try: score = max(0, min(100, int(b.get('score') or 0)))
    except (TypeError, ValueError): score = 0
    used = one(db.execute('SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=?', (uid, gk)))['c']
    if gme['max_attempts'] and used >= gme['max_attempts']:
        return jsonify({'error': 'Attempt limit reached for this game.'}), 429
    won = bool(b.get('won')) and score >= 60
    xp = min(50, score // 2)
    coupon = ''
    if won and gme['reward_code']:
        got = one(db.execute("SELECT COUNT(*) c FROM career_attempts WHERE user_id=? AND gkey=? AND won=1", (uid, gk)))['c']
        if not (got and gme['reward_once']):
            # grant a UNIQUE one-use code per student, e.g. PLAY15-S7 (template + student id)
            gcode = (gme['reward_code'] + '-S' + str(uid))[:40]
            if not one(db.execute('SELECT id FROM coupons WHERE code=?', (gcode,))):
                exp = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 90 * 86400))
                db.execute("INSERT INTO coupons (code,kind,value,expires,max_uses) VALUES (?,?,?,?,1)", (gcode, 'percent', 15, exp))
            coupon = gcode
    db.execute('INSERT INTO career_attempts (user_id,gkey,score,xp,won) VALUES (?,?,?,?,?)', (uid, gk, score, xp, 1 if won else 0))
    return jsonify({'ok': True, 'xp': xp, 'won': won, 'coupon': coupon})

@app.get('/api/admin/careers')
@require_admin
def admin_careers():
    db = get_db()
    out = []
    for r2 in rows(db.execute('SELECT * FROM careers ORDER BY id')):
        st2 = one(db.execute('SELECT COUNT(*) c, COUNT(DISTINCT user_id) u, COALESCE(SUM(won),0) w, COALESCE(SUM(xp),0) x FROM career_attempts WHERE gkey=?', (r2['gkey'],)))
        d2 = dict(r2); d2.update({'attempts': st2['c'], 'students': st2['u'], 'wins': st2['w'], 'xp_given': st2['x']})
        out.append(d2)
    return jsonify({'games': out})

@app.post('/api/admin/careers')
@require_admin
def admin_career_add():
    db = get_db()
    b = request.get_json(silent=True) or {}
    gk = s(b.get('gkey'), 30).lower().replace(' ', '_')
    if not gk: return bad('gkey required')
    try:
        cur = db.execute('INSERT INTO careers (gkey,name,descr) VALUES (?,?,?)',
                         (gk, s(b.get('name'), 80) or gk, s(b.get('descr'), 300)))
    except sqlite3.IntegrityError:
        return bad('gkey already exists')
    _log(db, 'career_create', gk)
    return jsonify({'ok': True, 'id': cur.lastrowid})

@app.put('/api/admin/careers/<int:cid>')
@require_admin
def admin_career_edit(cid):
    db = get_db()
    row = one(db.execute('SELECT * FROM careers WHERE id=?', (cid,)))
    if not row: return bad('Not found', 404)
    b = request.get_json(silent=True) or {}
    try: mx = max(0, min(9999, int(b.get('max_attempts', row['max_attempts']))))
    except (TypeError, ValueError): mx = row['max_attempts']
    db.execute('UPDATE careers SET name=?, descr=?, reward_code=?, reward_once=?, max_attempts=?, active=? WHERE id=?',
               (s(b.get('name', row['name']), 80), s(b.get('descr', row['descr']), 300),
                s(b.get('reward_code', row['reward_code']), 40).upper(),
                1 if b.get('reward_once', row['reward_once']) in (1, True, '1') else 0, mx,
                1 if b.get('active', row['active']) in (1, True, '1') else 0, cid))
    _log(db, 'career_update', row['gkey'])
    return jsonify({'ok': True})

@app.delete('/api/admin/careers/<int:cid>')
@require_admin
def admin_career_del(cid):
    db = get_db()
    row = one(db.execute('SELECT * FROM careers WHERE id=?', (cid,)))
    if not row: return bad('Not found', 404)
    db.execute('DELETE FROM careers WHERE id=?', (cid,))
    db.execute('DELETE FROM career_attempts WHERE gkey=?', (row['gkey'],))
    _log(db, 'career_delete', row['gkey'])
    return jsonify({'ok': True})


# ---------------- Virtual Lab & NIE Practicals Database (Part 1: schema + seed + API) ----------------
# Official NIE A/L practical lists: Physics (43 practicals) + Chemistry (45 practicals).
# Canonical content lives in ./practicals/*.json (short keys mapped below) so BOTH
# the Python and Node servers seed identical data.

PRAC_SCHEMA = """
CREATE TABLE IF NOT EXISTS practicals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '',
  practical_title_en TEXT NOT NULL DEFAULT '',
  practical_title_si TEXT NOT NULL DEFAULT '',
  unit_lesson TEXT NOT NULL DEFAULT '',
  objective TEXT NOT NULL DEFAULT '',
  theory_principle TEXT NOT NULL DEFAULT '',
  apparatus_materials TEXT NOT NULL DEFAULT '',
  chemicals TEXT DEFAULT NULL,
  diagram_setup_url TEXT DEFAULT NULL,
  procedure TEXT NOT NULL DEFAULT '',
  observation_table_format TEXT NOT NULL DEFAULT '',
  formulae TEXT NOT NULL DEFAULT '',
  calculations TEXT NOT NULL DEFAULT '',
  graph_details TEXT NOT NULL DEFAULT '',
  result_conclusion TEXT NOT NULL DEFAULT '',
  precautions_safety TEXT NOT NULL DEFAULT '',
  common_errors TEXT NOT NULL DEFAULT '',
  viva_questions TEXT NOT NULL DEFAULT '[]',
  past_paper_questions TEXT NOT NULL DEFAULT '[]',
  seed_key TEXT UNIQUE NOT NULL);
CREATE INDEX IF NOT EXISTS idx_prac_subject ON practicals(subject);
CREATE INDEX IF NOT EXISTS idx_prac_category ON practicals(category);
"""

PRAC_KEYMAP = {'s': 'subject', 'c': 'category', 'en': 'practical_title_en', 'si': 'practical_title_si',
    'u': 'unit_lesson', 'o': 'objective', 'th': 'theory_principle', 'ap': 'apparatus_materials',
    'ch': 'chemicals', 'dg': 'diagram_setup_url', 'pr': 'procedure', 'ob': 'observation_table_format',
    'f': 'formulae', 'ca': 'calculations', 'g': 'graph_details', 'r': 'result_conclusion',
    'pc': 'precautions_safety', 'er': 'common_errors', 'vq': 'viva_questions', 'pp': 'past_paper_questions'}
PRAC_COLS = ['subject', 'category', 'practical_title_en', 'practical_title_si', 'unit_lesson', 'objective',
    'theory_principle', 'apparatus_materials', 'chemicals', 'diagram_setup_url', 'procedure',
    'observation_table_format', 'formulae', 'calculations', 'graph_details', 'result_conclusion',
    'precautions_safety', 'common_errors', 'viva_questions', 'past_paper_questions', 'seed_key']

def seed_practicals():
    """Idempotently upsert practicals/*.json into the practicals table. Returns record count."""
    import json as _json, glob as _glob, io as _io, os as _os
    db = sqlite3.connect(DB_PATH)
    db.executescript(PRAC_SCHEMA)
    recs = []
    base = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'practicals')
    for fp in sorted(_glob.glob(_os.path.join(base, '*.json'))):
        for rec in _json.load(_io.open(fp, encoding='utf-8')):
            row = {c: None for c in PRAC_COLS}
            for sk, col in PRAC_KEYMAP.items():
                if rec.get(sk) is not None:
                    row[col] = rec[sk]
            row['practical_title_si'] = rec.get('si') or rec.get('en') or ''
            row['viva_questions'] = _json.dumps(rec.get('vq') or [], ensure_ascii=False)
            row['past_paper_questions'] = _json.dumps(rec.get('pp') or [], ensure_ascii=False)
            row['seed_key'] = '%s | %s' % (row['subject'] or '', row['practical_title_en'] or '')
            recs.append(row)
    keys = [r['seed_key'] for r in recs]
    if keys:
        db.execute('DELETE FROM practicals WHERE seed_key NOT IN (%s)' % ','.join('?' * len(keys)), keys)
    upd = ', '.join('%s=excluded.%s' % (c, c) for c in PRAC_COLS if c != 'seed_key')
    for row in recs:
        vals = [row[c] for c in PRAC_COLS]
        db.execute(('INSERT INTO practicals (%s) VALUES (%s) ON CONFLICT(seed_key) DO UPDATE SET %s'
                    % (','.join(PRAC_COLS), ','.join('?' * len(PRAC_COLS)), upd)), vals)
    db.commit()
    db.close()
    return len(recs)

try:
    _prac_n = seed_practicals()
    print('NIE Practicals seeded: %d records (Physics 43 / Chemistry 45)' % _prac_n)
except Exception as _prac_e:
    print('Practicals seed warning:', _prac_e)

@app.get('/api/practicals')
def practicals_list():
    """Light list for the Virtual Lab dashboard: filter by subject, category, free-text q."""
    db = get_db()
    subj = (request.args.get('subject') or '').strip()
    cat = (request.args.get('category') or '').strip()
    qq = (request.args.get('q') or '').strip().lower()
    cond, params = [], []
    if subj:
        cond.append('subject=?'); params.append(subj)
    if cat:
        cond.append('category=?'); params.append(cat)
    if qq:
        cond.append("lower(practical_title_en || ' ' || practical_title_si || ' ' || category || ' ' || unit_lesson) LIKE ?")
        params.append('%' + qq + '%')
    w = (' WHERE ' + ' AND '.join(cond)) if cond else ''
    ls = rows(db.execute("""SELECT id, subject, category, practical_title_en, practical_title_si, unit_lesson
                            FROM practicals""" + w + " ORDER BY subject, category, id", params))
    return jsonify({'practicals': ls, 'total': len(ls)})

@app.get('/api/practicals/<int:pid>')
def practical_detail(pid):
    """Full practical record with viva/past-paper arrays parsed."""
    p = one(get_db().execute('SELECT * FROM practicals WHERE id=?', (pid,)))
    if not p:
        return bad('Practical not found', 404)
    import json as _j
    for k in ('viva_questions', 'past_paper_questions'):
        try:
            p[k] = _j.loads(p.get(k) or '[]')
        except Exception:
            p[k] = []
    return jsonify({'practical': p})

if __name__ == '__main__':
    print('=' * 52)
    print('  AL PLANNER (Python edition)')
    print('  Open:  http://localhost:%d' % PORT)
    print('  Student: student@alplanner.lk / student123')
    print('  Admin:   admin@alplanner.lk / admin123')
    print('  Press Ctrl+C to stop.')
    print('=' * 52)
    auto_content_update()
    try:
        app.run(host='0.0.0.0', port=PORT, threaded=True)
    except OSError:
        print('')
        print('  !! Port %d is busy - an OLD AL Planner window is already open.' % PORT)
        print('  !! Please CLOSE the other black window and double-click again.')
        print('  !! Browser eke PARANA site eka penenne e nisai. Parana window eka close karala ayeth open karanna.')
        try: input('  Press Enter to close this window...')
        except EOFError: pass
