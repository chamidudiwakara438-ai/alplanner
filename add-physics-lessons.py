#!/usr/bin/env python3
"""
AL Planner - Physics video lesson pack (Units 1 & 2)
=====================================================
What it does, all automatically:
  * Renames the 11 Physics units to bilingual titles (English + Sinhala)
  * Unit 1  Measurement   -> "Measurement - Minum"
  * Unit 2  Mechanics     -> "Mechanics - Yanthra Vidyawa"
  * Adds the 12 YouTube links Team Akoit sent as video lessons
  * Teacher names are attached (Nilantha / Ushan / Aruna Pallekumbura /
    Saranga Palihawadana / Anuradha Perera / Nirosh Malinga)
  * Detects duplicates - already-added videos are skipped
  * Your accounts, uploads, progress and other subjects are NOT touched

Safe to run many times.

How to run:
  1. Stop the website (click its window, press Ctrl+C)
  2. python add-physics-lessons.py
     (on your PC:  & "C:\\Users\\Team Akoit\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" add-physics-lessons.py)
  3. Start the website again and press Ctrl+F5 in the browser
"""
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('AL_DATA_DIR', os.path.join(BASE, 'data'))
DB = os.path.join(DATA_DIR, 'alplanner.db')

# Official A/L Physics unit names, bilingual (English + Sinhala)
UNITS = [
    'Measurement \u2013 \u0db8\u0dd2\u0dab\u0dd4\u0db8\u0dca',                                    # 1
    'Mechanics \u2013 \u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',  # 2
    'Oscillations and Waves \u2013 \u0daf\u0ddd\u0dbd\u0db1 \u0dc3\u0dc4 \u0dad\u0dbb\u0d82\u0d9c',                      # 3
    'Thermal Physics \u2013 \u0dad\u0dcf\u0db4 \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',                        # 4
    'Gravitational Field \u2013 \u0d9c\u0dd4\u0dbb\u0dd4\u0dad\u0dca\u0dc0 \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',  # 5
    'Electrostatic Field \u2013 \u0dc3\u0dca\u0dae\u0dd2\u0dad \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dd4\u0dad\u0dca \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',  # 6
    'Magnetic Field \u2013 \u0da0\u0dd4\u0db8\u0dca\u0db6\u0d9a \u0d9a\u0dca\u0dc2\u0dda\u0dad\u0dca\u200d\u0dbb\u0dba',   # 7
    'Current Electricity \u2013 \u0db0\u0dcf\u0dbb\u0dcf \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dd4\u0dad\u0dca\u0dba',   # 8
    'Electronics \u2013 \u0d89\u0dbd\u0d9a\u0dca\u0da7\u0dca\u200d\u0dbb\u0ddd\u0db1\u0dd2\u0d9a \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0',  # 9
    'Mechanical Properties of Matter – පදාර්ථයේ යාන්ත්‍රික ගුණ',  # 10
    'Matter and Radiation – පදාර්ථය හා විකිරණ',  # 11
]

