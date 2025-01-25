import os
import discord
from discord.ext import commands

token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!!!", intents=intents)


@bot.command()
@commands.has_permissions(administrator=True)
async def synccommands(ctx):
    await bot.tree.sync()
    await ctx.send("Commands synced!")


@bot.hybrid_command()
async def hello(ctx):
    await ctx.send("Hello! I'm your Discord bot!")


bot.run(token)
