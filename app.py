import streamlit as st
import math
import datetime
import zoneinfo
import random

# Utility functions
def rev(angle):
    return angle - math.floor(angle / 360) * 360

# Julian Date calculation
def julian_date(year, month, day, hour=0, minute=0, second=0):
    if month == 1 or month == 2:
        yearp = year - 1
        monthp = month + 12
    else:
        yearp = year
        monthp = month
    
    if year < 1582 or (year == 1582 and (month < 10 or (month == 10 and day < 15))):
        B = 0
    else:
        A = math.floor(yearp / 100)
        B = 2 - A + math.floor(A / 4)
    
    C = math.floor(365.25 * (yearp + 4716))
    D = math.floor(30.6001 * (monthp + 1))
    jd = B + day + C + D - 1524.5
    jd += (hour + minute / 60.0 + second / 3600.0) / 24.0
    return jd

# Calculate Sun's ecliptic longitude
def calculate_sun_longitude(d):
    w = 282.9404 + 4.70935e-5 * d
    e = 0.016709 - 1.151e-9 * d
    M = rev(356.0470 + 0.9856002585 * d)
    Mrad = math.radians(M)
    E = M + math.degrees(e * math.sin(Mrad) * (1.0 + e * math.cos(Mrad)))
    Erad = math.radians(E)
    xv = math.cos(Erad) - e
    yv = math.sin(Erad) * math.sqrt(1.0 - e*e)
    v = math.degrees(math.atan2(yv, xv))
    lonsun = rev(v + w)
    return lonsun

# Improved Moon's ecliptic longitude calculation
def calculate_moon_longitude(d):
    T = d / 36525.0
    L0 = 218.31617 + 481267.88088 * T - 4.06 * T**2 / 3600.0
    M = 134.96292 + 477198.86753 * T + 33.25 * T**2 / 3600.0
    MSun = 357.52543 + 35999.04944 * T - 0.58 * T**2 / 3600.0
    F = 93.27283 + 483202.01873 * T - 11.56 * T**2 / 3600.0
    D = 297.85027 + 445267.11135 * T - 5.15 * T**2 / 3600.0
    Delta = (22640 * math.sin(math.radians(M))
             + 769 * math.sin(math.radians(2 * M))
             - 4586 * math.sin(math.radians(M - 2 * D))
             + 2370 * math.sin(math.radians(2 * D))
             - 668 * math.sin(math.radians(MSun))
             - 412 * math.sin(math.radians(2 * F))
             - 125 * math.sin(math.radians(D))
             - 212 * math.sin(math.radians(2 * M - 2 * D))
             - 206 * math.sin(math.radians(M + MSun - 2 * D))
             + 192 * math.sin(math.radians(M + 2 * D))
             - 165 * math.sin(math.radians(MSun - 2 * D))
             + 148 * math.sin(math.radians(L0 - MSun))
             - 110 * math.sin(math.radians(M + MSun))
             - 55 * math.sin(math.radians(2 * F - 2 * D))) / 3600.0
    lonecl = rev(L0 + Delta)
    return lonecl

# Lahiri Ayanamsa approximation
def calculate_ayanamsa(jd):
    base_ayan = 23.853  # for J2000
    rate_per_year = 50.2719 / 3600  # degrees per year
    years = (jd - 2451545.0) / 365.25
    ayan = base_ayan + years * rate_per_year
    return ayan

# Calculate approximate ascendant
def calculate_ascendant(jd, lat, lon):
    d = jd - 2451545.0
    eps = 23.439281 - 0.0000004 * d
    gmst = rev(280.46061837 + 360.98564736629 * d)
    lst = rev(gmst + lon + 90)  # Adjustment for sidereal time
    lst_rad = math.radians(lst)
    eps_rad = math.radians(eps)
    lat_rad = math.radians(lat)
    y = math.sin(lst_rad)
    x = math.cos(lst_rad) * math.cos(eps_rad) - math.sin(eps_rad) * math.tan(lat_rad)
    asc_trop = math.degrees(math.atan2(y, x))
    if asc_trop < 0:
        asc_trop += 360
    return asc_trop

# Planetary elements at J2000
planetary_elements = {
    'mercury': {
        'N0': 48.3313, 'N_rate': 3.24587e-5,
        'i0': 7.0047, 'i_rate': 5.00e-8,
        'w0': 29.1241, 'w_rate': 1.01444e-5,
        'a': 0.387098,
        'e0': 0.205635, 'e_rate': 5.59e-10,
        'M0': 168.6562, 'M_rate': 4.0923344368
    },
    'venus': {
        'N0': 76.6799, 'N_rate': 2.46590e-5,
        'i0': 3.3946, 'i_rate': 2.75e-8,
        'w0': 54.8910, 'w_rate': 1.38374e-5,
        'a': 0.723330,
        'e0': 0.006773, 'e_rate': -1.302e-9,
        'M0': 48.0052, 'M_rate': 1.6021302244
    },
    'mars': {
        'N0': 49.5574, 'N_rate': 2.11081e-5,
        'i0': 1.8497, 'i_rate': -1.78e-8,
        'w0': 286.5016, 'w_rate': 2.92961e-5,
        'a': 1.523688,
        'e0': 0.093405, 'e_rate': 2.516e-9,
        'M0': 18.6021, 'M_rate': 0.5240207766
    },
    'jupiter': {
        'N0': 100.4542, 'N_rate': 2.76854e-5,
        'i0': 1.3030, 'i_rate': -1.557e-7,
        'w0': 273.8777, 'w_rate': 1.64505e-5,
        'a': 5.20256,
        'e0': 0.048498, 'e_rate': 4.469e-9,
        'M0': 19.8950, 'M_rate': 0.0830853001
    },
    'saturn': {
        'N0': 113.6634, 'N_rate': 2.38980e-5,
        'i0': 2.4886, 'i_rate': -1.081e-7,
        'w0': 339.3939, 'w_rate': 2.97661e-5,
        'a': 9.55475,
        'e0': 0.055546, 'e_rate': -9.499e-9,
        'M0': 316.9670, 'M_rate': 0.0334442282
    }
}

