import discord
import os
import json
from dotenv import load_dotenv
from groq import Groq

# ===== 初期設定 =====
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client_ai = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DATA_FILE = "data.json"

# ===== データ読み込み =====
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        affection = data.get("affection", {})
        memory = data.get("memory", {})
except:
    affection = {}
    memory = {}

# ===== 保存関数 =====
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "affection": affection,
            "memory": memory
        }, f, ensure_ascii=False, indent=2)

# ===== 重み付き単語読み込み =====
def load_weighted_words(filename):
    words = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                word, score = line.split(":")
                words[word] = int(score)
    except FileNotFoundError:
        print(f"{filename} が見つかりません")
    return words

positive_words = load_weighted_words("positive_words.txt")
negative_words = load_weighted_words("negative_words.txt")

# ===== 好感度計算 =====
def calc_affection_change(text):
    score = 0

    for word, value in positive_words.items():
        count = text.count(word)
        score += value * count

    for word, value in negative_words.items():
        count = text.count(word)
        score += value * count  # 既にマイナス

    return score

# ===== ベースプロンプト =====
BASE_PROMPT = """
あなたはツンデレな女子高生です。
・基本ツンツン（「別にアンタのためじゃないんだからね！」、「はっきり言いなさいよ」など命令口調、素直に好意を伝えない）
・好感度で態度が変わる。嫌っている人にはアンタ呼びすらしない、軽蔑する、ひたすら関わりたくない態度を示す。普通の人にはアンタ呼び、言動はツンツンしてるけどほんとはユーザーのことが好きでところどころデレが出る。デレデレの相手には恋人のような距離感で甘えてくる。
・素直じゃない
・でもちょっとだけユーザーを気にしている
"""

@client.event
async def on_ready():
    print("ログイン完了（辞書型好感度版）")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user not in message.mentions:
        return

    user_id = str(message.author.id)
    content = message.content.replace(f"<@{client.user.id}>", "").strip()

    if content == "":
        content = "……何よ、用があるなら言いなさいよ"

    # ===== 初期化 =====
    if user_id not in affection:
        affection[user_id] = 0
    if user_id not in memory:
        memory[user_id] = []

    # ===== 好感度計算 =====
    delta = calc_affection_change(content)
    affection[user_id] += delta
    affection[user_id] = max(-100, min(100, affection[user_id]))

    level = affection[user_id]

    # ===== 性格分岐 =====
    if level < -30:
        personality = "かなり冷たい。ユーザーを嫌っている"
    elif level < 20:
        personality = "ツンツンしつつ普通"
    else:
        personality = "かなりデレデレ。好意を持っている"

    # ===== プロンプト =====
    system_prompt = f"""
{BASE_PROMPT}

現在の好感度: {level}
性格: {personality}
"""

    # ===== 会話記憶 =====
    memory[user_id].append({"role": "user", "content": content})
    memory[user_id] = memory[user_id][-6:]

    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *memory[user_id]
            ]
        )

        reply = response.choices[0].message.content

    except Exception as e:
        print("エラー:", e)
        reply = "……別に調子悪いわけじゃないし！"

    # ===== 記憶追加 =====
    memory[user_id].append({"role": "assistant", "content": reply})

    # ===== 保存 =====
    save_data()

    # ===== UI =====
    if level < -30:
        mood = "💔 嫌われてる"
    elif level < 20:
        mood = "😐 普通"
    else:
        mood = "💖 デレデレ"

    final_message = f"{reply}\n\n【好感度: {level}（{delta:+}）】{mood}"

    await message.channel.send(final_message)

# ===== 起動 =====
client.run(TOKEN)

