import os
import io
import random
import asyncio
import urllib.parse
import requests
import discord

from datetime import timedelta
from flask import Flask
from threading import Thread

from discord.ext import commands
from discord import app_commands

from supabase import create_client, Client

# ======================================================
# FLASK
# ======================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Arcad operante!"

Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=10000
    ),
    daemon=True
).start()

# ======================================================
# BOT
# ======================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ======================================================
# SUPABASE
# ======================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL não encontrada.")

if not SUPABASE_KEY:
    raise Exception("SUPABASE_KEY não encontrada.")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ======================================================
# SISTEMA XP
# ======================================================

def adicionar_xp(user_id: int, quantidade: int):

    resultado = (
        supabase.table("usuarios")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    if resultado.data:

        xp_atual = resultado.data[0]["xp"]

        (
            supabase.table("usuarios")
            .update({
                "xp": xp_atual + quantidade
            })
            .eq("user_id", str(user_id))
            .execute()
        )

    else:

        (
            supabase.table("usuarios")
            .insert({
                "user_id": str(user_id),
                "xp": quantidade
            })
            .execute()
        )


def obter_xp(user_id: int):

    resultado = (
        supabase.table("usuarios")
        .select("xp")
        .eq("user_id", str(user_id))
        .execute()
    )

    if resultado.data:
        return resultado.data[0]["xp"]

    return 0


def definir_xp(user_id: int, xp: int):

    resultado = (
        supabase.table("usuarios")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    if resultado.data:

        (
            supabase.table("usuarios")
            .update({
                "xp": xp
            })
            .eq("user_id", str(user_id))
            .execute()
        )

    else:

        (
            supabase.table("usuarios")
            .insert({
                "user_id": str(user_id),
                "xp": xp
            })
            .execute()
        )


def obter_rank_global():

    resultado = (
        supabase.table("usuarios")
        .select("*")
        .order(
            "xp",
            desc=True
        )
        .limit(10)
        .execute()
    )

    return resultado.data


# ======================================================
# VARIÁVEIS GLOBAIS
# ======================================================

jogos_ativos = {}

anagramas_ativos = {}

forca_ativos = {}

ppt_duelos = {}

PALAVRAS_ANAGRAMA = [
    "computador", "discord", "inteligencia", "teclado", "celular", "planeta", "biologia", "geografia", "bot", 
    "internet", "games", "controle", "suporte", "servidor", "developer", "cafe", "algoritmo", "database", "tecnologia", 
    "hardware", "software", "monitor", "mouse", "navegador", "criptografia", "seguranca", "nuvem", "astronomia", "galaxia", 
    "universo", "fisica", "quimica", "matematica", "historia", "literatura", "filosofia", "psicologia", "musica", "cinema", 
    "fotografia", "pintura", "escultura", "arquitetura", "engenharia", "medicina", "economia", "politica", "idioma", "viagem",
    "foguete", "bateria", "televisao", "lampada", "caminho", "mochila", "floresta", "oceano", "montanha", "deserto",
    "inverno", "verao", "outono", "primavera", "festival", "cidade", "paisagem", "bicicleta", "aventura", "desafio",
    "misterio", "fantasia", "codigo", "cripto", "memoria", "processo", "sistema", "rede", "grafico", "estudo",
    "desenho", "esporte", "corrida", "futebol", "basquete", "natacao", "viola", "piano", "teatro", "danca"
]

LISTA_CANTADAS = [
    "Você não é Google, mas tem tudo o que eu procuro.", "Você é o queijo do meu hambúrguer.", "Você é a página que faltava no meu livro.", 
    "Se beleza fosse tempo, você seria uma eternidade.", "Gata, você não é Wi-Fi, mas sinto uma conexão.", "Você é o café que eu precisava hoje.", 
    "Onde é que eu clico para te ter no meu coração?", "Você não é mapa, mas estou perdido em você.", "Seu sorriso é a minha dose diária de alegria.", 
    "Você é a tradução da felicidade.", "Meu coração disparou quando te vi.", "Você é uma obra-prima.", "Você merece o mundo.", 
    "Sua presença ilumina qualquer ambiente.", "Beijar você deve ser como ver o sol nascer.", "Você é o motivo da minha insônia.", 
    "Gata, você é um erro 404?", "Seus olhos são como o mar.", "Você é a melodia que não sai da cabeça.", "Você é o doce que falta na minha vida.", 
    "Tem um espelho no seu bolso?", "Se você fosse um filme, seria o favorito.", "Você é a estrela do meu céu.", "Gata, você é açúcar?", 
    "Você é o presente que a vida me deu.", "Não sou fotógrafo, mas te imagino comigo.", "Você é mais bonita que o pôr do sol.", 
    "Seu abraço é o meu lugar favorito.", "Você é a peça que faltava no meu quebra-cabeça.", "Você é tão linda que deveria vir com aviso de perigo.", 
    "Você é a calma no meio da tempestade.", "Seu riso é o meu som preferido.", "Você é o que me faz querer ser melhor.", 
    "Gata, você é o Wi-Fi?", "Você é a letra da minha música favorita.", "Você é o sol que brilha no meu dia.", "Seu carinho é a melhor coisa.", 
    "Você é o sonho que se tornou realidade.", "Gata, você tem um mapa?", "Você é a perfeição em forma de gente.", 
    "Seus olhos brilham mais que estrelas.", "Você é o tesouro que eu sempre quis.", "Você é o brilho nos meus dias cinzentos.", 
    "Nossa conexão é perfeita.", "Você é incrível.", "Você é o motivo do meu sorriso matinal.", "Seus abraços são como abraçar uma nuvem.", 
    "Você é a cor do meu arco-íris.", "Você é a paz.", "Você é a luz do meu caminho.", "Seu beijo é o meu paraíso.", 
    "Você é o sol no meu inverno.", "Sua presença me dá choque.", "Você é a música que acalma minha alma.", 
    "Você é o meu destino final.", "Você é a beleza que o mundo esqueceu de ver.", "Seu olhar diz tudo.", "Você é o meu abrigo seguro.", 
    "Não consigo parar de te ler.", "Você é o ar que me falta.", "Se o beijo fosse palavra, o nosso seria um poema.", 
    "Você não é vidente, mas já previ nosso futuro.", "Sua beleza causa desvio de atenção.", "Você é o capítulo mais feliz da minha vida.", 
    "Não sou astrônomo, mas vi um planeta no seu olhar.", "Seu abraço cura qualquer tristeza.", "Você é a nota perfeita da minha vida.", 
    "Você é a sorte que eu pedi a Deus.", "Seu amor é o meu norte.", "Você é o meu sim favorito.", "Você é o motivo do meu brilho no olho.",
    "Se beleza fosse pecado, você não teria perdão.", "Você é o motivo da minha felicidade.", "Você é o sol no meu dia cinza.",
    "Você é o presente mais bonito que recebi.", "Seu sorriso vale mais que ouro.", "Você é a minha inspiração constante.",
    "Você é a pessoa mais incrível que já conheci.", "Você é o que faltava no meu dia.", "Você é a minha doce melodia.",
    "Você é a definição de perfeição.", "Você é a minha melhor companhia.", "Você é o sol que ilumina meu caminho.",
    "Você é a estrela do meu show.", "Você é o motivo dos meus sonhos.", "Você é a minha paz.", "Você é o meu tudo.",
    "Você é a razão do meu sorriso.", "Você é a minha melhor escolha."
]

FRASES_BISCOITO = [
    "A sorte favorece os audazes.", "Grandes mudanças estão por vir.", "A felicidade é uma escolha.", "O sucesso está a um passo.", 
    "Mantenha a calma e siga em frente.", "Um novo amigo trará alegria.", "Seu esforço será recompensado.", "Confie na sua intuição.", 
    "Seu futuro é brilhante.", "Dê um tempo para si mesmo.", "A paciência é uma virtude.", "Algo maravilhoso vai acontecer.", 
    "A vida é um presente, aproveite.", "Você é mais forte do que imagina.", "Grandes coisas vêm para quem espera.", 
    "O amor está no ar.", "Seja a mudança que deseja ver no mundo.", "O momento certo é agora.", 
    "A jornada é tão importante quanto o destino.", "Acredite nos seus sonhos.", "Sua mente é um jardim.", 
    "A simplicidade é o segredo da paz.", "Aproveite as pequenas alegrias.", "A coragem é sua melhor aliada.", 
    "Hoje é um bom dia para começar.", "Sua criatividade não tem limites.", "Tudo se ajeita.", 
    "Seja grato por tudo.", "A verdade libertará você.", "Sua bondade é sua maior força.", 
    "Novas oportunidades surgirão.", "O otimismo ém a chave do sucesso.", "Siga o seu coração.", 
    "A vida é uma aventura.", "Sua dedicação dará frutos.", "O sol sempre volta a brilhar.", 
    "Aprenda com seus erros.", "Sua voz tem poder.", "Mantenha o foco no positivo.", 
    "A esperança é eterna.", "A harmonia está dentro de você.", "Sua sabedoria crescerá.", 
    "A vida recompensa o esforço.", "O presente é o único lugar que importa.", "Seja gentil consigo mesmo.", 
    "A vida flui como um rio.", "Sua intuição está correta.", "O equilíbrio é essencial.", 
    "A alegria é contagiante.", "Suas escolhas definem seu caminho.", "Mantenha o coração aberto.", 
    "A vitória é uma questão de tempo.", "Sua resiliência é inspiradora.", "O aprendizado nunca termina.", 
    "Seu valor é imensurável.", "A amizade é um tesouro.", "O sucesso exige persistência.", 
    "A beleza está nos olhos de quem vê.", "Sua energia atrai o bem.", "O silêncio também traz respostas.", 
    "A mudança é inevitável.", "Sua autenticidade é seu brilho.", "O futuro pertence a você.", 
    "A paz é o seu maior bem.", "A sorte acompanha a preparação.", "Seu caminho será iluminado.", 
    "A vida ama você.", "O riso é o melhor remédio.", "A esperança é o primeiro passo.", 
    "Sua jornada é única.", "O universo tem planos incríveis para você hoje.", "Acredite no seu potencial.",
    "A magia acontece onde você está.", "Seu riso transforma o mundo.", "Tudo flui para o melhor.",
    "Você está brilhando hoje.", "O amanhã começa agora.", "Sua luz é inesgotável.",
    "A bondade abre caminhos.", "Sua calma é sua força.", "O mundo precisa da sua energia.",
    "Você é capaz de grandes coisas.", "Siga seus sonhos com coragem.", "O presente é sagrado.",
    "A vida é plena.", "Sua sabedoria é um presente.", "A felicidade mora nos detalhes.",
    "Você faz a diferença.", "Tudo dará certo.", "Seu brilho próprio encanta.", "A paz começa em você."
]

MOEDA = ["Cara", "Coroa"]

class PPTView(discord.ui.View):
    def __init__(self, jogador1, jogador2):
        super().__init__(timeout=60)
        self.jogador1 = jogador1
        self.jogador2 = jogador2
        self.escolhas = {}

    async def processar(self, interaction, escolha):
        if interaction.user.id not in [self.jogador1, self.jogador2]:
            await interaction.response.send_message("❌ Você não participa deste duelo.", ephemeral=True)
            return

        self.escolhas[interaction.user.id] = escolha
        await interaction.response.send_message(f"✅ Você escolheu **{escolha}**", ephemeral=True)

        if len(self.escolhas) == 2:
            p1 = self.escolhas[self.jogador1]
            p2 = self.escolhas[self.jogador2]

            if p1 == p2:
                resultado = "🤝 Empate!"
            elif ((p1 == "pedra" and p2 == "tesoura") or (p1 == "papel" and p2 == "pedra") or (p1 == "tesoura" and p2 == "papel")):
                resultado = f"🏆 <@{self.jogador1}> venceu!"
                adicionar_xp(self.jogador1, 30)
            else:
                resultado = f"🏆 <@{self.jogador2}> venceu!"
                adicionar_xp(self.jogador2, 30)

            embed = discord.Embed(title="⚔️ Duelo Finalizado", description=resultado, color=discord.Color.green())
            embed.add_field(name="Jogador 1", value=p1.capitalize())
            embed.add_field(name="Jogador 2", value=p2.capitalize())
            await interaction.channel.send(embed=embed)
            self.stop()

    @discord.ui.button(label="🪨 Pedra", style=discord.ButtonStyle.secondary)
    async def pedra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar(interaction, "pedra")

    @discord.ui.button(label="📄 Papel", style=discord.ButtonStyle.primary)
    async def papel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar(interaction, "papel")

    @discord.ui.button(label="✂️ Tesoura", style=discord.ButtonStyle.danger)
    async def tesoura(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar(interaction, "tesoura")

# ======================================================
# EVENTOS
# ======================================================

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print("=" * 40)
        print(f"✅ Bot conectado como {bot.user}")
        print(f"📡 Latência: {round(bot.latency * 1000)}ms")
        print("✅ Slash Commands sincronizados.")
        print("=" * 40)
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")


@bot.event
async def on_message(message: discord.Message):

    # Ignora mensagens de bots
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None

    # ======================================================
    # JOGO DE ADIVINHAÇÃO
    # ======================================================

    if guild_id in jogos_ativos:

        try:
            tentativa = int(message.content)

            numero = jogos_ativos[guild_id]

            if tentativa == numero:

                adicionar_xp(message.author.id, 20)

                await message.reply(
                    "🎉 Parabéns! Você acertou o número!\n⭐ +20 XP"
                )

                del jogos_ativos[guild_id]

            elif tentativa < numero:

                await message.reply(
                    "📈 O número secreto é **maior**."
                )

            else:

                await message.reply(
                    "📉 O número secreto é **menor**."
                )

        except ValueError:
            # Ignora mensagens que não são números
            pass

    # ======================================================
    # JOGO DO ANAGRAMA
    # ======================================================

    elif guild_id in anagramas_ativos:

        resposta = message.content.strip().lower()

        palavra = anagramas_ativos[guild_id].lower()

        if resposta == palavra:

            adicionar_xp(message.author.id, 25)

            embed = discord.Embed(
                title="🏆 Anagrama",
                description=(
                    f"Parabéns, {message.author.mention}!\n\n"
                    f"Você acertou a palavra **{palavra}**.\n"
                    "⭐ Você recebeu **25 XP**."
                ),
                color=discord.Color.green()
            )

            await message.reply(embed=embed)

            del anagramas_ativos[guild_id]

        else:

            try:
                await message.add_reaction("❌")
            except discord.HTTPException:
                pass

    # ======================================================
    # JOGO DA FORCA
    # ======================================================

    if guild_id in forca_ativos:

        jogo = forca_ativos[guild_id]

        letra = message.content.strip().lower()

        # Aceita apenas uma letra
        if len(letra) != 1 or not letra.isalpha():
            await bot.process_commands(message)
            return

        # Evita repetir letra
        if letra in jogo["letras"]:
            await message.add_reaction("⚠️")
            await bot.process_commands(message)
            return

        jogo["letras"].append(letra)

        # Conta erro
        if letra not in jogo["palavra"]:
            jogo["erros"] += 1

        palavra_exibida = " ".join(
            l if l in jogo["letras"] else "_"
            for l in jogo["palavra"]
        )

        # ==========================
        # Vitória
        # ==========================

        if "_" not in palavra_exibida:

            adicionar_xp(message.author.id, 30)

            embed = discord.Embed(
                title="🏆 Você venceu!",
                description=(
                    f"A palavra era **{jogo['palavra']}**\n\n"
                    "⭐ Você ganhou **30 XP**."
                ),
                color=discord.Color.green()
            )

            await message.reply(embed=embed)

            del forca_ativos[guild_id]

        # ==========================
        # Derrota
        # ==========================

        elif jogo["erros"] >= 6:

            embed = discord.Embed(
                title="💀 Você perdeu!",
                description=f"A palavra era **{jogo['palavra']}**",
                color=discord.Color.red()
            )

            await message.reply(embed=embed)

            del forca_ativos[guild_id]

        # ==========================
        # Continua jogando
        # ==========================

        else:

            embed = discord.Embed(
                title="🔨 Jogo da Forca",
                description=f"`{palavra_exibida}`",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="❌ Erros",
                value=f"{jogo['erros']}/6",
                inline=False
            )

            embed.add_field(
                name="🔤 Letras utilizadas",
                value=", ".join(jogo["letras"]),
                inline=False
            )

            embed.set_footer(
                text="Digite outra letra no chat."
            )

            await message.reply(embed=embed)

    # ======================================================
    # PROCESSA OS COMANDOS DO BOT
    # ======================================================

    await bot.process_commands(message)

# ======================================================
# FIM DOS EVENTOS
# ======================================================


# --- SLASH COMMANDS ---
@bot.tree.command(name="ajuda", description="Menu de ajuda do arcad")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Vanguard - Central de Ajuda",
        description="Confira todos os comandos disponíveis:",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="🎨 IA & Imagens",
        value="`/imagem` → Gera imagens por IA",
        inline=False
    )

    embed.add_field(
        name="🎮 Jogos",
        value=(
            "`/adivinhar` → Jogo de adivinhação\n"
            "`/anagrama` → Desafio de palavras\n"
            "`/dado` → Rola um dado\n"
            "`/forca` → Jogo da forca\n"
            "`/caraoucoroa` → Jogue cara ou coroa\n"
            "`/escolha` → Arcad escolhe uma opção aleatória"
        ),
        inline=False
    )

    embed.add_field(
        name="✨ Diversão",
        value=(
            "`/biscoito` → Frase da sorte\n"
            "`/cantada` → Envia uma cantada"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Utilidades",
        value=(
            "`/ping` → Latência do bot\n"
            "`/avatar` → Mostra um avatar\n"
            "`/userinfo` → Informações de usuário\n"
            "`/serverinfo` → Informações do servidor\n"
            "`/calcular` → Resolve cálculos\n`/xp` → Mostra seu XP\n`/level` → Mostra seu nível\n`/rankxp` → Ranking do servidor\n`/globalxp` → Ranking global"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Administração (apenas Staff)",
        value=(
            "`/limpar` → Limpa mensagens\n"
            "`/mute` → Silencia um membro\n"
            "`/unmute` → Remove o silêncio\n"
            "`/ban` → Bane um membro\n"
            "`/aviso` → envia avisos para o servidor\n"
            "`/lock`→ bloqueia o canal\n"
            "`/unlock`→ desbloqueia o canal"
        ),
        inline=False
    )

    embed.set_footer(text="Vanguard • Desenvolvido porwinchesstter 🚀")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="imagem", description="Gera uma imagem via IA")
async def imagem(interaction: discord.Interaction, descricao: str):
    await interaction.response.defer()

    try:
        url = f"https://image.pollinations.ai/p/{urllib.parse.quote(descricao)}?seed={random.randint(1,9999)}"

        resposta = requests.get(url, timeout=60)

        arquivo = discord.File(
            io.BytesIO(resposta.content),
            filename="arte.png"
        )

        embed = discord.Embed(
            title="🎨 Arte Gerada",
            description=descricao,
            color=discord.Color.purple()
        )

        embed.set_image(url="attachment://arte.png")

        await interaction.followup.send(
            embed=embed,
            file=arquivo
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Erro ao gerar imagem: {e}"
            )

@bot.tree.command(name="adivinhar", description="Jogo 1-100")
async def adivinhar(interaction: discord.Interaction):
    jogos_ativos[interaction.guild.id] = random.randint(1, 100)
    await interaction.response.send_message("🎯 Jogo iniciado! Digite um número de 1 a 100 no chat.")

@bot.tree.command(name="anagrama", description="Desafio de anagrama")
async def anagrama(interaction: discord.Interaction):
    p = random.choice(PALAVRAS_ANAGRAMA)
    anagramas_ativos[interaction.guild.id] = p
    l = list(p.upper()); random.shuffle(l)
    await interaction.response.send_message(f"🔤 Desafio: `{''.join(l)}` (Digite a palavra correta no chat)")

    
@bot.tree.command(name="caraoucoroa", description="Jogue cara ou coroa")
async def caraoucoroa(interaction: discord.Interaction):

    adicionar_xp(interaction.user.id, 5)

    resultado = random.choice(MOEDA)

    embed = discord.Embed(
        title="🪙 Cara ou Coroa",
        description=f"Resultado: **{resultado}**",
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="forca", description="Jogo da forca")
async def forca(interaction: discord.Interaction):

    palavra = random.choice(PALAVRAS_ANAGRAMA).lower()

    forca_ativos[interaction.guild.id] = {
        "palavra": palavra,
        "letras": [],
        "erros": 0
    }

    palavra_oculta = " ".join("_" for _ in palavra)

    embed = discord.Embed(
        title="🔨 Jogo da Forca",
        description=f"Palavra:\n`{palavra_oculta}`",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="❌ Erros",
        value="0/6",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dado", description="Gira um dado")
async def dado(interaction: discord.Interaction, lados: int = 6):
    await interaction.response.send_message(f"🎲 Resultado: **{random.randint(1, lados)}**")

@bot.tree.command(name="escolha", description="Escolhe entre duas opções")
async def escolha(
    interaction: discord.Interaction,
    opcao1: str,
    opcao2: str
):
    escolhida = random.choice([opcao1, opcao2])

    embed = discord.Embed(
        title="🤔 Escolha Aleatória",
        description=f"Eu escolhi: **{escolhida}**",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="biscoito", description="Sorte")
async def biscoito(interaction: discord.Interaction):
    await interaction.response.send_message(f"🥠 {random.choice(FRASES_BISCOITO)}")

@bot.tree.command(name="cantada", description="Envia cantada")
async def cantada(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.send_message(f"💘 {membro.mention}, {random.choice(LISTA_CANTADAS)}")

@bot.tree.command(name="avatar", description="Mostra avatar")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    m = membro or interaction.user
    await interaction.response.send_message(embed=discord.Embed(title=f"Avatar de {m.name}").set_image(url=m.display_avatar.url))

@bot.tree.command(name="ping", description="Latência")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! **{round(bot.latency * 1000)}ms**")

@bot.tree.command(name="serverinfo", description="Info do servidor")
async def serverinfo(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏰 Servidor: {interaction.guild.name} | Membros: {interaction.guild.member_count}")

@bot.tree.command(name="userinfo", description="Info de usuário")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    m = membro or interaction.user
    await interaction.response.send_message(f"👤 {m.name} | ID: {m.id}")

@bot.tree.command(name="calcular", description="Matemática")
async def calcular(interaction: discord.Interaction, expressao: str):
    try: await interaction.response.send_message(f"🧮 Resultado: **{eval(expressao)}**")
    except: await interaction.response.send_message("❌ Expressão inválida.")

@bot.tree.command(name="limpar", description="Limpa chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, qtd: int):
    await interaction.channel.purge(limit=qtd)
    await interaction.response.send_message("🧹 Limpo.", ephemeral=True)


@bot.tree.command(name="aviso", description="Envia um aviso para o servidor")
@app_commands.checks.has_permissions(manage_guild=True)
async def aviso(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str,
    imagem: str = None
):

    embed = discord.Embed(
        title=f"📢 {titulo}",
        description=mensagem,
        color=discord.Color.gold()
    )

    embed.set_footer(
        text=f"Aviso enviado por {interaction.user}"
    )

    # Ícone do servidor como miniatura
    if interaction.guild.icon:
        embed.set_thumbnail(
            url=interaction.guild.icon.url
        )

    # Adiciona imagem apenas se for informada
    if imagem:
        embed.set_image(url=imagem)

    await interaction.response.send_message(
        "✅ Aviso enviado com sucesso!",
        ephemeral=True
    )

    await interaction.channel.send(
        "@here",
        embed=embed
    )
@bot.tree.command(name="mute", description="Muta membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, min: int):
    await membro.timeout(discord.utils.utcnow() + timedelta(minutes=min))
    await interaction.response.send_message(f"🔇 {membro.name} mutado.")

@bot.tree.command(name="unmute", description="Desmuta")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    await membro.timeout(None)
    await interaction.response.send_message(f"🔊 {membro.name} desmutado.")

@bot.tree.command(name="lock", description="Bloqueia o canal")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 Canal bloqueado!"
    )

@bot.tree.command(name="unlock", description="Desbloqueia o canal")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = True

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 Canal desbloqueado!"
    )
    
@bot.tree.command(name="ban", description="Banir")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member):
    await membro.ban(); await interaction.response.send_message(f"🔨 {membro.name} banido.")

@bot.tree.command(name="ppt", description="Pedra, Papel e Tesoura contra o Vanguard")
@app_commands.choices(escolha=[
    app_commands.Choice(name="Pedra", value="pedra"),
    app_commands.Choice(name="Papel", value="papel"),
    app_commands.Choice(name="Tesoura", value="tesoura")
])
async def ppt(interaction: discord.Interaction, escolha: app_commands.Choice[str]):
    jogador = escolha.value
    bot_escolha = random.choice(["pedra", "papel", "tesoura"])

    if jogador == bot_escolha:
        resultado = "🤝 Empate!"
        xp = 5
    elif (
        (jogador == "pedra" and bot_escolha == "tesoura") or
        (jogador == "papel" and bot_escolha == "pedra") or
        (jogador == "tesoura" and bot_escolha == "papel")
    ):
        resultado = "🏆 Você venceu!"
        xp = 20
    else:
        resultado = "💀 Você perdeu!"
        xp = 0

    if xp > 0:
        adicionar_xp(interaction.user.id, xp)

    embed = discord.Embed(
        title="✂️ Pedra, Papel e Tesoura",
        color=discord.Color.blue()
    )
    embed.add_field(name="Sua escolha", value=jogador.capitalize(), inline=False)
    embed.add_field(name="Escolha do Vanguard", value=bot_escolha.capitalize(), inline=False)
    embed.add_field(name="Resultado", value=f"{resultado}\n⭐ +{xp} XP", inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="dueloppt", description="Desafie alguém para Pedra, Papel e Tesoura")
async def dueloppt(interaction: discord.Interaction, usuario: discord.Member):

    if usuario.bot:
        await interaction.response.send_message(
            "❌ Você não pode desafiar bots.",
            ephemeral=True
        )
        return

    if usuario.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Você não pode desafiar a si mesmo.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚔️ Duelo PPT",
        description=(
            f"{interaction.user.mention} desafiou {usuario.mention}\n\n"
            "Escolham uma opção nos botões abaixo."
        ),
        color=discord.Color.red()
    )

    embed.add_field(name="Prêmio", value="🏆 30 XP", inline=False)

    await interaction.response.send_message(
        embed=embed,
        view=PPTView(interaction.user.id, usuario.id)
    )

@bot.tree.command(name="xp", description="Mostra seu XP")
async def xp(interaction: discord.Interaction):
    xp_usuario = obter_xp(interaction.user.id)

    await interaction.response.send_message(
        f"⭐ Você possui **{xp_usuario} XP**"
    )

@bot.tree.command(name="level", description="Mostra seu nível")
async def level(interaction: discord.Interaction):

    xp_usuario = obter_xp(interaction.user.id)

    nivel = xp_usuario // 100

    await interaction.response.send_message(
        f"🏆 Nível: **{nivel}**\n"
        f"⭐ XP: **{xp_usuario}**"
    )

@bot.tree.command(name="rankxp", description="Ranking do servidor")
async def rankxp(interaction: discord.Interaction):

    resultado = (
        supabase.table("usuarios")
        .select("*")
        .order("xp", desc=True)
        .execute()
    )

    membros = {str(m.id): m for m in interaction.guild.members}

    texto = ""
    posicao = 1

    for usuario in resultado.data:

        if usuario["user_id"] in membros:

            membro = membros[usuario["user_id"]]

            texto += (
                f"{posicao}. {membro.display_name} - "
                f"{usuario['xp']} XP\n"
            )

            posicao += 1

            if posicao > 10:
                break

    if texto == "":
        texto = "Nenhum jogador encontrado."

    embed = discord.Embed(
        title="🏆 Ranking do Servidor",
        description=texto,
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="globalxp", description="Ranking Global")
async def globalxp(interaction: discord.Interaction):

    resultado = (
        supabase.table("usuarios")
        .select("*")
        .order("xp", desc=True)
        .limit(10)
        .execute()
    )

    texto = ""

    for posicao, usuario in enumerate(resultado.data, start=1):

        texto += (
            f"{posicao}. "
            f"{usuario['user_id']} - "
            f"{usuario['xp']} XP\n"
        )

    if texto == "":
        texto = "Nenhum jogador encontrado."

    embed = discord.Embed(
        title="🌎 Ranking Global",
        description=texto,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

# ======================================================
# INICIAR BOT
# ======================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise Exception("DISCORD_TOKEN não encontrado nas variáveis de ambiente.")

bot.run(TOKEN)