# Function to get ecliptic longitude for a planet
def get_ecliptic_longitude(d, planet):
    if planet == 'sun':
        return calculate_sun_longitude(d)
    elif planet == 'moon':
        return calculate_moon_longitude(d)
    elif planet == 'rahu':
        N = 125.1228 - 0.0529538083 * d
        return rev(N)
    elif planet == 'ketu':
        return rev(get_ecliptic_longitude(d, 'rahu') + 180)
    else:
        # Compute Sun's position for geocentric correction
        sun_lon = calculate_sun_longitude(d)
        xs = math.cos(math.radians(sun_lon))
        ys = math.sin(math.radians(sun_lon))
        # Planet elements
        el = planetary_elements[planet]
        N = el['N0'] + el['N_rate'] * d
        i = el['i0'] + el['i_rate'] * d
        w = el['w0'] + el['w_rate'] * d
        a = el['a']
        e = el['e0'] + el['e_rate'] * d
        M = rev(el['M0'] + el['M_rate'] * d)
        # Eccentric anomaly E
        E = M + math.degrees(e * math.sin(math.radians(M)) * (1 + e * math.cos(math.radians(M))))
        for _ in range(5):
            E_prev = E
            E = E_prev - (E_prev - math.degrees(e * math.sin(math.radians(E_prev))) - M) / (1 - e * math.cos(math.radians(E_prev)))
            if abs(E - E_prev) < 0.001:
                break
        # True anomaly v and r
        xv = a * (math.cos(math.radians(E)) - e)
        yv = a * math.sqrt(1 - e**2) * math.sin(math.radians(E))
        v = math.degrees(math.atan2(yv, xv))
        r = math.sqrt(xv**2 + yv**2)
        # Heliocentric coordinates
        xh = r * (math.cos(math.radians(N)) * math.cos(math.radians(v + w)) - math.sin(math.radians(N)) * math.sin(math.radians(v + w)) * math.cos(math.radians(i)))
        yh = r * (math.sin(math.radians(N)) * math.cos(math.radians(v + w)) + math.cos(math.radians(N)) * math.sin(math.radians(v + w)) * math.cos(math.radians(i)))
        zh = r * math.sin(math.radians(v + w)) * math.sin(math.radians(i))
        # Geocentric
        xge = xs + xh
        yge = ys + yh
        zge = zh
        # Ecliptic longitude
        lon = math.degrees(math.atan2(yge, xge))
        return rev(lon)

# Get approximate speed for retrograde detection
def get_speed(d, planet):
    dt = 0.01  # small fraction of day
    long1 = get_ecliptic_longitude(d, planet)
    long2 = get_ecliptic_longitude(d + dt, planet)
    delta = (long2 - long1 + 180) % 360 - 180
    return delta / dt

# Dictionary for sign rulers
ruler_of = {
    0: 'mars',  # Aries
    1: 'venus',  # Taurus
    2: 'mercury',  # Gemini
    3: 'moon',  # Cancer
    4: 'sun',  # Leo
    5: 'mercury',  # Virgo
    6: 'venus',  # Libra
    7: 'mars',  # Scorpio
    8: 'jupiter',  # Sagittarius
    9: 'saturn',  # Capricorn
    10: 'saturn',  # Aquarius
    11: 'jupiter'  # Pisces
}

# Deity map from planets for Ishta and Aradhya
deity_map = {
    'sun': 'Shiva or Rama',
    'moon': 'Parvati or Krishna',
    'mars': 'Skanda (Kartikeya) or Narasimha',
    'mercury': 'Vishnu',
    'jupiter': 'Brahma or Guru forms',
    'venus': 'Lakshmi',
    'saturn': 'Shani or Ayyappa',
    'rahu': 'Durga',
    'ketu': 'Ganesha'
}

# Additional map for Aradhya Devata examples
aradhya_map = {
    'mars': 'Hanuman',
    'venus': 'Lakshmi',
    'mercury': 'Durga',
    'sun': 'Surya or Vishnu',
    'moon': 'Chandra or Parvati',
    'jupiter': 'Guru or Brahma',
    'saturn': 'Shani'
}

# Fun descriptions for Devas (shared for Ishta and Aradhya, with imagination)
fun_desc = {
    'Shiva or Rama': '🌟 Cosmic warrior of destruction and devotion! As Shiva or Rama, you channel the dance of creation and the arrow of justice. 🛡️🔥 Imagine leading epic quests, meditating in Himalayan caves, or battling demons with unwavering dharma—your spirit is a whirlwind of transformation and righteousness! 💃🕺🙏 Boundless energy awaits in yoga and chants like "Om Namah Shivaya". ✨',
    'Parvati or Krishna': '💖 Enchanting harmonizer of love and play! With Parvati or Krishna, you embody nurturing grace and flute-melody mischief. 🦚🎶 Picture twirling in divine leelas, fostering eternal bonds, or charming the universe with compassion—your soul thrives on beauty, arts, and heartfelt connections! 🥰🌸 Offer sweets for blessings in romance and creativity. 😄',
    'Skanda (Kartikeya) or Narasimha': '🦁 Fierce guardian of courage and justice! As Skanda or Narasimha, you roar with protective might and spear-sharp determination. ⚔️💥 Envision conquering inner beasts, leading valiant charges, or shielding loved ones like a divine warrior—your path is action-hero epic! 🏆🙌 Chant for victory with red offerings. 🛡️🔥',
    'Vishnu': '🌀 Timeless preserver of balance and avatars! Vishnu guides you through infinite forms, adapting with wisdom and empathy. 🌌📜 Dream of sustaining worlds, helping humanity, or evolving through cosmic cycles—your superpower is harmonious navigation! ❤️🙏 Float on Shesha with "Om Namo Narayanaya" for abundance. 🐍✨',
    'Brahma or Guru forms': '📚 Supreme creator of knowledge and universes! Brahma or Guru inspires innovation, teaching, and profound insights. 🧠🌟 Visualize crafting realities with four-faced vision, mentoring souls, or unlocking cosmic secrets—your mind is a boundless canvas! 🔮🙏 Yellow blooms for intellectual blooms. 🎨✨',
    'Lakshmi': '💰 Radiant bestower of prosperity and beauty! Lakshmi elevates you from lotuses, attracting wealth and elegance effortlessly. 🌺🏆 Fancy rising above muddles with grace, mastering finances, or hosting opulent gatherings—success is your aura! 🎉🪔 Light diyas for riches in all realms. 🌸✨',
    'Shani or Ayyappa': '🪐 Stern teacher of karma and perseverance! Shani or Ayyappa builds your empire through trials and discipline. ⚖️🛠️ Picture conquering mountains of challenges, forging resilience, or reaping long-term rewards—your strength shines in adversity! 💪🙏 Blue petals for justice and transformation. 🏔️🔥',
    'Durga': '🛡️ Invincible slayer of evils and fears! Durga empowers multitasking mastery and tiger-riding courage. 🐅⚔️ Imagine wielding arms against demons, activating boldly, or protecting realms with determination—victory is destined! 🏅🙏 Red hibiscus and "Om Dum Durgayei Namaha" for power. 🐯✨',
    'Ganesha': '🐘 Wise remover of barriers and new beginnings! Ganesha navigates with elephantine smarts and modak-loving joy. 📿🧩 Envision clearing paths, starting ventures, or puzzling through life cleverly—success smiles! 🎉🙏 "Om Gam Ganapataye Namaha" for smooth sails. 🥳✨',
    'Hanuman': '🙏 Devoted servant of strength and loyalty! Hanuman leaps oceans with unwavering faith and monkey-army might. 🐒💪 Fantasize carrying mountains, serving causes, or embodying selfless power—your devotion conquers all! 🏔️🔥 Chant Hanuman Chalisa for boundless vigor. ✨',
    'Surya or Vishnu': '☀️ Radiant life-giver and preserver! Surya or Vishnu illuminates paths with solar energy and avatar wisdom. 🌞🌀 Dream of chariot-riding dawns, sustaining balance, or evolving divinely—your light guides! 📜🙏 Surya Namaskar for vitality. ✨',
    'Chandra or Parvati': '🌙 Gentle nurturer of emotions and grace! Chandra or Parvati soothes with lunar calm and mountainous strength. 🌕❤️ Picture phasing through feelings, fostering homes, or standing firm—your intuition flows! 🌊🙏 Moon gazing for peace. ✨'
}

