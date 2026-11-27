import os
import re
import time
from collections import defaultdict, deque
from datetime import timedelta
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from database import DB_PATH

STAFF_ROLES = {"STAFF", "Administrador", "Moderador"}
INVITE_REGEX = re.compile(r"(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)", re.IGNORECASE)
SCAM_KEYWORDS = ("pix dobrado", "urubu do pix", "dobro seu pix", "dinheiro fácil garantido", "nitro grátis")
SPAM_WINDOW_SECONDS = 6
SPAM_MAX_MESSAGES = 5


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    raw_ids = os.getenv("STAFF_ROLE_IDS", "")
    staff_ids = {int(x.strip()) for x in raw_ids.split(",") if x.strip().isdigit()}
    return any(r.id in staff_ids for r in member.roles)


async def get_log_channel(guild: discord.Guild) -> discord.TextChannel | None:
    channel_id = int(os.getenv("LOGS_CHANNEL_ID", "0") or 0)
    if not channel_id:
        return None
    ch = guild.get_channel(channel_id)
    return ch if isinstance(ch, discord.TextChannel) else None


async def log_mod_action(
    guild: discord.Guild | None,
    title: str,
    moderator: discord.abc.User,
    target: str,
    details: str = "",
) -> None:
    if not guild:
        return
    log_ch = await get_log_channel(guild)
    if not log_ch:
        return
    embed = discord.Embed(title=title, color=discord.Color.red())
    embed.add_field(name="Moderador", value=moderator.mention, inline=True)
    embed.add_field(name="Alvo", value=target, inline=True)
    if details:
        embed.add_field(name="Detalhes", value=details, inline=False)
    await log_ch.send(embed=embed)


