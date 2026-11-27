import os
import discord
from discord.ext import commands
from mensagens import BOAS_VINDAS


def _get_text_channel(guild: discord.Guild, env_key: str) -> discord.TextChannel | None:
    channel_id = int(os.getenv(env_key, "0") or 0)
    if not channel_id:
        return None
    ch = guild.get_channel(channel_id)
    return ch if isinstance(ch, discord.TextChannel) else None


class BoasVindas(commands.Cog):
    """Autorole e mensagens de entrada e saída configuráveis por ID no .env."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        role_id = int(os.getenv("AUTOROLE_ID", "0") or 0)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Autorole ao entrar no servidor")
                except discord.Forbidden:
                    pass

        channel = _get_text_channel(member.guild, "WELCOME_CHANNEL_ID")
        if channel:
            embed = discord.Embed(
                title=BOAS_VINDAS["entrada_titulo"],
                description=BOAS_VINDAS["entrada_descricao"].format(
                    member=member.mention,
                    member_count=member.guild.member_count,
                ),
                color=discord.Color.green(),
            )
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        channel = _get_text_channel(member.guild, "GOODBYE_CHANNEL_ID") or _get_text_channel(
            member.guild, "WELCOME_CHANNEL_ID"
        )
        if channel:
            embed = discord.Embed(
                title=BOAS_VINDAS["saida_titulo"],
                description=BOAS_VINDAS["saida_descricao"].format(
                    display_name=member.display_name,
                    username=member.name,
                ),
                color=discord.Color.orange(),
            )
            await channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BoasVindas(bot))
