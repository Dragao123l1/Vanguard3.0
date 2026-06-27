import os
import discord
import random
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- INFRAESTRUTURA ---
app = Flask('')
@app.route('/')
def home(): return "Vanguard Operante!"
Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

# --- CONFIGURAÇÃO ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
client = MongoClient(os.getenv("MONGO_URI"))
db = client["vanguard"]
usuarios = db["usuarios"]

# --- FUNÇÕES DE DADOS ---
def get_user(uid):
    user = usuarios.find_one({"user_id": str(uid)})
    if not user:
        user = {"user_id": str(uid), "xp": 0, "coins": 100}
        usuarios.insert_one(user)
    return user

def update_user(uid, xp_inc, coin_inc):
    usuarios.update_one({"user_id": str(uid)}, {"$inc": {"xp": xp_inc, "coins": coin_inc}}, upsert=True)

# --- COMANDOS ---
@bot.tree.command(name="ajuda", description="Exibe o painel de comandos do bot")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Central de Ajuda - Vanguard",
        description="Confira abaixo a lista de todos os comandos disponíveis:",
        color=discord.Color.blue()
    )
    
    # Jogos
    embed.add_field(
        name="🎮 Jogos & Diversão", 
        value=(
            "**/anagrama** - Desembaralhe a palavra\n"
            "**/forca** - Tente adivinhar a palavra\n"
            "**/ppt** - Duelo de Pedra, Papel e Tesoura"
        ), 
        inline=False
    )
    
    # Economia
    embed.add_field(
        name="💰 Economia & Perfil", 
        value=(
            "**/perfil** - Veja seu saldo, XP e nível\n"
            "**/daily** - Resgate suas moedas diárias\n"
            "**/apostar** - Tente a sorte com suas moedas"
        ), 
        inline=False
    )
    
    # Utilidades
    embed.add_field(
        name="🛠️ Utilidades", 
        value=(
            "**/ping** - Latência do bot\n"
            "**/servidor** - Info do servidor\n"
            "**/ajuda** - Exibe este menu"
        ), 
        inline=False
    )
    
    # Staff
    embed.add_field(
        name="🛡️ Staff (Moderadores)", 
        value=(
            "**/ban** - Bane um membro\n"
            "**/unban** - Remove banimento\n"
            "**/kick** - Expulsa um membro\n"
            "**/mute** - Silencia um membro\n"
            "**/unmute** - Remove silenciamento\n"
            "**/limpar** - Apaga mensagens\n"
            "**/warn** - Avisa um membro\n"
            "**/anunciar** - Faz um anúncio"
        ), 
        inline=False
    )
    
    embed.set_footer(text="Vanguard Bot | Mantenha a ordem e divirta-se!")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else "")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="anagrama", description="Desafio de anagrama")
async def anagrama(interaction: discord.Interaction):
    p = random.choice(PALAVRAS)
    l = list(p); random.shuffle(l)
    await interaction.response.send_message(f"🔤 Desembaralhe: `{ ''.join(l) }`")

@bot.tree.command(name="forca", description="Jogo da forca")
async def forca(interaction: discord.Interaction):
    p = random.choice(PALAVRAS)
    await interaction.response.send_message(f"🔨 Forca: `{' _ ' * len(p)}`")

