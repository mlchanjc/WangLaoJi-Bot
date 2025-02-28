import os
import dotenv
import discord
from discord.ext import commands
from image_handler import ImageSelectionView
from guess_image import init_game
from bot import bot

dotenv.load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")


@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Commands synced!")


@bot.command()
async def create(ctx):
    if ctx.message.reference is not None:
        reference_message = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )
        if len(reference_message.attachments) > 0 and reference_message.attachments[
            0
        ].content_type.startswith("image/"):
            view = ImageSelectionView(reference_message.attachments[0].url)
            await ctx.send("Choose a base image", view=view)
        else:
            await ctx.send("Please upload a valid image file.")


@bot.hybrid_command()
async def testbot(ctx):
    """testbot"""
    await ctx.send("i hate nig")


@bot.hybrid_command()
async def createimage(ctx, file: discord.Attachment):
    """Creates shit"""
    if file.content_type.startswith("image/"):
        view = ImageSelectionView(file.url)
        await ctx.send("Choose a base image", view=view)
    else:
        await ctx.send("Please upload a valid image file.")


@bot.hybrid_command()
async def guess(ctx):
    """Guess image"""
    await init_game(ctx)


bot.run(token)