# Adityas list and fun descriptions (imaginative enhancements)
adityas = ['Dhata', 'Aryama', 'Mitra', 'Varuna', 'Indra', 'Vivasvan', 'Parjanya', 'Amsu', 'Bhaga', 'Tvashta', 'Pusha', 'Vishnu']
aditya_desc = {
    0: '🛠️ Dhata, cosmic creator! Infuse inventions with divine spark, crafting realities like a Vedic architect—dreams manifest wildly! 🚀🌟 Imagine building starships from ether! ✨',
    1: '👑 Aryama, noble ally! Forge bonds with honor, leading realms in harmony—your loyalty builds empires of friendship! ❤️🤝 Picture knightly quests in astral courts! ⚔️',
    2: '🤝 Mitra, eternal friend! Warm alliances bloom, spreading peace across universes—kindness your superpower! 😊🌍 Envision galactic peace summits! 🕊️',
    3: '🌊 Varuna, ocean sage! Dive intuitive depths, mastering emotions like tidal waves—wisdom surges! 🧜‍♂️💧 Fantasize mermaid adventures in cosmic seas! 🌌',
    4: '⚡ Indra, thunder lord! Surge with bravery, conquering storms in epic battles—victory roars! 🏆🌩️ Imagine wielding Vajra against cosmic foes! 💥',
    5: '☀️ Vivasvan, radiant beacon! Inspire growth with solar vitality, energizing worlds—shine eternally! 🌞🌱 Picture sun-dancing in heavenly meadows! 🕺',
    6: '☁️ Parjanya, rain bringer! Shower abundance, nurturing harvests of dreams—bounty flows! 🌧️🌾 Envision cloud-riding to fertile paradises! ☁️',
    7: '💧 Amsu, nectar healer! Spread purity and joy, elixirs of life in simple moments—sweet serenity! 🍯😇 Fantasize ambrosia fountains in Eden! 🌈',
    8: '🌟 Bhaga, fortune sharer! Bless with luck, giving generously for manifold returns—prosperity multiplies! 🎁🍀 Imagine treasure hunts in golden realms! 🏅',
    9: '🔨 Tvashta, master craftsman! Forge artistry and legacies, building beauty eternal—skills divine! 🎨🛠️ Picture sculpting stars in heavenly forges! ⭐',
    10: '🚀 Pusha, growth nourisher! Fuel ambitions to soar, pushing boundaries infinitely—ascend! 📈🌟 Envision rocket rides through astral highways! 🌌',
    11: '🕉️ Vishnu, supreme preserver! Guard balance and evolution, sustaining harmony forever—peace prevails! 🌀🙏 Imagine avatar adventures across yugas! 🐟🐢🦁'
}

# Descriptions for Sun, Moon, Ascendant based on Rashi
descriptions = {
    "Mesha": {
        "sun": "Your soul ignites as an energetic pioneer, fueling bold leadership and vitality! 🌞🚀⚡",
        "moon": "Your mind races with pioneering energy, emotionally charged and impulsive! 🌙🔥🏃‍♂️",
        "asc": "Your personality bursts forth as a fiery pioneer, appearing dynamic and trailblazing! ⬆️🦸‍♂️💥"
    },
    "Vrishabha": {
        "sun": "Your soul grounds as a patient builder, embodying steady strength and endurance! 🌞🏰🌱",
        "moon": "Your mind nurtures with building patience, emotionally stable and sensual! 🌙🛡️🍃",
        "asc": "Your personality presents as a reliable builder, looking calm and materially focused! ⬆️🧱🌿"
    },
    "Mithuna": {
        "sun": "Your soul communicates as a curious explorer, vitalizing intellect and adaptability! 🌞🗣️🔎",
        "moon": "Your mind buzzes with curious communication, emotionally versatile and witty! 🌙💡🌀",
        "asc": "Your personality shines as a social communicator, appearing quick-witted and engaging! ⬆️🎭🌟"
    },
    "Karka": {
        "sun": "Your soul protects as a nurturing guardian, radiating emotional depth and care! 🌞🏡❤️",
        "moon": "Your mind flows with protective nurturing, intuitively sensitive and moody! 🌙🛡️🌊",
        "asc": "Your personality emerges as a caring protector, looking empathetic and home-loving! ⬆️🤗💙"
    },
    "Simha": {
        "sun": "Your soul roars as a confident leader, embodying royal charisma and creativity! 🌞👑🌟",
        "moon": "Your mind leads with confident pride, emotionally dramatic and generous! 🌙🦁🎭",
        "asc": "Your personality commands as a bold leader, appearing sunny and authoritative! ⬆️🏆🔥"
    },
    "Kanya": {
        "sun": "Your soul analyzes as a perfectionist, vitalizing precision and service! 🌞📊🔍",
        "moon": "Your mind critiques with analytical detail, emotionally practical and worrisome! 🌙🧠🛠️",
        "asc": "Your personality details as a meticulous helper, looking organized and humble! ⬆️📋🌿"
    },
    "Tula": {
        "sun": "Your soul balances as a diplomatic harmonizer, radiating fairness and partnerships! 🌞⚖️💕",
        "moon": "Your mind seeks harmony diplomatically, emotionally relational and indecisive! 🌙🤝❤️",
        "asc": "Your personality charms as a graceful mediator, appearing elegant and social! ⬆️🌹🕊️"
    },
    "Vrishchika": {
        "sun": "Your soul transforms intensely, embodying depth, power, and resilience! 🌞🦂🔥",
        "moon": "Your mind probes with intense emotions, intuitively secretive and passionate! 🌙🕵️‍♂️🌊",
        "asc": "Your personality magnetizes as a mysterious transformer, looking intense and probing! ⬆️🔮💥"
    },
    "Dhanu": {
        "sun": "Your soul adventures as a philosopher, vitalizing optimism and exploration! 🌞🏹📜",
        "moon": "Your mind wanders philosophically, emotionally free-spirited and blunt! 🌙🧭😊",
        "asc": "Your personality expands as an enthusiastic seeker, appearing jovial and wise! ⬆️🌍🔥"
    },
    "Makara": {
        "sun": "Your soul achieves with discipline, embodying ambition and responsibility! 🌞🏔️🏆",
        "moon": "Your mind structures with disciplined caution, emotionally reserved and pragmatic! 🌙🛡️⏳",
        "asc": "Your personality climbs as a steadfast achiever, looking serious and determined! ⬆️🧗‍♂️🌿"
    },
    "Kumbha": {
        "sun": "Your soul innovates as a visionary, radiating uniqueness and humanitarianism! 🌞💡🌐",
        "moon": "Your mind rebels with innovative ideas, emotionally detached and eccentric! 🌙🤖🌀",
        "asc": "Your personality networks as a forward-thinker, appearing unconventional and friendly! ⬆️🌟🤝"
    },
    "Meena": {
        "sun": "Your soul dreams compassionately, embodying spirituality and empathy! 🌞🌊✨",
        "moon": "Your mind imagines with dreamy intuition, emotionally sensitive and escapist! 🌙🔮💭",
        "asc": "Your personality flows as a mystical dreamer, looking gentle and artistic! ⬆️🧜‍♀️🌈"
    }
}

