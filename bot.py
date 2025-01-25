import os
import dotenv
import discord
from discord.ext import commands
from image_handler import ImageSelectionView

dotenv.load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!!!", intents=intents)


@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Commands synced!")


@bot.hybrid_command()
async def testbot(ctx):
    """testbot"""
    await ctx.send("Hello! I'm your Discord bot!")


@bot.hybrid_command()
async def createimage(ctx, file: discord.Attachment):
    """Creates shit"""
    if file.content_type.startswith("image/"):
        view = ImageSelectionView(file.url)
        await ctx.send("Choose a static image to append:", view=view)
    else:
        await ctx.send("Please upload a valid image file.")


bot.run(token)
