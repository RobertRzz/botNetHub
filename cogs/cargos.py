import os
import discord
from discord import app_commands
from discord.ext import commands

ROLE_OPTIONS = [
    ("Tráfego Pago", "📊", "ROLE_TRAFEGO_ID"),
    ("Copywriting", "✍️", "ROLE_COPY_ID"),
    ("Vendas & Prospecção", "💼", "ROLE_VENDAS_ID"),
    ("Design / Dev", "💻", "ROLE_DESIGN_DEV_ID"),
    ("Automação & IA", "🤖", "ROLE_AUTOMACAO_IA_ID"),
    ("Iniciante", "🌱", "ROLE_INICIANTE_ID"),
]


class RoleButton(discord.ui.Button):
    def __init__(self, role_name: str, emoji: str, env_key: str) -> None:
        super().__init__(
            label=role_name,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_toggle:{env_key}",
        )
        self.role_name = role_name
        self.env_key = env_key

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return
        role_id = int(os.getenv(self.env_key, "0") or 0)
        role = interaction.guild.get_role(role_id) if role_id else None
        if not role:
            await interaction.response.send_message(
                f"Cargo `{self.role_name}` não configurado (`{self.env_key}` no `.env`).", ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Auto-cargo removido pelo membro")
            await interaction.response.send_message(f"❌ Cargo **{role.name}** removido.", ephemeral=True)
        else:
            await interaction.user.add_roles(role, reason="Auto-cargo selecionado pelo membro")
            await interaction.response.send_message(f"✅ Cargo **{role.name}** adicionado!", ephemeral=True)


class RolePanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        for role_name, emoji, env_key in ROLE_OPTIONS:
            self.add_item(RoleButton(role_name, emoji, env_key))


class Cargos(commands.Cog):
    """Painel persistente de auto-cargos por interesse (inspirado no YAGPDB)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(RolePanelView())

    @app_commands.command(name="painel_cargos", description="Envia o painel de seleção de cargos no canal atual.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_cargos(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🎯 Escolha suas áreas de interesse",
            description="Clique nos botões abaixo para adicionar ou remover seus cargos na comunidade:",
            color=discord.Color.blurple(),
        )
        await interaction.channel.send(embed=embed, view=RolePanelView())
        await interaction.response.send_message("Painel de cargos publicado!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Cargos(bot))
