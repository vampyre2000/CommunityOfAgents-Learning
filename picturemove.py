import os
import hashlib
import shutil

# Function to calculate the hash of a file
def calculate_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to ensure the filename is unique in the target directory
def get_unique_filename(dest_dir, filename):
    original_name, file_extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(dest_dir, new_filename)):
        new_filename = f"{original_name}_{counter}{file_extension}"
        counter += 1

    return new_filename

# Function to move photos to the target directory
def move_unique_photos(source_dir, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    seen_photos = {}

    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_hash = calculate_hash(file_path)

            # Check if the photo is already in the target directory
            if (file_size, file_hash) not in seen_photos:
                seen_photos[(file_size, file_hash)] = file

                # Ensure unique filename if the same name exists
                unique_filename = get_unique_filename(target_dir, file)
                target_path = os.path.join(target_dir, unique_filename)

                shutil.move(file_path, target_path)
                print(f"Moved: {file} to {target_path}")
            else:
                print(f"Duplicate found, skipping: {file}")

# Set your source and target directories
source_directory = "/media/brendan/9A06829D06827A51/Test/orig"
target_directory = "/media/brendan/9A06829D06827A51/Test/dest"

move_unique_photos(source_directory, target_directory)