@bot.tree.command(name="perfil", description="Veja seu XP, Nível e Dinheiro")
async def perfil(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    xp = user.get("xp", 0)
    coins = user.get("coins", 0)
    level = xp // 100
    await interaction.response.send_message(f"👤 **{interaction.user.name}**\n⭐ Nível: {level} ({xp} XP)\n💰 Moedas: {coins}")

@bot.tree.command(name="daily", description="Resgate suas moedas diárias")
async def daily(interaction: discord.Interaction):
    update_user(interaction.user.id, 10, 100)
    await interaction.response.send_message("💰 Resgataste 100 moedas e 10 XP!")

@bot.tree.command(name="apostar", description="Aposte moedas")
async def apostar(interaction: discord.Interaction, valor: int, palpite: int):
    user = get_user(interaction.user.id)
    if user["coins"] < valor: return await interaction.response.send_message("❌ Saldo insuficiente.")
    
    num = random.randint(1, 10)
    if palpite == num:
        update_user(interaction.user.id, 20, valor)
        await interaction.response.send_message(f"🎉 Ganhaste! O número era {num}. (+20 XP)")
    else:
        update_user(interaction.user.id, 0, -valor)
        await interaction.response.send_message(f"❌ Perdeste! O número era {num}.")

@bot.tree.command(name="ppt", description="Duelo PPT")
async def ppt(interaction: discord.Interaction):
    class PPTView(discord.ui.View):
        @discord.ui.button(label="Pedra", style=discord.ButtonStyle.secondary)
        async def pedra(self, i, b):
            update_user(i.user.id, 20, 0)
            await i.response.send_message("Escolheste Pedra! (+20 XP)")
    await interaction.response.send_message("Escolhe:", view=PPTView())

@bot.tree.command(name="ping", description="Verifica a latência do bot e a resposta do sistema")
async def ping(interaction: discord.Interaction):
    # Calcula a latência em milissegundos
    latencia = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"A minha latência atual é de **{latencia}ms**.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="servidor", description="Exibe informações detalhadas sobre o servidor")
async def servidor(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(
        title=f"Informações de {guild.name}",
        color=discord.Color.blue()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.add_field(name="👑 Dono", value=guild.owner, inline=True)
    embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="🆔 ID do Servidor", value=guild.id, inline=True)
    
    await interaction.response.send_message(embed=embed)

# 1. BANIR UM UTILIZADOR
@bot.tree.command(name="ban", description="Bane um membro do servidor")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    await membro.ban(reason=motivo)
    await interaction.response.send_message(f"🔨 {membro.name} foi banido. Motivo: {motivo}")

# 2. EXPULSAR UM UTILIZADOR
@bot.tree.command(name="kick", description="Expulsa um membro do servidor")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    await membro.kick(reason=motivo)
    await interaction.response.send_message(f"👢 {membro.name} foi expulso. Motivo: {motivo}")

# 3. LIMPAR O CHAT (PURGE)
@bot.tree.command(name="limpar", description="Apaga um número de mensagens")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int):
    if quantidade > 100: quantidade = 100
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.response.send_message(f"🧹 {len(deleted)} mensagens apagadas!", ephemeral=True)

# 4. SILENCIAR (MUTE) POR TEMPO
@bot.tree.command(name="mute", description="Silencia um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member):
    # Nota: Requer cargo de 'Muted' configurado no servidor
    await membro.edit(timed_out_until=discord.utils.utcnow() + discord.timedelta(minutes=10))
    await interaction.response.send_message(f"🤐 {membro.name} foi silenciado por 10 minutos.")

# 5. AVISAR (WARN) - (Salvo no Mongo)
@bot.tree.command(name="warn", description="Avisa um membro")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, membro: discord.Member, aviso: str):
    usuarios.update_one({"user_id": str(membro.id)}, {"$push": {"avisos": aviso}}, upsert=True)
    await interaction.response.send_message(f"⚠️ {membro.name} recebeu um aviso: {aviso}")

# 6. DESBANIR
@bot.tree.command(name="unban", description="Remove o banimento de um utilizador")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = discord.Object(id=int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"🔓 Utilizador com ID {user_id} foi desbanido.")

@bot.tree.command(name="anunciar", description="Faz um anúncio oficial com foto e menção")
@app_commands.checks.has_permissions(administrator=True)
async def anunciar(interaction: discord.Interaction, 
                   titulo: str, 
                   mensagem: str, 
                   imagem_url: str = None, 
                   mencionar_todos: bool = False, 
                   canal: discord.TextChannel = None):
    
    canal_alvo = canal or interaction.channel
    
    # Prepara o texto da menção caso o usuário escolha True
    texto_mencao = "@everyone" if mencionar_todos else ""
    
    embed = discord.Embed(
        title=f"📢 {titulo}",
        description=mensagem,
        color=discord.Color.blue()
    )
    
    if imagem_url:
        embed.set_image(url=imagem_url)
        
    embed.set_footer(text=f"Anunciado por: {interaction.user.name}")
    
    # Envia a menção junto com o Embed
    await canal_alvo.send(content=texto_mencao, embed=embed)
    await interaction.response.send_message(f"✅ Anúncio enviado para {canal_alvo.mention}!", ephemeral=True)

@bot.tree.command(name="unmute", description="Remove o silenciamento de um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    # Definir o timeout como None remove o silenciamento
    await membro.edit(timed_out_until=None)
    
    await interaction.response.send_message(f"✅ {membro.name} foi desmutado com sucesso.")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ Bot online e comandos sincronizados!")

bot.run(os.getenv("DISCORD_TOKEN"))
