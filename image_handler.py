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

                image_io = create_image(
                    is_base_bg,
                    os.path.join(IMAGE_URL, img),
                    self.user_image_url,
                    location,
                    size,
                )

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
        tuple: (is_base_bg, position, size) where position is (x, y) and size is (width_percentage, height_percentage).
    """
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split("_")

    is_base_bg = parts[1] == "1"
    if is_base_bg:
        position_x = float(parts[2].strip("%")) / 100
        position_y = float(parts[3].strip("%")) / 100
        width_pct = float(parts[4].strip("%")) / 100
        height_pct = float(parts[5].strip("%")) / 100

        return is_base_bg, (position_x, position_y), (width_pct, height_pct)
    else:
        return is_base_bg, None, None


def create_image(is_base_bg, base_img_src, user_img_src, position, size):
    if is_base_bg:
        bg_img = open_image(base_img_src).convert("RGBA")
        fg_img = open_image(user_img_src).convert("RGBA")

        # Determine the smaller width between background and foreground
        result_width = min(bg_img.width, fg_img.width)

        # Calculate new height for the background maintaining aspect ratio
        bg_aspect_ratio = bg_img.height / bg_img.width
        result_height = int(result_width * bg_aspect_ratio)

        # Resize the background image
        bg_img = bg_img.resize((result_width, result_height), Image.LANCZOS)

        # Calculate target dimensions for the foreground based on allocated size
        target_width = int(result_width * size[0])
        target_height = int(result_height * size[1])

        # Handle cases where target dimensions might be zero
        if target_width <= 0 or target_height <= 0:
            raise ValueError(
                "Allocated size results in invalid dimensions for the foreground image."
            )

        # Calculate scaling factor to cover the target size while maintaining aspect ratio
        original_fg_width, original_fg_height = fg_img.size
        scale = max(
            target_width / original_fg_width, target_height / original_fg_height
        )
        new_fg_width = int(original_fg_width * scale)
        new_fg_height = int(original_fg_height * scale)

        # Resize the foreground image
        fg_img = fg_img.resize((new_fg_width, new_fg_height), Image.LANCZOS)

        # Calculate crop coordinates to center the image
        left = (new_fg_width - target_width) // 2
        top = (new_fg_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        # Crop the foreground image to the target dimensions
        fg_img = fg_img.crop((left, top, right, bottom))

        # Calculate paste position
        paste_x = int(result_width * position[0])
        paste_y = int(result_height * position[1])
    else:
        bg_img = open_image(user_img_src)
        fg_img = open_image(base_img_src)

        result_width = bg_img.width
        result_height = bg_img.height

        fg_new_height = int(bg_img.width / fg_img.width * fg_img.height)
        fg_img = fg_img.resize((bg_img.width, fg_new_height), Image.LANCZOS)

        paste_x = 0
        paste_y = 0

    # Create a new image with the dimensions of the resized background
    new_image = Image.new("RGBA", (result_width, result_height))
    new_image.paste(bg_img, (0, 0))

    # Paste the cropped foreground image onto the background
    new_image.paste(fg_img, (paste_x, paste_y), fg_img)

    # Save the result to a BytesIO object
    result_image_io = BytesIO()
    new_image.save(result_image_io, format="PNG")
    result_image_io.seek(0)

    return result_image_io
