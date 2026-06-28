import discord
discord.VoiceClient.warn_nacl = False
import os
import random
import io
import urllib.parse
import discord
import requests

from flask import Flask
from threading import Thread
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

# ======================================================
# KEEP ALIVE (RENDER)
# ======================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de diversão online 🚀"

Thread(
    target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))),
    daemon=True
).start()

# ======================================================
# BOT
# ======================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# DADOS
# ======================================================

PALAVRAS = [
    "computador", "discord", "teclado", "internet", "servidor",
    "python", "codigo", "programa", "developer"
]

MOEDA = ["Cara", "Coroa"]

CANTADAS = [
    "Você é o bug que eu não quero corrigir 😏",
    "Você é mais bonita que código funcionando de primeira 💘",
    "Se beleza fosse CPU, você seria um supercomputador 🔥"
]

BISCOITOS = [
    "Hoje vai dar bom 🍀",
    "Você vai surpreender alguém hoje ✨",
    "Algo incrível vai acontecer 👀"
]

# ======================================================
# JOGOS EM MEMÓRIA
# ======================================================

adivinhar = {}
anagrama = {}
forca = {}

# ======================================================
# READY
# ======================================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Online como {bot.user}")

# ======================================================
# ON MESSAGE (JOGOS)
# ======================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if not message.guild:
        return

    gid = message.guild.id

    # =========================
    # ADIVINHAR
    # =========================
    if gid in adivinhar:
        try:
            num = int(message.content)

            if num == adivinhar[gid]:
                await message.reply("🎉 Acertou o número!")
                del adivinhar[gid]
            elif num < adivinhar[gid]:
                await message.reply("📈 maior")
            else:
                await message.reply("📉 menor")
        except:
            pass

    # =========================
    # ANAGRAMA
    # =========================
    elif gid in anagrama:
        if message.content.lower() == anagrama[gid]:
            await message.reply("🏆 Acertou o anagrama!")
            del anagrama[gid]

    # =========================
    # FORCA (SIMPLES E SEGURA)
    # =========================
    elif gid in forca:
        palavra = forca[gid]

        if message.content.lower() == palavra:
            await message.reply("🏆 Você venceu a forca!")
            del forca[gid]

    await bot.process_commands(message)

# ======================================================
# HELP UI (PROFISSIONAL)
# ======================================================

