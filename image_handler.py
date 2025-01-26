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
            button = discord.ui.Button(
                label=get_file_name(img),
                style=discord.ButtonStyle.primary,
            )

            async def button_callback(interaction, img=img):
                is_base_bg, location, size = parse_filename(img)

                # Determine the paths based on whether it's a base background or not
                if is_base_bg:
                    bg_img_src = os.path.join(IMAGE_URL, img)
                    fg_img_src = self.user_image_url
                else:
                    bg_img_src = self.user_image_url
                    fg_img_src = os.path.join(IMAGE_URL, img)

                image_io = create_image(bg_img_src, fg_img_src, location, size)

                await interaction.message.edit(
                    content="",
                    attachments=[
                        discord.File(
                            image_io, filename=f"{get_file_name(img)}_result.png"
                        )
                    ],
                    view=None,
                )

            button.callback = button_callback
            self.add_item(button)


def get_file_name(file):
    return os.path.splitext(os.path.basename(file))[0].split("_")[0]


def open_image(source):
    """
    Open an image from a local file or a URL.

    Args:
        source (str): The file path of the local image or the URL of the image.

    Returns:
        Image: An Image object opened from the specified source.
    """
    if source.startswith("http://") or source.startswith("https://"):
        # It's a URL, download the image
        response = requests.get(source)
        response.raise_for_status()  # Raise an error for bad responses
        image = Image.open(BytesIO(response.content))
    else:
        # It's a local file
        image = Image.open(source)

    return image


def parse_filename(filename):
    """
    Parse the filename to extract parameters.

    Args:
        filename (str): The filename to parse.

    Returns:
        tuple: (position, size) where position is (x, y) and size is (width_percentage, height_percentage)
    """
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split("_")

    is_base_bg = parts[1] == "1"
    position_x = float(parts[2].strip("%")) / 100
    position_y = float(parts[3].strip("%")) / 100
    width_pct = float(parts[4].strip("%")) / 100
    height_pct = float(parts[5].strip("%")) / 100

    return is_base_bg, (position_x, position_y), (width_pct, height_pct)


def create_image(bg_img_src, fg_img_src, position, size):
    bg_img = open_image(bg_img_src)
    fg_img = open_image(fg_img_src)

    # Determine the smaller width
    min_width = min(bg_img.width, fg_img.width)

    # Calculate new heights maintaining aspect ratio
    bg_new_height = int((min_width / bg_img.width) * bg_img.height)
    fg_new_height = int((min_width / fg_img.width) * fg_img.height)

    # Resize both images to the same width while keeping the aspect ratio
    bg_img = bg_img.resize((min_width, bg_new_height), Image.LANCZOS)
    fg_img = fg_img.resize(
        (int(min_width * size[0]), int(fg_new_height * size[1])), Image.LANCZOS
    )

    # Create a new image with the width of the resized images and maximum height
    new_image = Image.new("RGB", (min_width, bg_new_height))

    # Paste the user image as the background
    new_image.paste(bg_img, (0, 0))

    # Paste the base image on top of the user image
    new_image.paste(
        fg_img,
        (
            int(new_image.width * position[0]),
            int(new_image.height * position[1]),
        ),
        fg_img.convert("RGBA") if fg_img.mode in ("RGBA", "LA") else None,
    )

    # Save the image to a BytesIO object instead of the filesystem
    result_image_io = BytesIO()
    new_image.save(result_image_io, format="PNG")
    result_image_io.seek(0)  # Rewind the BytesIO object to the beginning

    return result_image_io
