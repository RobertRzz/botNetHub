import os
import discord
from discord import app_commands
from discord.ext import commands
from mensagens import OPORTUNIDADES


class OportunidadeModal(discord.ui.Modal, title="Publicar Oportunidade"):
    titulo = discord.ui.TextInput(label="Título da vaga ou parceria", placeholder="Ex: Procuro Editor de Vídeo", max_length=80)
    orcamento = discord.ui.TextInput(label="Orçamento / Modelo", placeholder="Ex: R$ 500/mês ou 50/50 sociedade", max_length=60)
    descricao = discord.ui.TextInput(
        label="Detalhes",
        style=discord.TextStyle.paragraph,
        placeholder="Explique o projeto, requisitos e como entrar em contato.",
        max_length=1000,
    )

    def __init__(self, target_env_key: str) -> None:
        super().__init__()
        self.target_env_key = target_env_key

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return
        channel_id = int(os.getenv(self.target_env_key, "0") or 0)
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            await interaction.response.send_message(
                f"Canal ou fórum não configurado/encontrado (`{self.target_env_key}` no `.env`).",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"{OPORTUNIDADES['titulo_prefixo']}{self.titulo.value}",
            description=self.descricao.value,
            color=discord.Color.green(),
        )
        embed.add_field(name=OPORTUNIDADES["campo_orcamento"], value=self.orcamento.value, inline=True)
        embed.add_field(name=OPORTUNIDADES["campo_autor"], value=interaction.user.mention, inline=True)

        if isinstance(channel, discord.ForumChannel):
            await channel.create_thread(name=self.titulo.value, embed=embed)
        else:
            await channel.send(embed=embed)

        await interaction.response.send_message(
            OPORTUNIDADES["confirmacao"].format(channel=channel.mention),
            ephemeral=True,
        )


class Oportunidades(commands.Cog):
    """Formulário padronizado para #vagas-e-freelas e #procura-se-parceiro."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="oportunidade", description="Publica uma vaga, freela ou busca por sócio de forma padronizada.")
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="Vaga / Freela", value="VAGAS_CHANNEL_ID"),
            app_commands.Choice(name="Parceiro / Sócio", value="PARCEIROS_CHANNEL_ID"),
        ]
    )
    async def oportunidade(self, interaction: discord.Interaction, tipo: app_commands.Choice[str]) -> None:
        await interaction.response.send_modal(OportunidadeModal(tipo.value))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Oportunidades(bot))
