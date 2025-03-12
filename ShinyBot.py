import discord
from discord.ext import commands
import json
import logging
from datetime import timedelta
import mysecrets

# Configuración de logs
logging.basicConfig(level=logging.INFO)

# Habilitar intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cargar palabras prohibidas
with open('banned_words.json', 'r') as f:
    banned_words = json.load(f)

# Diccionario para advertencias de usuarios
user_warnings = {}

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    triggered = any(
        word.lower() in content for lang in banned_words for word in banned_words[lang]
    )

    # Verificar si el mensaje contiene un enlace
    if any(prefix in content for prefix in ["http://", "https://", "www."]):
        triggered = True

    if triggered:
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

        # **Enviar el mensaje de advertencia SIEMPRE**
        await message.channel.send(f"{message.author.mention}, **Don't use inappropriate language!**")

        # **Registrar la advertencia**
        user_id = message.author.id
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        warning_count = user_warnings[user_id]

        # **Aplicar castigos según las advertencias**
        if warning_count >= 2:
            try:
                duration_map = {2: timedelta(minutes=5), 3: timedelta(hours=1), 4: timedelta(days=1)}
                if warning_count in duration_map:
                    duration = duration_map[warning_count]
                    await message.author.timeout_for(duration, reason=f"{warning_count} advertencias")
                    await message.channel.send(
                        f"{message.author.mention}, you have been muted for {duration} due to repeated violations."
                    )
                elif warning_count >= 5:
                    await message.guild.ban(message.author, reason="5 advertencias")
                    await message.channel.send(
                        f"{message.author.mention}, you have been permanently banned due to repeated violations."
                    )
            except Exception as e:
                logging.error(f"Error applying moderation: {e}")

    await bot.process_commands(message)

# 🔥 NUEVO COMANDO: PRUNE (BORRAR MENSAJES)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def prune(ctx, amount: int):
    """Elimina una cantidad de mensajes en el canal actual (máx 100)."""
    if amount <= 0 or amount > 100:
        await ctx.send("Por favor, elige un número entre **1 y 100**.")
        return

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 para incluir el comando
        await ctx.send(f"✅ **{len(deleted)-1} mensajes eliminados**.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ No tengo permisos para borrar mensajes.")
    except discord.HTTPException:
        await ctx.send("❌ Error al eliminar mensajes. Inténtalo de nuevo.")

# Comando de prueba para verificar que el bot funciona
@bot.command()
async def test(ctx):
    await ctx.send("¡El bot está funcionando correctamente!")

bot.run(mysecrets.Token)
