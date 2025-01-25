from PIL import Image
import requests
from io import BytesIO
import discord
import os

IMAGE_URL = "base_images"


class ImageSelectionView(discord.ui.View):
    def __init__(self, user_image_url):
        super().__init__()
        self.user_image_url = user_image_url

        # Read all base image names in the directory
        self.base_images = [
            f for f in os.listdir(IMAGE_URL) if f.endswith((".png", ".jpg", ".jpeg"))
        ]

        # Create a button for each base image
        for img in self.base_images:
            button = discord.ui.Button(label=img, style=discord.ButtonStyle.primary)

            async def button_callback(interaction, img_name=img):
                image_io = create_image(
                    os.path.join(IMAGE_URL, img_name), self.user_image_url
                )
                await interaction.message.edit(
                    content="Result:",
                    attachments=[
                        discord.File(image_io, filename=f"{img_name}_result.png")
                    ],
                    view=None,
                )

            button.callback = button_callback
            self.add_item(button)


def create_image(base_image_path, user_image_url):
    # Open the base image
    base_image = Image.open(base_image_path)

    # Download the user's image
    response = requests.get(user_image_url)
    user_image = Image.open(BytesIO(response.content))

    # Create the new image
    new_image = Image.new(
        "RGB", (base_image.width, base_image.height + user_image.height)
    )
    new_image.paste(base_image, (0, 0))
    new_image.paste(user_image, (0, base_image.height))

    # Save the image to a BytesIO object instead of the filesystem
    result_image_io = BytesIO()
    new_image.save(result_image_io, format="PNG")
    result_image_io.seek(0)  # Rewind the BytesIO object to the beginning

    return result_image_io
