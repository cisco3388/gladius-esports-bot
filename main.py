import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import Button, View
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ====== CONFIGURA QUI ======
TICKET_CATEGORY_NAME = "TICKET🎫"
STAFF_ROLE_IDS = [
    1535548341130362901,  # Ruolo 1 - metti l'ID vero
    1535586623218257940,  # Ruolo 2 - metti l'ID vero
    1535555615923896370,  # Ruolo 3 - metti l'ID vero
    444444444444444444,  # Ruolo 4 - metti l'ID vero
]
LOG_CHANNEL_NAME = "ticket-log"
# ===========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_channels and not any(r.id in STAFF_ROLE_IDS for r in interaction.user.roles):
            return await interaction.response.send_message("Solo lo staff può chiudere i ticket.", ephemeral=True)

        await interaction.response.send_message("Ticket in chiusura tra 5 secondi...", ephemeral=True)
        await interaction.channel.send(f"Ticket chiuso da {interaction.user.mention}")
        await interaction.channel.delete(delay=5)

class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Ticket Supporto", style=discord.ButtonStyle.green, custom_id="open_ticket", emoji="🎫")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower().replace(' ', '-')}")
        if existing:
            return await interaction.response.send_message(f"Hai già un ticket aperto: {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        for role_id in STAFF_ROLE_IDS:
            staff_role = guild.get_role(role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket di {interaction.user} | ID: {interaction.user.id}"
        )

        embed = discord.Embed(
            title="🎫 Ticket Supporto — Gladius eSports",
            description=f"Ciao {interaction.user.mention},\n\nLo staff ti risponderà a breve.\nDescrivi il tuo problema nel modo più chiaro possibile.\n\nPer chiudere il ticket usa il bottone qui sotto.",
            color=0x00FFAA,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Gladius eSports Support")

        staff_mentions = " ".join([f"<@&{role_id}>" for role_id in STAFF_ROLE_IDS])
        await channel.send(content=f"{interaction.user.mention} {staff_mentions}", embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"Ticket creato: {channel.mention}", ephemeral=True)

        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            log_embed = discord.Embed(title="Nuovo Ticket Aperto", color=0x00FF00)
            log_embed.add_field(name="Utente", value=f"{interaction.user} (`{interaction.user.id}`)")
            log_embed.add_field(name="Canale", value=channel.mention)
            log_embed.timestamp = datetime.utcnow()
            await log_channel.send(embed=log_embed)

@bot.event
async def on_ready():
    print(f"Gladius eSports online come {bot.user}")
    bot.add_view(TicketPanelView())
    bot.add_view(TicketCloseView())
    try:
        synced = await bot.tree.sync()
        print(f"Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(e)

@bot.command(name="setup-ticket")
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="Gladius eSports — Supporto",
        description="Hai bisogno di aiuto?\nClicca il bottone qui sotto per aprire un ticket privato con lo staff.\n\nRispondiamo il prima possibile.",
        color=0x00FFAA
    )
    embed.set_footer(text="Gladius eSports • Support System")
    await ctx.send(embed=embed, view=TicketPanelView())
    await ctx.message.delete()

@bot.tree.command(name="chiudi", description="Chiudi il ticket corrente")
async def chiudi(interaction: discord.Interaction):
    if not interaction.channel.name.startswith("ticket-"):
        return await interaction.response.send_message("Questo comando funziona solo nei ticket.", ephemeral=True)
    
    if not interaction.user.guild_permissions.manage_channels and not any(r.id in STAFF_ROLE_IDS for r in interaction.user.roles):
        return await interaction.response.send_message("Solo lo staff può chiudere i ticket.", ephemeral=True)

    await interaction.response.send_message("Ticket in chiusura...")
    await interaction.channel.delete(delay=3)

bot.run(TOKEN)
