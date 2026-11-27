import io
import os
import discord
from discord import app_commands
from discord.ext import commands
from database import next_ticket_number

STAFF_ROLES = {"STAFF", "Administrador", "Moderador"}
TICKET_CATEGORIES = [
    ("Dúvida Geral", "❓", "duvida"),
    ("Denunciar Golpe", "🚨", "denuncia"),
    ("Validação / Faturando", "💰", "validacao"),
    ("Parcerias", "🤝", "parceria"),
]


class CloseTicketView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not isinstance(interaction.channel, discord.TextChannel) or not interaction.guild:
            return

        await interaction.response.send_message("Gerando transcrição e fechando o ticket...")

        lines = []
        async for msg in interaction.channel.history(limit=300, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"[{timestamp}] {msg.author} ({msg.author.id}): {msg.content}")

        transcript = "\n".join(lines) or "Sem mensagens registradas."
        log_id = int(os.getenv("LOGS_CHANNEL_ID", "0") or 0)
        log_ch = interaction.guild.get_channel(log_id) if log_id else None
        if isinstance(log_ch, discord.TextChannel):
            file = discord.File(io.BytesIO(transcript.encode("utf-8")), filename=f"{interaction.channel.name}.txt")
            await log_ch.send(
                f"📁 **Ticket fechado:** `{interaction.channel.name}` por {interaction.user.mention}",
                file=file,
            )

        await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user}")


class TicketButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str, slug: str) -> None:
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.primary, custom_id=f"ticket_open:{slug}")
        self.slug = slug
        self.topic_label = label

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        number = await next_ticket_number()
        channel_name = f"ticket-{self.slug}-{number:03d}"

        category = discord.utils.get(interaction.guild.categories, name="VALIDAÇÃO & SUPORTE")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for role_name in STAFF_ROLES:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_ch = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket de {interaction.user} | Assunto: {self.topic_label}",
        )

        embed = discord.Embed(
            title=f"🎫 {self.topic_label} (#{number:03d})",
            description=f"Olá {interaction.user.mention}, descreva sua solicitação abaixo. A equipe já vai atender você.",
            color=discord.Color.green(),
        )
        await ticket_ch.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket criado: {ticket_ch.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        for label, emoji, slug in TICKET_CATEGORIES:
            self.add_item(TicketButton(label, emoji, slug))


class Tickets(commands.Cog):
    """Sistema de tickets com botões e transcrição (inspirado em Open Ticket e Modmail)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(CloseTicketView())

    @app_commands.command(name="painel_tickets", description="Publica o painel de abertura de tickets no canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_tickets(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🎫 Central de Atendimento & Validação",
            description="Selecione abaixo o tipo de atendimento que você precisa:",
            color=discord.Color.gold(),
        )
        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message("Painel de tickets publicado!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tickets(bot))
