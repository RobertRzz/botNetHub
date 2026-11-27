import asyncio
import os
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import init_db

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COGS = [
    "cogs.boas_vindas",
    "cogs.talk",
    "cogs.comunidade",
    "cogs.seguranca",
    "cogs.cargos",
    "cogs.tickets",
    "cogs.reputacao",
    "cogs.oportunidades",
]


class ComunidadeBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await init_db()
        for cog in COGS:
            await self.load_extension(cog)
            print(f"[OK] Cog carregado: {cog}")

        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"[OK] Slash commands sincronizados no servidor {GUILD_ID}")
        else:
            await self.tree.sync()
            print("[OK] Slash commands sincronizados globalmente")

    async def on_ready(self) -> None:
        print(f"Bot online como {self.user} (ID: {self.user.id})")


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("Configure o DISCORD_TOKEN no arquivo .env antes de iniciar o bot.")
    async with ComunidadeBot() as bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