class PPTWView(discord.ui.View):
    def __init__(self, p1: int, p2: int):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.escolhas = {}

    async def process(self, interaction: discord.Interaction, escolha: str):

        if interaction.user.id not in [self.p1, self.p2]:
            return await interaction.response.send_message(
                "❌ Você não está neste duelo.",
                ephemeral=True
            )

        self.escolhas[interaction.user.id] = escolha
        await interaction.response.send_message(f"✔ Escolheu {escolha}", ephemeral=True)

        if len(self.escolhas) < 2:
            return

        p1_escolha = self.escolhas[self.p1]
        p2_escolha = self.escolhas[self.p2]

        if p1_escolha == p2_escolha:
            resultado = "🤝 Empate!"
        elif (
            (p1_escolha == "pedra" and p2_escolha == "tesoura") or
            (p1_escolha == "papel" and p2_escolha == "pedra") or
            (p1_escolha == "tesoura" and p2_escolha == "papel")
        ):
            resultado = f"🏆 <@{self.p1}> venceu!"
        else:
            resultado = f"🏆 <@{self.p2}> venceu!"

        embed = discord.Embed(
            title="⚔️ Duelo Finalizado",
            description=resultado,
            color=discord.Color.gold()
        )

        embed.add_field(name="Jogador 1", value=p1_escolha)
        embed.add_field(name="Jogador 2", value=p2_escolha)

        await interaction.channel.send(embed=embed)
        self.stop()

    @discord.ui.button(label="🪨 Pedra", style=discord.ButtonStyle.secondary)
    async def pedra(self, interaction, button):
        await self.process(interaction, "pedra")

    @discord.ui.button(label="📄 Papel", style=discord.ButtonStyle.primary)
    async def papel(self, interaction, button):
        await self.process(interaction, "papel")

    @discord.ui.button(label="✂️ Tesoura", style=discord.ButtonStyle.danger)
    async def tesoura(self, interaction, button):
        await self.process(interaction, "tesoura")

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    async def update(self, interaction, embed):
        await interaction.response.edit_message(embed=embed, view=self)

    # ======================
    # 🎮 JOGOS
    # ======================
    @discord.ui.button(label="Jogos", style=discord.ButtonStyle.primary, emoji="🎮")
    async def jogos(self, interaction, button):

        embed = discord.Embed(
            title="🎮 Jogos",
            color=discord.Color.blue(),
            description=(
                "**/adivinhar** → Tente acertar um número de 1 a 100\n"
                "**/anagrama** → Descubra a palavra embaralhada\n"
                "**/forca** → Jogo da forca simples\n"
                "**/ppt** → Pedra, papel e tesoura contra o bot\n"
                "**/dueloppt** → Desafie outro jogador no PPT"
            )
        )

        await self.update(interaction, embed)

    # ======================
    # 🎲 ALEATÓRIOS
    # ======================
    @discord.ui.button(label="Aleatórios", style=discord.ButtonStyle.success, emoji="🎲")
    async def aleatorios(self, interaction, button):

        embed = discord.Embed(
            title="🎲 Aleatórios",
            color=discord.Color.green(),
            description=(
                "**/dado** → Rola um dado com X lados\n"
                "**/escolha** → Escolhe entre duas opções\n"
                "**/caraoucoroa** → Sorteia cara ou coroa\n"
                "**/biscoito** → Recebe uma frase da sorte\n"
                "**/cantada** → Envia uma cantada para alguém"
            )
        )

        await self.update(interaction, embed)

    # ======================
    # 📊 INFO
    # ======================
    @discord.ui.button(label="Info", style=discord.ButtonStyle.secondary, emoji="📊")
    async def info(self, interaction, button):

        embed = discord.Embed(
            title="📊 Informações",
            color=discord.Color.grey(),
            description=(
                "**/ping** → Mostra latência do bot\n"
                "**/avatar** → Mostra avatar de um usuário\n"
                "**/serverinfo** → Informações do servidor\n"
                "**/userinfo** → Informações de um usuário"
            )
        )

        await self.update(interaction, embed)

    # ======================
    # 🛡️ STAFF
    # ======================
    @discord.ui.button(label="Staff", style=discord.ButtonStyle.danger, emoji="🛡️")
    async def staff(self, interaction, button):

        embed = discord.Embed(
            title="🛡️ Comandos de Moderação",
            color=discord.Color.red(),
            description=(
                "**/ban** → Bane um usuário do servidor\n"
                "**/mute** → Silencia um usuário por tempo\n"
                "**/unmute** → Remove o silêncio\n"
                "**/limpar** → Apaga mensagens do chat\n"
                "**/lock** → Bloqueia o envio de mensagens\n"
                "**/unlock** → Desbloqueia o canal"
            )
        )

        await self.update(interaction, embed)

# ======================================================
# AJUDA
# ======================================================

@bot.tree.command(name="ajuda")
async def ajuda(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎮 Painel de Ajuda",
        description="Use os botões abaixo 👇",
        color=discord.Color.purple()
    )

    await interaction.response.send_message(embed=embed, view=HelpView())

# ======================================================
# IA IMAGEM
# ======================================================

@bot.tree.command(name="imagem")
async def imagem(interaction: discord.Interaction, descricao: str):

    await interaction.response.defer()

    url = f"https://image.pollinations.ai/p/{urllib.parse.quote(descricao)}"
    r = requests.get(url)

    file = discord.File(io.BytesIO(r.content), filename="img.png")

    embed = discord.Embed(
        title="🎨 Imagem gerada",
        description=descricao,
        color=discord.Color.blue()
    )

    embed.set_image(url="attachment://img.png")

    await interaction.followup.send(embed=embed, file=file)

# ======================================================
# JOGOS
# ======================================================

@bot.tree.command(name="adivinhar")
async def adivinhar_cmd(interaction: discord.Interaction):
    adivinhar[interaction.guild.id] = random.randint(1, 100)
    await interaction.response.send_message("🎯 Adivinhe de 1 a 100")


