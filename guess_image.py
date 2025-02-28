from datetime import datetime, timedelta
import hashlib
import math
from PIL import Image
from io import BytesIO
import discord
import os
import json
import random
import asyncio
import difflib
from bot import bot

time_limit = 20

active_game = None

with open("full_song_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def is_correct_guess(guess):
    global active_game
    item = active_game["item"]

    guess = guess.lower()

    item_fields = {
        "title": item["title"],
        "reading": item.get("reading", ""),
        "romonizedTitle": item.get("romonizedTitle", ""),
        "fullRomonizedTitle": item.get("fullRomonizedTitle", ""),
        "aliases": item.get("aliases", []),
    }

    """ def get_threshold(length):
        if length < 5:
            return 0.7
        elif length > 30:
            return 0.52
        return 0.35 * math.exp(-0.06 * (length - 5)) + 0.35 """

    def get_threshold(length):
        if length < 5:
            return 0.6
        elif length > 30:
            return 0.45
        return 0.2 * math.exp(-0.1 * (length - 5)) + 0.45

    for field_name, field_value in item_fields.items():
        if (
            isinstance(field_value, str) and len(field_value) >= 3
        ):  # Check only valid string fields
            threshold = get_threshold(len(field_value))
            similarity = difflib.SequenceMatcher(
                None, guess, field_value.lower()
            ).ratio()
            """ print(
                f"Similarity for {field_name}: {similarity:.2f} (Threshold: {threshold:.2f})"
            ) """
            if similarity > threshold:
                return True

    # Check aliases
    for alias in item_fields["aliases"]:
        if len(alias) >= 3:
            similarity = difflib.SequenceMatcher(None, guess, alias.lower()).ratio()
            threshold = get_threshold(len(alias))
            """ print(
                f"Similarity for alias: {similarity:.2f} (Threshold: {threshold:.2f})"
            ) """
            if similarity > threshold:
                return True

    return False


async def wait_for_guess(ctx):
    global active_game

    def check(m):
        return m.channel == ctx.channel and m.author != bot.user

    while True:
        try:
            current_time = datetime.now()
            end_time = active_game["end_time"]
            time_difference = (end_time - current_time).total_seconds()

            guess_msg = await bot.wait_for(
                "message", check=check, timeout=time_difference
            )

            if is_correct_guess(guess_msg.content):
                await send_correct_message(ctx, guess_msg)
                break

        except asyncio.TimeoutError:
            await send_times_up_message(ctx)
            break

        except asyncio.CancelledError:
            break

    active_game = None


async def init_game(ctx):
    global active_game
    # Check if a game is already active in this channel
    if active_game != None:
        # Cancel the previous game logic
        active_game["task"].cancel()
        active_game = None  # Remove the existing game state

    # Randomly select an item from the JSON data
    item = random.choice(data)
    image_path = get_file_path(item)

    # Check if the image exists
    if not os.path.exists(image_path):
        await ctx.send("Image not found!")
        return

    # Send the image to the channel
    await send_start_message(ctx, image_path)

    # Set the game active for this channel
    active_game = {
        "item": item,
        "start_time": datetime.now(),
        "end_time": datetime.now() + timedelta(seconds=time_limit),
    }

    """ print(item["title"]) """

    # Run the waiting for guess logic in a separate task
    active_game["task"] = asyncio.create_task(wait_for_guess(ctx))


class NewGameView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        button = discord.ui.Button(
            label="New game",
            style=discord.ButtonStyle.green,
        )

        async def button_callback(interaction):
            await init_game(self.ctx)
            await interaction.message.edit(
                view=None,
            )

        button.callback = button_callback
        self.add_item(button)


class SkipGameView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        button = discord.ui.Button(
            label="⏩",
            style=discord.ButtonStyle.red,
        )

        async def button_callback(interaction):
            await send_skip_message(self.ctx)
            global active_game
            if active_game != None:
                # Cancel the previous game logic
                active_game["task"].cancel()
                active_game = None  # Remove the existing game state
            await interaction.message.edit(
                view=None,
            )

        button.callback = button_callback
        self.add_item(button)


async def send_start_message(ctx, file_path: str):
    # Extract the filename from the file path
    filename = hash_filename(file_path)

    # Create the embed
    embed = discord.Embed(
        title="Guess the song!",
        description=f"You have {time_limit} seconds to guess the song.",
    )

    # Get the cropped image as a BytesIO object
    cropped_image_bytes = get_random_square_fraction(file_path, 0.4)

    # Create a Discord file from the BytesIO object
    file = discord.File(cropped_image_bytes, filename=filename)

    # Set the image using the filename
    embed.set_image(url=f"attachment://{filename}")

    view = SkipGameView(ctx)

    # Send the message with the file and embed
    await ctx.send(
        f"Game started by {ctx.author.mention}", file=file, embed=embed, view=view
    )


async def send_correct_message(ctx, msg):
    # Extract the filename from the file path
    item = active_game["item"]
    file_path = get_file_path(item)
    filename = hash_filename(file_path)

    # Create the embed
    embed = discord.Embed(
        description=f"**Answer**: {item['title']}\n\n**Artist**: {item['artist']}\n**Category**: {item['category']}\n",
    )
    file = discord.File(file_path, filename=filename)

    # Set the image using the filename
    embed.set_image(url=f"attachment://{filename}")

    view = NewGameView(ctx)

    # Send the message with the file and embed
    await ctx.send(
        f"{msg.author.mention} has the correct answer!",
        file=file,
        embed=embed,
        view=view,
    )


async def send_times_up_message(ctx):
    # Extract the filename from the file path
    item = active_game["item"]
    file_path = get_file_path(item)
    filename = hash_filename(file_path)

    # Create the embed
    embed = discord.Embed(
        description=f"**Answer**: {item['title']}\n\n**Artist**: {item['artist']}\n**Category**: {item['category']}\n",
    )
    file = discord.File(file_path, filename=filename)

    # Set the image using the filename
    embed.set_image(url=f"attachment://{filename}")

    view = NewGameView(ctx)

    # Send the message with the file and embed
    await ctx.send("Time's up!", file=file, embed=embed, view=view)


async def send_skip_message(ctx):
    # Extract the filename from the file path
    item = active_game["item"]
    file_path = get_file_path(item)
    filename = hash_filename(file_path)

    # Create the embed
    embed = discord.Embed(
        description=f"**Answer**: {item['title']}\n\n**Artist**: {item['artist']}\n**Category**: {item['category']}\n",
    )
    file = discord.File(file_path, filename=filename)

    # Set the image using the filename
    embed.set_image(url=f"attachment://{filename}")

    view = NewGameView(ctx)

    # Send the message with the file and embed
    await ctx.send("Skipped!", file=file, embed=embed, view=view)


def get_random_square_fraction(image_path, fraction):
    """
    Select a random square fraction from an image.

    :param image_path: Path to the input image.
    :param fraction: The fraction of the image size (0 < fraction <= 1).
    :return: A BytesIO object containing the cropped image.
    """
    # Open the image
    with Image.open(image_path) as img:
        # Get dimensions
        img_width, img_height = img.size

        # Calculate the size of the square
        square_size = int(min(img_width, img_height) * fraction)

        # Randomly select the top left corner for the square
        x = random.randint(0, img_width - square_size)
        y = random.randint(0, img_height - square_size)

        # Crop the image to get the square fraction
        square_image = img.crop((x, y, x + square_size, y + square_size))

        # Save cropped image to BytesIO
        img_byte_arr = BytesIO()
        square_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)  # Reset the pointer to the start of the stream

        return img_byte_arr


def get_file_path(item=None):
    global active_game
    if item == None:
        if active_game != None:
            item = active_game["item"]
        else:
            return None

    item_id = item["songId"]
    _, file_extension = os.path.splitext(item["imageName"])

    return f"images/{item_id}{file_extension}"


def hash_filename(file_path):
    filename = os.path.basename(file_path)
    _, file_extension = os.path.splitext(filename)
    filename_bytes = filename.encode("utf-8")
    hash_object = hashlib.sha256()
    hash_object.update(filename_bytes)
    hashed_filename = hash_object.hexdigest()

    return hashed_filename + file_extension
