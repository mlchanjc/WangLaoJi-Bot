import os
import json
import requests

# Create a folder for images if it doesn't exist
images_folder = "images"
os.makedirs(images_folder, exist_ok=True)


# Function to download an image
def download_image(url, image_name):
    # Construct the full path to the image
    image_path = os.path.join(images_folder, image_name)

    # Check if the image already exists
    if os.path.exists(image_path):
        print(f"Image already exists: {image_name}")
        return True

    # Proceed to download the image if it doesn't exist
    response = requests.get(
        f"https://dp4p6x0xfi5o9.cloudfront.net/chunithm/img/cover/{url}", stream=True
    )

    if response.status_code == 200:
        with open(image_path, "wb") as writer:
            for chunk in response.iter_content(chunk_size=8192):
                writer.write(chunk)
        print(f"Downloaded: {image_name}")
        return True
    else:
        print(
            f"Failed to download image: {url} with status code: {response.status_code}"
        )
        return False


# Download songs from full_song_data.json
with open("full_song_data.json", "r", encoding="utf-8") as file:
    try:
        json_array = json.load(file)

        x = 0
        for item in json_array:
            _, file_extension = os.path.splitext(item["imageName"])
            image_name = f"{item['songId']}{file_extension}"
            download_image(item["imageName"], image_name)

    except json.JSONDecodeError as parse_error:
        print("Error parsing JSON:", parse_error)
    except Exception as err:
        print("An error occurred:", err)
