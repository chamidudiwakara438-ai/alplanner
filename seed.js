'use strict';
// Seed data for AL Planner: subjects, Chemistry unit tree, Combined Maths,
// Biology, teachers, lessons (with real YouTube lessons), PDF resources,
// tutors, A/L years and demo accounts.
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const { db, UPLOAD_DIR } = require('./db');
const { makePdf } = require('./pdfgen');

function slug(t) {
  return 'seed-' + String(t).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) + '.pdf';
}

function seed(force) {
  const has = db.prepare('SELECT COUNT(*) AS c FROM users').get().c > 0;
  if (has && !force) return false;

  db.exec(`
    DELETE FROM sessions; DELETE FROM progress; DELETE FROM saved_resources;
    DELETE FROM tutor_messages; DELETE FROM resources; DELETE FROM lessons;
    DELETE FROM units; DELETE FROM teachers; DELETE FROM tutors;
    DELETE FROM subjects; DELETE FROM al_years; DELETE FROM users;
    DELETE FROM sqlite_sequence;
  `);

  const tx = db.transaction(() => {
    // ---------- Users ----------
    const insUser = db.prepare(`INSERT INTO users (name,email,password_hash,role,school,district,al_year,medium,stream,subjects)
      VALUES (?,?,?,?,?,?,?,?,?,?)`);
    insUser.run('Platform Admin', 'admin@alplanner.lk', bcrypt.hashSync('admin123', 10), 'admin', 'AL Planner HQ', 'Colombo', '', 'en', '', '[]');
    insUser.run('Kavindu Samarasinghe', 'student@alplanner.lk', bcrypt.hashSync('student123', 10), 'student',
      'Ananda College, Colombo 10', 'Colombo', 'A/L 2027', 'en', 'Physical Science', JSON.stringify(['Chemistry', 'Combined Mathematics']));

    // ---------- A/L years ----------
    const insYear = db.prepare('INSERT INTO al_years (label, active) VALUES (?,1)');
    insYear.run('A/L 2027');
    insYear.run('A/L 2028');

    // ---------- Teachers ----------
    const insTeacher = db.prepare('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)');
    insTeacher.run('Mr. Nimal Perera', 'Senior Chemistry teacher with 18+ years of G.C.E. A/L classroom experience. Famous for building rock-solid fundamentals in General and Inorganic Chemistry.', 'Chemistry');              // 1
    insTeacher.run('Prof. Anura Jayasuriya', 'Former university lecturer specialising in Physical Chemistry. Makes thermodynamics, kinetics and equilibrium feel simple and logical.', 'Chemistry');                        // 2
    insTeacher.run('Ms. Sanduni Fernando', 'Organic Chemistry specialist. Known for clear mechanism-based teaching and exam-focused paper discussion.', 'Chemistry');                                                          // 3
    insTeacher.run('Mr. Kasun Bandara', 'Combined Mathematics (Pure) teacher with 15 years of experience producing island ranks. Structured, proof-driven lessons.', 'Combined Mathematics');                                  // 4
    insTeacher.run('Ms. Dilani Wickramasinghe', 'Combined Mathematics (Applied) teacher. Turns mechanics and probability into intuitive, picture-first ideas.', 'Combined Mathematics');                                       // 5
    insTeacher.run('Dr. Tharushi Jayasinghe', 'Medical faculty graduate and Biology teacher. Diagram-first teaching for molecular and cellular biology.', 'Biology');                                                          // 6
    insTeacher.run('Mr. Ruwan Gunasekara', 'Biology teacher with 20 years of experience. Specialises in plant and human bio-systems and paper-marking technique.', 'Biology');                                                 // 7

    // ---------- Subjects ----------
    const insSubject = db.prepare('INSERT INTO subjects (name,name_si,name_ta,code,icon,color1,color2) VALUES (?,?,?,?,?,?,?)');
    insSubject.run('Chemistry', 'රසායන විද්‍යාව', 'வேதியியல்', 'CHEM', 'flask', '#8b5cf6', '#22d3ee');   // 1
    insSubject.run('Combined Mathematics', 'සංයුක්ත ගණිතය', 'இணை கணிதம்', 'CM', 'sigma', '#6366f1', '#ec4899'); // 2
    insSubject.run('Biology', 'ජීව විද්‍යාව', 'உயிரியல்', 'BIO', 'dna', '#22c55e', '#a3e635');            // 3
    insSubject.run('Physics', 'භෞතික විද්‍යාව', 'இயற்பியல்', 'PHY', 'book', '#f97316', '#e11d48');        // 4
    insSubject.run('ICT', 'තොරතුරු හා සන්නිවේදන තාක්ෂණය', 'தகவல் தொழில்நுட்பம்', 'ICT', 'cap', '#06b6d4', '#3b82f6'); // 5

    // ---------- Units ----------
    const insUnit = db.prepare('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)');
    insUnit.run(1, 'General Chemistry', 1);            // 1
    insUnit.run(1, 'Physical Chemistry', 2);           // 2
    insUnit.run(1, 'Organic Chemistry', 3);            // 3
    insUnit.run(1, 'Inorganic Chemistry', 4);          // 4
    insUnit.run(2, 'Pure Mathematics', 1);             // 5
    insUnit.run(2, 'Applied Mathematics', 2);          // 6
    insUnit.run(3, 'Molecular & Cellular Biology', 1); // 7
    insUnit.run(3, 'Plant & Animal Systems', 2);       // 8
    // Physics (official NIE syllabus units)
    ['Measurement','Mechanics','Oscillations and Waves','Thermal Physics','Gravitational Field',
     'Electrostatic Field','Magnetic Field','Current Electricity','Electronics',
     'Mechanical Properties of Matter','Matter and Radiation'].forEach((n, i) => insUnit.run(4, n, i + 1));
    // ICT (official NIE syllabus units)
    ['Concept of ICT','Introduction to Computer','Data Representation','Fundamentals of Digital Circuits',
     'Computer Operating Systems','Data Communication and Networking','System Analysis and Design',
     'Database Management','Programming','Web Development','Internet of Things','ICT in Business',
     'New Trends and Future Directions of ICT','Project'].forEach((n, i) => insUnit.run(5, n, i + 1));

    // ---------- Lessons ----------
    const insLesson = db.prepare('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)');
    const L = (u, t, title, desc, yt, notes, ord) => insLesson.run(u, t, title, desc, yt, notes, ord).lastInsertRowid;

    // === General Chemistry ===
    L(1, 1, 'Atomic Structure & Electronic Configuration',
      'Protons, neutrons and electrons, isotopes, and how electrons fill orbitals. The foundation every other Chemistry unit is built on.',
      '1xSQlwWGT8M',
      'Key points\n- Atom = nucleus (protons + neutrons) surrounded by electrons in shells.\n- Atomic number (Z) = protons. Mass number (A) = protons + neutrons.\n- Isotopes: same Z, different A (e.g. C-12 and C-14).\n- Fill orbitals by Aufbau order: 1s 2s 2p 3s 3p 4s 3d ...\n- Each orbital holds max 2 electrons (Pauli). Fill degenerate orbitals singly first (Hund).\n- Exam tip: always write the full electron configuration before the short form.',
      1);
    L(1, 1, 'The Mole Concept & Stoichiometry',
      'Moles, molar mass, Avogadro\'s number and how to convert between mass, moles and number of particles in calculations.',
      'AsqEkF7hcII',
      'Key points\n- 1 mole = 6.022 x 10^23 particles (Avogadro constant).\n- n = m / M (moles = mass / molar mass).\n- Concentration: c = n / V (mol dm-3).\n- At STP, 1 mole of gas occupies 22.4 dm3.\n- Stoichiometry: use the balanced equation mole ratios to move between substances.\n- Exam tip: keep 3 significant figures and carry units through every step.',
      2);
    L(1, 1, 'Chemical Bonding & Molecular Structure',
      'Ionic, covalent, coordinate and metallic bonding, shapes of molecules (VSEPR) and how bonding decides properties.',
      'playlist:PLSQl0a2vh4HAYCvTHhMGsNvLS-btVPXRw',
      'Key points\n- Ionic bond: complete electron transfer (metal + non-metal), high m.p., conducts when molten/aqueous.\n- Covalent bond: sharing of electron pairs (non-metals), low m.p., usually non-conductors.\n- Coordinate (dative) bond: both shared electrons from one atom (e.g. NH4+).\n- VSEPR: electron pairs repel; lone pairs squeeze bond angles (CH4 109.5, NH3 107, H2O 104.5).\n- Metallic bonding: lattice of positive ions in a sea of delocalised electrons.',
      3);

    // === Physical Chemistry ===
    L(2, 2, 'The Gaseous State of Matter',
      'Boyle\'s and Charles\' laws, the ideal gas equation PV = nRT, kinetic theory and real gas deviations.',
      'erjMiErRgSQ',
      'Key points\n- Boyle: P1V1 = P2V2 (constant T). Charles: V/T = constant (constant P).\n- Combined: PV/T = constant. Ideal gas: PV = nRT, R = 8.314 J K-1 mol-1.\n- Kinetic theory: negligible molecular volume, no intermolecular forces, elastic collisions.\n- Real gases deviate at high pressure and low temperature.\n- Diffusion rate inversely proportional to sqrt of molar mass (Graham).',
      1);
    L(2, 2, 'Chemical Thermodynamics & Enthalpy',
      'System vs surroundings, exothermic and endothermic reactions, enthalpy change and calorimetry basics.',
      'fucyI7Ouj2c',
      'Key points\n- Enthalpy H = heat content at constant pressure.\n- deltaH negative = exothermic (releases heat), positive = endothermic.\n- Standard enthalpy of formation: 1 mole of compound from elements in standard states.\n- q = mc x deltaT for calorimetry experiments.\n- Activation energy: minimum energy for a successful collision.',
      2);
    L(2, 2, "Hess's Law & Enthalpy Calculations",
      'Hess\'s law of constant heat summation, enthalpy cycles, and calculating reaction enthalpy from formation and combustion data.',
      'chXMpDwjBDk',
      'Key points\n- Hess: total enthalpy change is independent of the route taken.\n- deltaH(reaction) = SUM deltaHf(products) - SUM deltaHf(reactants).\n- Using combustion data: deltaH = SUM deltaHc(reactants) - SUM deltaHc(products).\n- Bond enthalpy method: deltaH = bonds broken - bonds formed.\n- Exam tip: draw the enthalpy cycle and label every arrow direction.',
      3);

    // === Organic Chemistry ===
    const org1 = L(3, 3, 'Introduction to Organic Chemistry',
      'What makes carbon special, catenation, hybridisation (sp3, sp2, sp), functional groups and the main families of organic compounds.',
      'JHgTNNX01r4',
      'Key points\n- Carbon forms 4 covalent bonds and long stable chains (catenation).\n- sp3 carbon: 4 single bonds, tetrahedral, 109.5. sp2: 1 double bond, trigonal planar, 120. sp: triple bond, linear, 180.\n- Homologous series: same functional group, same general formula, gradual property change.\n- Main families: alkanes, alkenes, alkynes, alcohols, aldehydes, ketones, carboxylic acids, esters.\n- Isomerism: structural (chain / position / functional) and stereoisomerism (geometrical, optical).',
      1);
    const org2 = L(3, 3, 'IUPAC Nomenclature of Organic Compounds',
      'Systematic naming of alkanes, alkenes, alkynes, alcohols, haloalkanes and more using IUPAC rules, step by step.',
      'TYU_JluleME',
      'Key points\n- Step 1: find the longest chain containing the principal functional group.\n- Step 2: number to give the principal group the lowest locant.\n- Step 3: name substituents alphabetically with their locants.\n- Suffixes: -ane, -ene, -yne, -ol, -al, -one, -oic acid.\n- Common exam traps: ethyl- before methyl- alphabetically; count from the end near the functional group.',
      2);
    L(3, 3, 'Hydrocarbons: Alkanes, Alkenes & Alkynes',
      'Structure, preparation and characteristic reactions of hydrocarbons: substitution vs addition vs oxidation.',
      'hcpWpluvXgc',
      'Key points\n- Alkanes (CnH2n+2): free-radical substitution with Br2/Cl2 in sunlight; generally unreactive.\n- Alkenes (CnH2n): electrophilic addition - H2/Ni, HX, X2, cold dilute KMnO4 (forms diol).\n- Markovnikov rule for unsymmetrical alkenes + HX.\n- Alkynes: addition reactions, terminal alkynes are weakly acidic.\n- Baeyer test (decolourising purple KMnO4) detects unsaturation.',
      3);

    // === Inorganic Chemistry ===
    L(4, 1, 'The Periodic Table & Periodicity',
      'How the table is organised, periodic trends in atomic radius, ionisation energy, electronegativity and their explanations.',
      't_f8bB1kf6M',
      'Key points\n- Elements arranged by increasing atomic number; groups share outer electron configuration.\n- Atomic radius decreases across a period, increases down a group.\n- Ionisation energy increases across a period (with small dips at group 13 and 16), decreases down a group.\n- Electronegativity peaks at fluorine.\n- Metallic character increases down a group and towards the left.',
      1);
    L(4, 1, 's-Block & p-Block Elements',
      'Group 1, 2 and 17 trends, important compounds of Na, Mg and the halogens, and their everyday uses.',
      '', // admin can attach a video later
      'Key points\n- Group 1 (alkali metals): soft, reactive, stored under oil; reactivity increases downwards.\n- Group 2: harder and less reactive; solubility of hydroxides increases down the group.\n- Group 17 (halogens): oxidising power decreases down the group; displacement reactions.\n- Important compounds: NaOH (chlor-alkali), Na2CO3 (Solvay), CaO (limestone).\n- Flame tests: Na yellow, K lilac, Ca brick-red.',
      2);
    L(4, 1, 'Industrial & Environmental Chemistry',
      'How Chemistry is applied in Sri Lankan industry and the environment: fertilisers, cement, air and water pollution.',
      '',
      'Key points\n- Haber process: N2 + 3H2 -> 2NH3, Fe catalyst, ~450 C, ~200 atm.\n- Contact process for H2SO4: V2O5 catalyst.\n- Air pollutants: CO, NOx, SO2, particulates; photochemical smog.\n- Water quality: dissolved oxygen, BOD, eutrophication from fertiliser runoff.\n- Ozone layer: CFCs break O3; Montreal Protocol phase-out.',
      3);

    // === Combined Mathematics ===
    const lim1 = L(5, 4, 'Limits & Continuity',
      'The idea of a limit, evaluating limits analytically, limits at infinity and the sandwich theorem.',
      'riXcZT2ICjA',
      'Key points\n- Limit: value f(x) approaches as x -> a (function need not be defined at a).\n- Techniques: direct substitution, factorising, rationalising, standard limits.\n- Standard results: lim(x->0) sin x / x = 1; lim(x->0) (e^x - 1)/x = 1.\n- Continuity at a: f(a) defined, limit exists, both equal.\n- Exam tip: for 0/0 forms, factor or rationalise before substituting.',
      1);
    L(5, 4, 'Differentiation & Applications',
      'First principles, power, product, quotient and chain rules, gradients of tangents and rate-of-change problems.',
      'bRZmfc1YFsQ',
      'Key points\n- f\'(x) = lim(h->0) [f(x+h) - f(x)] / h.\n- d/dx x^n = n x^(n-1). Sum, product, quotient and chain rules.\n- Tangent gradient = dy/dx at the point; normal gradient = -1/m.\n- Stationary points where dy/dx = 0; classify with the second derivative.\n- Applications: maxima/minima, related rates, small increments.',
      2);
    L(5, 4, 'Integration & Its Applications',
      'Indefinite integrals as antiderivatives, standard integrals, substitution, definite integrals and areas under curves.',
      'MMv-027KEqU',
      'Key points\n- Integral of x^n = x^(n+1)/(n+1) + C (n != -1); integral of 1/x = ln|x| + C.\n- Standard integrals: e^x, sin x, cos x, sec^2 x.\n- Substitution: pick u = inner function; convert dx fully.\n- Definite integral = signed area; area between curve and x-axis.\n- Trapezium rule for numerical integration when exact form is hard.',
      3);
    L(6, 5, 'Vectors in Two Dimensions',
      'Vector notation, magnitude and direction, unit vectors, scalar product and resolving forces with vectors.',
      'br7tS1t2SFE',
      'Key points\n- A vector has magnitude and direction; written ai + bj or as a column.\n- Magnitude = sqrt(a^2 + b^2); unit vector = vector / magnitude.\n- Scalar (dot) product: a.b = |a||b| cos theta = a1a2 + b1b2.\n- Perpendicular vectors have a.b = 0.\n- Position vectors make geometry proofs much easier.',
      1);
    L(6, 5, 'Motion in a Straight Line (Kinematics)',
      'Displacement, velocity and acceleration, SUVAT equations, velocity-time graphs and vertical motion under gravity.',
      'XIJAZM5G5Fg',
      'Key points\n- v = u + at; s = ut + (1/2)at^2; v^2 = u^2 + 2as. Use only for constant acceleration.\n- Area under v-t graph = displacement; gradient of v-t graph = acceleration.\n- Under gravity: a = -g = -9.8 m s-2 (or -10 for quick work).\n- Relative velocity: velocity of A relative to B = vA - vB.\n- Exam tip: draw the v-t graph even when you use equations.',
      2);
    L(6, 5, 'Probability & Statistics',
      'Sample spaces, addition and multiplication rules, conditional probability, mean, variance and their exam patterns.',
      'uzkc-qNVoOk',
      'Key points\n- P(A) = favourable outcomes / total outcomes (equally likely cases).\n- Addition rule: P(A u B) = P(A) + P(B) - P(A n B).\n- Independent events: P(A n B) = P(A)P(B); conditional: P(A|B) = P(A n B)/P(B).\n- Tree diagrams organise multi-stage experiments.\n- Mean = SIGMA fx / N; variance = SIGMA f(x - mean)^2 / N.',
      3);

    // === Biology ===
    L(7, 6, 'Cell Structure & Function',
      'Prokaryotic vs eukaryotic cells, organelles and their jobs, and how membrane structure controls transport.',
      '1aJBToJrlvA',
      'Key points\n- Eukaryotes have a true nucleus and membrane-bound organelles; prokaryotes do not.\n- Mitochondria: aerobic respiration. Ribosomes: protein synthesis. RER vs SER.\n- Golgi: modifies, packages, secretes. Lysosomes: intracellular digestion.\n- Fluid mosaic model: phospholipid bilayer + proteins; controls diffusion, osmosis, active transport.\n- Plant cells add: cell wall, chloroplasts, large central vacuole.',
      1);
    L(7, 6, 'Biological Molecules',
      'Carbohydrates, lipids, proteins and nucleic acids: monomers, polymers, bonds and food tests.',
      'j5VA6YrqTNs',
      'Key points\n- Carbohydrates: monosaccharides (glucose), disaccharides (maltose), polysaccharides (starch, cellulose).\n- Lipids: glycerol + fatty acids; saturated vs unsaturated; energy stores and membranes.\n- Proteins: amino acids joined by peptide bonds; 4 levels of structure; enzymes are proteins.\n- Nucleic acids: DNA and RNA made of nucleotides (sugar, phosphate, base).\n- Food tests: Benedict (reducing sugar), iodine (starch), Biuret (protein), ethanol emulsion (lipid).',
      2);
    L(7, 6, 'Photosynthesis & Cellular Respiration',
      'Light and dark reactions, the Calvin cycle, glycolysis, Krebs cycle and the electron transport chain.',
      'nbDV6dRnEy8',
      'Key points\n- Photosynthesis: 6CO2 + 6H2O -> C6H12O6 + 6O2 (light, chlorophyll).\n- Light reactions in thylakoids produce ATP and NADPH2 and release O2.\n- Calvin cycle (stroma) fixes CO2 using RuBP; rate limited by light, CO2, temperature.\n- Respiration: glycolysis (cytoplasm), Krebs (matrix), ETC (cristae) -> ~36 ATP.\n- C4 plants (e.g. sugarcane) minimise photorespiration in hot climates.',
      3);
    L(8, 7, 'Plant Cells, Tissues & Transport',
      'Xylem and phloem, transpiration pull, root pressure and how water and food move through the plant.',
      'd9GkH4vpK3w',
      'Key points\n- Xylem transports water and minerals upward; vessels are dead, lignified tubes.\n- Phloem transports food (translocation) using companion cells and sieve tubes.\n- Transpiration pull is the main driver; affected by light, temperature, humidity, wind.\n- Cohesion-tension theory explains the continuous water column.\n- Guard cells open/close stomata using turgor changes driven by K+ movement.',
      1);
    L(8, 7, 'Human Circulatory System',
      'Heart structure, the double circulation, blood vessels, cardiac cycle and common exam diagrams.',
      '9fxm85Fy4sQ',
      'Key points\n- Double circulation: pulmonary (heart -> lungs) and systemic (heart -> body).\n- Left side carries oxygenated blood and is more muscular (higher pressure).\n- Valves prevent backflow: bicuspid, tricuspid, semilunar.\n- SA node is the natural pacemaker; AV node delays the impulse.\n- Arteries: thick elastic walls; capillaries: one cell thick for exchange; veins: valves, low pressure.',
      2);
    L(8, 7, 'Genetics & Inheritance',
      'Mendel\'s laws, monohybrid and dihybrid crosses, sex determination and common pedigree questions.',
      'CBezq1fFUEA',
      'Key points\n- Gene: DNA segment coding for a trait; alleles are alternative forms.\n- Law of segregation: allele pairs separate during gamete formation.\n- Monohybrid cross ratio 3:1 (phenotype), 1:2:1 (genotype); test cross gives 1:1.\n- Independent assortment: genes on different chromosomes inherit independently (dihybrid 9:3:3:1).\n- Humans: XX female, XY male; haemophilia and colour blindness are X-linked.',
      3);

    // ---------- Resources (real PDF files) ----------
    const addPdf = (title, paragraphs) => {
      const buf = makePdf(title, paragraphs);
      const fname = slug(title);
      fs.writeFileSync(path.join(UPLOAD_DIR, fname), buf);
      return { fname, size: buf.length };
    };
    const insRes = db.prepare(`INSERT INTO resources (title,category,file_path,orig_name,size,mime,subject_id,lesson_id,uploaded_by,status,downloads)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`);
    const R = (title, cat, subj, lesson, paragraphs, status = 'approved', by = 1, dl = 0) => {
      const p = addPdf(title, paragraphs);
      return insRes.run(title, cat, p.fname, title + '.pdf', p.size, 'application/pdf', subj, lesson, by, status, dl).lastInsertRowid;
    };
    const c = (s) => s;

    R('Atomic Structure — Short Notes', 'short_notes', 1, 1, [
      'Everything you need about the atom on two pages.',
      '', '1. Subatomic particles',
      'Proton: mass 1 u, charge +1, inside nucleus. Neutron: mass 1 u, no charge.',
      'Electron: mass about 1/1836 u, charge -1, occupies shells around the nucleus.',
      '', '2. Isotopes',
      'Atoms of the same element with different numbers of neutrons.',
      'Example: chlorine exists as Cl-35 (75%) and Cl-37 (25%), giving RAM 35.5.',
      '', '3. Electronic configuration',
      'Order of filling: 1s 2s 2p 3s 3p 4s 3d 4p ... (use the diagonal rule).',
      'Chromium and copper are exceptions: [Ar] 3d5 4s1 and [Ar] 3d10 4s1.',
      '', 'Quick practice',
      'Write the configuration of Fe2+ and Fe3+ and explain why Fe3+ is more stable.'
    ], 'approved', 1, 132);
    R('Mole Concept — Calculation Question Pack', 'question_papers', 1, 2, [
      '25 graded calculation questions on the mole, concentration and gas volumes.',
      '', 'Section A — basics',
      'Q1. How many moles are there in 8.0 g of NaOH? (M = 40)',
      'Q2. How many molecules are present in 0.25 mol of CO2?',
      'Q3. What volume does 3.2 g of O2 occupy at STP?',
      '', 'Section B — concentration',
      'Q4. 5.85 g of NaCl is dissolved to make 250 cm3 of solution. Find the concentration.',
      'Q5. What mass of KOH is needed for 500 cm3 of a 0.2 mol dm-3 solution?',
      '', 'Section C — stoichiometry',
      'Q6. CaCO3 -> CaO + CO2. What mass of CaO forms from 25 g of pure CaCO3?',
      'Q7. 4.6 g of Na reacts with excess water. Find the volume of H2 at STP.',
      '', 'Answers are printed upside-down on the last page. Attempt before checking!'
    ], 'approved', 1, 98);
    R('Introduction to Organic Chemistry — Complete Notes', 'notes', 1, 7, [
      'A complete starter pack for Unit 12-14 Organic Chemistry.',
      '', '1. Why carbon is unique',
      'Tetravalency and catenation let carbon build millions of stable compounds.',
      '', '2. Hybridisation',
      'sp3: four sigma bonds, tetrahedral, 109.5 degrees (methane).',
      'sp2: three sigma + one pi, trigonal planar, 120 degrees (ethene).',
      'sp: two sigma + two pi, linear, 180 degrees (ethyne).',
      '', '3. Functional groups to memorise',
      'Alkane (-), alkene (C=C), alkyne (C triple C), halide (-X), alcohol (-OH),',
      'aldehyde (-CHO), ketone (>C=O), carboxylic acid (-COOH), ester (-COO-), amine (-NH2).',
      '', '4. Isomerism checklist',
      'Chain isomers - position isomers - functional group isomers.',
      'Geometrical (cis/trans) needs restricted rotation + two different groups on each C.',
      '', 'Study plan: watch the video lesson, copy the family tree, then do the 50-question set.'
    ], 'approved', 1, 214);
    R('Organic Nomenclature — 50 Practice Questions', 'question_papers', 1, 8, [
      'Name these compounds (IUPAC). Difficulty increases gradually.',
      '', '1. CH3CH2CH2CH3        2. CH3CH(CH3)CH2CH3       3. CH2=CHCH2CH3',
      '4. CH3C(CH3)2CH3       5. CH triple C-CH3          6. CH3CH2CH2OH',
      '7. CH3CH(Br)CH3        8. CH3CH2CHO               9. CH3COCH2CH3',
      '10. CH3CH2COOH         11. (CH3)2CHCH2CH2Cl       12. CH2=CHCH(CH3)2',
      '...', 'Questions 13-50 continue with branched, cyclic and polyfunctional examples.',
      '', 'Marking scheme included: each correct name = 1 mark, correct locants = half mark.'
    ], 'approved', 1, 76);
    R('Organic Chemistry — Past Paper Collection (2019–2024)', 'past_papers', 1, 7, [
      'Organic Chemistry structured and essay questions extracted from AL papers.',
      '', '2024 Paper II Q9 (excerpt)',
      'Compound A (C4H10O) reacts with acidified K2Cr2O7 to give B which gives a silver',
      'mirror with Tollens reagent. Identify A and B and write the mechanism.',
      '', '2023 Paper II Q10 (excerpt)',
      'Show how you would convert ethanol to ethyl ethanoate using inorganic reagents only.',
      '', '2022 Paper I — MCQ set on isomerism and reaction types (10 questions with key).',
      '', 'How to use: attempt under timed conditions, then compare with the marking points.'
    ], 'approved', 1, 187);
    R('AL Chemistry Model Paper 2026 — Full Paper I & II', 'model_papers', 1, null, [
      'A full-length model paper in the new pattern. Paper I: 50 MCQ. Paper II: structured + essay.',
      '', 'Paper I instructions: 2 hours. Answer all 50 questions. No negative marking.',
      'Paper II instructions: 3 hours. Part A structured (compulsory). Part B: answer 4 of 6 essays.',
      '', 'Syllabus coverage',
      'General Chemistry 25% | Physical Chemistry 25% | Organic Chemistry 30% | Inorganic 20%',
      '', 'A detailed marking scheme with examiner comments follows every paper.',
      '', 'Recommended: sit the paper first, then watch the related video lessons for weak areas.'
    ], 'approved', 1, 342);
    R('Limits & Continuity — Theory + Worked Examples', 'notes', 2, 13, [
      'Pure Mathematics unit 01 quick reference.',
      '', 'Standard limits (memorise!)',
      'lim(x->0) sin x / x = 1        lim(x->0) tan x / x = 1',
      'lim(x->0) (e^x - 1) / x = 1    lim(x->0) ln(1+x) / x = 1',
      'lim(x->a) (x^n - a^n)/(x - a) = n a^(n-1)',
      '', 'Worked example',
      'lim(x->0) (sin 3x)/(x) = lim 3 x sin3x/(3x) = 3.',
      '', 'Continuity checklist at x = a:',
      '1) f(a) exists  2) both one-sided limits exist and agree  3) limit = f(a).',
      '', '12 practice problems with full solutions are included at the end.'
    ], 'approved', 1, 154);
    R('Integration Formula Sheet — Quick Revision', 'short_notes', 2, 15, [
      'One-page formula sheet for the integration unit.',
      '', 'Basic: x^n -> x^(n+1)/(n+1) + C, 1/x -> ln|x| + C, e^x -> e^x + C',
      'Trig: sin x -> -cos x + C, cos x -> sin x + C, sec^2 x -> tan x + C',
      '', 'Reverse chain rule (substitution): integral f(g(x)) g\'(x) dx; set u = g(x).',
      'Definite integrals: swap the limits when you substitute for u.',
      '', 'Area under curve y = f(x) from a to b = integral(a,b) f(x) dx (split at zeros).',
      'Trapezium rule: h/2 [y0 + yn + 2(sum of middle ordinates)].'
    ], 'approved', 1, 121);
    R('AL Combined Mathematics — Past Paper 2023', 'past_papers', 2, null, [
      'Combined Mathematics 2023 past paper — Paper I and Paper II combined booklet.',
      '', 'Paper I: 2 hours, 25 structured questions, answer all.',
      'Paper II Part A: 3 questions (Pure + Applied mix). Part B: choose 5 of 7.',
      '', 'Topics weighted heavily this year: differentiation applications,',
      'integration areas, SUVAT, friction and probability trees.',
      '', 'Includes the official-style marking guide with alternative-method credit.'
    ], 'approved', 1, 268);
    R('Cell Structure & Function — Illustrated Notes', 'notes', 3, 19, [
      'Biology unit 02 illustrated notes for revision.',
      '', 'Organelle job list',
      'Nucleus - stores DNA, controls the cell.        Mitochondrion - aerobic respiration.',
      'Ribosome - protein synthesis.                    RER - protein transport with ribosomes.',
      'Golgi - packaging and secretion.                 Lysosome - digestion of worn organelles.',
      'Chloroplast - photosynthesis (plants).           Cell wall - cellulose support (plants).',
      '', 'Membrane fluid mosaic model',
      'Phospholipid bilayer with cholesterol, intrinsic and extrinsic proteins.',
      'Diffusion, facilitated diffusion, osmosis and active transport compared in a table.',
      '', 'Draw and label: a generalised animal cell and plant cell (exam favourite!).'
    ], 'approved', 1, 143);
    R('Photosynthesis Light Reactions — Short Notes', 'short_notes', 3, 21, [
      'Light reactions summarised in one page.',
      '', 'Site: thylakoid membranes of the chloroplast.',
      'Inputs: light, H2O, ADP + Pi, NADP.  Outputs: ATP, NADPH2, O2.',
      '', 'Photolysis of water supplies electrons and releases oxygen.',
      'Non-cyclic photophosphorylation: PSII -> ETC -> PSI -> NADPH2.',
      'Cyclic photophosphorylation: PSI only, produces extra ATP.',
      '', 'Limiting factors graph shapes: light, CO2 and temperature — know all three!'
    ], 'approved', 1, 87);
    R('AL Biology Model Paper 2026 — Full Paper', 'model_papers', 3, null, [
      'Biology model paper in the current pattern with a complete marking scheme.',
      '', 'Paper I: 50 MCQ (2 hours). Paper II: 4 structured + 4 of 6 essays (3 hours).',
      '', 'Coverage: molecular biology 20%, cells 20%, plant & animal systems 30%,',
      'genetics & evolution 15%, environment & applied biology 15%.',
      '', 'Examiner tips: keep diagrams large and labelled; quote numerical data;',
      'answer exactly what the command word asks (state / describe / explain / compare).'
    ], 'approved', 1, 305);
    // One pending student upload to demonstrate the approval queue
    R('Organic Reaction Mechanisms — Summary Sheet', 'study_material', 1, 7, [
      'Student-made summary of the main organic mechanisms (curly arrows).',
      'Free radical substitution (methane + Br2), electrophilic addition (ethene + HBr),',
      'nucleophilic substitution (haloalkane + OH-), oxidation of alcohols ladder.',
      '', 'Uploaded by a student - waiting for admin approval before public release.'
    ], 'pending', 2, 0);

    // ---------- Demo student progress ----------
    const insProg = db.prepare('INSERT INTO progress (user_id,lesson_id,completed,completed_at,watched,watched_at,favourite) VALUES (?,?,?,?,?,?,?)');
    const now = "datetime('now')";
    const mark = (lid, comp, wat, fav) =>
      insProg.run(2, lid, comp, comp ? new Date().toISOString() : null, wat, wat ? new Date().toISOString() : null, fav);
    [1, 2, 13, 19].forEach((l) => mark(l, 1, 1, 0));
    [3, 7, 14].forEach((l) => mark(l, 0, 1, 0));
    db.prepare('UPDATE progress SET favourite=1 WHERE user_id=2 AND lesson_id IN (7,13)').run();
    db.prepare('INSERT OR IGNORE INTO saved_resources (user_id,resource_id) VALUES (2,?)').run(4);
    db.prepare('INSERT OR IGNORE INTO saved_resources (user_id,resource_id) VALUES (2,?)').run(8);

    // ---------- Tutor marketplace ----------
    const insTutor = db.prepare(`INSERT INTO tutors (name,photo,subjects,experience,classes,location,phone,whatsapp,email,bio)
      VALUES (?,?,?,?,?,?,?,?,?,?)`);
    insTutor.run('Eng. Pradeep Kumara', '/assets/tutors/tutor1.jpg',
      JSON.stringify(['Combined Mathematics']), '12 years',
      JSON.stringify(['2027 Theory — Sat 8.00 AM (Zoom)', '2028 Theory — Sun 3.30 PM (Colombo 05)', 'Revision & Paper Class — Wed 6.00 PM (Zoom)']),
      'Colombo 05 + Online', '077 123 4567', '94771234567', 'pradeep.kumara.maths@gmail.com',
      'Engineering graduate who has produced 40+ island ranks. Step-by-step pure and applied maths with weekly quizzes and individual paper marking.');
    insTutor.run('Ms. Nadeesha Silva', '/assets/tutors/tutor2.jpg',
      JSON.stringify(['Chemistry']), '8 years',
      JSON.stringify(['2027 Theory — Tue 4.00 PM (Kandy)', '2028 Theory — Thu 4.00 PM (Online)', 'Paper Class — Sat 10.00 AM (Online)']),
      'Kandy + Online', '071 555 2890', '94715552890', 'nadeesha.chem@gmail.com',
      'B.Sc. (Hons) Chemistry. Colourful summaries, mnemonics for inorganic trends and 10 years of past-paper discussion built into every unit.');
    insTutor.run('Dr. Kavindu Rathnayake', '/assets/tutors/tutor3.jpg',
      JSON.stringify(['Biology']), '10 years',
      JSON.stringify(['2027 Theory — Fri 5.00 PM (Zoom)', '2028 Theory — Sun 8.00 AM (Gampaha)', 'MCQ Masterclass — Monthly']),
      'Gampaha + Online', '076 442 1188', '94764421188', 'dr.kavindu.bio@gmail.com',
      'Medical faculty graduate. Diagram-first biology teaching with memory palaces for long essays. Free WhatsApp doubt-clearing group.');
    insTutor.run('Mr. S. Thayalan', '/assets/tutors/tutor4.jpg',
      JSON.stringify(['Combined Mathematics']), '14 years',
      JSON.stringify(['2027 Theory — Mon 4.30 PM (Jaffna)', '2028 Theory — Sat 9.00 AM (Zoom)', 'Revision — Sun 4.00 PM (Jaffna)']),
      'Jaffna + Online', '077 890 3345', '94778903345', 'thayalan.maths@gmail.com',
      'Veteran Northern-province maths teacher, bilingual Tamil/English classes. Rigorous problem sheets every week with model-answer walkthroughs.');
    insTutor.run('Ms. Fathima Rizna', '/assets/tutors/tutor5.jpg',
      JSON.stringify(['Chemistry']), '6 years',
      JSON.stringify(['2028 Theory — Wed 5.30 PM (Online)', 'Organic Crash Course — Monthly (Colombo 03)']),
      'Colombo 03 + Online', '075 667 9021', '94756679021', 'rizna.chem@gmail.com',
      'Young, energetic chemistry teacher focused on organic mechanisms and MCQ speed technique. Small-group online classes, recordings provided.');
    insTutor.run('Mr. Chaminda Herath', '/assets/tutors/tutor6.jpg',
      JSON.stringify(['Biology', 'Chemistry']), '15 years',
      JSON.stringify(['2027 Biology — Sat 6.00 AM (Kurunegala)', '2027 Chemistry — Sun 6.00 AM (Kurunegala)', 'Online Revision — Daily 8.00 PM']),
      'Kurunegala + Online', '070 234 8876', '94702348876', 'chaminda.herath@gmail.com',
      'The North-Western province\'s best-known bio/chem combination teacher. Full-day seminar series before every term test. Printed tutes included.');
  });
  tx();
  return true;
}

if (require.main === module) {
  const force = process.argv.includes('--force');
  const done = seed(force);
  console.log(done ? 'Database seeded successfully.' : 'Database already seeded (use --force to reseed).');
}

module.exports = { seed };
