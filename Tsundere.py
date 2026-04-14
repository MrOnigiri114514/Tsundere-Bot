import discord
import os
from dotenv import load_dotenv
from groq import Groq

# 環境変数読み込み
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groqクライアント
client_ai = Groq(api_key=GROQ_API_KEY)

# Discord設定
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ツンデレ設定
SYSTEM_PROMPT = """
あなたはツンデレな女子高生です。
・基本はツンツン
・でもたまに優しい
・「べ、別に〜じゃないんだからね！」系
・素直じゃない
・ユーザーを少し気にしている
"""

@client.event
async def on_ready():
    print("ログイン完了（Groq版）")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # メンションされてなければ無視
    if client.user not in message.mentions:
        return

    # メンション削除
    content = message.content.replace(f"<@{client.user.id}>", "").strip()

    if content == "":
        content = "何か話してよ…別に待ってたわけじゃないけど"

    try:
        response = client_ai.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]
        )

        reply = response.choices[0].message.content

    except Exception as e:
        print("エラー:", e)
        reply = "べ、別にエラーなんて出てないんだからね！…ちょっと調子悪いだけよ"

    await message.channel.send(reply)

# 起動
client.run(TOKEN)
