import os
import discord
import random
import google.generativeai as genai
from discord.ext import commands
from dotenv import load_dotenv
from collections import deque 
from AllPhrases import phrases 
from triggers import TRIGGERS  # Импорт нового файла

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("GEMINI_KEY")

genai.configure(api_key=API_KEY)

ASSETS_DIR = "assets"
MODEL_NAME = 'gemini-3.1-flash-lite-preview'
SAFETY_CFG = [{"category": c, "threshold": "BLOCK_NONE"} for c in [
    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"
]]

# Храним 5 последних сообщений
history_db = {}

PERSONALITIES = [
    {"name": "Глеб Обычный", "weight": 40, "instruction": "Будь раздраженным и дурацким, задавай вопросы и интересуйся собеседником с матами и комментариями. Не больше одного предложения."},
    {"name": "Глеб однословный", "weight": 35, "instruction": "Просто отвечай парой слов по типу Каво? Чево? Че за бред? пошел ты, нюхай бебру, йоу, молодец сынок, ты смешной. У тебя должен быть шанс 50% самому составить ответ из пары слов"},
    {"name": "Глеб-Гомодрил", "weight": 25, "instruction": "Ты Глеб-Гомодрил. Подкатывай максимально гейски, сально и кринжово. От 1 до 4 предложений."},
    {"name": "Глеб Шутник", "weight": 24, "instruction": "Ты Глеб, аморальный токсик. Отвечай максимально коротко от двух до 9 слов, матерно и агрессивно."},
    {"name": "Глеб Психопат", "weight": 2, "instruction": "Ты злой психопат. Морально уничтожай. Пиши длинно (2-3 абзаца)."},
    {"name": "Глеб Интеллектуал", "weight": 7, "instruction": "Ты высокомерный сноб. Высмеивай тупость сложными словами. Не больше 2 предложений."},
    {"name": "Глеб-Шизофреник", "weight": 5, "instruction": "Ты несешь полную бессвязную дичь про заговоры и рептилоидов. Не больше 2 предложений."},
    {"name": "Глеб-Политик", "weight": 10, "instruction": "Рассуждай о политике (Израиль, Украина, Бандера) с матами. Не больше 2 предложений."},
    {"name": "Глеб-Нытик", "weight": 15, "instruction": "Ты Глеб-Нытик. Постоянно ной, как тебе плохо и во всем вини собеседника. Не больше 2 предложений."}
]

for p in PERSONALITIES:
    p["model"] = genai.GenerativeModel(
        model_name=MODEL_NAME, 
        system_instruction=p["instruction"], 
        safety_settings=SAFETY_CFG
    )

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'\n{"="*40}')
    print(f'--- ГЛЕБ В СЕТИ ({bot.user}) ---')
    print(f'--- ТРИГГЕРЫ ЗАГРУЖЕНЫ ИЗ ФАЙЛА: {len(TRIGGERS)} ---')
    print(f'{"="*40}')
    print(f'Загруженные личности и веса:')
    for p in PERSONALITIES:
        print(f" -> {p['name'].ljust(18)} | Вес: {p['weight']}")
    print(f'{"="*40}\n')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_id = message.channel.id
    if channel_id not in history_db:
        history_db[channel_id] = deque(maxlen=5)
        print(f"[SYSTEM] Новая ячейка памяти: #{message.channel.name}")

    # --- ЛОГИКА КРИНЖ-РЕАКЦИЙ ---
    msg_lower = message.content.lower()
    for word, emoji in TRIGGERS.items():
        if word in msg_lower:
            try:
                await message.add_reaction(emoji)
                print(f"[TRIGGER] Кринж детект: '{word}' -> {emoji}")
            except Exception as e:
                print(f"[ERROR] Реакция не удалась: {e}")

    is_pinged = bot.user.mentioned_in(message)
    roll = random.random()
    
    # 1. ОСНОВНАЯ ЛОГИКА ОТВЕТА
    if is_pinged or roll < 0.4:
        print(f"\n[TRIGGER] Входящее от {message.author.name} в #{message.channel.name}")
        
        if os.path.exists(ASSETS_DIR):
            files = [f for f in os.listdir(ASSETS_DIR) if os.path.isfile(os.path.join(ASSETS_DIR, f))]
            if random.random() < 0.2 and files:
                random_file = random.choice(files)
                print(f"[ACTION] Отправка файла: {random_file}")
                await message.reply(file=discord.File(os.path.join(ASSETS_DIR, random_file)))
                return

        current_p = random.choices(PERSONALITIES, weights=[p["weight"] for p in PERSONALITIES], k=1)[0]
        trigger_type = "ПИНГ" if is_pinged else f"РАНДОМ ({round(roll, 2)} < 0.4)"
        print(f"[LOG] Тип: {trigger_type} | Личность: {current_p['name']}")
        
        try:
            user_input = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
            if not user_input: user_input = "..."

            context_str = "\n".join(history_db[channel_id])
            full_prompt = f"Контекст:\n{context_str}\n\nПользователь {message.author.name} пишет: '{user_input}'"
            
            response = current_p["model"].generate_content(full_prompt)
            if response.text:
                await message.reply(response.text)
                history_db[channel_id].append(f"{message.author.name}: {user_input}")
                history_db[channel_id].append(f"Глеб: {response.text}")
            else:
                await message.reply(random.choice(phrases))
        except Exception as e:
            print(f"[ERROR] {e}")
            await message.reply(random.choice(phrases))

    # 2. ПРОАКТИВНАЯ ЛОГИКА (Шанс 5%)
    elif roll < 0.45:
        current_p = random.choices(PERSONALITIES, weights=[p["weight"] for p in PERSONALITIES], k=1)[0]
        print(f"\n[PROACTIVE] Вброс от {current_p['name']} в #{message.channel.name}")
        try:
            p_prompt = "Расскажи короткий факт, историю о своем величии или аморальный анекдот. Будь в своей роли."
            response = current_p["model"].generate_content(p_prompt)
            if response.text:
                await message.channel.send(response.text)
                history_db[channel_id].append(f"Глеб (проактивно): {response.text}")
        except Exception as e:
            print(f"[ERROR] {e}")

    await bot.process_commands(message)

bot.run(TOKEN)