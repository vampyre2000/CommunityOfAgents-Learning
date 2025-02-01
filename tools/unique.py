import os
import hashlib
import shutil

def calculate_file_hash(filepath, hash_algorithm=hashlib.sha256):
    """Calculate the hash of a file based on its content."""
    hash_obj = hash_algorithm()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def find_unique_photos(directory):
    """Find unique photos in a directory based on their content hash."""
    unique_photos = {}
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            file_hash = calculate_file_hash(filepath)
            if file_hash not in unique_photos:
                unique_photos[file_hash] = filepath
    return unique_photos.values()

def copy_unique_photos_to_new_directory(unique_photos, destination_dir):
    """Copy unique photos to a new directory."""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    for photo in unique_photos:
        filename = os.path.basename(photo)
        destination_path = os.path.join(destination_dir, filename)
        # Ensure the filename is unique in the destination directory
        counter = 1
        while os.path.exists(destination_path):
            name, ext = os.path.splitext(filename)
            destination_path = os.path.join(destination_dir, f"{name}_{counter}{ext}")
            counter += 1
        shutil.copy2(photo, destination_path)
        print(f"Copied: {photo} -> {destination_path}")

def main(source_directory, destination_directory):
    print("Finding unique photos...")
    unique_photos = find_unique_photos(source_directory)
    print(f"Found {len(unique_photos)} unique photos.")
    print("Copying unique photos to the new directory...")
    copy_unique_photos_to_new_directory(unique_photos, destination_directory)
    print("Done!")

if __name__ == "__main__":
    source_directory = "/media/vampyre/1cacf427-fddf-43b0-9809-97e10c14a239/Pictures-migrated-2024-09-02/"  # Replace with the path to your source directory
    destination_directory = "/media/vampyre/1cacf427-fddf-43b0-9809-97e10c14a239/Pictures-migrated-2024-12-27/"  # Replace with the path to your new directory
    main(source_directory, destination_directory)