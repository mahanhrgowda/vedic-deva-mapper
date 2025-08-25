import streamlit as st
import math
import datetime

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

# Deity map from planets
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

# Fun descriptions for Ishta Devata
fun_desc = {
    'Shiva or Rama': '🌟 Hey there, cosmic warrior! Your Ishta Devata is Shiva or Rama, the ultimate symbols of strength, devotion, and triumph over evil. 🛡️ Like Rama\'s unerring arrow or Shiva\'s meditative trance, you possess an inner power to overcome obstacles and lead with righteousness. 🔥 Embrace adventures, practice yoga, and chant "Om Namah Shivaya" for boundless energy and clarity. 🙏 Your life is a epic tale of balance between action and peace—dance through challenges like Shiva\'s Tandava! 💃🕺 Remember, with this divine guidance, prosperity and spiritual growth are your birthrights. ✨',
    'Parvati or Krishna': '💖 Divine lover of harmony! Your Ishta Devata is Parvati or Krishna, embodying love, playfulness, and nurturing energy. 🦚 Just as Krishna charms with his flute or Parvati stands strong beside Shiva, you bring joy, creativity, and compassion to everyone around you. 🎶 Dive into arts, music, or heartfelt connections—your soul thrives on beauty and devotion! 🥰 Offer sweets and flowers in prayer for endless blessings in relationships and self-expression. 🌸 Life\'s a divine leela (play); twirl through it with Krishna\'s mischief and Parvati\'s grace! 😄',
    'Skanda (Kartikeya) or Narasimha': '🦁 Fierce protector alert! Your Ishta Devata is Skanda or Narasimha, fierce guardians of justice and courage. ⚔️ Like Narasimha\'s roar or Skanda\'s spear, you\'re born to battle injustices and emerge victorious. 💥 Channel this energy into leadership roles or sports—your determination is unbeatable! 🏆 Pray with red flowers and mantras for protection and quick wins. 🙌 Your journey is action-packed; roar through challenges and protect your loved ones like a divine warrior! 🛡️🔥',
    'Vishnu': '🌀 Eternal preserver! Your Ishta Devata is Vishnu, the sustainer of the universe with infinite avatars. 🌌 From Rama to Krishna, you embody adaptability, wisdom, and cosmic balance. 📜 Navigate life\'s changes with grace, helping others along the way—your empathy is your superpower! ❤️ Chant "Om Namo Narayanaya" for harmony and abundance. 🙏 Your path is one of preservation and evolution; float through cosmos like Vishnu on Shesha! 🐍✨',
    'Brahma or Guru forms': '📚 Wise creator! Your Ishta Devata is Brahma or Guru, fountains of knowledge and creation. 🧠 Like Brahma\'s four faces seeing all, you have a knack for innovation, teaching, and deep insights. 🌟 Pursue learning, writing, or mentoring—your mind is a universe-builder! 🔮 Offer yellow flowers and seek blessings for intellectual growth. 🙏 Your life is a canvas of ideas; create worlds with Brahma\'s inspiration! 🎨✨',
    'Lakshmi': '💰 Goddess of fortune! Your Ishta Devata is Lakshmi, bringing wealth, beauty, and prosperity. 🌺 Like her lotus throne, you rise above challenges with elegance and attract abundance effortlessly. 🏆 Focus on finances, aesthetics, or hospitality—success follows you! 🎉 Light lamps and chant for endless blessings in material and spiritual riches. 🪔 Your journey is golden; bloom like a lotus in Lakshmi\'s grace! 🌸✨',
    'Shani or Ayyappa': '🪐 Master of discipline! Your Ishta Devata is Shani or Ayyappa, teachers of patience and karma. ⚖️ Like Shani\'s steady gaze, you build lasting success through hard work and resilience. 🛠️ Embrace challenges as lessons—your strength grows in trials! 💪 Pray with blue flowers for justice and long-term rewards. 🙏 Your path is transformative; rise like Ayyappa conquering inner demons! 🏔️🔥',
    'Durga': '🛡️ Warrior goddess! Your Ishta Devata is Durga, slayer of demons and protector supreme. 🐅 With her many arms, you multitask and conquer fears with fierce determination. ⚔️ Channel into activism, fitness, or bold pursuits—victory is yours! 🏅 Offer red hibiscus and chant "Om Dum Durgayei Namaha" for invincible power. 🙏 Your life is a battle won; ride the tiger of courage! 🐯✨',
    'Ganesha': '🐘 Remover of obstacles! Your Ishta Devata is Ganesha, lord of beginnings and wisdom. 📿 With his elephant head, you navigate life smartly, turning hurdles into stepping stones. 🧩 Start new ventures with confidence—success awaits! 🎉 Offer modaks and chant "Om Gam Ganapataye Namaha" for smooth paths. 🙏 Your journey is joyful; dance through life with Ganesha\'s blessings! 🥳✨'
}