# Traits for elemental interplays (dynamic generation)
sun_element_traits = {
    "Fire": "a passionate, leadership-driven purpose that ignites action and boldness 🔥🚀",
    "Earth": "a practical, stable ambition focused on building lasting foundations 🌍🏗️",
    "Air": "an intellectual, innovative vision that soars with ideas and adaptability 🌬️💡",
    "Water": "an empathetic, nurturing goal oriented towards emotional depth and care 💧❤️"
}
moon_element_traits = {
    "Fire": "tempered by fiery, impulsive emotions that fuel quick reactions and enthusiasm 🔥🏃‍♂️",
    "Earth": "grounded in steady, sensual feelings that provide reliability and patience 🌍🍃",
    "Air": "influenced by versatile, witty moods that bring curiosity and social flair 🌬️🌀",
    "Water": "flowing with intuitive, sensitive sentiments that enhance empathy and moodiness 💧🌊"
}
asc_element_traits = {
    "Fire": "presented as dynamic and trailblazing, appearing confident and energetic 🔥💥",
    "Earth": "shown through a calm and organized demeanor, looking grounded and humble 🌍🌿",
    "Air": "expressed with engaging and quick-witted charm, seeming social and unconventional 🌬️🌟",
    "Water": "revealed in an empathetic and gentle manner, appearing home-loving and artistic 💧🧜‍♀️"
}
element_interplay_phrases = {
    ("Fire", "Fire"): "amplifying intensity and drive, but watch for burnout! 🔥🔥",
    ("Fire", "Earth"): "stabilizing passion with practicality for enduring success 🌍🔥",
    ("Fire", "Air"): "fanning flames with ideas, creating innovative sparks 🌬️🔥",
    ("Fire", "Water"): "steaming with emotional depth, balancing heat with sensitivity 💧🔥",
    ("Earth", "Fire"): "igniting steady growth with bold energy 🔥🌍",
    ("Earth", "Earth"): "doubling down on stability, but may resist change 🌍🌍",
    ("Earth", "Air"): "grounding airy thoughts into tangible plans 🌬️🌍",
    ("Earth", "Water"): "nurturing growth like fertile soil, fostering emotional security 💧🌍",
    ("Air", "Fire"): "fueling intellectual pursuits with passionate winds 🔥🌬️",
    ("Air", "Earth"): "anchoring ideas in reality for practical innovation 🌍🌬️",
    ("Air", "Air"): "whirling with endless curiosity, but may lack focus 🌬️🌬️",
    ("Air", "Water"): "blending logic with intuition for creative flows 💧🌬️",
    ("Water", "Fire"): "evaporating into transformative steam, intense yet fluid 🔥💧",
    ("Water", "Earth"): "creating mud-like adaptability, solid yet malleable 🌍💧",
    ("Water", "Air"): "misting ideas with empathy, fostering compassionate communication 🌬️💧",
    ("Water", "Water"): "diving deep into emotions, but risk of overwhelming floods 💧💧"
}

# List of Nakshatras (consistent across both apps)
nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purvaphalguni", "Uttaraphalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshta", "Mula", "Purvashada", "Uttarashada", "Shravana", "Dhanishta", "Shatabhisha", "Purvabhadra", "Uttarabhadra", "Revati"]

# Original Pancha Pakshi bird mapping
shukla_birds = {
    "Vulture": ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira"],
    "Owl": ["Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purvaphalguni"],
    "Crow": ["Uttaraphalguni", "Hasta", "Chitra", "Swati", "Vishakha"],
    "Cock": ["Anuradha", "Jyeshta", "Mula", "Purvashada", "Uttarashada"],
    "Peacock": ["Shravana", "Dhanishta", "Shatabhisha", "Purvabhadra", "Uttarabhadra", "Revati"]
}
krishna_birds = {
    "Peacock": ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira"],
    "Cock": ["Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purvaphalguni"],
    "Crow": ["Uttaraphalguni", "Hasta", "Chitra", "Swati", "Vishakha"],
    "Owl": ["Anuradha", "Jyeshta", "Mula", "Purvashada", "Uttarashada"],
    "Vulture": ["Shravana", "Dhanishta", "Shatabhisha", "Purvabhadra", "Uttarabhadra", "Revati"]
}

