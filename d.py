import requests
import json
import os
from bs4 import BeautifulSoup

def get_image_url_and_id(image_data):
    image_url = image_data["representations"]["full"]
    image_id = image_data["id"]
    return image_url, image_id

def download_image(image_url, image_name):
    response = requests.get(image_url)
    with open(image_name, "wb") as f:
        f.write(response.content)

def download_tags(image_id, tag_separator):
    tag_file_name = f"{image_id}.txt"
    response = requests.get(f"https://derpibooru.org/{image_id}")
    soup = BeautifulSoup(response.content, "html.parser")
    tag_list = [tag.text for tag in soup.select(".tag__name")]
    tag_list = tag_separator.join(tag_list)
    with open(tag_file_name, "w", encoding="utf-8") as f:
        f.write(tag_list)
        print(f"Downloaded {tag_file_name}")

def process_images(images, total_images, download_tags_enabled, tag_separator):
    downloaded_images = 0
    for image in images:
        if downloaded_images == total_images:
            break
        image_url, image_id = get_image_url_and_id(image)
        image_name = f"{image_id}{os.path.splitext(image_url)[1]}"
        if os.path.exists(image_name):
            print(f"Skipping {image_name} ({downloaded_images+1}/{total_images})")
            downloaded_images += 1
            continue
        download_image(image_url, image_name)
        print(f"Downloaded {image_name} ({downloaded_images+1}/{total_images})")
        downloaded_images += 1
        if download_tags_enabled:
            download_tags(image_id, tag_separator)

# Define request parameters
params = {
    "key": "", # Optional: Replace with your Derpibooru API key
    "filter_id": 56027,
}

# Set default values
mode = "1"
download_tags_enabled = False
tag_separator = ", "

# Prompt user for input
mode_input = input("Enter mode (1 for search query, 2 for image IDs), default is 1: ")
if mode_input in ("1", "2"):
    mode = mode_input

download_tags_input = input("Do you want to download tags? (y/n, default is y): ") or "y"
if download_tags_input.lower() == "y":
    download_tags_enabled = True
    tag_separator_input = input("Enter separator to use for tags (default is ', '): ")
    if tag_separator_input:
        tag_separator = tag_separator_input

if mode == "1":
    query = input("Enter your search query: ")
    num_images_input = input("How many images do you want to download? (default is 50): ")
    try:
        num_images = int(num_images_input) if num_images_input else 50
    except ValueError:
        print("Invalid input for number of images. Defaulting to 50.")
        num_images = 50

    params["q"] = query
    params["per_page"] = 50

    response = requests.get("https://derpibooru.org/api/v1/json/search/images", params=params)
    data = json.loads(response.text)
    total_images = min(data["total"], num_images)
    print(f"Total images found: {total_images}")

    num_pages = (total_images // 50) + 1

    for page in range(1, num_pages+1):
        params["page"] = page
        response = requests.get("https://derpibooru.org/api/v1/json/search/images", params=params)
        data = json.loads(response.text)
        process_images(data["images"], total_images, download_tags_enabled, tag_separator)

elif mode == "2":
    image_ids = []
    while True:
        image_id_input = input("Enter image ID (or any non-numeric value to stop): ")
        try:
            image_id = int(image_id_input)
        except ValueError:
            break
        image_ids.append(str(image_id))

    images_data = []
    for image_id in image_ids:
        response = requests.get(f"https://derpibooru.org/api/v1/json/images/{image_id}")
        if response.status_code == 404:
            print(f"Image with ID {image_id} not found.")
            continue
        data = json.loads(response.text)
        images_data.append(data["image"])

    process_images(images_data, len(image_ids), download_tags_enabled, tag_separator)

else:
    print("Invalid mode entered. Please enter either 1 or 2.")