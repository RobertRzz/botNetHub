import time
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from database import DB_PATH

REP_COOLDOWN_SECONDS = 3600  # 1 hora entre reputações dadas


class Reputacao(commands.Cog):
    """Sistema de reputação e economia interna (inspirado no Red-DiscordBot)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rep", description="Dá +1 de reputação para um membro que te ajudou.")
    async def rep(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Ajudou na comunidade") -> None:
        if membro.bot or membro.id == interaction.user.id:
            await interaction.response.send_message("Você não pode dar reputação para si mesmo ou para bots.", ephemeral=True)
            return

        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (interaction.user.id,))
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (membro.id,))

            async with db.execute("SELECT last_rep_at FROM users WHERE user_id = ?", (interaction.user.id,)) as cur:
                last_rep = (await cur.fetchone())[0]

            remaining = int(REP_COOLDOWN_SECONDS - (now - last_rep))
            if remaining > 0:
                mins = max(1, remaining // 60)
                await interaction.response.send_message(
                    f"⏳ Aguarde **{mins} minutos** para dar reputação novamente.", ephemeral=True
                )
                return

            await db.execute("UPDATE users SET last_rep_at = ? WHERE user_id = ?", (now, interaction.user.id))
            await db.execute("UPDATE users SET rep = rep + 1, coins = coins + 10 WHERE user_id = ?", (membro.id,))
            await db.commit()

            async with db.execute("SELECT rep FROM users WHERE user_id = ?", (membro.id,)) as cur:
                new_rep = (await cur.fetchone())[0]

        await interaction.response.send_message(
            f"⭐ {interaction.user.mention} deu **+1 rep** para {membro.mention} (Total: **{new_rep}**)\n"
            f"**Motivo:** {motivo}"
        )

    @app_commands.command(name="perfil", description="Mostra a reputação e moedas internas de um membro.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member | None = None) -> None:
        target = membro or interaction.user
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT rep, coins FROM users WHERE user_id = ?", (target.id,)) as cur:
                row = await cur.fetchone()

        rep, coins = row if row else (0, 0)
        embed = discord.Embed(title=f"Perfil de {target.display_name}", color=discord.Color.teal())
        embed.add_field(name="⭐ Reputação", value=str(rep), inline=True)
        embed.add_field(name="🪙 Moedas", value=str(coins), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ranking", description="Mostra o Top 10 membros com mais reputação.")
    async def ranking(self, interaction: discord.Interaction) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, rep FROM users ORDER BY rep DESC LIMIT 10") as cur:
                rows = await cur.fetchall()

        if not rows:
            await interaction.response.send_message("Ainda não há reputação registrada.", ephemeral=True)
            return

        lines = [f"**{idx}.** <@{uid}> — **{rep}** rep" for idx, (uid, rep) in enumerate(rows, start=1)]
        embed = discord.Embed(title="🏆 Ranking de Reputação", description="\n".join(lines), color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reputacao(bot))
