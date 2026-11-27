import os
import discord
from discord import app_commands
from discord.ext import commands


async def _send_to_text_or_forum(
    channel: discord.TextChannel | discord.ForumChannel,
    title: str,
    embed: discord.Embed,
) -> discord.Message | None:
    if isinstance(channel, discord.ForumChannel):
        thread_with_msg = await channel.create_thread(name=title[:100], embed=embed)
        return thread_with_msg.message
    return await channel.send(embed=embed)


class Comunidade(commands.Cog):
    """Comandos de sugestão e changelog da comunidade."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="sugestao", description="Envia uma sugestão para a comunidade votar.")
    @app_commands.describe(titulo="Resumo curto da sugestão.", descricao="Explique sua ideia em detalhes.")
    async def sugestao(self, interaction: discord.Interaction, titulo: str, descricao: str) -> None:
        if not interaction.guild:
            return

        channel_id = int(os.getenv("SUGESTOES_CHANNEL_ID", "0") or 0)
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            if isinstance(interaction.channel, (discord.TextChannel, discord.ForumChannel)):
                channel = interaction.channel
            else:
                await interaction.response.send_message(
                    "Canal `SUGESTOES_CHANNEL_ID` não encontrado.", ephemeral=True
                )
                return

        embed = discord.Embed(
            title=f"💡 {titulo}",
            description=descricao,
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Sugestão enviada por {interaction.user.display_name}")

        msg = await _send_to_text_or_forum(channel, f"💡 {titulo}", embed)
        if msg:
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")

        await interaction.response.send_message(f"✅ Sugestão enviada em {channel.mention}!", ephemeral=True)

    @app_commands.command(name="changelog", description="Publica uma atualização/novidade do servidor.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(versao="Versão ou título da atualização.", novidades="O que mudou (use \\n para pular linha).")
    async def changelog(self, interaction: discord.Interaction, versao: str, novidades: str) -> None:
        if not interaction.guild:
            return

        channel_id = int(os.getenv("CHANGELOG_CHANNEL_ID", "0") or 0)
        channel = (interaction.guild.get_channel(channel_id) if channel_id else None) or interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            await interaction.response.send_message("Não foi possível publicar neste canal.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🚀 Atualização — {versao}",
            description=novidades.replace("\\n", "\n"),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Publicado por {interaction.user.display_name}")

        await _send_to_text_or_forum(channel, f"🚀 {versao}", embed)
        await interaction.response.send_message(f"✅ Changelog publicado em {channel.mention}!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Comunidade(bot))
