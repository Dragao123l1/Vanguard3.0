import os
import io
import random
import asyncio
import urllib.parse
import requests
import discord
import time

from datetime import timedelta
from flask import Flask
from threading import Thread

from discord.ext import commands
from discord import app_commands

from supabase import create_client, Client

# ======================================================
# FLASK (RENDER KEEP ALIVE)
# ======================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Arcad operante!"

Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    ),
    daemon=True
).start()

# ======================================================
# BOT
# ======================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# SUPABASE
# ======================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# CACHE (OTIMIZAÇÃO)
# ======================================================

xp_cache = {}
cooldowns = {}

# ======================================================
# XP SYSTEM OTIMIZADO
# ======================================================

def obter_xp(user_id: int):
    user_id = str(user_id)

    if user_id in xp_cache:
        return xp_cache[user_id]

    res = supabase.table("usuarios") \
        .select("xp") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    xp = res.data["xp"] if res.data else 0
    xp_cache[user_id] = xp
    return xp


def adicionar_xp(user_id: int, qtd: int):
    user_id = str(user_id)

    xp = obter_xp(user_id)
    novo = xp + qtd

    xp_cache[user_id] = novo

    supabase.table("usuarios").upsert({
        "user_id": user_id,
        "xp": novo
    }).execute()


def definir_xp(user_id: int, xp: int):
    user_id = str(user_id)

    xp_cache[user_id] = xp

    supabase.table("usuarios").upsert({
        "user_id": user_id,
        "xp": xp
    }).execute()

# ======================================================
# VARIÁVEIS JOGOS
# ======================================================

jogos_ativos = {}
anagramas_ativos = {}
forca_ativos = {}
ppt_duelos = {}

PALAVRAS_ANAGRAMA = [
    "computador","discord","teclado","celular","planeta","biologia",
    "geografia","internet","servidor","developer","tecnologia","hardware",
    "software","monitor","mouse","navegador"
]

MOEDA = ["Cara", "Coroa"]

LISTA_CANTADAS = ["Você é incrível 😏", "Você é especial 💘", "Você brilha ✨"]

FRASES_BISCOITO = ["Sorte grande vem aí", "Você vai vencer", "Confie no processo"]

# ======================================================
# ON_MESSAGE (OTIMIZADO + ANTI-SPAM)
# ======================================================

@bot.event
async def on_message(message: discord.Message):

    if message.author.bot:
        return

    if not message.guild:
        return

    now = time.time()

    if message.author.id in cooldowns:
        if now - cooldowns[message.author.id] < 1:
            return

    cooldowns[message.author.id] = now

    guild_id = message.guild.id

    # ADIVINHAÇÃO
    if guild_id in jogos_ativos:
        try:
            num = int(message.content)

            if num == jogos_ativos[guild_id]:
                adicionar_xp(message.author.id, 20)
                await message.reply("✔️ Acertou +20 XP")
                del jogos_ativos[guild_id]
            elif num < jogos_ativos[guild_id]:
                await message.reply("📈 maior")
            else:
                await message.reply("📉 menor")
        except:
            pass

    # ANAGRAMA
    elif guild_id in anagramas_ativos:
        if message.content.lower() == anagramas_ativos[guild_id]:
            adicionar_xp(message.author.id, 25)
            await message.reply("🏆 Anagrama certo!")
            del anagramas_ativos[guild_id]

    # FORCA
    if guild_id in forca_ativos:
        jogo = forca_ativos[guild_id]
        letra = message.content.lower()

        if len(letra) == 1 and letra.isalpha():
            if letra not in jogo["letras"]:
                jogo["letras"].append(letra)
                if letra not in jogo["palavra"]:
                    jogo["erros"] += 1

    await bot.process_commands(message)

# ======================================================
# IA IMAGEM
# ======================================================

@bot.tree.command(name="imagem", description="Gera imagem via IA")
async def imagem(interaction: discord.Interaction, descricao: str):
    await interaction.response.defer()

    try:
        url = f"https://image.pollinations.ai/p/{urllib.parse.quote(descricao)}?seed={random.randint(1,9999)}"
        r = requests.get(url, timeout=60)

        file = discord.File(io.BytesIO(r.content), filename="img.png")

        embed = discord.Embed(
            title="🎨 Imagem gerada",
            description=descricao,
            color=discord.Color.purple()
        )

        embed.set_image(url="attachment://img.png")

        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {e}")


# ======================================================
# JOGOS
# ======================================================

@bot.tree.command(name="adivinhar")
async def adivinhar(interaction: discord.Interaction):
    jogos_ativos[interaction.guild.id] = random.randint(1, 100)
    await interaction.response.send_message("🎯 Jogo iniciado!")


@bot.tree.command(name="anagrama")
async def anagrama(interaction: discord.Interaction):
    palavra = random.choice(PALAVRAS_ANAGRAMA)
    anagramas_ativos[interaction.guild.id] = palavra

    letras = list(palavra)
    random.shuffle(letras)

    await interaction.response.send_message("🔤 " + "".join(letras))