@bot.tree.command(name="anagrama")
async def anagrama_cmd(interaction: discord.Interaction):

    palavra = random.choice(PALAVRAS)
    anagrama[interaction.guild.id] = palavra

    letras = list(palavra)
    random.shuffle(letras)

    await interaction.response.send_message("🔤 " + "".join(letras))


@bot.tree.command(name="forca")
async def forca_cmd(interaction: discord.Interaction):

    palavra = random.choice(PALAVRAS)
    forca[interaction.guild.id] = palavra

    await interaction.response.send_message("🔨 Jogo da forca iniciado!")

@bot.tree.command(name="dueloppt", description="Desafie alguém no PPTW PRO")
async def dueloppt(interaction: discord.Interaction, usuario: discord.Member):

    if usuario.bot:
        return await interaction.response.send_message("❌ Não pode desafiar bot.", ephemeral=True)

    if usuario.id == interaction.user.id:
        return await interaction.response.send_message("❌ Não pode se auto-desafiar.", ephemeral=True)

    embed = discord.Embed(
        title="⚔️ Duelo PPTW PRO",
        description=f"{interaction.user.mention} vs {usuario.mention}\n\nClique nos botões para jogar!",
        color=discord.Color.red()
    )

    view = PPTWView(interaction.user.id, usuario.id)

    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="ppt", description="Jogue Pedra, Papel e Tesoura contra o bot")
async def ppt(interaction: discord.Interaction, escolha: str):

    escolha = escolha.lower()
    opcoes = ["pedra", "papel", "tesoura"]

    if escolha not in opcoes:
        return await interaction.response.send_message(
            "❌ Escolha inválida! Use: pedra, papel ou tesoura.",
            ephemeral=True
        )

    bot_escolha = random.choice(opcoes)

    # Regras
    if escolha == bot_escolha:
        resultado = "🤝 Empate!"
        xp = 5
    elif (
        (escolha == "pedra" and bot_escolha == "tesoura") or
        (escolha == "papel" and bot_escolha == "pedra") or
        (escolha == "tesoura" and bot_escolha == "papel")
    ):
        resultado = "🏆 Você venceu!"
        xp = 10
    else:
        resultado = "💀 Você perdeu!"
        xp = 0

    embed = discord.Embed(
        title="✂️ Pedra, Papel e Tesoura",
        color=discord.Color.blue()
    )

    embed.add_field(name="Sua escolha", value=escolha.capitalize(), inline=True)
    embed.add_field(name="Bot", value=bot_escolha.capitalize(), inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)

    await interaction.response.send_message(embed=embed)
    
# ======================================================
# ALEATÓRIOS
# ======================================================

@bot.tree.command(name="dado")
async def dado(interaction: discord.Interaction, lados: int = 6):
    await interaction.response.send_message(f"🎲 {random.randint(1,lados)}")


@bot.tree.command(name="escolha")
async def escolha(interaction: discord.Interaction, op1: str, op2: str):
    await interaction.response.send_message(random.choice([op1, op2]))


@bot.tree.command(name="caraoucoroa")
async def caraoucoroa(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(MOEDA))


@bot.tree.command(name="biscoito")
async def biscoito(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(BISCOITOS))


@bot.tree.command(name="cantada")
async def cantada(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.send_message(f"{membro.mention} {random.choice(CANTADAS)}")

# ======================================================
# INFO
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
    await interaction.response.send_message(f"🏰 {g.name} | {g.member_count}")


@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    m = membro or interaction.user
    await interaction.response.send_message(f"👤 {m.name} | {m.id}")

# ======================================================
# STAFF
# ======================================================

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member):
    await membro.ban()
    await interaction.response.send_message("🔨 Banido")


@bot.tree.command(name="mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, minutos: int):
    await membro.timeout(discord.utils.utcnow() + timedelta(minutes=minutos))
    await interaction.response.send_message("🔇 Mutado")


@bot.tree.command(name="unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    await membro.timeout(None)
    await interaction.response.send_message("🔊 Desmutado")


@bot.tree.command(name="limpar")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, qtd: int):
    await interaction.channel.purge(limit=qtd)
    await interaction.response.send_message("🧹 Limpo", ephemeral=True)


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
# START
# ======================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise Exception("DISCORD_TOKEN não encontrado")

bot.run(TOKEN)
