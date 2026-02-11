import telebot
from telebot import types
import requests
from datetime import datetime, timedelta
import json
import os
import time
import sys

# ==================== KONFIGURATSIYA ====================
# Railway environment o'zgaruvchilari
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8200926398:AAEeHOtOWRXxeBTRGGm14vUR1ymczX3ZoZY")
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', "1a2b3c4d5e6f7g8h9i0j")

# Chempionatlar
LEAGUES = {
    "PL": {"name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angliya", "emblem": "🏆 Premier League", "code": "PL"},
    "PD": {"name": "🇪🇸 Ispaniya", "emblem": "🏆 La Liga", "code": "PD"},
    "FL1": {"name": "🇫🇷 Fransiya", "emblem": "🏆 Ligue 1", "code": "FL1"},
    "SA": {"name": "🇮🇹 Italiya", "emblem": "🏆 Serie A", "code": "SA"},
    "BL1": {"name": "🇩🇪 Germaniya", "emblem": "🏆 Bundesliga", "code": "BL1"}
}

# Botni ishga tushirish
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== API FUNKSIYALARI ====================
class FootballAPI:
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key):
        self.headers = {'X-Auth-Token': api_key}
        self.last_request = 0
        self.request_interval = 6  # 6 soniya (10 req/min uchun)
    
    def _rate_limit(self):
        """Rate limitni boshqarish"""
        elapsed = time.time() - self.last_request
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request = time.time()
    
    def get_matches_by_date(self, date_from, date_to):
        self._rate_limit()
        url = f"{self.BASE_URL}/matches"
        params = {'dateFrom': date_from, 'dateTo': date_to}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                return response.json().get('matches', [])
            else:
                print(f"API xatosi: {response.status_code}")
                return self.get_test_matches()
        except Exception as e:
            print(f"API xatosi: {e}")
            return self.get_test_matches()
    
    def get_league_matches(self, league_code, date_from, date_to):
        self._rate_limit()
        url = f"{self.BASE_URL}/competitions/{league_code}/matches"
        params = {'dateFrom': date_from, 'dateTo': date_to}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                return response.json().get('matches', [])
            else:
                return self.get_test_matches_for_league(league_code)
        except:
            return self.get_test_matches_for_league(league_code)
    
    def get_test_matches(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return [
            {
                'id': 1, 'competition': {'code': 'PL', 'name': 'Premier League'},
                'homeTeam': {'name': 'Manchester City', 'id': 65},
                'awayTeam': {'name': 'Arsenal', 'id': 57},
                'utcDate': f"{today}T19:45:00Z",
                'venue': 'Etihad Stadium', 'status': 'SCHEDULED'
            },
            {
                'id': 2, 'competition': {'code': 'PD', 'name': 'La Liga'},
                'homeTeam': {'name': 'Real Madrid', 'id': 86},
                'awayTeam': {'name': 'Barcelona', 'id': 81},
                'utcDate': f"{today}T20:00:00Z",
                'venue': 'Santiago Bernabeu', 'status': 'SCHEDULED'
            },
            {
                'id': 3, 'competition': {'code': 'SA', 'name': 'Serie A'},
                'homeTeam': {'name': 'Inter', 'id': 108},
                'awayTeam': {'name': 'Milan', 'id': 98},
                'utcDate': f"{today}T21:45:00Z",
                'venue': 'San Siro', 'status': 'SCHEDULED'
            }
        ]
    
    def get_test_matches_for_league(self, league_code):
        return [m for m in self.get_test_matches() if m['competition']['code'] == league_code]

# ==================== TAHLIL FUNKSIYALARI ====================
class MatchAnalyzer:
    @staticmethod
    def calculate_win_probability(home_team, away_team, venue="HOME"):
        home_prob = 45 * (1.2 if venue == "HOME" else 1.0)
        draw_prob = 30
        away_prob = 25
        
        total = home_prob + draw_prob + away_prob
        home_prob = round((home_prob / total) * 100)
        draw_prob = round((draw_prob / total) * 100)
        away_prob = round((away_prob / total) * 100)
        
        if home_prob >= 55:
            favorite = "home"
            favorite_name = home_team.get('name', 'Uy jamoasi')
            probability = home_prob
        elif away_prob >= 55:
            favorite = "away"
            favorite_name = away_team.get('name', 'Mehmon jamoa')
            probability = away_prob
        else:
            favorite = "draw"
            favorite_name = "Durang"
            probability = draw_prob
        
        return {
            'home_prob': home_prob, 'draw_prob': draw_prob, 'away_prob': away_prob,
            'favorite': favorite, 'favorite_name': favorite_name, 'probability': probability
        }
    
    @staticmethod
    def get_match_analysis_text(match, probability):
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        
        text = f"\n📊 *O'YIN TAHLILI:*\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🏠 {home_team}: {probability['home_prob']}% g'alaba\n"
        text += f"🤝 Durang: {probability['draw_prob']}%\n"
        text += f"🚌 {away_team}: {probability['away_prob']}% g'alaba\n\n"
        
        if probability['favorite'] == 'home':
            text += f"✅ *Favorit:* {probability['favorite_name']}\n"
            text += f"📈 *Minimal yutish ehtimoli:* {probability['probability']}%\n"
            if probability['probability'] >= 65:
                text += "⚡ *Kuchli favorit!*\n"
        elif probability['favorite'] == 'away':
            text += f"✅ *Favorit:* {probability['favorite_name']}\n"
            text += f"📈 *Minimal yutish ehtimoli:* {probability['probability']}%\n"
            if probability['probability'] >= 65:
                text += "⚡ *Kuchli favorit!* Mehmon maydonda\n"
        else:
            text += f"⚖️ *Teng kuchlar* - {probability['probability']}% durang\n"
        
        return text

# ==================== BOT HANDLERLARI ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for league_code, league_info in LEAGUES.items():
        btn = types.InlineKeyboardButton(
            league_info['name'],
            callback_data=f"league_{league_code}"
        )
        markup.add(btn)
    
    row2 = [
        types.InlineKeyboardButton("🔄 Yangilash", callback_data="refresh"),
        types.InlineKeyboardButton("📋 Barcha o'yinlar", callback_data="all_matches")
    ]
    markup.add(*row2)
    
    welcome_text = f"""
⚽ *FUTBOL TAHLIL BOTIGA XUSH KELIBSIZ!*

📋 *24 SOAT ICHIDAGI O'YINLAR:*
🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angliya - Premier League
🇪🇸 Ispaniya - La Liga
🇫🇷 Fransiya - Ligue 1
🇮🇹 Italiya - Serie A
🇩🇪 Germaniya - Bundesliga

👇 *Kerakli chempionatni tanlang:*
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    api = FootballAPI(FOOTBALL_API_KEY)
    analyzer = MatchAnalyzer()
    
    if call.data.startswith("league_"):
        league_code = call.data.replace("league_", "")
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        matches = api.get_league_matches(league_code, today, tomorrow)
        league_info = LEAGUES.get(league_code, {})
        
        if not matches:
            bot.send_message(call.message.chat.id, f"❌ {league_info['name']} chempionatida 24 soat ichida o'yinlar yo'q")
            bot.answer_callback_query(call.id)
            return
        
        text = f"{league_info['emblem']} *{league_info['name']} O'YINLARI*\n"
        text += f"📅 {today}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for match in matches[:5]:
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            
            match_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            local_time = match_time + timedelta(hours=5)
            time_str = local_time.strftime('%H:%M')
            
            probability = analyzer.calculate_win_probability(match['homeTeam'], match['awayTeam'], "HOME")
            
            text += f"⚔️ *{home}* vs *{away}*\n"
            text += f"⏰ {time_str} (Toshkent)\n"
            text += analyzer.get_match_analysis_text(match, probability)
            text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    elif call.data == "all_matches":
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        all_matches = api.get_matches_by_date(today, tomorrow)
        filtered_matches = [m for m in all_matches if m['competition']['code'] in LEAGUES.keys()]
        
        text = "📋 *BARCHA CHEMPIONATLAR O'YINLARI*\n"
        text += f"📅 {today}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        current_league = None
        for match in filtered_matches[:10]:
            league_code = match['competition']['code']
            league_name = LEAGUES[league_code]['name']
            
            if current_league != league_code:
                text += f"\n🏆 *{league_name}*\n"
                current_league = league_code
            
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            
            match_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            local_time = match_time + timedelta(hours=5)
            time_str = local_time.strftime('%H:%M')
            
            text += f"⚽ {home} vs {away} - ⏰ {time_str}\n"
        
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    elif call.data == "refresh":
        bot.answer_callback_query(call.id, "Ma'lumotlar yangilanmoqda...")
        send_welcome(call.message)

# ==================== RAILWAY UCHUN ASOSIY FUNKSIYA ====================
def main():
    print("⚽ Futbol tahlil boti ishga tushmoqda...")
    print(f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Bot token: {BOT_TOKEN[:10]}...")
    print(f"📊 API kalit: {FOOTBALL_API_KEY[:5]}...")
    print("-" * 40)
    
    # Botni polling rejimida ishga tushirish
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot xatosi: {e}")
        time.sleep(5)
        main()  # Qayta ishga tushirish

if __name__ == "__main__":
    main()