# Original elements and mappings (Pancha Pakshi system)
rashi_elements = {
    "Mesha": "Fire", "Vrishabha": "Earth", "Mithuna": "Air", "Karka": "Water",
    "Simha": "Fire", "Kanya": "Earth", "Tula": "Air", "Vrishchika": "Water",
    "Dhanu": "Fire", "Makara": "Earth", "Kumbha": "Air", "Meena": "Water"
}
bird_to_sanskrit = {
    "Vulture": "Gṛdhra",
    "Owl": "Ulūka",
    "Crow": "Kāka",
    "Cock": "Kukkuṭa",
    "Peacock": "Mayūra"
}
bird_to_element = {
    "Vulture": "Fire",
    "Owl": "Water",
    "Crow": "Earth",
    "Cock": "Air",
    "Peacock": "Ether"
}
bird_descriptions = {
    "Vulture": "In Pancha Pakshi Shastra, the Vulture (Gṛdhra) symbolizes transformation, power, and leadership. Mythically linked to Garuda, Vishnu's vehicle, it embodies swift action and protection. It engages in activities like Ruling (strongest) to Dying (weakest), influencing auspicious timings. Enhancing fiery Rashis like Mesha with passionate drive! 🦅⚡",
    "Owl": "The Owl (Ulūka) in Pancha Pakshi stands for Water 💧, signifying intuition, wisdom, and adaptability. Associated with Lakshmi's night vigilance, it's a harbinger of deep knowledge. Cycles through Eating, Walking, etc., for daily predictions. Amplifying watery traits in Nakshatras like Pushya with emotional depth! 🦉🌊🔮",
    "Crow": "Crow (Kāka) represents Earth 🌍, denoting practicality, intelligence, and ancestral connections. As Shani's messenger, it signifies resourcefulness and caution. Its states (Ruling to Sleeping) guide mundane tasks. Stabilizing earthy Kanya Rashi with wise, analytical energy! 🐦🌿🧠",
    "Cock": "The Cock (Kukkuṭa) embodies Air 🌬️, symbolizing alertness, courage, and communication. Linked to dawn and warriors like Kartikeya, it crows awakening and vigilance. Activities cycle for timing battles or starts. Boosting airy Mithuna with swift, intellectual winds! 🐔☁️🏹",
    "Peacock": "Peacock (Mayūra) signifies Ether ✨, illustrating expansion, beauty, and spirituality. Vehicle of Kartikeya, it dances in royal harmony, representing boundless space. From Ruling (peak creativity) to Dying, it aids spiritual pursuits. Elevating ethereal Meena with cosmic visions! 🦚🌌💫"
}
rashi_traits = {
    "Mesha": "energetic pioneer 🔥🚀",
    "Vrishabha": "patient builder 🌱🏰",
    "Mithuna": "curious communicator 🗣️🌟",
    "Karka": "nurturing protector 🏡❤️",
    "Simha": "confident leader 👑🌞",
    "Kanya": "analytical perfectionist 📊🔍",
    "Tula": "diplomatic harmonizer ⚖️💕",
    "Vrishchika": "intense transformer 🦂🔥",
    "Dhanu": "adventurous philosopher 🏹📜",
    "Makara": "disciplined achiever 🏔️🏆",
    "Kumbha": "innovative visionary 💡🌐",
    "Meena": "compassionate dreamer 🌊✨"
}
nak_traits = {
    "Ashwini": "swift healer 🏇💨",
    "Bharani": "creative warrior ⚔️🎨",
    "Krittika": "fiery critic 🔥🗡️",
    "Rohini": "artistic nurturer 🌸🍼",
    "Mrigashira": "curious explorer 🦌🔎",
    "Ardra": "stormy intellectual 🌩️🧠",
    "Punarvasu": "renewing archer 🏹🔄",
    "Pushya": "protective guru 🌟🛡️",
    "Ashlesha": "intuitive serpent 🐍🔮",
    "Magha": "regal ancestor 👑🕊️",
    "Purvaphalguni": "loving performer ❤️🎭",
    "Uttaraphalguni": "helpful analyst 🤝📈",
    "Hasta": "skillful artisan 🖐️🛠️",
    "Chitra": "charismatic architect 🌟🏗️",
    "Swati": "independent diplomat ⚖️🌬️",
    "Vishakha": "ambitious goal-setter 🏆🔥",
    "Anuradha": "devoted friend 🤝❤️",
    "Jyeshta": "protective elder 🛡️👴",
    "Mula": "truth-seeking root 🌿🔍",
    "Purvashada": "invincible optimist 🏹😊",
    "Uttarashada": "enduring victor 🏆💪",
    "Shravana": "learning listener 👂📚",
    "Dhanishta": "musical networker 🎶🤝",
    "Shatabhisha": "healing mystic 🌟🧙",
    "Purvabhadra": "spiritual warrior ⚔️🙏",
    "Uttarabhadra": "wise supporter 🧠🤝",
    "Revati": "compassionate guide 🐟❤️"
}
fun_phrases = {
    "Fire": ["ignite passions like a blazing star! 🔥🌟🦅", "transform challenges into victories with fiery zeal! ⚡🏆🔥", "soar high with unstoppable energy! 🚀🔥🕊️"],
    "Water": ["flow through life with deep intuition! 💧🌊🦉", "adapt and nurture like ocean waves! 🌊❤️💙", "dive into emotions with graceful wisdom! 🏊‍♂️🔮💧"],
    "Earth": ["build stable foundations with earthy wisdom! 🌍🏗️🐦", "grow steadily like ancient trees! 🌳💪🟫", "caw out practical solutions grounded in reality! 🐦🛠️🌿"],
    "Air": ["dance freely with intellectual winds! 🌬️💃🐔", "crow ideas that soar through the skies! 🐔☁️🧠", "breeze through challenges with swift agility! 🌪️🏃‍♂️🌬️"],
    "Ether": ["expand infinitely like cosmic space! ✨🌌🦚", "harmonize universes with ethereal grace! 🔮💫🌠", "peacock your boundless potential! 🦚🌈✨"]
}

# Imaginative mappings for Vasus, Rudras (rooted in elements, nodes)
vasus = ['Dhara (Earth)', 'Anala (Fire)', 'Anila (Wind)', 'Aha (Sky)', 'Pratyusha (Dawn)', 'Prabhasa (Light)', 'Soma (Moon)', 'Dhruva (Pole Star)']
rudras = ['Raivata', 'Aja', 'Ekapada', 'Ahirbudhnya', 'Pinaki', 'Aparajita', 'Tryambaka', 'Maheshvara', 'Vamadeva', 'Kapardin', 'Trilochana']

def get_vasu(moon_element):
    vasu_map = {
        'Earth': 'Dhara (Earth)',
        'Fire': 'Anala (Fire)',
        'Air': 'Anila (Wind)',
        'Water': 'Soma (Moon)'
    }
    return vasu_map.get(moon_element, random.choice(vasus))

def get_rudra(rahu_sign):
    return rudras[rahu_sign % 11]

vasu_fun = {
    'Dhara (Earth)': '🌍 Grounding force of stability! Dhara anchors your essence like cosmic soil, nurturing growth and endurance—imagine rooting like ancient banyans in Vedic realms! 🌳💪',
    'Anala (Fire)': '🔥 Blazing transformer! Anala ignites passions, purifying paths with fiery vigor—envision volcanic rebirths in divine forges! 🌋⚡',
    'Anila (Wind)': '🌬️ Swift messenger! Anila carries whispers of change, adapting with breezy freedom—picture kite-soaring through astral winds! 🪁🌀',
    'Aha (Sky)': '☁️ Expansive visionary! Aha spans infinite skies, inspiring lofty dreams—fantasize cloud-castles in heavenly expanses! 🏰✨',
    'Pratyusha (Dawn)': '🌅 Awakening light! Pratyusha heralds new beginnings with rosy hope—dream of sunrise rituals in sacred horizons! 🌄🙏',
    'Prabhasa (Light)': '🌟 Illuminating radiance! Prabhasa shines truth, guiding through darkness—envision lantern-lit paths in cosmic nights! 🏮🔮',
    'Soma (Moon)': '🌙 Mystical nurturer! Soma flows with lunar elixir, healing emotions—imagine moonlit elixirs in enchanted groves! 🍯🕊️',
    'Dhruva (Pole Star)': '⭐ Steadfast guide! Dhruva points eternal north, symbolizing unwavering focus—picture star-gazing quests to destiny! 🧭✨'
}

