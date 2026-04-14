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
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        affection = data.get("affection", {})
        memory = data.get("memory", {})
except:
    affection = {}
    memory = {}

# ===== 保存関数 =====
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "affection": affection,
            "memory": memory
        }, f)

# ===== ベース設定 =====
BASE_PROMPT = """
あなたはツンデレな女子高生です。
・基本ツンツン
・好感度で態度が変わる
・素直じゃない
・ユーザーを少し気にしている
"""

@client.event
async def on_ready():
    print("ログイン完了（AI好感度版）")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user not in message.mentions:
        return

    user_id = str(message.author.id)
    content = message.content.replace(f"<@{client.user.id}>", "").strip()

    if content == "":
        content = "……何よ、用があるならはっきり言いなさいよ"

    # ===== 初期化 =====
    if user_id not in affection:
        affection[user_id] = 0
    if user_id not in memory:
        memory[user_id] = []

    level = affection[user_id]

    # ===== 性格分岐 =====
    if level < -30:
        personality = "かなり冷たい。ユーザーを嫌っている"
    elif level < 20:
        personality = "ツンツンしつつ普通"
    else:
        personality = "かなりデレデレ。好意を持っている"

    # ===== システムプロンプト =====
    system_prompt = f"""
{BASE_PROMPT}

現在の好感度: {level}
性格: {personality}

ユーザーの発言に対して以下をJSONで出力してください：

{{
  "reply": "ツンデレとしての返答",
  "affection": -10から+10の整数（好感度変化）
}}

必ずJSON形式のみで返してください。
"""

    # ===== 会話記憶追加 =====
    memory[user_id].append({"role": "user", "content": content})
    memory[user_id] = memory[user_id][-6:]

    try:
        response = client_ai.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                *memory[user_id]
            ]
        )

        response_text = response.choices[0].message.content

        # ===== JSONパース =====
        data = json.loads(response_text)
        reply = data["reply"]
        delta = int(data["affection"])

    except Exception as e:
        print("エラー:", e)
        reply = "……なによ、ちょっと調子悪いだけなんだから！"
        delta = 0

    # ===== 好感度更新 =====
    affection[user_id] += delta
    affection[user_id] = max(-100, min(100, affection[user_id]))

    level = affection[user_id]

    # ===== 記憶保存 =====
    memory[user_id].append({"role": "assistant", "content": reply})

    save_data()

    # ===== UI表示 =====
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
