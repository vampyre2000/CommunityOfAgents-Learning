import os
import sys
import logging
from pathlib import Path
from typing import List, Optional


logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

def list_images() -> str:
    """
    Lists all image files in the project's images directory.
    
    Returns:
        str: A formatted string containing the list of images
    """
    try:
        # Get the project root directory (two levels up from the current file)
        project_root = Path(__file__).resolve().parent.parent
        images_directory = project_root / "images"
        
        # Debug output
        logger.debug(f"Project root: {project_root}")
        logger.debug(f"Images directory: {images_directory}")
        
        if not images_directory.exists():
            return "The images directory does not exist."
            
        # List all image files
        image_files = [
            f for f in images_directory.iterdir() 
            if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']
        ]
        
        if not image_files:
            return "No images found in the images directory."
            
        # Format the output
        result = "Available images:\n"
        for image_file in image_files:
            result += f"- {image_file.name}\n"
        return result
        
    except Exception as e:
        return f"Error listing images: {str(e)}"

if __name__ == "__main__":
    print(list_images())

def change_image(imagename: str) -> str:
    """
    Changes the displayed image from the project's images directory.
    
    Args:
        imagename: Name of the image file to find
        
    Returns:
        str: The name of the image file if found, error message if not
    """
    try:
        # Get the project root directory (two levels up from the current file)
        project_root = Path(__file__).resolve().parent.parent
        images_directory = project_root / "images"
        image_path = images_directory / imagename
        
        # Debug output
        logger.debug(f"Looking for image: {image_path}")
        
        # Check if the image exists
        if not image_path.exists():
            logger.error(f"Image not found: {imagename}")
            return f"Image {imagename} not found in the images directory."
            
        # Verify it's an image file
        if image_path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
            logger.error(f"Invalid image type: {imagename}")
            return f"File {imagename} is not a valid image type."
            
        logger.debug(f"Image found: {imagename}")
        return imagename
        
    except Exception as e:
        logger.error(f"Error changing image: {str(e)}")
        return f"Error changing image: {str(e)}"

if __name__ == "__main__":
    print(change_image("agent2.jpg"))
    print(change_image("agent.jpg"))
    print(change_image("agent3.jpg"))