class Seguranca(commands.Cog):
    """AutoMod, anti-spam, anti-golpe, logs e moderação (inspirado em YAGPDB e Red-DiscordBot)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg_history: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=SPAM_MAX_MESSAGES))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild or not isinstance(message.author, discord.Member):
            return
        if is_staff(message.author):
            return

        content_lower = message.content.lower()

        # 1. Anti-convite de outros servidores
        if INVITE_REGEX.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, não é permitido enviar convites de outros servidores aqui.",
                delete_after=6,
            )
            return

        # 2. Filtro de palavras-chave de golpe
        if any(word in content_lower for word in SCAM_KEYWORDS):
            await message.delete()
            await message.author.timeout(timedelta(minutes=10), reason="Possível tentativa de golpe/scam")
            log_ch = await get_log_channel(message.guild)
            if log_ch:
                await log_ch.send(
                    f"🚨 **Anti-Golpe:** {message.author.mention} teve mensagem removida e recebeu timeout de 10m.\n"
                    f"Conteúdo: `{message.content[:200]}`"
                )
            return

        # 3. Anti-spam por frequência
        now = time.monotonic()
        history = self.msg_history[message.author.id]
        history.append(now)
        if len(history) == SPAM_MAX_MESSAGES and (now - history[0]) <= SPAM_WINDOW_SECONDS:
            history.clear()
            await message.author.timeout(timedelta(minutes=5), reason="Spam / flood no chat")
            await message.channel.send(
                f"{message.author.mention} recebeu timeout de 5 minutos por spam.",
                delete_after=8,
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild or not message.content:
            return
        log_ch = await get_log_channel(message.guild)
        if log_ch and log_ch.id != message.channel.id:
            embed = discord.Embed(title="🗑️ Mensagem Apagada", color=discord.Color.orange())
            embed.add_field(name="Autor", value=message.author.mention, inline=True)
            embed.add_field(name="Canal", value=message.channel.mention, inline=True)
            embed.add_field(name="Conteúdo", value=message.content[:1000], inline=False)
            await log_ch.send(embed=embed)

    @app_commands.command(name="warn", description="Aplica uma advertência a um membro.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membro: discord.Member, motivo: str) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO warnings (user_id, moderator_id, reason) VALUES (?, ?, ?)",
                (membro.id, interaction.user.id, motivo),
            )
            await db.commit()
            async with db.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ?", (membro.id,)) as cur:
                total = (await cur.fetchone())[0]

        await interaction.response.send_message(
            f"⚠️ {membro.mention} recebeu uma advertência (**{total}ª**).\n**Motivo:** {motivo}"
        )

    @app_commands.command(name="warnings", description="Lista as advertências de um membro.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, membro: discord.Member) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT reason, created_at FROM warnings WHERE user_id = ? ORDER BY id DESC LIMIT 10",
                (membro.id,),
            ) as cur:
                rows = await cur.fetchall()

        if not rows:
            await interaction.response.send_message(f"{membro.mention} não possui advertências.", ephemeral=True)
            return

        desc = "\n".join(f"• `{created_at}` — {reason}" for reason, created_at in rows)
        embed = discord.Embed(title=f"Advertências de {membro.display_name}", description=desc, color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot or not before.guild or before.content == after.content:
            return
        log_ch = await get_log_channel(before.guild)
        if log_ch:
            embed = discord.Embed(title="✏️ Mensagem Editada", color=discord.Color.gold())
            embed.add_field(name="Autor", value=before.author.mention, inline=True)
            embed.add_field(name="Canal", value=before.channel.mention, inline=True)
            embed.add_field(name="Antes", value=before.content[:500] or "*(vazio)*", inline=False)
            embed.add_field(name="Depois", value=after.content[:500] or "*(vazio)*", inline=False)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.roles == after.roles:
            return
        added = [r.mention for r in after.roles if r not in before.roles]
        removed = [r.mention for r in before.roles if r not in after.roles]
        if not added and not removed:
            return
        log_ch = await get_log_channel(after.guild)
        if log_ch:
            embed = discord.Embed(title="🎭 Cargos Atualizados", color=discord.Color.blurple())
            embed.add_field(name="Membro", value=after.mention, inline=False)
            if added:
                embed.add_field(name="Adicionados", value=", ".join(added), inline=True)
            if removed:
                embed.add_field(name="Removidos", value=", ".join(removed), inline=True)
            await log_ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        if member.bot or before.channel == after.channel:
            return
        log_ch = await get_log_channel(member.guild)
        if not log_ch:
            return
        if before.channel is None and after.channel is not None:
            desc = f"🔊 {member.mention} entrou no canal de voz **{after.channel.name}**."
        elif before.channel is not None and after.channel is None:
            desc = f"🔇 {member.mention} saiu do canal de voz **{before.channel.name}**."
        else:
            desc = f"🔁 {member.mention} mudou de **{before.channel.name}** para **{after.channel.name}**."
        await log_ch.send(desc)

    @app_commands.command(name="clear", description="Apaga uma quantidade de mensagens do canal.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, quantidade: app_commands.Range[int, 1, 100]) -> None:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(f"🧹 {len(deleted)} mensagens apagadas.", ephemeral=True)

    @app_commands.command(name="kick", description="Expulsa um membro do servidor.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado") -> None:
        await membro.kick(reason=motivo)
        await log_mod_action(interaction.guild, "👢 Membro Expulso", interaction.user, membro.mention, f"Motivo: {motivo}")
        await interaction.response.send_message(f"👢 {membro.mention} foi expulso. Motivo: `{motivo}`")

    @app_commands.command(name="ban", description="Bane um membro do servidor.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado") -> None:
        await membro.ban(reason=motivo)
        await log_mod_action(interaction.guild, "🔨 Membro Banido", interaction.user, membro.mention, f"Motivo: {motivo}")
        await interaction.response.send_message(f"🔨 {membro.mention} foi banido. Motivo: `{motivo}`")

    @app_commands.command(name="unban", description="Remove o banimento de um usuário pelo ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str) -> None:
        if not interaction.guild:
            return
        user = await self.bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=f"Desbanido por {interaction.user}")
        await log_mod_action(interaction.guild, "✅ Usuário Desbanido", interaction.user, f"`{user}` (`{user.id}`)")
        await interaction.response.send_message(f"✅ `{user}` (`{user.id}`) foi desbanido.")

    @app_commands.command(name="mute", description="Silencia (timeout) um membro por X minutos.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        minutos: app_commands.Range[int, 1, 40320] = 10,
        motivo: str = "Não informado",
    ) -> None:
        await membro.timeout(timedelta(minutes=minutos), reason=motivo)
        await log_mod_action(
            interaction.guild, "🔇 Membro Silenciado", interaction.user, membro.mention, f"Duração: {minutos} min | Motivo: {motivo}"
        )
        await interaction.response.send_message(f"🔇 {membro.mention} silenciado por **{minutos} min**. Motivo: `{motivo}`")

    @app_commands.command(name="unmute", description="Remove o silenciamento (timeout) de um membro.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membro: discord.Member) -> None:
        await membro.timeout(None, reason=f"Timeout removido por {interaction.user}")
        await log_mod_action(interaction.guild, "🔊 Silenciamento Removido", interaction.user, membro.mention)
        await interaction.response.send_message(f"🔊 {membro.mention} teve o silenciamento removido.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Seguranca(bot))