rudra_fun = {
    'Raivata': '🎶 Melodic protector! Raivata harmonizes chaos with rhythmic power—imagine drumming storms into serenity! 🥁🌩️',
    'Aja': '🐐 Eternal unborn! Aja embodies timeless creation, leaping bounds—envision goat-climbing cosmic peaks! 🏔️✨',
    'Ekapada': '🦵 One-footed dancer! Ekapada balances universes on single stance—picture whirling dervish in divine spins! 💃🌀',
    'Ahirbudhnya': '🐍 Serpent guardian! Ahirbudhnya coils depths, transforming poisons—fantasize naga-realms of hidden wisdom! 🔮🐉',
    'Pinaki': '🏹 Bow-wielder! Pinaki shoots arrows of truth, piercing illusions—dream of archery in astral battles! 🎯⚔️',
    'Aparajita': '🏆 Unconquerable victor! Aparajita triumphs eternally, inspiring resilience—envision undefeated gladiators in heavenly arenas! 🛡️💥',
    'Tryambaka': '👁️ Three-eyed seer! Tryambaka gazes beyond, burning ignorance—imagine third-eye visions in meditative trances! 🧘🔥',
    'Maheshvara': '👑 Great lord! Maheshvara rules with supreme grace, weaving fates—picture kingly thrones in cosmic palaces! 🏰🌟',
    'Vamadeva': '🌹 Beautiful left! Vamadeva charms with gentle might, balancing forces—envision rose-petaled paths to enlightenment! 🌸🙏',
    'Kapardin': '🦁 Matted-hair warrior! Kapardin roars with wild energy, taming beasts—fantasize lion-maned adventures in jungles of soul! 🦁🌿',
    'Trilochana': '🌌 Triple-visioned! Trilochana perceives past-present-future, guiding destinies—dream of oracle eyes in starry voids! ⭐🔮'
}

# General explanation text
general_text = """
No, there is no established tradition or system in Vedic astrology or Hindu scriptures that directly maps or assigns the 33 Vedic devas (comprising 8 Vasus, 11 Rudras, 12 Adityas, Indra, and Prajapati) to an individual based on their birth date and time. The 33 devas are primarily described in Vedic texts (such as the Brihadaranyaka Upanishad and Shatapatha Brahmana) as categories of cosmic forces, natural elements, and deities invoked collectively in rituals like yajnas, rather than as personal assignments for individuals.
That said, Vedic astrology (Jyotisha) does offer ways to identify personal or presiding deities (such as Ishta Devata or Kul Devata) through birth chart analysis, which indirectly draws from broader Vedic concepts of devas as cosmic influencers. These methods focus on major deities (e.g., forms of Vishnu, Shiva, Durga, or planetary gods) rather than the specific groups within the 33 devas. Here's a breakdown:
### Key Concepts in Vedic Astrology for Deity Assignment
Vedic astrology uses the birth chart (kundli or janam patri) calculated from the exact date, time, and place of birth to determine planetary positions, houses, and divisional charts. Deities are derived from these elements, but not as a one-to-one mapping of the 33 devas.
1. **Ishta Devata (Personal or Chosen Deity)**:
   - This is the most common way to find a guiding deity tailored to an individual.
   - **How it's determined**:
     - Identify the Atmakaraka (planet with the highest degree in the birth chart, representing the soul's desires).
     - In the Navamsa chart (D9, a divisional chart for dharma and spirituality), look at the 12th house from the Atmakaraka's position (known as Karakamsa).
     - The planet in or ruling that house indicates the Ishta Devata.
   - **Associated Deities** (based on planets):
     | Planet | Associated Deity/Devas |
     |--------------|-------------------------|
     | Sun | Shiva or Rama |
     | Moon | Parvati or Krishna |
     | Mars | Skanda (Kartikeya) or Narasimha |
     | Mercury | Vishnu |
     | Jupiter | Brahma or Guru forms |
     | Venus | Lakshmi |
     | Saturn | Shani or Ayyappa |
     | Rahu | Durga |
     | Ketu | Ganesha |
   - Worshipping this deity is believed to aid spiritual growth, protection, and moksha (liberation). Tools like online Ishta Devata calculators use birth details to compute this.
2. **Presiding Deity Based on the 5th House**:
   - The 5th house in the birth chart (Rashi or D1 chart) relates to intelligence, past karma (purva punya), and a suitable deity for worship (Aradhya Devata).
   - **How it's determined**: The sign or planet in the 5th house points to a deity.
     - Examples: Aries/Scorpio (or Mars) → Hanuman; Taurus/Libra (or Venus) → Lakshmi; Gemini (or Mercury) → Durga.
   - This is simpler and based directly on birth details but still focuses on major gods, not the 33 devas.
3. **Indirect Connections to the 33 Devas in Astrology**:
   - The 33 devas form the "celestial framework" of Vedic astrology, representing cosmic structures rather than personal assignments.
     - **12 Adityas**: Linked to the 12 zodiac signs and solar months. Your Sun sign (based on birth date) could loosely correspond to one Aditya (e.g., Dhata for Aries), influencing sustenance and energy.
     - **8 Vasus**: Associated with elements and celestial bodies (e.g., Moon, Sun, nakshatras), which factor into birth chart calculations.
     - **11 Rudras**: Tied to life force and nodes like Rahu/Ketu, which are analyzed in the chart for obstacles and transformation.
     - **Indra and Prajapati**: Indra relates to authority (midheaven/10th house), while Prajapati connects to the ascendant (Lagna), which is time-sensitive in the birth chart.
   - These influence the overall chart interpretation (e.g., for life events, health, or career) but aren't assigned as "your deva" based on birth.
### Why No Direct Mapping to the 33 Devas?
- The 33 are often symbolic of the universe's structure (e.g., 33 koti meaning "types" of devas, not literally 330 million gods). They are invoked collectively for balance, not individually per person.
- Birth-based systems prioritize planetary deities (Navagrahas) or major gods, as seen in texts like Parashara's Brihat Parashara Hora Shastra.
- Esoteric or regional traditions might interpret the 33 differently, but no widely documented evidence supports personal mapping.
If you're interested in your own chart, you can use free online tools (e.g., AstroSage or Vedic calculators) with your birth details to find your Ishta Devata or planetary influences. For personalized advice, consult a Vedic astrologer, as accuracy depends on precise birth time.
"""

st.title("Enhanced Vedic Deva Mapper & Divination Insights! 🕉️✨🔮")

st.write("Enter your details to discover personalized Vedic devas, astrology, and imaginative divination insights rooted in basic Vedic concepts! This app computes Ishta Devata, Aradhya Devata, Adityas, Pancha Pakshi, and fun connections to Vasus/Rudras for entertainment. Note: Calculations are approximate; consult professionals for accuracy.")

with st.expander("About Vedic Devas and Astrology (General Explanation)"):
    st.markdown(general_text)

name = st.text_input("Your Name", value="Mahān")
place = st.text_input("Birth Place (Optional, for display)", value="Chikkamagaluru")
dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 12, 31), value=datetime.date(1993, 7, 12))
tob = st.time_input("Time of Birth (Local Time)", step=datetime.timedelta(minutes=1), value=datetime.time(12, 26))