# Adityas list and fun descriptions
adityas = ['Dhata', 'Aryama', 'Mitra', 'Varuna', 'Indra', 'Vivasvan', 'Parjanya', 'Amsu', 'Bhaga', 'Tvashta', 'Pusha', 'Vishnu']
aditya_desc = {
    0: '🛠️ Dhata, the creator! You\'re infused with inventive energy, crafting dreams into reality. Innovate boldly and watch your creations flourish! 🚀🌟',
    1: '👑 Aryama, the noble! Honor and loyalty define you, building unbreakable bonds. Lead with integrity for a life of respect and harmony! ❤️🤝',
    2: '🤝 Mitra, the friend! Your warmth fosters alliances and peace. Spread kindness and enjoy a network of supportive souls! 😊🌍',
    3: '🌊 Varuna, the ocean lord! Depth and intuition guide you through emotions. Dive deep for wisdom and emotional mastery! 🧜‍♂️💧',
    4: '⚡ Indra, the thunder king! Power and bravery surge through you. Conquer storms and claim victories with thunderous applause! 🏆🌩️',
    5: '☀️ Vivasvan, the radiant! Your light inspires growth and vitality. Shine bright and energize the world around you! 🌞🌱',
    6: '☁️ Parjanya, the rainmaker! Abundance flows like rain in your life. Nurture ideas and reap bountiful harvests! 🌧️🌾',
    7: '💧 Amsu, the nectar! Purity and healing are your gifts. Spread sweetness and find joy in life\'s simple elixirs! 🍯😇',
    8: '🌟 Bhaga, the fortunate! Luck and shares bless you. Give generously and receive manifold rewards! 🎁🍀',
    9: '🔨 Tvashta, the craftsman! Skill and artistry define your path. Forge masterpieces and build a legacy of beauty! 🎨🛠️',
    10: '🚀 Pusha, the nourisher! Growth and prosperity fuel you. Push boundaries and watch your ambitions soar! 📈🌟',
    11: '🕉️ Vishnu, the preserver! Balance and protection guard your journey. Sustain harmony for eternal peace and evolution! 🌀🙏'
}

st.title("Vedic Deva Mapper: Fun Astrological Insights! 🕉️✨")

st.write("Enter your details to discover your personal Vedic devas with fun, extensive descriptions! Based on Vedic astrology concepts like Ishta Devata and Adityas. Note: This is for entertainment and requires precise birth time. Birth time should be in local time; provide UTC offset for conversion.")

name = st.text_input("Your Name")
dob = st.date_input("Date of Birth")
tob = st.time_input("Time of Birth (Local Time)")
utc_offset = st.number_input("UTC Offset in hours (e.g., 5.5 for IST, -5 for EST)", min_value=-12.0, max_value=14.0, value=0.0, step=0.5)
lat = st.number_input("Latitude of Birth Place", min_value=-90.0, max_value=90.0, value=0.0)
lon = st.number_input("Longitude of Birth Place", min_value=-180.0, max_value=180.0, value=0.0)

if st.button("Generate Fun Insights! 🌟"):
    try:
        local_dt = datetime.datetime.combine(dob, tob)
        utc_dt = local_dt - datetime.timedelta(hours=utc_offset)
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
        
        # Output
        st.write(f"🌌 **Hey {name}!** Based on your birth on {dob} at {tob} (UTC offset {utc_offset}, {lat}° lat, {lon}° long), here's your fun Vedic deva mapping inspired by the 33 Devas and astrology! 🕉️")
        st.write("### Your Ishta Devata (Personal Guiding Deity):")
        st.write(f"**{ishta_deva}**")
        st.write(ishta_fun)
        st.write("### Your Aditya (Solar Deva from the 12 Adityas):")
        st.write(f"**{aditya}**")
        st.write(aditya_fun)
        st.write("These insights draw from Vedic concepts like the Adityas (part of the 33 Devas) and Ishta Devata, mapped via your birth chart for fun and inspiration! Consult a professional astrologer for detailed readings. ✨")
    
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}. Make sure details are correct.")
