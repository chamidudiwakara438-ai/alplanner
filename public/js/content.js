/* Extra syllabus content — MCQs, more practicals */
window.CONTENT = {
  extraPracticals: [
    { id: 9, subject: 'Physics', category: 'Mechanics', en: 'Parallelogram of forces', si: 'බල සමාන්තරාස්‍රය', obj: 'Verify the parallelogram law with a force board.', theory: 'Two forces P and Q at angle θ have resultant R² = P²+Q²+2PQ cosθ.', proc: 'Hang known masses. Adjust the knot to equilibrium. Measure angles. Compare calculated R with the third weight.', formula: 'R = √(P²+Q²+2PQ cosθ)', viva: ['What if θ = 90°?', 'Why must the knot be free?'] },
    { id: 10, subject: 'Physics', category: 'Mechanics', en: 'Young’s modulus of a wire', si: 'යං මාපාංකය', obj: 'Find Y for steel/copper from extension.', theory: 'Y = (F/A) / (e/L) in the elastic region.', proc: 'Measure diameter with micrometer. Load stepwise. Read vernier extension. Plot F vs e. Y from slope.', formula: 'Y = (F L) / (A e)', viva: ['Why wait after each load?', 'What is permanent set?'] },
    { id: 11, subject: 'Physics', category: 'Waves', en: 'Sonometer — μ of wire', si: 'ස්වරමාපකය', obj: 'Find linear density from f vs 1/L.', theory: 'f = (1/2L)√(T/μ). Slope of f against 1/L is (1/2)√(T/μ).', proc: 'Fix tension. Move bridges to resonance (paper rider flips). Repeat 5 lengths.', formula: 'μ = T / (2 f L)²', viva: ['Why a paper rider?'] },
    { id: 12, subject: 'Physics', category: 'Heat', en: 'Quill tube — Boyle’s law', si: 'ක්විල් නලය', obj: 'Show pV constant for trapped air.', theory: 'At constant T, p ∝ 1/V. Length of air column ∝ V.', proc: 'Tilt the tube. Record mercury length and air length. Plot L vs 1/P.', formula: 'pV = const', viva: ['Why dry air?'] },
    { id: 13, subject: 'Physics', category: 'Electricity', en: 'Potentiometer — E of a cell', si: 'විභවමානය', obj: 'Compare emfs by balancing lengths.', theory: 'E ∝ l at null. E₁/E₂ = l₁/l₂.', proc: 'Standardise with a Daniel cell. Find balancing length. Swap the unknown.', formula: 'E = k l', viva: ['Why is a potentiometer better than a voltmeter?'] },
    { id: 14, subject: 'Chemistry', category: 'Kinetics', en: 'Rate of reaction — marble + HCl', si: 'ප්‍රතික්‍රියා වේගය', obj: 'Compare rates by collecting CO₂ volume vs time.', theory: 'Rate rises with [HCl] and surface area. Gradient of V–t is the rate.', proc: 'Add chips to acid. Collect gas over water. Plot two runs.', formula: 'rate = ΔV/Δt', viva: ['Why powder is faster?'] },
    { id: 15, subject: 'Chemistry', category: 'Organic', en: 'Functional group tests', si: 'ක්‍රියාකාරී කාණ්ඩ', obj: 'Identify alkene, aldehyde, acid, alcohol.', theory: 'Br₂ water, Fehling, Tollens, Na₂CO₃ fizz, acid dichromate.', proc: 'Do each test on unknowns. Record colour changes.', formula: 'RCHO + 2Cu²⁺ → RCOOH + Cu₂O (red)', viva: ['Why don’t ketones give Tollens?'] },
    { id: 16, subject: 'Chemistry', category: 'Electrochem', en: 'Daniell cell EMF', si: 'ඩැනියල් කෝෂය', obj: 'Measure E of Zn–Cu cell.', theory: 'E° = E_cathode − E_anode = 0.34 − (−0.76) = 1.10 V.', proc: 'Set up half-cells, salt bridge. Read voltmeter. Reverse leads to check sign.', formula: 'E = E° − (RT/nF) ln Q', viva: ['Which way do electrons flow?'] },
    { id: 17, subject: 'Biology', category: 'Cells', en: 'Onion epidermis under microscope', si: 'ලූනු පටලය', obj: 'Observe cell wall, nucleus, cytoplasm.', theory: 'Plant cells have cellulose walls and a large vacuole.', proc: 'Peel epidermis. Stain with iodine. Draw at low then high power. Calculate magnification.', formula: 'magnification = image / actual', viva: ['Why iodine?'] },
    { id: 18, subject: 'Biology', category: 'Physiology', en: 'Stomatal peel', si: 'පත්‍ර සිදුරු', obj: 'Count stomata and relate to transpiration.', theory: 'Guard cells open when turgid (K⁺ in).', proc: 'Nail-varnish peel of lower epidermis. Count stomata in 5 fields.', formula: 'density = n / area', viva: ['Why more stomata below?'] },
  ],
  mcq: [
    { subj: 'chem', t: 'atomic', q: 'How many electrons can a 2p sub-shell hold?', a: '2', b: '6', c: '8', d: '10', ans: 'b' },
    { subj: 'chem', t: 'mole', q: 'Moles in 8.0 g of NaOH (M=40)?', a: '0.10', b: '0.20', c: '0.40', d: '2.0', ans: 'b' },
    { subj: 'chem', t: 'gas', q: 'Boyle’s law keeps which pair constant?', a: 'p and V', b: 'T and n', c: 'p and T', d: 'V and n', ans: 'b' },
    { subj: 'chem', t: 'ph', q: 'pH of 0.010 mol dm⁻³ HCl?', a: '1', b: '2', c: '12', d: '0.01', ans: 'b' },
    { subj: 'chem', t: 'eq', q: 'Kc changes only when you change', a: 'concentration', b: 'pressure', c: 'catalyst', d: 'temperature', ans: 'd' },
    { subj: 'chem', t: 'flame', q: 'Lilac flame is', a: 'Na⁺', b: 'K⁺', c: 'Ca²⁺', d: 'Cu²⁺', ans: 'b' },
    { subj: 'chem', t: 'redox', q: 'Oxidation is', a: 'gain of electrons', b: 'loss of electrons', c: 'gain of H', d: 'loss of O', ans: 'b' },
    { subj: 'phys', t: 'suvat', q: 'v² = u² + 2as needs', a: 'constant v', b: 'constant a', c: 'zero u', d: 'zero s', ans: 'b' },
    { subj: 'phys', t: 'proj', q: 'Maximum range (level ground) is at', a: '30°', b: '45°', c: '60°', d: '90°', ans: 'b' },
    { subj: 'phys', t: 'newton', q: 'F = ma uses', a: 'any force', b: 'weight only', c: 'net force', d: 'friction only', ans: 'c' },
    { subj: 'phys', t: 'wave', q: 'v = fλ. If f doubles and v fixed, λ', a: 'doubles', b: 'halves', c: 'same', d: 'zero', ans: 'b' },
    { subj: 'phys', t: 'ohm', q: 'Two 6 Ω resistors in parallel equal', a: '12 Ω', b: '6 Ω', c: '3 Ω', d: '0 Ω', ans: 'c' },
    { subj: 'phys', t: 'lens', q: 'Real-is-positive: convex lens f is', a: 'negative', b: 'zero', c: 'positive', d: 'infinite', ans: 'c' },
    { subj: 'phys', t: 'shm', q: 'Pendulum T = 2π√(l/g) does not depend on', a: 'l', b: 'g', c: 'amplitude (small)', d: 'length', ans: 'c' },
    { subj: 'cm', t: 'quad', q: 'x² − 5x + 6 = 0 roots are', a: '1,6', b: '2,3', c: '−2,−3', d: '5,6', ans: 'b' },
    { subj: 'cm', t: 'diff', q: 'd/dx (x³) =', a: 'x²', b: '3x²', c: '3x', d: 'x³/3', ans: 'b' },
    { subj: 'cm', t: 'int', q: '∫ x² dx =', a: 'x³', b: '2x', c: 'x³/3 + C', d: '3x²', ans: 'c' },
    { subj: 'cm', t: 'trig', q: 'sin²θ + cos²θ =', a: '0', b: '1', c: '2', d: 'tanθ', ans: 'b' },
    { subj: 'cm', t: 'vec', q: 'a·b = 0 means vectors are', a: 'parallel', b: 'equal', c: 'perpendicular', d: 'zero', ans: 'c' },
    { subj: 'bio', t: 'cell', q: 'ATP is mainly made in the', a: 'nucleus', b: 'ribosome', c: 'mitochondrion', d: 'Golgi', ans: 'c' },
    { subj: 'bio', t: 'photo', q: 'O₂ in photosynthesis comes from', a: 'CO₂', b: 'glucose', c: 'water', d: 'chlorophyll', ans: 'c' },
    { subj: 'bio', t: 'dna', q: 'A pairs with', a: 'A', b: 'G', c: 'C', d: 'T', ans: 'd' },
    { subj: 'bio', t: 'enz', q: 'High heat denatures enzymes by', a: 'adding substrate', b: 'breaking 3-D shape', c: 'raising Km forever', d: 'making more product', ans: 'b' },
    { subj: 'ict', t: 'bin', q: '1101₂ in decimal is', a: '11', b: '12', c: '13', d: '14', ans: 'c' },
    { subj: 'ict', t: 'gate', q: 'XOR output is 1 when inputs', a: 'are both 1', b: 'are both 0', c: 'differ', d: 'are equal', ans: 'c' },
    { subj: 'ict', t: 'net', q: 'IPv4 address has', a: '16 bits', b: '32 bits', c: '64 bits', d: '128 bits', ans: 'b' },
    { subj: 'ict', t: 'sql', q: 'Primary key must be', a: 'null', b: 'duplicated', c: 'unique and not null', d: 'a foreign key only', ans: 'c' },
  ],
};
window.CONTENT.pickExam = function (subj, n) {
  const pool = this.mcq.filter((q) => subj === 'mixed' || q.subj === subj);
  const copy = pool.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = copy[i]; copy[i] = copy[j]; copy[j] = t;
  }
  return copy.slice(0, Math.min(n, copy.length)).map((q) => {
    const keys = ['a', 'b', 'c', 'd'];
    const opts = keys.map((k) => ({ k, t: q[k] }));
    for (let i = opts.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = opts[i]; opts[i] = opts[j]; opts[j] = t;
    }
    return { q: q.q, opts, ans: q.ans, subj: q.subj };
  });
};