# All timezones
timezones = sorted(zoneinfo.available_timezones())
timezone = st.selectbox("Timezone 🌍", timezones, index=timezones.index("Asia/Kolkata") if "Asia/Kolkata" in timezones else 0)

lat = st.number_input("Latitude of Birth Place", min_value=-90.0, max_value=90.0, value=13.32)
lon = st.number_input("Longitude of Birth Place", min_value=-180.0, max_value=180.0, value=75.77)

if st.button("Generate Fun Insights! 🌟"):
    try:
        local_dt = datetime.datetime.combine(dob, tob)
        tz = zoneinfo.ZoneInfo(timezone)
        local_dt = local_dt.replace(tzinfo=tz)
        utc_dt = local_dt.astimezone(zoneinfo.ZoneInfo("UTC"))
        year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
        hour, minute, second = utc_dt.hour, utc_dt.minute, utc_dt.second
        jd = julian_date(year, month, day, hour, minute, second)
        d = jd - 2451545.0
        
        # Compute longitudes
        longitudes = {}
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']
        for planet in planets:
            longitudes[planet] = get_ecliptic_longitude(d, planet)
        
        # Speeds and retrogrades
        retro = {}
        speeds = {}
        for planet in planets:
            speeds[planet] = get_speed(d, planet)
            retro[planet] = speeds[planet] < 0
        
        # Sign degrees for Atmakaraka (exclude ketu)
        sign_deg = {}
        ak_planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu']
        for planet in ak_planets:
            sl = longitudes[planet] % 30
            if retro[planet]:
                sl = 30 - sl
            sign_deg[planet] = sl
        
        atmakaraka = max(sign_deg, key=sign_deg.get)
        
        # Navamsa signs (D9 longitude = sid_long * 9 % 360, sign = floor(/30))
        nav_signs = {}
        for planet in planets:
            sid_long = longitudes[planet]
            nav_long = (sid_long * 9) % 360
            nav_sign = int(nav_long // 30)
            nav_signs[planet] = nav_sign
        
        # Karakamsa = nav sign of atmakaraka
        karakamsa = nav_signs[atmakaraka]
        
        # 12th from Karakamsa
        twelfth_sign = (karakamsa + 11) % 12
        
        # Planets in 12th navamsa sign
        planets_in_twelfth = [p for p in planets if nav_signs[p] == twelfth_sign]
        
        # Ishta planet
        if planets_in_twelfth:
            ishta_planet = planets_in_twelfth[0]  # Pick first for fun
        else:
            ishta_planet = ruler_of[twelfth_sign]
        
        # Ishta Devata
        ishta_deva = deity_map[ishta_planet]
        ishta_fun = fun_desc[ishta_deva]
        
        # Aditya from Sun sign (sidereal Sun //30)
        ayan = calculate_ayanamsa(jd)
        sid_sun = (longitudes['sun'] - ayan) % 360
        sun_sign = int(sid_sun // 30)
        aditya = adityas[sun_sign]
        aditya_fun = aditya_desc[sun_sign]
        
        # Additional computations from divination code
        sun_long = longitudes['sun']
        moon_long = longitudes['moon']
        sid_moon = (moon_long - ayan) % 360
        
        nak_num = math.floor(sid_moon / (360 / 27))
        nak_rem = sid_moon % (360 / 27)
        pada = math.floor(nak_rem / (360 / 108)) + 1
        
        rashi_num = math.floor(sid_moon / 30)
        
        elong = (moon_long - sun_long) % 360
        paksha = "Shukla" if elong < 180 else "Krishna"
        
        nak_name = nakshatras[nak_num]
        
        rashis = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
        rashi_name = rashis[rashi_num]
        
        # Pancha Pakshi ruling bird (original system)
        ruling_bird = None
        if paksha == "Shukla":
            for bird, naks in shukla_birds.items():
                if nak_name in naks:
                    ruling_bird = bird
                    break
        else:
            for bird, naks in krishna_birds.items():
                if nak_name in naks:
                    ruling_bird = bird
                    break
        
        element = bird_to_element.get(ruling_bird, "Unknown")
        
        sanskrit_name = bird_to_sanskrit.get(ruling_bird, "Unknown")
        bird_desc = bird_descriptions.get(ruling_bird, "This bird embodies cosmic mysteries! 🌌")
        r_trait = rashi_traits.get(rashi_name, "mysterious soul 🌌")
        n_trait = nak_traits.get(nak_name, "cosmic wanderer ⭐")
        fun_phrase = random.choice(fun_phrases.get(element, ["embody the universe's mysteries! 🌌🔮✨"]))
        
        dynamic_desc = f"You are a {r_trait} infused with {n_trait} in Pada {pada} precision ⏳, guided by {ruling_bird} ({sanskrit_name}) of {element} vibes as per Agastya Muni's Pancha Pakshi Shastra, where your bird cycles through Ruling (powerful actions), Eating (gains), Walking (progress), Sleeping (rest), and Dying (caution)—time your endeavors accordingly for cosmic harmony! {fun_phrase}"
        
        # Calculate Sun sign and Ascendant sign
        sun_rashi_num = math.floor(sid_sun / 30)
        sun_rashi_name = rashis[sun_rashi_num]
        asc_trop = calculate_ascendant(jd, lat, lon)
        sid_asc = (asc_trop - ayan) % 360
        asc_rashi_num = math.floor(sid_asc / 30)
        asc_rashi_name = rashis[asc_rashi_num]
        
        # Get descriptions
        sun_desc = descriptions.get(sun_rashi_name, {"sun": "Unknown soul description 🌌"})["sun"]
        moon_desc = descriptions.get(rashi_name, {"moon": "Unknown mind description 🌌"})["moon"]
        asc_desc = descriptions.get(asc_rashi_name, {"asc": "Unknown personality description 🌌"})["asc"]
        
        # Get elements
        sun_element = rashi_elements.get(sun_rashi_name, "Unknown")
        moon_element = rashi_elements.get(rashi_name, "Unknown")
        asc_element = rashi_elements.get(asc_rashi_name, "Unknown")
        
        # Generate interplay description dynamically
        sun_moon_interplay = element_interplay_phrases.get((sun_element, moon_element), "blending in mysterious harmony 🌌")
        moon_asc_interplay = element_interplay_phrases.get((moon_element, asc_element), "interacting in cosmic balance ✨")
        sun_asc_interplay = element_interplay_phrases.get((sun_element, asc_element), "connecting with universal flow 🔮")
        interplay_desc = (
            f"Your {sun_element_traits.get(sun_element, 'mysterious purpose 🌌')} is {sun_moon_interplay}, "
            f"while your emotional world {moon_asc_interplay} in presentation. "
            f"Overall, your core drive and outward self {sun_asc_interplay}, creating a unique elemental symphony! 🎶"
        )
        
        # Aradhya Devata from 5th house (imaginative, based on ruler)
        fifth_sign = (asc_rashi_num + 4) % 12
        fifth_ruler = ruler_of[fifth_sign]
        aradhya_deva = aradhya_map.get(fifth_ruler, deity_map.get(fifth_ruler, 'Unknown'))
        aradhya_fun = fun_desc.get(aradhya_deva, 'Mysterious guiding force! 🌌')
        
        # Imaginative Vasu and Rudra
        vasu = get_vasu(moon_element)
        vasu_fun_desc = vasu_fun.get(vasu, 'Cosmic element anchor! ✨')
        rahu_long = longitudes['rahu']
        sid_rahu = (rahu_long - ayan) % 360
        rahu_sign = int(sid_rahu // 30)
        rudra = get_rudra(rahu_sign)
        rudra_fun_desc = rudra_fun.get(rudra, 'Life-force transformer! 💥')
        
        # Indra from 10th house (authority)
        tenth_sign = (asc_rashi_num + 9) % 12
        indra_influence = f"Indra's authority surges in your {rashis[tenth_sign]} 10th house, empowering career conquests like thunderbolts! ⚡🏆 Imagine ruling realms with divine might!"
        
        # Prajapati from Lagna
        prajapati_influence = f"Prajapati creates your {asc_rashi_name} ascendant, birthing your persona with cosmic creativity—envision weaving fates like a Vedic architect! 🕸️✨"
        
        # Output
        st.write(f"🌌 **Hey {name}!** Based on your birth on {dob} at {tob} ({place if place else 'Unknown Place'}, timezone {timezone}, {lat}° lat, {lon}° long), here's your enhanced Vedic deva mapping with imaginative twists inspired by the 33 Devas and astrology! 🕉️")
        st.write("### Your Ishta Devata (Personal Guiding Deity):")
        st.write(f"**{ishta_deva}**")
        st.write(ishta_fun)
        st.write("### Your Aradhya Devata (Presiding Deity from 5th House):")
        st.write(f"**{aradhya_deva}**")
        st.write(aradhya_fun)
        st.write("### Your Aditya (Solar Deva from the 12 Adityas):")
        st.write(f"**{aditya}**")
        st.write(aditya_fun)
        st.write(f"🌟 **Your Vedic Astrology & Divination Snapshot for {place if place else 'Unknown Place'}:** 🌟")
        st.write(f"- **Sun Sign:** {sun_rashi_name} (Element: {sun_element}) - {sun_desc}")
        st.write(f"- **Moon Sign:** {rashi_name} (Element: {moon_element}) - {moon_desc}")
        st.write(f"- **Ascendant Sign:** {asc_rashi_name} (Element: {asc_element}) - {asc_desc}")
        st.write(f"- **Nakshatra:** {nak_name}, Pada {pada}")
        st.write(f"- **Paksha:** {paksha}")
        st.write(f"- **Pancha Pakshi Ruling Bird (Panchabhuta):** {ruling_bird} ({sanskrit_name}) ({element})")
        st.write(f"**Dynamic Fun Description:** {dynamic_desc}")
        st.write(f"**Bird Meaning in Pancha Pakshi Context:** {bird_desc}")
        st.write(f"**Elemental Interplays (Sun-Moon-Asc):** {interplay_desc}")
        st.write("### Imaginative Connections to 33 Devas (Rooted in Vedic Concepts):")
        st.write(f"- **Your Vasu (from 8 Vasus, linked to Moon element):** {vasu} - {vasu_fun_desc}")
        st.write(f"- **Your Rudra (from 11 Rudras, tied to Rahu sign):** {rudra} - {rudra_fun_desc}")
        st.write(f"- **Indra Influence (Authority from 10th House):** {indra_influence}")
        st.write(f"- **Prajapati Influence (Creation from Ascendant):** {prajapati_influence}")
        st.write("These insights draw from Vedic concepts like the Adityas, Vasus, Rudras (part of the 33 Devas), Ishta/Aradhya Devata, and more—mapped imaginatively via your birth chart for fun and inspiration! Consult a professional astrologer for detailed readings. ✨")
        
        with st.expander("Significance of Sun, Moon, and Ascendant Signs"):
            st.write("""
            - **Sun Sign (Surya Rashi)** 🌞: Represents your core soul (Atma), ego, vitality, father, authority, and career path. It embodies your inner strength and life purpose, shining light on your leadership and societal role.
            - **Moon Sign (Chandra Rashi)** 🌙: Governs your mind (Manas), emotions, intuition, mother, home life, and inner comfort. It's central in Vedic astrology for daily predictions and personality, reflecting how you process feelings and nurture others.
            - **Ascendant Sign (Lagna)** ⬆️: Defines your physical body, appearance, health, self-image, and outward personality—how the world perceives you and your approach to life challenges.
            These three form the "Big Three" in Vedic charts, blending to create your holistic persona. The Sun provides the "why" (purpose) 🔥, Moon the "how" (emotions) 💧, and Ascendant the "what" (presentation) 🌍. Their interplay accounts for unique traits; e.g., a fiery Sun with watery Moon might mean passionate drive tempered by empathy, presented through an earthy Ascendant as grounded ambition.
            """)
        
        with st.expander("Meanings of All Birds in Pancha Pakshi Shastra"):
            for bird, desc in bird_descriptions.items():
                st.write(f"- **{bird}:** {desc}")
        
        with st.expander("All Possible Elemental Interplays for Sun-Moon-Asc"):
            st.write("Here are dynamic descriptions for all 64 possible combinations of Sun, Moon, Asc elements (Fire, Earth, Air, Water). Note: Ether is not included as it's from birds, not rashis.")
            rashi_el = ["Fire", "Earth", "Air", "Water"]
            for sun_el in rashi_el:
                for moon_el in rashi_el:
                    for asc_el in rashi_el:
                        sm_inter = element_interplay_phrases.get((sun_el, moon_el), "blending mysteriously")
                        ma_inter = element_interplay_phrases.get((moon_el, asc_el), "interacting cosmically")
                        sa_inter = element_interplay_phrases.get((sun_el, asc_el), "connecting universally")
                        desc = (
                            f"{sun_element_traits.get(sun_el)} is {sm_inter}, "
                            f"while emotional world {ma_inter} in presentation. "
                            f"Core drive and outward self {sa_inter}."
                        )
                        st.write(f"- **Sun:{sun_el}, Moon:{moon_el}, Asc:{asc_el}:** {desc}")
        
        with st.expander("Imaginative Meanings of All Vasus (8 Vasus)"):
            for v, desc in vasu_fun.items():
                st.write(f"- **{v}:** {desc}")
        
        with st.expander("Imaginative Meanings of All Rudras (11 Rudras)"):
            for r, desc in rudra_fun.items():
                st.write(f"- **{r}:** {desc}")
    
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}. Make sure details are correct.")
