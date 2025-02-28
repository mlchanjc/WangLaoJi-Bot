import re
import requests
import json
import os
import cutlet


def get_aliases_dict(input_source):
    aliases_dict = dict()
    lines = []

    try:
        # Check if the input source is a URL
        if input_source.startswith("http://") or input_source.startswith("https://"):
            response = requests.get(input_source)
            response.raise_for_status()  # Raise an error for bad responses

            # Split the response text into lines
            lines = response.text.strip().split("\n")

        # If not a URL, assume it's a file path
        else:
            if not os.path.exists(input_source):
                print(f"Error: The file '{input_source}' was not found.")
                return aliases_dict

            # Read the TSV file
            with open(input_source, "r", encoding="utf-8") as file:
                lines = file.readlines()  # Read all lines

        # Process each line
        for line in lines:
            aliases = line.strip().split("\t")
            if len(aliases) >= 2:
                aliases_dict[aliases[0]] = aliases[1:]

        return aliases_dict

    except json.JSONDecodeError:
        print("Error decoding JSON. Please ensure the content is valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_reading_dict(input_source):
    reading_dict = dict()

    try:
        # Check if the input source is a URL
        if input_source.startswith("http://") or input_source.startswith("https://"):
            response = requests.get(input_source)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the JSON content from the URL
            data = response.json()

            for item in data:
                reading_dict[item["title"]] = item["reading"]

        # If not a URL, assume it's a file path
        else:
            if not os.path.exists(input_source):
                print(f"Error: The file '{input_source}' was not found.")
                return reading_dict

            # Read the JSON file
            with open(input_source, "r", encoding="utf-8") as file:
                json_array = json.load(file)

            for item in json_array:
                reading_dict[item["title"]] = item["reading"]

        return reading_dict

    except json.JSONDecodeError:
        print("Error decoding JSON. Please ensure the content is valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")


def generate_full_song_data(input_source, output_file):
    try:
        data = None

        # Check if the input source is a URL
        if input_source.startswith("http://") or input_source.startswith("https://"):
            response = requests.get(input_source)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the JSON content from the URL
            data = response.json()

        # If not a URL, assume it's a file path
        else:
            if not os.path.exists(input_source):
                print(f"Error: The file '{input_source}' was not found.")
                return

            # Read the JSON file
            with open(input_source, "r", encoding="utf-8") as file:
                data = json.load(file)

        result = []

        reading_dict = get_reading_dict(
            "music.json"
        )  # Source: https://github.com/zvuc/otoge-db/blob/master/chunithm/data/music.json

        aliases_dict = get_aliases_dict(
            "https://raw.githubusercontent.com/lomotos10/GCM-bot/main/data/aliases/en/chuni.tsv"
        )

        # Process each item in the JSON array
        for item in data["songs"]:
            if item["category"] == "WORLD'S END":
                continue

            katsu = cutlet.Cutlet()
            romonizedTitle = katsu.romaji(item["title"])

            katsu.use_foreign_spelling = False
            fullRomonizedTitle = katsu.romaji(item["title"])

            # Some special characters cause the romonized title to become contain "?" only.
            # In this case, we use the reading from reading_dict.
            # Only do this if the romonized title contains "??" to avoid processing songs with title originally containing "?".
            if "??" in romonizedTitle and item["title"] in reading_dict:
                romonizedTitle = katsu.romaji(reading_dict[item["title"]])

                katsu.use_foreign_spelling = False
                fullRomonizedTitle = katsu.romaji(reading_dict[item["title"]])

            song = {
                "songId": re.sub(
                    r'[<>:"/\\|?*]', "_", item.get("songId")
                ),  # Replace invalid characters with underscores
                "category": item.get("category"),
                "artist": item.get("artist"),
                "title": item.get("title"),
                "reading": reading_dict.get(item["title"], None),
                "romonizedTitle": romonizedTitle,
                "fullRomonizedTitle": fullRomonizedTitle,
                "aliases": aliases_dict.get(item["title"], []),
                "bpm": item.get("bpm"),
                "imageName": item.get("imageName"),
                "version": item.get("version"),
                "releaseDate": item.get("releaseDate"),
                "isNew": item.get("isNew"),
                "isLocked": item.get("isLocked"),
                "comment": item.get("comment"),
                "sheets": item.get(
                    "sheets", []
                ),  # Default to empty list if not present
            }

            result.append(song)

        # Write the result to a new JSON file
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)

        print(f"JSON data has been written to {output_file}")

    except FileNotFoundError:
        print(f"Error: The file '{input_source}' was not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON. Please ensure the file contains valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")


input_source = "https://dp4p6x0xfi5o9.cloudfront.net/chunithm/data.json"
output_file = "full_song_data.json"


generate_full_song_data(input_source, output_file)
