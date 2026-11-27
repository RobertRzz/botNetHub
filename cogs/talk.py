import discord
from discord import app_commands
from discord.ext import commands
from cogs.cargos import RolePanelView


class Talk(commands.Cog):
    """Permite que administradores enviem mensagens personalizadas como o bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="talk", description="Envia uma mensagem personalizada como o bot no canal atual.")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.choices(
        formato=[
            app_commands.Choice(name="Normal (texto)", value="normal"),
            app_commands.Choice(name="Embed (caixa)", value="embed"),
        ],
        anexo=[
            app_commands.Choice(name="Nenhum", value="nenhum"),
            app_commands.Choice(name="Lista de Cargos (botões)", value="cargos"),
        ],
    )
    @app_commands.describe(
        formato="Escolha se a mensagem vai como texto normal ou Embed.",
        mensagem="Texto da mensagem (use \\n para pular linha).",
        anexo="Opcional: anexa os botões de cargos junto à mensagem.",
        titulo="Opcional: título da caixa (usado apenas no formato Embed).",
    )
    async def talk(
        self,
        interaction: discord.Interaction,
        formato: app_commands.Choice[str],
        mensagem: str,
        anexo: app_commands.Choice[str] | None = None,
        titulo: str | None = None,
    ) -> None:
        if not interaction.channel or not isinstance(interaction.channel, discord.abc.Messageable):
            await interaction.response.send_message("Não foi possível enviar neste canal.", ephemeral=True)
            return

        texto = mensagem.replace("\\n", "\n")
        view = RolePanelView() if (anexo and anexo.value == "cargos") else None

        if formato.value == "embed":
            embed = discord.Embed(
                title=titulo or None,
                description=texto,
                color=discord.Color.blurple(),
            )
            await interaction.channel.send(embed=embed, view=view)
        else:
            await interaction.channel.send(content=texto, view=view)

        await interaction.response.send_message("✅ Mensagem enviada!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Talk(bot))