# (unit_ord, youtube_id, title, teacher)
LESSONS = [
    # ---- Unit 1: Measurement (minum) ---------------------------------------
    (1, '_0t4l6q9RTU', '2025 Revision \u2013 \u0db8\u0dd2\u0dab\u0dd4\u0db8\u0dca \u0d92\u0d9a\u0d9a\u0dba (Measurement) Online Class', 'Nilantha Jayasuriya'),
    (1, '6dj27T5DIzA', '\u0d92\u0d9a\u0d9a \u0dc4\u0dcf \u0db8\u0dcf\u0db1 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab\u0dba\u0dd9\u0db1\u0dca\u0db8\u0dca (Units & Dimensions \u2013 Full Theory)', 'Ushan Gunasekara'),
    (1, 'DZEfX4NFDLg', 'Flash Practicals 01 \u2013 \u0dc0\u0dbb\u0dca\u0db1\u0dd2\u0dba\u0dbb\u0dca \u0d9a\u0dd0\u0dbd\u0dd2\u0db4\u0dbb\u0dba (Vernier Caliper)', 'Aruna Pallekumbura'),
    (1, 'Z8U3RY8sVRw', 'Flash Practicals 02 \u2013 \u0db8\u0dba\u0dd2\u0d9a\u0dca\u200d\u0dbb\u0ddd\u0db8\u0dd3\u0da7\u0dbb\u0dca \u0d89\u0dc3\u0dca\u0d9a\u0dd4\u0dbb\u0dd4\u0db4\u0dca\u0db4\u0dd4 \u0d86\u0db8\u0dcf\u0db1\u0dba (Micrometer Screw Gauge)', 'Aruna Pallekumbura'),
    (1, 'E7QbzysxmyE', "Newton's Cradle", 'Aruna Pallekumbura'),
    (1, 'EPNxatmApmk', 'Flash Practicals 03 \u2013 \u0d9c\u0ddd\u0dbd\u0db8\u0dcf\u0db1\u0dba (Spherometer)', 'Aruna Pallekumbura'),
    (1, 'DNDe1owhI70', 'Flash Practicals 04 \u2013 \u0da0\u0dbd \u0d85\u0db1\u0dca\u0dc0\u0dd3\u0d9a\u0dca\u0dc2\u0dba (Travelling Microscope)', 'Aruna Pallekumbura'),
    (1, 'PRhSs6Oh7Qc', 'Flash Practicals Special \u2013 \u0dad\u0dd9\u0daf\u0da9\u0dd4 \u0dad\u0dd4\u0dbd\u0dcf\u0dc0 (Triple-beam Balance)', 'Aruna Pallekumbura'),
    # ---- Unit 2: Mechanics (yanthra vidyawa) --------------------------------
    (2, 'Eo9AApyncnA', '\u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dcf\u0da9\u0db8 (Mechanics \u2013 Full Lesson)', 'Ushan Gunasekara'),
    (2, 'B2b_FiKsncY', '\u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0 (Mechanics) \u2013 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dcf\u0da9\u0db8 \u0dc0\u0dd2\u0db1\u0dcf\u0da9\u0dd2 84\u0db1\u0dca | Speed Revision', 'Saranga Palihawadana (Einsphysics)'),
    (2, 'vU3zH2PWldY', '2025 A/L \u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0 Practical Day LIVE (Mechanics)', 'Anuradha Perera'),
    (2, '7qeIuq5zqwg', '\u0dba\u0dcf\u0db1\u0dca\u0dad\u0dca\u200d\u0dbb \u0dc0\u0dd2\u0daf\u0dca\u200d\u0dba\u0dcf\u0dc0 FULL LESSON (Mechanics)', 'Nirosh Malinga (Physics)'),
    # ---- Unit 3: Oscillations and Waves (alokaya / light) -------------------
    (3, 'hoBRT67LZvc', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 01: \u0d86\u0dbb\u0db8\u0dca\u0db7\u0dba (Introduction)', 'Dr Darshana Ukuwela'),
    (3, 'pUCPyRvPrDk', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 02', 'Dr Darshana Ukuwela'),
    (3, 'awfDF04soZI', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 03', 'Dr Darshana Ukuwela'),
    (3, 'AUA9JdunRfA', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 04', 'Dr Darshana Ukuwela'),
    (3, 'NnyzBU2g5XI', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 05', 'Dr Darshana Ukuwela'),
    (3, 'IXOqaaE20z0', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 06', 'Dr Darshana Ukuwela'),
    (3, '85NmeuO741g', '2025 \u0d86\u0dbd\u0ddd\u0d9a\u0dba (Light) \u2013 Day 07', 'Dr Darshana Ukuwela'),
    (3, 'Cw5mS8WskN4', '\u0d86\u0dbd\u0ddd\u0d9a\u0dba: \u0d9a\u0dcf\u0da0 (Lenses) \u2013 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dcf\u0da9\u0db8 \u0d91\u0d9a \u0daf\u0dd2\u0db1\u0d9a\u0dd2\u0db1\u0dca (Full Lesson in One Day)', 'Dr Darshana Ukuwela'),
    (3, 'CFgaWaiMxm8', '\u0d86\u0dbd\u0ddd\u0d9a\u0dba: \u0d87\u0dc3 \u0dc3\u0dc4 \u0db4\u0dca\u200d\u0dbb\u0d9a\u0dcf\u0dc1 \u0d8b\u0db4\u0d9a\u0dbb\u0dab (Eye & Optical Instruments) \u2013 \u0dc3\u0db8\u0dca\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0db4\u0dcf\u0da9\u0db8 (Full Lesson)', 'Dr Darshana Ukuwela'),
    (3, '6HSB2TRx7Qw', '\u0db4\u0dd6\u0dbb\u0dca\u0dab \u0d85\u0db7\u0dca\u200d\u0dba\u0db1\u0dca\u0dad\u0dbb \u0db4\u0dbb\u0dcf\u0dc0\u0dbb\u0dca\u0dad\u0db1\u0dba \u0dc3\u0dc4 \u0db4\u0dca\u200d\u0dbb\u0dd2\u0dc3\u0dca\u0db8 (Total Internal Reflection & Prisms)', 'Dr Darshana Ukuwela'),
]
# ---- Unit 3 BULK PACK: Ushan one-day revision + Aruna Light playlist + Mahen Jecob past-paper playlist
BULK = [
    (3, 'qR1il9T5C8Q', 'ආලෝකය (Light) – සම්පූර්ණ පාඩම එක දවසින්! (One-Day Full Revision)', 'Ushan Gunasekara'),
    (3, 'Z0ULyBXpZgw', 'ආලෝකය (Light) Revision – Day 01', 'Aruna Pallekumbura'),
    (3, 'vSh0hCEwm7o', 'ආලෝකය (Light) Revision – Day 02', 'Aruna Pallekumbura'),
    (3, 'bfXgQw7YSY0', 'ආලෝකය (Light) Revision – Day 03', 'Aruna Pallekumbura'),
    (3, 'fytxIAjni34', 'M-23 Discussion (2024 A/L)', 'Aruna Pallekumbura'),
    (3, 'JBKCBQS3PxI', 'ආලෝකය (Light) Revision – Day 04', 'Aruna Pallekumbura'),
    (3, '3NEO5QL5cQ8', 'ප්\u200dරිස්ම (Prisms) – පසුගිය විභාග බහුවරණ සාකච්ඡාව (Past MCQ Discussion)', 'Aruna Pallekumbura'),
    (3, 'lV0Sz8ZqpRU', 'ආලෝකය (Light) Revision – Day 05', 'Aruna Pallekumbura'),
    (3, 'js442NwkDm0', 'ආලෝකය (Light) Revision – Day 06', 'Aruna Pallekumbura'),
    (3, 'kgdNW3kWoGo', 'ආලෝකය (Light) Revision – Day 07', 'Aruna Pallekumbura'),
    (3, 'BCO7NLvOqME', 'වර්තනය (Refraction) – පසුගිය විභාග බහුවරණ සාකච්ඡාව (Past MCQ Discussion)', 'Aruna Pallekumbura'),
    (3, 'Kd-F1NwHfvU', 'මිනිස් ඇස (Human Eye) – සම්පූර්ණ කොටස (Full Revision)', 'Aruna Pallekumbura'),
    (3, 'Jxaj7E0NyUo', 'ප්\u200dරකාශ උපකරණ (Optical Instruments) – සම්පූර්ණ කොටස (Full Revision)', 'Aruna Pallekumbura'),
    (3, 'A4sLZfVhDlc', 'ආලෝකය | Light | 1966 Essay', 'Mahen Jecob'),
    (3, '3yp1uTp8GVI', 'ආලෝකය | Light | 1980 Essay', 'Mahen Jecob'),
    (3, 'JizJM7ZUVyw', 'ආලෝකය | Light | 1982 Structured Essay', 'Mahen Jecob'),
    (3, 'Iy6L7-6NuQg', 'ආලෝකය | Light | 1984 Structured Essay', 'Mahen Jecob'),
    (3, 'DbFPawWxCFE', 'ආලෝකය | Light | 1988 Essay', 'Mahen Jecob'),
    (3, 'O6R246UKCDU', 'ආලෝකය | Light | 1986 Essay', 'Mahen Jecob'),
    (3, '3vMdbA3GUtM', 'ආලෝකය | Light | 1993 Essay', 'Mahen Jecob'),
    (3, 'anGGo_XIfTQ', 'ආලෝකය | Light | 1990 Essay', 'Mahen Jecob'),
    (3, 'urSL59DkNAc', 'ආලෝකය | Light | 1994 Essay', 'Mahen Jecob'),
    (3, '2dwYUEo2Ur4', 'ආලෝකය | Light | 1996 Essay', 'Mahen Jecob'),
    (3, 'sqvKX67UpTc', 'ආලෝකය | Light | 1997 Essay', 'Mahen Jecob'),
    (3, 'u1puhwUVAdM', 'ආලෝකය | Light | 2002 Essay', 'Mahen Jecob'),
    (3, 'jqk9jbM57NY', 'ආලෝකය | Light | 1999 Structured Essay', 'Mahen Jecob'),
    (3, 'NZ5lOOQGbOY', 'ආලෝකය | Light | 2006 Structured Essay', 'Mahen Jecob'),
    (3, 'JmawRfHCJlo', 'ආලෝකය | Light | 2014 Structured Essay', 'Mahen Jecob'),
    (3, '7LKhQ-RY8NA', 'ආලෝකය | Light | 2009 Essay', 'Mahen Jecob'),
    (3, 'ljpb_Sp1_oE', 'Light | 1981 Structured Essay', 'Mahen Jecob'),
    (3, 'xLzMrSFIVl4', 'Light | 1982 Essay', 'Mahen Jecob'),
    (3, 'hjkVlnhHyy0', 'Light | 1993 Structured Essay', 'Mahen Jecob'),
    (3, 'l1uMRkmZqB4', 'Light | 1989 Essay', 'Mahen Jecob'),
    (3, 'yXWceHKgJ7k', 'Light | 1996 Essay', 'Mahen Jecob'),
    (3, 'jfl-2BtgvpM', 'Light | 2000 Essay', 'Mahen Jecob'),
    (3, 'aL3TTXuKbU0', 'Light | 2011 Essay', 'Mahen Jecob'),
    (3, 'Kl7pCB6pfb0', 'ආලෝකය | Light | 1987 Essay', 'Mahen Jecob'),
    (3, 'CpjVRcOhPLU', 'ආලෝකය | Light | 1991 Essay', 'Mahen Jecob'),
    (3, 'c658Mk6QaUg', 'ආලෝකය | Light | 1994 Essay', 'Mahen Jecob'),
    (3, 'Qs0hhElOUwE', 'ආලෝකය | Light | 2003 Essay', 'Mahen Jecob'),
    (3, 'H58xZ38vJ_c', 'ආලෝකය | Light | 2005 Essay', 'Mahen Jecob'),
    (3, 'lRDHtVzFxqc', 'ආලෝකය | Light | 2017 Essay', 'Mahen Jecob'),
    (3, 'cxUmlhGLU1g', 'ආලෝකය | Light | 2010 Structured Essay', 'Mahen Jecob'),
    (3, 'LEeDQRYFOzg', 'ආලෝකය | Light | 2020 Essay', 'Mahen Jecob'),
    (3, 'IBT95tqF-1I', 'ආලෝකය | Light | 2012 Structured Essay', 'Mahen Jecob'),
    (3, 'HhACogfZlN8', 'ආලෝකය | Light | 2012 Structured Essay', 'Mahen Jecob'),
    (3, 'VVyTnV-QUYg', 'ආලෝකය | Light | 1996 Structured Essay', 'Mahen Jecob'),
    (3, '1P3S4KI6S2w', 'ආලෝකය | Light | 1987 Essay', 'Mahen Jecob'),
    (3, 'Bel0V9XoWdE', 'ආලෝකය | Light | 1979 Structured Essay', 'Mahen Jecob'),
    (3, 'JWr-wjwD9rg', 'ආලෝකය | Light | 2008 Structured Essay', 'Mahen Jecob'),
    (3, 'd-Pl70opXio', 'ආලෝකය | Light | 1980 Structured Essay', 'Mahen Jecob'),
    (3, 'ZJ3o6zU0Qrw', 'ආලෝකය | Light | 2001 Structured Essay', 'Mahen Jecob'),
    (3, 'DDKOdAIfSw4', 'ආලෝකය | Light | 1989 Structured Essay', 'Mahen Jecob'),
    (3, 'zkttbfiwvpo', 'ආලෝකය | Light | 1998 Structured Essay', 'Mahen Jecob'),
    (3, 'DCj0c4SGcCo', 'ආලෝකය | Light | 1994 Structured Essay', 'Mahen Jecob'),
    (3, 'SERLQYot6Ic', 'ආලෝකය | Light | 2021 Structured Essay', 'Mahen Jecob'),
    (3, 'D8XzZ8qneVY', 'ආලෝකය | Light | 2013 Essay', 'Mahen Jecob'),
    (3, '7pVuoY9SDCA', 'ආලෝකය | Light | 2007 Essay', 'Mahen Jecob'),
    (3, '-Tpd2YKfxXc', 'ආලෝකය | Light | 1983 Essay', 'Mahen Jecob'),
    (3, '9-CgDu_rFXw', 'ආලෝකය | Light | 2016 Essay', 'Mahen Jecob'),
    (3, 'Gfm9REWXDao', 'ආලෝකය | Light | 2019 Structured Essay', 'Mahen Jecob'),
    (3, 'hlidK6eDvfc', 'ආලෝකය | Light | 2018 Structured Essay', 'Mahen Jecob'),
    (3, 'BPdOIXc1rPg', 'ආලෝකය | Light | 1995 Structured Essay', 'Mahen Jecob'),
    (3, 'ffZMjHsF9mY', 'ආලෝකය | Light | 2015 Structured Essay', 'Mahen Jecob'),
    (3, 'ZRRE_L6BBMw', 'ආලෝකය | Light | 2004 Structured Essay', 'Mahen Jecob'),
    (3, 'AuJ47de1bO4', 'ආලෝකය | Light | 2022 Essay', 'Mahen Jecob'),
    (3, 'Q95qPuTYPw0', '2023 A/L Structured Essay දෝලන හා තරංග විවරණය | No.zero Physics | Isuru B. Rathnayake', 'Isuru B. Rathnayake'),
]
# ---- BULK 2: Mechanics MCQ pack + Oscillations & Waves packs (Nilantha/Samitha/Ushan/Physics Kuppi/Mahen)
BULK2 = [
    (2, '6FHEZjYkUqY', 'කාර්යය, ශක්තිය හා ක්ෂමතාවය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'chRk74T-vTY', 'බල සමතුලිතතාව | පසුගිය විභාග බහුවරණ විවරණය - 01 | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, '6g-Ujxzs9Ps', 'භ්\u200dරමණ චලිතය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, '0mNNGJkrDHk', 'තරල ගතිකය පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, '-QfN_5q4ymU', 'නිව්ටන් නියම | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'RbqSjvodC68', 'ගුරුත්ව කේන්ද්\u200dරය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'OFf_y0mv2Os', 'ද්\u200dරවස්ථිතිය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'W9By5P6NIX0', 'ඝර්ෂණය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'YZ5wXtNxZS4', 'වෘත්ත චලිතය | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'dTqla2EyMW8', 'Revision සඳහා theory | Mechanics | කාර්යය හා ශක්තිය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'bpxa8Uox6os', 'බල සමතුලිතතාව | පසුගිය විභාග බහුවරණ විවරණය - 02 | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (2, 'w261GjtnQ0s', 'මිනුම් උපකරණ | පසුගිය විභාග බහුවරණ විවරණය | Mechanics – Past Paper MCQ', 'Mahen Jecob'),
    (3, 'RbP3vOE5FRQ', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 01 EX', 'Nilantha Jayasuriya'),
    (3, 'nYEtiX3G1ng', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 02 EX', 'Nilantha Jayasuriya'),
    (3, 'p3rg7uZGcTs', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 03 EX', 'Nilantha Jayasuriya'),
    (3, 'crVbs-VIvMU', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 04 EX', 'Nilantha Jayasuriya'),
    (3, 'M3R2BVlCSSE', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 05', 'Nilantha Jayasuriya'),
    (3, 'liXjoCJ0Zuo', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 06', 'Nilantha Jayasuriya'),
    (3, 'Ct9VGXryE9Q', 'A/L Physics | Nilantha Jayasuriya | 2024 Theory දෝලන හා තරංග (පරීක්ෂණ) 07 EX', 'Nilantha Jayasuriya'),
    (3, 'LRLQluK4XJw', 'දෝලන හා තරංග (Oscillations & Waves) – 2024 Theory 15 EX', 'Nilantha Jayasuriya'),
    (3, 'em43vvTaKl0', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY01-PART 01', 'Samitha Rathnayake'),
    (3, 'pS4Wy12ASaI', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY01-PART 02', 'Samitha Rathnayake'),
    (3, '22fLZDTyOys', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY01-PART 03', 'Samitha Rathnayake'),
    (3, 'JQIqhrgQOag', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY01-PART 04', 'Samitha Rathnayake'),
    (3, 'VAOT395QV9c', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY02-PART 01', 'Samitha Rathnayake'),
    (3, 'i_u7_ewIjm0', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY02-PART 02', 'Samitha Rathnayake'),
    (3, 'H7SgO_l5rGo', 'Oscillations and Waves (දෝලන හා තරංග) Unit 03 - DAY02-PART 03', 'Samitha Rathnayake'),
    (3, 'dttPh7dkucM', 'දෝලන හා තරංග (Oscillations & Waves) – සම්පූර්ණ පාඩම LIVE (Full Lesson)', 'Ushan Gunasekara'),
    (3, 'otm7ZdPDIig', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 01', 'Physics Kuppi'),
    (3, 'AzeFNtT5LbI', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 01 - PART 2', 'Physics Kuppi'),
    (3, '5BYx9h1_iSA', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 02', 'Physics Kuppi'),
    (3, 'gjE4PfaLkzo', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 03', 'Physics Kuppi'),
    (3, 'F59glLCQU6o', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 04', 'Physics Kuppi'),
    (3, '9P_MZvQUqnI', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 05', 'Physics Kuppi'),
    (3, 'k4wCfpavTdo', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Day 06', 'Physics Kuppi'),
    (3, 'qcSYLe37xvM', 'AL Physics Doppler Effect (ඩොප්ලර් ආචරණය) | Waves and Oscillation (දෝලන හා තරංග) Day 07', 'Physics Kuppi'),
    (3, '3eCAqE0xJy4', 'AL Physics Waves and Oscillation ( දෝලන හා තරංග ) Complete video pack', 'Physics Kuppi'),
    (3, 'L3CZsaXsmHI', 'Waves and Oscillations | 1981 Essay', 'Mahen Jecob'),
    (3, 'onwQa2QateQ', 'Oscillation and Waves | 1983 Essay', 'Mahen Jecob'),
    (3, 'qM0DUfHMVuI', 'Oscillation and Waves | 1985 Essay', 'Mahen Jecob'),
    (3, '05ZmjgevqwU', 'Waves | 1987', 'Mahen Jecob'),
    (3, 'x8ujpzNyYFQ', 'Oscillation and Waves | 1988 Essay', 'Mahen Jecob'),
    (3, 'quOP4ylmBDI', 'Oscillations and Waves | 1989 Essay', 'Mahen Jecob'),
    (3, 'PSccKCTKpXc', 'No. Zero Physics | Waves and Oscillations | 1990 Essay', 'Mahen Jecob'),
    (3, 'PEFcqPi13po', 'Oscillation and Waves | 1991 Essay', 'Mahen Jecob'),
    (3, 'EHGkkgqRxyY', 'Waves and Oscillations | 1993 Essay', 'Mahen Jecob'),
    (3, '2E_AQ0I68oQ', 'Oscillation and Waves | 1994 Essay', 'Mahen Jecob'),
    (3, 'e0ClfpMXhlg', 'No. Zero Physics | Waves and Oscillations | 1995 Essay', 'Mahen Jecob'),
    (3, 'JqOJYR2tDKk', 'Oscillation and Waves | 1996 Essay', 'Mahen Jecob'),
    (3, 'aAxHtZ43z7Y', 'Oscillation and Waves | Doppler Effect | 1997 Essay', 'Mahen Jecob'),
    (3, 'yr92Piajk6g', 'Waves and Oscillations | 1998 Essay (Ripple Tank)', 'Mahen Jecob'),
    (3, 'Dqdcg9aqvDM', 'Waves and Oscillations | 1999 Essay', 'Mahen Jecob'),
    (3, '1OoMbWDkqS0', 'Oscillation and Waves | Doppler Effect | 2001 Essay', 'Mahen Jecob'),
    (3, 'd42ND0y1JTU', 'Oscillation and Waves | 2004 Essay', 'Mahen Jecob'),
    (3, 'FSPJg8QHFic', 'Oscillation and Waves | Doppler Effect | 2006 Essay', 'Mahen Jecob'),
    (3, 'Ygfgu0Pm830', 'Oscillation and Waves | 2008 Essay', 'Mahen Jecob'),
    (3, 'RNrH_lgvry4', 'Simple Harmonic Motion | 2010 Essay', 'Mahen Jecob'),
    (3, 'TEjnkkTcwYo', 'Oscillation and Waves | Doppler Effect | 2012 Essay', 'Mahen Jecob'),
    (3, 'KHDi1xuqWh8', 'Oscillation and Waves | 2014 Essay', 'Mahen Jecob'),
    (3, 'ITPTjrCQcqY', 'Waves and Oscillations | 2015 Essay', 'Mahen Jecob'),
    (3, 'cg2X9tMUSlk', 'No. Zero Physics | Waves and Oscillations | 2018 Essay', 'Mahen Jecob'),
    (3, '11RmuR6bqDE', 'Waves and Oscillations | 2019 Essay', 'Mahen Jecob'),
    (3, 'qvnDY3HwBXk', 'දෝලන හා තරංග - ඩොප්ලර් ආචරණය | Waves and Oscillations | 2021 Essay', 'Mahen Jecob'),
]
# ---- BULK 3: Thermal Physics packs (Anuradha Perera theory + Mahen Jecob essays/MCQ + Isuru structured)
BULK3 = [
    (4, 'JLTbph1MrT4', 'තාපය ආරම්භය 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'sW3wWZU6bZw', 'තාපය ද්\u200dරව ප්\u200dරසාරණය LIVE 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'fsK09AhO3ek', 'තාපය උෂ්ණත්වමිතිය සම්පූර්ණ පාඩම Part 1 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, '81_TwmRsY1A', 'තාපය උෂ්ණත්වමිතිය සම්පූර්ණ පාඩම Part 2 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'AED0ugnoNgQ', 'තාපය උෂ්ණත්වමිතිය සම්පූර්ණ පාඩම Part 3 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'up7Ghe3NjhM', 'තාපය වායු නියම සම්පූර්ණ පාඩම | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'rGjNypmOqjw', 'තාපය චාලක අණුක වාදය 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'zps95rbxiiM', 'තාපමිතිය ආරම්භය 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'qHr6S3q_PJs', '2026 තාපය HOMEWORK DISCUSSION 20 12 2025 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, '-p2_j2Pt_yA', '2026 තාපය HOMEWORK DISCUSSION 27 12 2025 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, '6vE9Qo-0NeU', '2026 තාපය HOMEWORK DISCUSSION 10 01 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'HpfxKRJJU8c', '2026 තාපය HOMEWORK DISCUSSION 24 01 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, '5njwvxAWq-o', '2026 HOMEWORK DISCUSSION තාපය 31 01 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'dtCQH88ZugU', 'තාපමිතිය විශේෂ කරුණු 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'pMhZaZxCyTY', 'තාප සන්නයනය සහ සම්පූර්ණ පාඩම 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'yCYMsckg5bc', '2026 HOMEWORK DISCUSSION තාපය 14 02 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'yYYNYD3_2Ik', '2026 HOMEWORK DISCUSSION - තාපය 21 02 2026 | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'CitiHFdYegI', 'තාපගති විද්\u200dයාව සම්පූර්ණ පාඩම | 2026 REVISION | Thermal Physics – 2026 Revision', 'Anuradha Perera'),
    (4, 'SGOQotPkZwc', 'තාප භෞතිකය | Thermal Physics | 2025 Structured Essay', 'Mahen Jecob'),
    (4, '0XXMK6tvwb8', 'තාප භෞතිකය | Thermal Physics | 2025 Essay', 'Mahen Jecob'),
    (4, '7c_Oqw-cyjs', 'තාප භෞතිකය | Thermal Physics | 1990 Essay (1)', 'Mahen Jecob'),
    (4, 'Mzdwc_9GTuQ', '2024 A/L Structured Essay | තාපය ව්\u200dයුහගත විවරණය | Thermal Physics', 'Isuru B. Rathnayake'),
    (4, 'FCvWXc9M91w', 'තාප භෞතිකය | Thermal Physics | 2024 Essay', 'Mahen Jecob'),
    (4, '-IVI5cBGUQw', 'සිසිලන ක්\u200dරමයෙන් ද්\u200dරවයක විශිෂ්ට තාප ධාරිතාව\xa0සෙවීම | Thermal Physics', 'Isuru B. Rathnayake'),
    (4, '7wvmRc153Pg', '2023 A/L Structured Essay | තාපය ව්\u200dයුහගත විවරණය | Thermal Physics', 'Isuru B. Rathnayake'),
    (4, 'yKO8qOT-lqE', 'තාප භෞතිකය | Thermal Physics | 2023 Essay', 'Mahen Jecob'),
    (4, 'yQxqSWKh4gI', 'තාප භෞතිකය | Thermal Physics | 2022 Structured Essay', 'Mahen Jecob'),
    (4, 'erqERQnMkno', 'තාප භෞතිකය | Thermal Physics | 2022 Essay', 'Mahen Jecob'),
    (4, '1ElpLMipqEI', 'තාප භෞතිකය | Thermal Physics | 2009 Essay', 'Mahen Jecob'),
    (4, 'nz-xCE_de1k', 'තාප භෞතිකය | Thermal Physics | 1997 Essay', 'Mahen Jecob'),
    (4, 'L6H1VmYPt7A', 'තාප භෞතිකය | Thermal Physics | 1983 Essay', 'Mahen Jecob'),
    (4, 'Tq-z1E9dhx4', 'තාප භෞතිකය | Thermal Physics | 1996 Essay', 'Mahen Jecob'),
    (4, 'Wiv-8VLWUNc', 'තාප භෞතිකය | Thermal Physics | 1970 Essay', 'Mahen Jecob'),
    (4, '_C3SuS6gqfQ', 'තාප භෞතිකය | Thermal Physics | 1969 Essay', 'Mahen Jecob'),
    (4, 'Ruhe03lh81k', 'තාප භෞතිකය | Thermal Physics | 1966 Essay', 'Mahen Jecob'),
    (4, 'cvClQr-oCsg', 'තාප භෞතිකය | Thermal Physics | 1999 Structured Essay', 'Mahen Jecob'),
    (4, 'MTLGjIiktFk', 'තාප භෞතිකය | Thermal Physics | 1979 Structured Essay', 'Mahen Jecob'),
    (4, '5T3VMKrUK4o', 'තාප භෞතිකය | වායු | Thermal Physics | 1992 Essay', 'Mahen Jecob'),
    (4, 'SXi1-0xI-PU', 'තාප භෞතිකය | Thermal Physics | 1976 Structured Essay', 'Mahen Jecob'),
    (4, 'cf9STVeAeuo', 'තාප භෞතිකය | Thermal Physics | 2021 Essay', 'Mahen Jecob'),
    (4, 'lIVxNORzNXU', 'තාප භෞතිකය | Thermal Physics | 2021 Structured Essay', 'Mahen Jecob'),
    (4, 'CDc0DmXHIsA', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2001 Structured Essay', 'Mahen Jecob'),
    (4, 'N9B-F3iQ5Ms', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2000 Essay', 'Mahen Jecob'),
    (4, '3cxGBNOF42A', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2012 Structured Essay', 'Mahen Jecob'),
    (4, 'Nma9i0E06rE', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1985 Structured Essay', 'Mahen Jecob'),
    (4, 'yXnuJ5-hoyg', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1982 Structured Essa', 'Mahen Jecob'),
    (4, '0_Fl4Yg0Cdw', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1993 Structured Essay', 'Mahen Jecob'),
    (4, 'bKF7tjfWfXI', 'තාප භෞතිකය | Thermal Physics | 1991 Essay', 'Mahen Jecob'),
    (4, 'sgjLQzu2kfo', 'තාප භෞතිකය | Thermal Physics | 1975 Essay', 'Mahen Jecob'),
    (4, 'Np8lPVkiTZ4', 'ආර්ද්\u200dරතාමිතිය No. Zero Physics', 'Mahen Jecob'),
    (4, 'noK6-RwOl4w', 'තාප භෞතිකය | Thermal Physics | 1969 Essay', 'Mahen Jecob'),
    (4, 'oUrCqBod4BY', 'තාප භෞතිකය | Thermal Physics | 2011 Essay', 'Mahen Jecob'),
    (4, '_ymGiVKfX9I', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1997 Essay', 'Mahen Jecob'),
    (4, 'ja1aYlBELfc', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1980 Structured Essay', 'Mahen Jecob'),
    (4, 'Uh9BGpSyIPY', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2016 Essay', 'Mahen Jecob'),
    (4, '93bVFhKJspM', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2014 Structured Essay', 'Mahen Jecob'),
    (4, 'IqJewslYuy8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2011 Structured Essay', 'Mahen Jecob'),
    (4, 'B1SozytfMvI', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2014 Essay', 'Mahen Jecob'),
    (4, '-zem2Rbn6dM', 'තාප භෞතිකය | Thermal Physics | 1994 Essay', 'Mahen Jecob'),
    (4, 'gcHxZAPspeM', 'තාප භෞතිකය | Thermal Physics | 1998 Structured Essay', 'Mahen Jecob'),
    (4, 'TmOm-Mw04oI', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2016 Structured Essay', 'Mahen Jecob'),
    (4, '2ALFGsSygr8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1988 Essay', 'Mahen Jecob'),
    (4, 'avESoaNAcs0', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1993 Essay', 'Mahen Jecob'),
    (4, 'gEdfeRnO7kU', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1996 Essay', 'Mahen Jecob'),
    (4, '07WSTlIMWmQ', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1997 Essay', 'Mahen Jecob'),
    (4, 'RvG-s2cXLi0', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2018 Structured Essay', 'Mahen Jecob'),
    (4, 'RZULAbaVnF8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2017 Essay', 'Mahen Jecob'),
    (4, 'fe1Y-pJOs1s', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1995 Essay', 'Mahen Jecob'),
    (4, 'RlmlFmyytwM', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1981 Structured Essay', 'Mahen Jecob'),
    (4, '5E9MTCWm7Go', 'තාප භෞතිකය | Thermal Physics | 2006 Structured Essay', 'Mahen Jecob'),
    (4, 'Xa3RqL2_5QE', 'තාප භෞතිකය | Thermal Physics | 2019 Structured Essay', 'Mahen Jecob'),
    (4, 'svvvL4L2ifE', 'තාප භෞතිකය | Thermal Physics | 2009 Structured Essay', 'Mahen Jecob'),
    (4, 'J0v4RgM_KaI', 'තාප භෞතිකය | Thermal Physics | 1966 Essay', 'Mahen Jecob'),
    (4, '4jLNGZ1F814', 'තාප භෞතිකය | Thermal Physics |2020 Essay', 'Mahen Jecob'),
    (4, 'yvaM0V7odec', 'තාප භෞතිකය | Thermal Physics | 2005 Essay', 'Mahen Jecob'),
    (4, 'sTc4rDyecIE', 'තාප භෞතිකය | Thermal Physics | 2001 Essay', 'Mahen Jecob'),
    (4, 'RfghTNvDkDI', 'තාප භෞතිකය | Thermal Physics | 1996 Essay', 'Mahen Jecob'),
    (4, 'x8KTcMNhUI0', 'තාප භෞතිකය | Thermal Physics | 1982 Essay', 'Mahen Jecob'),
    (4, 'nRCwltLeCLY', 'තාප භෞතිකය | Thermal Physics | 2007 Essay', 'Mahen Jecob'),
    (4, 'GUPeS0tEr30', 'තාප භෞතිකය | Thermal Physics | 2002 Essay', 'Mahen Jecob'),
    (4, '2ve37nBTokk', 'තාප භෞතිකය | Thermal Physics | 1992 Essay', 'Mahen Jecob'),
    (4, 'q87rJ_3Ve6s', 'තාප භෞතිකය | Thermal Physics | 1991 Essay', 'Mahen Jecob'),
    (4, 'LT0iC3UX4TA', 'තාප භෞතිකය | Thermal Physics | 1990 Essay', 'Mahen Jecob'),
    (4, 'tP2gWpMm0FA', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1985 Essay', 'Mahen Jecob'),
    (4, 'GQDMdfEPs7c', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1984 Structured Essay', 'Mahen Jecob'),
    (4, 'tgtNTVGEOS8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1991 Structured Essay', 'Mahen Jecob'),
    (4, 'CEZ0DRiKWnU', 'තාප භෞතිකය | Thermal Physics | 2012 Essay', 'Mahen Jecob'),
    (4, 'pHJLWJ40xzs', 'තාප භෞතිකය | Thermal Physics | 2018 Essay', 'Mahen Jecob'),
    (4, 'I3O5tcpDr_g', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2008 Essay', 'Mahen Jecob'),
    (4, 'l7LP2-FG22c', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2010 Structured Essay', 'Mahen Jecob'),
    (4, 'K0mE98y0Enw', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2017 Structured Essay', 'Mahen Jecob'),
    (4, 'pRJ_uHTsr4Y', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1992 Structured Essay', 'Mahen Jecob'),
    (4, '835u30dekK8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1994 Structured Essay', 'Mahen Jecob'),
    (4, 'IYuNgE1vkgI', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1994 Essay', 'Mahen Jecob'),
    (4, 'Qj5qtztcayg', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1995 Essay', 'Mahen Jecob'),
    (4, '8vDdinb8i4c', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1995 Practical & Structured Essay', 'Mahen Jecob'),
    (4, 'pTlekKNyl7s', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1999 Essay', 'Mahen Jecob'),
    (4, 'V9rml7hzq3E', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2002 Structured Essay', 'Mahen Jecob'),
    (4, 'VX9sIWaSfIk', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2003 Practical & Structured Essay', 'Mahen Jecob'),
    (4, 'sXhsd1kOhsQ', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2000 Practical & Structured Essay', 'Mahen Jecob'),
    (4, 'WbhOQjAnoKo', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1998 Essay', 'Mahen Jecob'),
    (4, 'zHdkv07Hftk', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2005 Structured Essay', 'Mahen Jecob'),
    (4, 'D1S51PuRTCI', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2008 Practical & Structured Essay', 'Mahen Jecob'),
    (4, 'GjqLbs1C9-4', 'තාප භෞතිකය | Thermal Physics | 2003 Essay', 'Mahen Jecob'),
    (4, '9ZuLwGSwXzA', 'තාප භෞතිකය | Thermal Physics | 2019 Essay', 'Mahen Jecob'),
    (4, 'YrX735fQ1-E', 'තාප භෞතිකය | Thermal Physics | 2020 Structured Essay', 'Mahen Jecob'),
    (4, 'NDrryz8SUaA', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2007 Structured Essay', 'Mahen Jecob'),
    (4, 'sGPXRrcnBCY', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2013 Essay', 'Mahen Jecob'),
    (4, 'k16LfCC2Rd8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics & Current Electricity | 2004 Structured Essay', 'Mahen Jecob'),
    (4, 'cdCDzVfQZWM', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1989 Essay', 'Mahen Jecob'),
    (4, '_dU-3LCwbcM', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2010 Essay', 'Mahen Jecob'),
    (4, '_V5wLBdWaiY', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1993 Essay', 'Mahen Jecob'),
    (4, 'k5l1AkTLvjA', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2004 Essay', 'Mahen Jecob'),
    (4, 'ivmWAy80i_8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 1987 Essay', 'Mahen Jecob'),
    (4, 'UqZYuk0VH_8', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2006 Essay', 'Mahen Jecob'),
    (4, 'z-dhD2MP7dc', 'No. Zero Physics | තාප භෞතිකය | Thermal Physics | 2013 Structured Essay', 'Mahen Jecob'),
    (4, 'qECdPu9h46A', 'තාප භෞතිකය | Thermal Physics | 1989 Essay', 'Mahen Jecob'),
    (4, '5b2R-9cax94', 'තාප භෞතිකය | Thermal Physics | 1986 Essay', 'Mahen Jecob'),
    (4, 'PLBmjEhfHqU', 'තාප භෞතිකය | Thermal Physics | 1968 Essay', 'Mahen Jecob'),
    (4, 'oQu8vOFbYIA', 'තාප භෞතිකය | Thermal Physics | 1966 Essay', 'Mahen Jecob'),
    (4, 'kXxZD3iq5O0', 'තාප භෞතිකය | Thermal Physics | 1948 Essay', 'Mahen Jecob'),
    (4, 'TYi5k5EFG8I', 'තාප භෞතිකය | Thermal Physics | 2015 Essay', 'Mahen Jecob'),
    (4, 'aAsKN0GdHdg', 'තාප භෞතිකය | තාපමිතිය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'c41__76gmtk', 'තාප භෞතිකය | උෂ්ණත්වමිතිය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, '6a4FaD3iAgc', 'තාප භෞතිකය | ඝන ද්\u200dරව්\u200dයවල ප්\u200dරසාරණය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'VbN2B9l4qHs', 'තාප භෞතිකය | ද්\u200dරව ප්\u200dරසාරණය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'OuvJlzOIZ4Q', 'තාප භෞතිකය | වායුවල හැසිරීම් සහ චාලක වාදය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'riTl0cYsU0Q', 'තාප භෞතිකය | තාප ගති විද්\u200dයාව | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'H1ky1F19ru4', 'තාප භෞතිකය | වාෂ්ප ගුණ සහ ආර්ද්\u200dරතාමිතිය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'np7kwj1PkqM', 'තාප භෞතිකය | අවස්ථා විපර්\u200dයාස | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'urCLyFrWsfc', 'තාප භෞතිකය | තාප සන්නායකතාව | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
    (4, 'BMr5_np26_0', 'තාප භෞතිකය | තාප සංවහනය | පසුගිය විභාග බහුවරණ විවරණය | Thermal Physics – Past Paper MCQ', 'Mahen Jecob'),
]
# ---- BULK 4: Unit 5 Gravitational Field (Mahen Jecob theory + past papers)
BULK4 = [
    (5, 'LJieyML6ZgQ', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර සිද්ධාන්ත – 01 කොටස (Gravitational Fields – Theory Part 1) | 2025 Theory', 'Mahen Jecob'),
    (5, 'yFwgF8avpdA', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර සිද්ධාන්ත – 01 කොටස (Gravitational Fields – Theory Part 1, 2nd Upload) | 2025 Theory', 'Mahen Jecob'),
    (5, 'QPPbAhFe49M', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර සිද්ධාන්ත – 02 කොටස (Gravitational Fields – Theory Part 2) | 2025 Theory', 'Mahen Jecob'),
    (5, 'DigqK4d_hEA', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 1991', 'Mahen Jecob'),
    (5, 'BLVOKhCsRr0', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 1998', 'Mahen Jecob'),
    (5, 'g66iBq5-Ygk', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2003 Essay', 'Mahen Jecob'),
    (5, 'ySWVpBDml_w', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2008 Essay', 'Mahen Jecob'),
    (5, 'S3Ph0ML6pg0', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2011', 'Mahen Jecob'),
    (5, 'C98aL5ifNPY', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2013', 'Mahen Jecob'),
    (5, 'ixfOk1Y_U0k', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2017', 'Mahen Jecob'),
    (5, 'OxFld_AYTN8', 'Electric Fields | 1993 Essay', 'Mahen Jecob'),
    (5, 'PUsmrg6W-Lw', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2022 Essay', 'Mahen Jecob'),
    (5, '6Ir7RCZ3_4c', 'ගුරුත්වාකර්ෂණ ක්ෂේත්\u200dර | Gravitational Fields | 2025 Essay', 'Mahen Jecob'),
]
# ---- BULK 5: Units 6-8 packs (Amith Pussella, Mahen Jecob, Darshana, Aruna, Ushan, Anuradha)
BULK5 = [
    (6, '56jCxZ1BhCM', 'විද්\u200dයුත් ක්ෂේත්\u200dර සම්පූර්ණ ඒකකයේ සාරාංශය (Electric Fields – Full Unit Summary in 1.5h)', 'Aruna Pallekumbura'),
    (6, 'ID6OjT9GgeQ', 'ස්ථිති විද්\u200dයුතය ආරම්භය / / Electrostatics DAY 1', 'Amith Pussella'),
    (6, 'HnC6NyBLyA0', 'ස්ථිති විද්\u200dයුත් ආරෝපණ සහ කුලෝම් නියමය (දෙවන දවස) / Electrostatics DAY 02', 'Amith Pussella'),
    (6, 'e6Jk1oX5pwE', 'ස්ථිති විද්\u200dයුත් ආරෝපණ සහ කුලෝම් නියමය (තුන්වන දවස) / Electrostatics DAY 03', 'Amith Pussella'),
    (6, '6UEGdk_GL6k', 'ස්ථිති විද්\u200dයුත් ක්ෂේත්\u200dරයක් තුල ආරෝපිත අංශුන්ගේ චලිතය / Electrostatics DAY 04', 'Amith Pussella'),
    (6, 'UCKs3xdf6ek', 'ස්ථිති විද්\u200dයුත් ක්ෂේත්\u200dරයක් තුල ආරෝපිත අංශුන්ගේ චලිතය (දෙවන දවස) / Electrostatics DAY 05', 'Amith Pussella'),
    (6, 'rjhxEbbl2o8', 'ස්ථිති විද්\u200dයුත් ස්\u200dරාවය සහ ගවුස් ප්\u200dරමේයය (පළමු දවස) - Electrostatics DAY 6', 'Amith Pussella'),
    (6, 'Tvp3Xqpwj8Q', 'ස්ථිති විද්\u200dයුත් ස්\u200dරාවය සහ ගවුස් ප්\u200dරමේයය දෙවන දවස / Electrostatics DAY 7', 'Amith Pussella'),
    (6, 'VhI5UQ5aNmc', 'ස්ථිති විද්\u200dයුත් විභවය පළමු දවස / Electrostatics', 'Amith Pussella'),
    (6, 'fUEdVzYLYNY', 'ස්ථිති විද්\u200dයුත් විභවය දෙවන දවස / Electrostatics', 'Amith Pussella'),
    (6, 's5MAdGigaw8', 'ස්ථිති විද්\u200dයුත් ධාරිතාවය සහ ධාරිත්\u200dරක පළමු දවස / Electrostatics', 'Amith Pussella'),
    (6, 'z9HwgArgzEs', 'ස්ථිති විද්\u200dයුත් ධාරිතාවය සහ ධාරිත්\u200dරක දෙවන දවස / Electrostatics', 'Amith Pussella'),
    (6, 'ORYCHlgt3FU', 'ස්ථිති විද්\u200dයුත් ධාරිතාවය සහ ධාරිත්\u200dරක තුන්වන දවස / Electrostatics', 'Amith Pussella'),
    (6, 'YV_Ba3POy_I', 'ස්ථිති විද්\u200dයුත් ධාරිතාවය සහ ධාරිත්\u200dරක හතරවන දවස / Electrostatics', 'Amith Pussella'),
    (6, 'hWkWUt-qazA', 'Electric Fields | 1992 MCQ No. 32', 'Mahen Jecob'),
    (6, 'idbPGy0cyw4', 'Electric Fields | 2009 MCQ No. 48', 'Mahen Jecob'),
    (6, 'cXYwmaFU4g0', 'Electric Fields | 2008 MCQ No. 48', 'Mahen Jecob'),
    (6, 'iPDtOkyy8aw', 'Electric Fields | 2004 MCQ No. 45', 'Mahen Jecob'),
    (6, '44e-MOBYq0M', 'Electric Fields | 2003 MCQ No.36', 'Mahen Jecob'),
    (6, 'GNrcmKntCnU', 'Electric Fields | 1998 MCQ No. 45', 'Mahen Jecob'),
    (6, 'MfIQdubhej0', 'Electric Fields | 2013 MCQ No.28', 'Mahen Jecob'),
    (6, 'coCw8WOMroQ', 'Electric Fields | 2000 MCQ No. 24', 'Mahen Jecob'),
    (6, 'rmDJMJt1xTw', 'Electric Fields | 1982 MCQ', 'Mahen Jecob'),
    (6, 'ISUIgblT3uc', 'Electric Fields | 2011 MCQ No. 46', 'Mahen Jecob'),
    (6, 'zcXzpAxidLA', 'Electric Fields | 1985 MCQ', 'Mahen Jecob'),
    (6, 'CnJ3he3UgMM', 'Electric Fields | 1993 MCQ No. 18', 'Mahen Jecob'),
    (6, 'gloYVzN0Jc4', 'Electric Fields | 2010 MCQ No. 46', 'Mahen Jecob'),
    (6, 'an71JD8cGvo', 'Electric Fields | 1996 MCQ No. 28', 'Mahen Jecob'),
    (6, 'unSTz5xp_Vs', 'Electric Fields | 2011 (Old) MCQ No. 31', 'Mahen Jecob'),
    (6, 'nPOSgHdUS4g', 'Electric Fields | 1983 MCQ', 'Mahen Jecob'),
    (6, 'TeWoWZ_-NTU', 'Electric Fields | 1999 MCQ No. 37', 'Mahen Jecob'),
    (6, '9q8C79E7LNc', 'Electric Fields | 2009 MCQ No. 47', 'Mahen Jecob'),
    (6, 'SZjEoIytxts', 'Electric Fields | 1985 MCQ', 'Mahen Jecob'),
    (6, 'aMVlIwiR9iE', 'Electric Fields | 2019 MCQ No. 21', 'Mahen Jecob'),
    (6, 'QsmYmGGNVY4', 'Electric Fields | 1994 MCQ No. 57', 'Mahen Jecob'),
    (6, 'xe_BrmFyYSY', 'Electric Fields | 1989 MCQ No. 36', 'Mahen Jecob'),
    (6, 'TxZ8Bva337M', 'Electric Fields | 2019 MCQ No. 17', 'Mahen Jecob'),
    (6, 'y6Y9qH0Qy5A', 'Electric Fields | 2007 MCQ No. 12', 'Mahen Jecob'),
    (6, 'Xd9SlpSwBqw', 'Electric Fields | 2005 MCQ No. 55', 'Mahen Jecob'),
    (6, '1KfESFbtMd0', 'Electric Fields | 1996 MCQ No. 57', 'Mahen Jecob'),
    (6, 'QyNif2vUlH4', 'Electric Fileds | 2010 MCQ No. 26', 'Mahen Jecob'),
    (6, 'RZq8EWjDyIw', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 1992 MCQ No. 12', 'Mahen Jecob'),
    (6, 'cKuQLYf33LE', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2001 MCQ No. 09', 'Mahen Jecob'),
    (6, 'vtv8SmmDsZI', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 1998 MCQ No. 46', 'Mahen Jecob'),
    (6, 'Q4w0bzaqgyE', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 1996 MCQ No. 49', 'Mahen Jecob'),
    (6, 'p_tiKgQ5l5c', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2008 MCQ No. 57', 'Mahen Jecob'),
    (6, 'nPZJRYneygg', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1989 MCQ No. 14', 'Mahen Jecob'),
    (6, 'H0xhq2sIezE', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1982 MCQ No. 34', 'Mahen Jecob'),
    (6, 'OmecOIKqjts', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1992 MCQ No. 47 + 48', 'Mahen Jecob'),
    (6, 'bbtMtDC0h2o', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2006 MCQ No. 37', 'Mahen Jecob'),
    (6, 'ny2PFChNt9I', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2009 MCQ No. 46', 'Mahen Jecob'),
    (6, 'TNqZw1l-FfA', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2011 MCQ No. 48', 'Mahen Jecob'),
    (6, 'aTe-yoPa-yc', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2016 MCQ No. 39', 'Mahen Jecob'),
    (6, 'W_oqevymWBw', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2020 MCQ No. 28', 'Mahen Jecob'),
    (6, 'cBZhij0ZaqM', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1991 MCQ No.60', 'Mahen Jecob'),
    (6, 'Y3DcwNjc2LQ', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1995 MCQ No.44', 'Mahen Jecob'),
    (6, 'syeBY60QHN8', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1996 MCQ No.27', 'Mahen Jecob'),
    (6, 'XVXFJFsY6XE', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2007 MCQ No.60', 'Mahen Jecob'),
    (6, 'Aeoi1xaN29A', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2010 MCQ No.16', 'Mahen Jecob'),
    (6, 'XAzkhmiynVY', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2014 MCQ No.08', 'Mahen Jecob'),
    (6, 'pyY5fQfFers', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1985 MCQ', 'Mahen Jecob'),
    (6, '2TgoTvzM3tA', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1986 MCQ', 'Mahen Jecob'),
    (6, '0U1UrvyipqI', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1996 MCQ', 'Mahen Jecob'),
    (6, 'oGuFGIWfP-4', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1997 MCQ', 'Mahen Jecob'),
    (6, '8xkGnfABkZ8', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1988 MCQ', 'Mahen Jecob'),
    (6, 'VXH9h32SfIk', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2017 MCQ', 'Mahen Jecob'),
    (6, 'nhUT0c9EIAc', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2018 MCQ', 'Mahen Jecob'),
    (6, '2hOj5dAZR40', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2019 MCQ', 'Mahen Jecob'),
    (6, 'J_ek2JnMoMw', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |2020 MCQ', 'Mahen Jecob'),
    (6, 'QBBvLjknagk', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1985 MCQ', 'Mahen Jecob'),
    (6, '7riVseZ_Uf8', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1983 MCQ', 'Mahen Jecob'),
    (6, '4TU2EZnuitg', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1987 MCQ', 'Mahen Jecob'),
    (6, 'N18dJMpxyE8', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field |1995 MCQ', 'Mahen Jecob'),
    (6, 'a_yAGAoMzC4', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2000 MCQ', 'Mahen Jecob'),
    (6, 'bmakzwU3QQ8', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2002 MCQ', 'Mahen Jecob'),
    (6, 'Qh2VIL8XFuI', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2011 MCQ', 'Mahen Jecob'),
    (6, '_65b6jgM_AI', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2012 MCQ', 'Mahen Jecob'),
    (6, 'tGaU5JItHiQ', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2013 MCQ', 'Mahen Jecob'),
    (6, 'h4hju91vTog', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2015 MCQ', 'Mahen Jecob'),
    (6, 'QKPrTyELM-o', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2018 MCQ', 'Mahen Jecob'),
    (6, 'dy_X1rOu__c', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2020 MCQ', 'Mahen Jecob'),
    (6, 'QERVQ9oQ-EY', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2000 MCQ', 'Mahen Jecob'),
    (6, 'qyRkSXgltFc', 'විද්\u200dයුත් ක්ෂේත්\u200dර | Electric Field | 2020 MCQ', 'Mahen Jecob'),
    (7, 'MprtOXg0J-Q', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත -01(Magnetic Fields 01)', 'Dr Darshana Ukuwela'),
    (7, 'CaIBbTZFeiI', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත -02 (Magnetic Fields 02)', 'Dr Darshana Ukuwela'),
    (7, '3vij75UuLOY', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත -03 (Magnetic Fields 03)', 'Dr Darshana Ukuwela'),
    (7, 'dBD4a_2wG8o', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 04 (Magnetic Fields 04)', 'Dr Darshana Ukuwela'),
    (7, 'n1R8W5rp8ek', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 05 (Magnetic Fields 05)', 'Dr Darshana Ukuwela'),
    (7, 'TSDzUWRNqsc', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 06 (Magnetic Fields 06)', 'Dr Darshana Ukuwela'),
    (7, 'j5vkrcu2sw0', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 07 (Magnetic Fields 07)', 'Dr Darshana Ukuwela'),
    (7, 'blDefrgQNQo', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 08 (Magnetic Fields 08)', 'Dr Darshana Ukuwela'),
    (7, 'eSZKDkvBblU', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 09 (Magnetic Fields 09)', 'Dr Darshana Ukuwela'),
    (7, '5UTWK-GmWhA', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 10 (Magnetic Fields 10)', 'Dr Darshana Ukuwela'),
    (7, 'lJV4FB8aNzM', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 11 (Magnetic Fields 11)', 'Dr Darshana Ukuwela'),
    (7, 'egg6XlKF41U', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 12 (Magnetic Fields 12)', 'Dr Darshana Ukuwela'),
    (7, '7J9wvcGtK60', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 13 (Magnetic Fields 13)', 'Dr Darshana Ukuwela'),
    (7, '7J9wvcGtK60', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 13 (Magnetic Fields 13)', 'Dr Darshana Ukuwela'),
    (7, 'HzWfKLq6OvY', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 14 (Magnetic Fields 14)', 'Dr Darshana Ukuwela'),
    (7, 'ENQHcUs2VUc', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 15 (Magnetic Fields 15)', 'Dr Darshana Ukuwela'),
    (7, '9VRjHhgCqlw', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 16 (Magnetic Fields 16)', 'Dr Darshana Ukuwela'),
    (7, 'QuZJuF93Zn8', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 18 (Magnetic Fields 18)', 'Dr Darshana Ukuwela'),
    (7, '7qNZZdJQhH4', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 19 (Magnetic Fields 19)', 'Dr Darshana Ukuwela'),
    (7, 'veHZSQilMZY', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 20 (Magnetic Fields 20)', 'Dr Darshana Ukuwela'),
    (7, 'ZmYWP7rm4Ec', 'චුම්බක ක්ෂේත්\u200dර සිද්ධාන්ත 21 (Magnetic Fields 21)', 'Dr Darshana Ukuwela'),
    (7, 'utFw5oduboQ', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2004 MCQ', 'Mahen Jecob'),
    (7, 'b1OjXd7tdB4', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2010 MCQ', 'Mahen Jecob'),
    (7, 'Di_e2t3mxIQ', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2020 MCQ', 'Mahen Jecob'),
    (7, '1H14duLSjkw', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2003 MCQ', 'Mahen Jecob'),
    (7, 'nwKyadj8La8', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2001 MCQ', 'Mahen Jecob'),
    (7, 'oVSaf7mt5n4', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2000 MCQ', 'Mahen Jecob'),
    (7, '4GOFwqDgyrI', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 1986 MCQ', 'Mahen Jecob'),
    (7, 'PUAkwd3dWTY', 'Magnetic Fields | 2019 MCQ No. 44', 'Mahen Jecob'),
    (7, 'FW2NdTbR_FY', 'Magnetic Fields | 1993 MCQ No. 19', 'Mahen Jecob'),
    (7, 'Rv9m-Fj2JCg', 'Magnetic Fields | 2011 MCQ No. 35', 'Mahen Jecob'),
    (7, 'qczKMmRRLzo', 'Magnetic Fields | 2014 MCQ No. 29', 'Mahen Jecob'),
    (7, 'TNNi3Nu7ymA', 'Magnetic Fields | 2002 MCQ No. 55', 'Mahen Jecob'),
    (7, 'eSAPkYBQCik', 'Magnetic Fields | 2018 MCQ No. 48', 'Mahen Jecob'),
    (7, 'kxSrc9NUuFs', 'Magnetic Fields | 1997 MCQ No. 56', 'Mahen Jecob'),
    (7, 'do-nVVHcdTE', 'Magnetic Fields | 2008 MCQ No. 36', 'Mahen Jecob'),
    (7, 'c_OGDQXnDh4', 'Magnetic Fields | 2011 (old) MCQ No. 54', 'Mahen Jecob'),
    (7, 'RjsJSWE1R64', 'Magnetic Fields | 2012 (new) MCQ No. 49', 'Mahen Jecob'),
    (7, 'FIGR_FardO4', 'Magnetic Fields | 1998 MCQ No. 54', 'Mahen Jecob'),
    (7, 'UTrqbjlvM_g', 'Magnetic Fields | 2016 MCQ No. 49', 'Mahen Jecob'),
    (7, 'pV0bSM02Pj8', 'Magnetic Fields | 2019 MCQ No. 48', 'Mahen Jecob'),
    (7, 'KJR4cp9Aj4A', 'Magnetic Fields | 2014 MCQ No. 27', 'Mahen Jecob'),
    (7, 'S_R6OdpwxgM', 'Magnetic Fields | 2013 MCQ No. 38', 'Mahen Jecob'),
    (7, 'atiZ1ijBFCs', 'Magnetic Fields | 1994 MCQ No. 50', 'Mahen Jecob'),
    (7, 'uM2doJXFNGQ', 'Magnetic Fields | 2010 MCQ No. 34', 'Mahen Jecob'),
    (7, '9VySdSUafrQ', 'Magnetic Fields | 2000 MCQ No. 12', 'Mahen Jecob'),
    (7, 'awYms-RcwLw', 'Magnetic Fields | 2004 MCQ No. 58', 'Mahen Jecob'),
    (7, 'F0mOGjD7460', 'Magnetic Fields | 2001 MCQ No. 26', 'Mahen Jecob'),
    (7, 'XQZzBV-P5bM', 'Magnetic Fields | 2000 MCQ No. 15', 'Mahen Jecob'),
    (7, '-Ptakqy1-58', 'Magnetic Fields | 2009 MCQ No. 24', 'Mahen Jecob'),
    (7, '87l1oR2MyEw', 'Magnetic Fields | 2009 MCQ No. 58', 'Mahen Jecob'),
    (7, 'vV0EaF7p4wA', 'Magnetic Fields | 2005 MCQ No. 47', 'Mahen Jecob'),
    (7, 'xP30c1zzYl8', 'Magnetic Fields | 2003 MCQ No. 59', 'Mahen Jecob'),
    (7, 'W0M5VtArQpg', 'Magnetic Fields | 2007 MCQ No. 55', 'Mahen Jecob'),
    (7, '_OM6nm7ldvg', 'Magnetic Fileds | 1988 MCQ No. 32', 'Mahen Jecob'),
    (7, 'DWuMEOF9fjo', 'Magnetic Fields | 2006 Structured Essay', 'Mahen Jecob'),
    (7, 'HKVWqwrXvBI', 'Magnetic Fields | 2000 Essay', 'Mahen Jecob'),
    (7, 'uecSWAzZXKQ', 'Magnetic Fields | 2010 Essay', 'Mahen Jecob'),
    (7, 'XUwLDbyH8I4', 'Magnetic Fields | 1994 Essay', 'Mahen Jecob'),
    (7, 'f3eM34ELyxs', 'Magnetic Fields | 1995 Essay', 'Mahen Jecob'),
    (7, 'HFTTXRCcNgA', 'Magnetic Fields | 1988 Structured Essay', 'Mahen Jecob'),
    (7, '3m-Zp_KNRQM', 'Magnetic Fields | 1995 Essay', 'Mahen Jecob'),
    (7, 'JZzZDniK2-E', 'Magnetic Fields | 2019 Essay', 'Mahen Jecob'),
    (7, 'OFDVp6S4kA0', 'Magnetic Fields | 1985 Essay', 'Mahen Jecob'),
    (7, 'qiakyjtt3wA', 'Magnetic Fields | 1997 Essay', 'Mahen Jecob'),
    (7, 'T_7kJe7RXIE', 'Magnetic Fields | 1996 Essay', 'Mahen Jecob'),
    (7, 'OxFld_AYTN8', 'No.Zero Physics | Electric Fields | 1993 Essay', 'Mahen Jecob'),
    (7, 'RgWutDjayQw', 'No. Zero Physics | Magnetic Fields | 1986 Essay', 'Mahen Jecob'),
    (7, 'EfEgDunuDPY', 'No. Zero Physics | Magnetic Fields | 2014 Essay', 'Mahen Jecob'),
    (7, 'NMC2BrPV9V4', 'No. Zero Physics | Magnetic Fields 2018 Essay', 'Mahen Jecob'),
    (7, 'cUSvEmUSW6M', 'No. Zero Physics | Magnetic Fields | 1979 Structured Essay', 'Mahen Jecob'),
    (7, 'm_QaNnJbtsg', 'No. Zero Physics | Magnetic Fields | 2004 Structured Essay', 'Mahen Jecob'),
    (7, 'xKjx2SqJXS8', 'No. Zero Physics | Magnetic Fields | 1984 Structured Essay', 'Mahen Jecob'),
    (7, 'XYMcFjMtp7M', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2021 Essay', 'Mahen Jecob'),
    (7, '1W14FEkK0hk', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2002 Essay', 'Mahen Jecob'),
    (7, 'yKsOGs7_k_U', 'චුම්බක ක්ෂේත්\u200dර | Magnetic Fields | 2024 Essay', 'Mahen Jecob'),
    (7, 'wuliq1_vRrg', 'No. Zero Physics | Magnetic Fields | 1990 Structured Essay', 'Mahen Jecob'),
    (7, 'orkO--lOWPE', 'විද්\u200dයුත් චුම්බකත්වය සහ විද්\u200dයුත් චුම්බක ප්\u200dරේරණය – සම්පූර්ණයෙන්ම් (Magnetism & Electromagnetic Induction – Full Lesson)', 'Ushan Gunasekara'),
    (7, 'QI5Pl1FM-Xg', 'චුම්බක ක්ෂේත්\u200dර සම්පූර්ණ ඒකකයේ සාරාංශය (Magnetic Fields – Full Unit Summary)', 'Aruna Pallekumbura'),
    (8, 'Zu6shi9ngjc', 'ධාරා විද්\u200dයුතය ආරම්භය 2026 REVISION', 'Anuradha Perera'),
    (8, 'A-nxvH4xcrA', 'ධාරා විද්\u200dයුතය ප්\u200dරතිරෝද පද්ධති 2026 REVISION', 'Anuradha Perera'),
    (8, 'LgVdfQ69YYM', 'ධාරා විද්\u200dයුතය කෝෂ ආරම්භය 2026 REVISION', 'Anuradha Perera'),
    (8, '5-v-glLs42g', 'ධාරා විද්\u200dයුතය කෝෂ ආරම්භය 2026 REVISION', 'Anuradha Perera'),
    (8, 'qtnes4rPzTg', 'ධාරා විද්\u200dයුත්\u200dය කර්චොෆ් ආරම්භය සහ සම්පූර්ණ පාඩම 2026 REVISION', 'Anuradha Perera'),
    (8, 'QDS7Hp-fMqs', 'ධාරා විද්\u200dයුතය සම්බන්ධ උපකරණ භාවිතය 2026 PHYSICS | ANURADHA PERERA', 'Anuradha Perera'),
    (8, 'p82ZvXHhDlk', 'ධාරා විද්\u200dයුතය තාපන ඵලය 2026 PHYSICS | ANURADHA PERERA', 'Anuradha Perera'),
    (8, 'wzOaj0ckxTY', 'ධාරා විද්\u200dයුතය මීටර් සේතුව විභවමානය සම්පූර්ණ පාඩම ආවරණය 2026 PHYSICS | ANURADHA PERERA', 'Anuradha Perera'),
    (8, 'R3T8ecrCwSw', 'ධාරා විද්\u200dයුතය - Part 1.විද්\u200dයුත් ධාරාව, ඕම් නියමය සහ ප්\u200dරතිරෝධ පද්ධති', 'Amith Pussella'),
    (8, '89aTO4ijVik', 'ධාරා විද්\u200dයුතය - Part 2.ප්\u200dරතිරෝධ පද්ධති', 'Amith Pussella'),
    (8, '3gEOQyaUs8c', 'ධාරා විද්\u200dයුතය - Part 3.විද්\u200dයුත් කෝෂ සහ සරල පූර්ණ පරිපථ', 'Amith Pussella'),
    (8, 'JPfjTtTgnUA', 'ධාරා විද්\u200dයුතය - Part 4.විද්\u200dයුත් ධාරාවක තාපන ඵලය', 'Amith Pussella'),
    (8, 'NgRo6j-2W0s', "ධාරා විද්\u200dයුතය - Part 5.ක'චොෆ් නියම", 'Amith Pussella'),
    (8, 'BzQDGjy7DbU', 'ධාරා විද්\u200dයුතය - Part 6 ගැල්වනෝමීටර මුලධර්මය', 'Amith Pussella'),
    (8, '_fjdoHTF_aE', 'ධාරා විද්\u200dයුතය - Part 7. විට්සන් සේතුව, මීටර සේතුව හා විභවමානය', 'Amith Pussella'),
]


def main():
    if not os.path.exists(DB):
        print('ERROR: database not found at ' + DB)
        print('Start the website once first (it creates the database), then run this again.')
        return 1

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    subj = db.execute("SELECT id FROM subjects WHERE name='Physics'").fetchone()
    if not subj:
        print('ERROR: Physics subject not found. Start the website once and re-run.')
        return 1
    sid = subj['id']

    # 4) merge duplicate/leftover units deterministically (older installs had
    #    English-name doubles; check by english-prefix, keep most-lessons unit)
    def _ekey(nm):
        return nm.split(' \u2013 ')[0].strip().lower()
    all_units = db.execute('SELECT id,name FROM units WHERE subject_id=? ORDER BY id', (sid,)).fetchall()
    for canon_ord, canon_name in enumerate(UNITS, start=1):
        ek = _ekey(canon_name)
        group = [u for u in all_units if _ekey(u['name']) == ek]
        if not group:
            continue
        def _nl(u):
            return db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (u['id'],)).fetchone()['c']
        keep = max(group, key=lambda u: (_nl(u), '\u2013' in u['name'], -u['id']))
        for u in group:
            if u['id'] == keep['id']:
                continue
            db.execute('UPDATE lessons SET unit_id=? WHERE unit_id=?', (keep['id'], u['id']))
            db.execute('UPDATE resources SET lesson_id=NULL WHERE lesson_id IN (SELECT id FROM lessons WHERE unit_id=?)', (u['id'],))
            db.execute('DELETE FROM units WHERE id=?', (u['id'],))
            print('   merged duplicate unit: "' + u['name'] + '"  ->  "' + keep['name'] + '"')
        db.execute('UPDATE units SET name=?, ord=? WHERE id=?', (canon_name, canon_ord, keep['id']))

    # 2) Make sure all 11 units exist + rename them to bilingual titles
    unit_id = {}
    for ord_val, name in enumerate(UNITS, start=1):
        row = db.execute('SELECT id,name FROM units WHERE subject_id=? AND ord=?', (sid, ord_val)).fetchone()
        if not row:
            cur = db.execute('INSERT INTO units (subject_id,name,ord) VALUES (?,?,?)', (sid, name, ord_val))
            unit_id[ord_val] = cur.lastrowid
        else:
            if row['name'] != name:
                db.execute('UPDATE units SET name=? WHERE id=?', (name, row['id']))
            unit_id[ord_val] = row['id']
    print('OK Physics now has ' + str(len(UNITS)) + ' bilingual units')

    # 3) fix old lesson titles that had made-up / typo Sinhala
    TITLE_FIX = {
        'E7QbzysxmyE': "Newton\u2019s Cradle",
        'DZEfX4NFDLg': 'Flash Practicals 01 \u2013 \u0dc0\u0dbb\u0dca\u0db1\u0dd2\u0dba\u0dbb\u0dca \u0d9a\u0dd0\u0dbd\u0dd2\u0db4\u0dbb\u0dba (Vernier Caliper)',
    }
    for _vid, _t in TITLE_FIX.items():
        db.execute('UPDATE lessons SET title=? WHERE youtube_id=? AND title<>?', (_t, _vid, _t))

    # 2) Teachers (create if missing)
    teacher_cache = {}
    def tid_for(name):
        if name in teacher_cache:
            return teacher_cache[name]
        row = db.execute('SELECT id FROM teachers WHERE name=?', (name,)).fetchone()
        if row:
            teacher_cache[name] = row['id']
            return row['id']
        cur = db.execute('INSERT INTO teachers (name,bio,subjects) VALUES (?,?,?)',
                         (name, 'Popular G.C.E. A/L Physics teacher (video lessons).', 'Physics'))
        teacher_cache[name] = cur.lastrowid
        return cur.lastrowid

    # 3) Add video lessons, skipping duplicates
    existing = {r['youtube_id'] for r in db.execute("SELECT youtube_id FROM lessons").fetchall() if r['youtube_id']}
    added = skipped = 0
    for ord_unit, vid, title, teacher in LESSONS + BULK + BULK2 + BULK3 + BULK4 + BULK5:
        if vid in existing:
            skipped += 1
            continue
        u_id = unit_id[ord_unit]
        count = db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (u_id,)).fetchone()['c']
        unit_name = UNITS[ord_unit - 1]
        desc = ('G.C.E. A/L Physics video lesson. Unit: ' + unit_name + '. Taught by ' + teacher +
                '.\nG.C.E. \u0d92/\u0dbd\u0dca \u0dad\u0dd9\u0dc0\u0dd2\u0dbd\u0dca \u0dc0\u0dd3\u0daf\u0dd2\u0dba\u0ddd \u0db4\u0dcf\u0da9\u0db8. \u0d92\u0d9a\u0d9a\u0dba: ' + unit_name + '.')
        db.execute('INSERT INTO lessons (unit_id,teacher_id,title,description,youtube_id,notes,ord) VALUES (?,?,?,?,?,?,?)',
                   (u_id, tid_for(teacher), title, desc, vid, '', count + 1))
        existing.add(vid)
        added += 1

    # cosmetic: collapse double slashes left by teacher-name stripping in titles
    db.execute("UPDATE lessons SET title = REPLACE(title, ' / / ', ' / ') WHERE title LIKE '%/ / %'")

    db.commit()

    print('')
    print('New lessons added: ' + str(added) + '   |   duplicates skipped: ' + str(skipped))
    print('')
    print('Physics units now:')
    for ord_val, name in enumerate(UNITS, start=1):
        c = db.execute('SELECT COUNT(*) c FROM lessons WHERE unit_id=?', (unit_id[ord_val],)).fetchone()['c']
        if c:
            print('   ' + str(ord_val).rjust(2) + '. ' + name + '  ->  ' + str(c) + ' lessons')
    db.close()
    print('')
    print('DONE! Start the website again and press Ctrl+F5:')
    print('   http://localhost:3000/#/subject/4')


if __name__ == '__main__':
    raise SystemExit(main())