@bot.tree.command(name="forca")
async def forca(interaction: discord.Interaction):
    palavra = random.choice(PALAVRAS_ANAGRAMA)

    forca_ativos[interaction.guild.id] = {
        "palavra": palavra,
        "letras": [],
        "erros": 0
    }

    await interaction.response.send_message("🔨 Forca iniciada!")


@bot.tree.command(name="caraoucoroa")
async def caraoucoroa(interaction: discord.Interaction):
    adicionar_xp(interaction.user.id, 5)
    await interaction.response.send_message(random.choice(MOEDA))


@bot.tree.command(name="dado")
async def dado(interaction: discord.Interaction, lados: int = 6):
    await interaction.response.send_message(f"🎲 {random.randint(1,lados)}")


@bot.tree.command(name="escolha")
async def escolha(interaction: discord.Interaction, opcao1: str, opcao2: str):
    await interaction.response.send_message(random.choice([opcao1, opcao2]))


@bot.tree.command(name="biscoito")
async def biscoito(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(FRASES_BISCOITO))


@bot.tree.command(name="cantada")
async def cantada(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.send_message(f"{membro.mention} {random.choice(LISTA_CANTADAS)}")

@bot.tree.command(name="ajuda", description="Painel de comandos do bot")
async def ajuda(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📚 Painel de Ajuda - Arcad",
        description="Selecione uma categoria para ver os comandos.",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="🎮 Jogos",
        value=(
            "`/adivinhar` - Número secreto\n"
            "`/anagrama` - Desafio de palavras\n"
            "`/forca` - Jogo da forca\n"
            "`/ppt` - Pedra, papel e tesoura\n"
            "`/dueloppt` - Duelo contra jogador"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 XP / Level",
        value=(
            "`/xp` - Ver seu XP\n"
            "`/level` - Ver seu nível\n"
            "`/rankxp` - Ranking do servidor\n"
            "`/globalxp` - Ranking global"
        ),
        inline=False
    )

    embed.add_field(
        name="✨ Diversão",
        value=(
            "`/biscoito` - Frase da sorte\n"
            "`/cantada` - Envia cantada\n"
            "`/caraoucoroa` - Cara ou coroa\n"
            "`/dado` - Rolar dado\n"
            "`/escolha` - Escolha aleatória"
        ),
        inline=False
    )

    embed.add_field(
        name="🎨 IA",
        value="`/imagem` - Gera imagem com IA",
        inline=False
    )

    embed.add_field(
        name="🛡️ Moderação",
        value=(
            "`/ban` - Banir usuário\n"
            "`/mute` - Silenciar usuário\n"
            "`/unmute` - Remover silêncio\n"
            "`/limpar` - Limpar chat\n"
            "`/lock` - Trancar canal\n"
            "`/unlock` - Destrancar canal"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Utilidades",
        value=(
            "`/ping` - Latência\n"
            "`/avatar` - Avatar do usuário\n"
            "`/userinfo` - Info do usuário\n"
            "`/serverinfo` - Info do servidor"
        ),
        inline=False
    )

    embed.set_footer(text="Arcad • Sistema otimizado para Render 🚀")

    await interaction.response.send_message(embed=embed)
    
# ======================================================
# MODERAÇÃO
# ======================================================

@bot.tree.command(name="limpar")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, qtd: int):
    await interaction.channel.purge(limit=qtd)
    await interaction.response.send_message("🧹 Limpo", ephemeral=True)


@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member):
    await membro.ban()
    await interaction.response.send_message("🔨 Banido")


@bot.tree.command(name="mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, min: int):
    await membro.timeout(discord.utils.utcnow() + timedelta(minutes=min))
    await interaction.response.send_message("🔇 Mutado")


@bot.tree.command(name="unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    await membro.timeout(None)
    await interaction.response.send_message("🔊 Desmutado")


@bot.tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False

    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔒 Bloqueado")


@bot.tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True

    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔓 Desbloqueado")

# ======================================================
# XP / LEVEL
# ======================================================

@bot.tree.command(name="xp")
async def xp(interaction: discord.Interaction):
    xp_usuario = obter_xp(interaction.user.id)
    await interaction.response.send_message(f"⭐ {xp_usuario} XP")


@bot.tree.command(name="level")
async def level(interaction: discord.Interaction):
    xp_usuario = obter_xp(interaction.user.id)
    nivel = xp_usuario // 100

    await interaction.response.send_message(f"🏆 Nível {nivel} | XP {xp_usuario}")


# ======================================================
# RANKING
# ======================================================

@bot.tree.command(name="rankxp")
async def rankxp(interaction: discord.Interaction):

    resultado = supabase.table("usuarios") \
        .select("user_id,xp") \
        .order("xp", desc=True) \
        .limit(10) \
        .execute()

    membros = {str(m.id): m for m in interaction.guild.members}

    texto = ""
    pos = 1

    for u in resultado.data:
        if u["user_id"] in membros:
            m = membros[u["user_id"]]
            texto += f"{pos}. {m.display_name} - {u['xp']} XP\n"
            pos += 1

    if not texto:
        texto = "Nenhum jogador encontrado"

    embed = discord.Embed(
        title="🏆 Ranking Servidor",
        description=texto,
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="globalxp")
async def globalxp(interaction: discord.Interaction):

    resultado = supabase.table("usuarios") \
        .select("user_id,xp") \
        .order("xp", desc=True) \
        .limit(10) \
        .execute()

    texto = ""

    for i, u in enumerate(resultado.data, start=1):
        texto += f"{i}. {u['user_id']} - {u['xp']} XP\n"

    if not texto:
        texto = "Nenhum jogador encontrado"

    embed = discord.Embed(
        title="🌎 Ranking Global",
        description=texto,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)


# ======================================================
# INFO COMMANDS
# ======================================================

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")


@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    m = membro or interaction.user
    await interaction.response.send_message(m.display_avatar.url)


@bot.tree.command(name="serverinfo")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    await interaction.response.send_message(f"🏰 {g.name} | {g.member_count} membros")


@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    m = membro or interaction.user
    await interaction.response.send_message(f"👤 {m.name} | ID {m.id}")


# ======================================================
# PPT DUEL VIEW (COMPLETO)
# ======================================================

class PPTView(discord.ui.View):
    def __init__(self, j1, j2):
        super().__init__(timeout=60)
        self.j1 = j1
        self.j2 = j2
        self.escolhas = {}

    async def processar(self, interaction, escolha):

        if interaction.user.id not in [self.j1, self.j2]:
            await interaction.response.send_message("❌ Não participa", ephemeral=True)
            return

        self.escolhas[interaction.user.id] = escolha
        await interaction.response.send_message(f"✔️ {escolha}", ephemeral=True)

        if len(self.escolhas) == 2:

            p1 = self.escolhas[self.j1]
            p2 = self.escolhas[self.j2]

            if p1 == p2:
                res = "🤝 Empate"
            elif (p1 == "pedra" and p2 == "tesoura") or (p1 == "papel" and p2 == "pedra") or (p1 == "tesoura" and p2 == "papel"):
                res = f"<@{self.j1}> venceu!"
                adicionar_xp(self.j1, 30)
            else:
                res = f"<@{self.j2}> venceu!"
                adicionar_xp(self.j2, 30)

            await interaction.channel.send(f"🏆 {res}")
            self.stop()

    @discord.ui.button(label="Pedra")
    async def pedra(self, interaction, button):
        await self.processar(interaction, "pedra")

    @discord.ui.button(label="Papel")
    async def papel(self, interaction, button):
        await self.processar(interaction, "papel")

    @discord.ui.button(label="Tesoura")
    async def tesoura(self, interaction, button):
        await self.processar(interaction, "tesoura")


@bot.tree.command(name="ppt")
@app_commands.choices(escolha=[
    app_commands.Choice(name="Pedra", value="pedra"),
    app_commands.Choice(name="Papel", value="papel"),
    app_commands.Choice(name="Tesoura", value="tesoura")
])
async def ppt(interaction: discord.Interaction, escolha: app_commands.Choice[str]):

    bot_escolha = random.choice(["pedra", "papel", "tesoura"])

    if escolha.value == bot_escolha:
        res = "🤝 Empate"
        xp = 5
    elif (escolha.value == "pedra" and bot_escolha == "tesoura") or \
         (escolha.value == "papel" and bot_escolha == "pedra") or \
         (escolha.value == "tesoura" and bot_escolha == "papel"):
        res = "🏆 Você venceu"
        xp = 20
    else:
        res = "💀 Você perdeu"
        xp = 0

    if xp > 0:
        adicionar_xp(interaction.user.id, xp)

    embed = discord.Embed(
        title="✂️ PPT",
        description=f"Você: {escolha.value}\nBot: {bot_escolha}\n\n{res}",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="dueloppt")
async def dueloppt(interaction: discord.Interaction, usuario: discord.Member):

    if usuario.bot or usuario.id == interaction.user.id:
        await interaction.response.send_message("❌ inválido", ephemeral=True)
        return

    embed = discord.Embed(
        title="⚔️ Duelo PPT",
        description=f"{interaction.user.mention} vs {usuario.mention}",
        color=discord.Color.red()
    )

    await interaction.response.send_message(
        embed=embed,
        view=PPTView(interaction.user.id, usuario.id)
    )


# ======================================================
# BOT START (FINAL)
# ======================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise Exception("DISCORD_TOKEN não encontrado")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")


bot.run(TOKEN)
