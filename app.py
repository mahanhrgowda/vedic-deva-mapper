import streamlit as st
import swisseph as swe
import os
import urllib.request
import datetime
from timezonefinder import TimezoneFinder
import pytz

# Download ephe files if not present
ephe_path = './ephe'
if not os.path.exists(ephe_path):
    os.makedirs(ephe_path)
    base_url = 'https://www.astro.com/ftp/swisseph/ephe/'
    files = [
        'sepl_18.se1', 'semo_18.se1',
        'sepl_30.se1', 'semo_30.se1',
        'sepl_42.se1', 'semo_42.se1'  # Adding for 2100-2199 if needed
    ]
    for f in files:
        urllib.request.urlretrieve(base_url + f, os.path.join(ephe_path, f))

swe.set_ephe_path(ephe_path)
swe.set_sid_mode(swe.SIDM_LAHIRI)  # For sidereal, Lahiri ayanamsa

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

st.write("Enter your details to discover your personal Vedic devas with fun, extensive descriptions! Based on Vedic astrology concepts like Ishta Devata and Adityas. Note: This is for entertainment and requires precise birth time. The app will download necessary ephemeris files on first run.")

name = st.text_input("Your Name")
dob = st.date_input("Date of Birth")
tob = st.time_input("Time of Birth (Local Time)")
lat = st.number_input("Latitude of Birth Place", min_value=-90.0, max_value=90.0, value=0.0)
lon = st.number_input("Longitude of Birth Place", min_value=-180.0, max_value=180.0, value=0.0)

if st.button("Generate Fun Insights! 🌟"):
    try:
        # Find timezone
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=lon, lat=lat)
        if tz_str is None:
            raise ValueError("Could not determine timezone from lat/lon.")
        
        tz = pytz.timezone(tz_str)
        local_dt = datetime.datetime.combine(dob, tob)
        local_dt = tz.localize(local_dt)
        utc_dt = local_dt.astimezone(pytz.utc)
        
        year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
        hour, minute, second = utc_dt.hour, utc_dt.minute, utc_dt.second
        
        # Julian day
        jd = swe.utc_to_jd(year, month, day, hour, minute, second, 1)[1]  # jd_ut
        
        # Planet IDs
        planet_ids = {
            'sun': swe.SUN,
            'moon': swe.MOON,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN,
            'rahu': swe.MEAN_NODE,
        }
        
        longitudes = {}
        speeds = {}
        for p, pid in planet_ids.items():
            xx = swe.calc_ut(jd, pid)[0]
            longitudes[p] = xx[0]
            speeds[p] = xx[3]
        
        longitudes['ketu'] = (longitudes['rahu'] + 180) % 360
        speeds['ketu'] = speeds['rahu']  # Usually negative
        
        # Retrogrades
        retro = {p: speeds[p] < 0 for p in longitudes}
        
        # Sign degrees for Atmakaraka (exclude ketu)
        sign_deg = {}
        ak_planets = list(planet_ids.keys())  # sun to rahu
        for p in ak_planets:
            sl = longitudes[p] % 30
            if retro[p]:
                sl = 30 - sl
            sign_deg[p] = sl
        
        atmakaraka = max(sign_deg, key=sign_deg.get)
        
        # Navamsa signs
        nav_signs = {}
        all_planets = list(longitudes.keys())
        for p in all_planets:
            sid_long = longitudes[p]
            nav_long = (sid_long * 9) % 360
            nav_sign = int(nav_long // 30)
            nav_signs[p] = nav_sign
        
        # Karakamsa
        karakamsa = nav_signs[atmakaraka]
        
        # 12th from Karakamsa
        twelfth_sign = (karakamsa + 11) % 12
        
        # Planets in 12th sign (in Navamsa)
        planets_in_twelfth = [p for p in all_planets if nav_signs[p] == twelfth_sign]
        
        # Determine Ishta planet
        if planets_in_twelfth:
            ishta_planet = planets_in_twelfth[0]  # Pick the first one for fun
        else:
            ishta_planet = ruler_of[twelfth_sign]
        
        # Ishta Devata
        ishta_deva = deity_map[ishta_planet]
        ishta_fun = fun_desc[ishta_deva]
        
        # Aditya based on Sun sign
        sun_sign = int(longitudes['sun'] // 30)
        aditya = adityas[sun_sign]
        aditya_fun = aditya_desc[sun_sign]
        
        # Output
        st.write(f"🌌 **Hey {name}!** Based on your birth on {dob} at {tob} ({lat}° lat, {lon}° long), here's your fun Vedic deva mapping inspired by the 33 Devas and astrology! 🕉️")
        st.write("### Your Ishta Devata (Personal Guiding Deity):")
        st.write(f"**{ishta_deva}**")
        st.write(ishta_fun)
        st.write("### Your Aditya (Solar Deva from the 12 Adityas):")
        st.write(f"**{aditya}**")
        st.write(aditya_fun)
        st.write("These insights draw from Vedic concepts like the Adityas (part of the 33 Devas) and Ishta Devata, mapped via your birth chart for fun and inspiration! Consult a professional astrologer for detailed readings. ✨")
    
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}. Make sure details are correct and libraries are installed (pip install streamlit pyswisseph timezonefinder pytz).")
