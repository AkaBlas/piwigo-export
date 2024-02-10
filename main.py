from pathlib import Path

from components.category import GalleryTree
from components.image import Image

mysql_export = Path("mysql_export")

# These must be exports from phpMyAdmin of the respective tables in JSON format
categories_path = mysql_export / "piwigo_categories.json"
images_path = mysql_export / "piwigo_images.json"
image_category_path = mysql_export / "piwigo_image_category.json"

# This directory must contain the "upload" directory from the Piwigo installation
piwigo_export_path = Path("piwigo_download")

target_path = Path("target_path")


def main():
    # Build a category tree from the JSON export
    gt = GalleryTree.from_json(categories_path)

    # Create the directory tree for the categories
    gt.create_directory_tree(root_path=target_path)

    # Load the images and move them to the correct directory
    images = Image.from_json(
        image_category_path=image_category_path, images_path=images_path
    )
    gt.move_images(
        images=list(images.values()),
        export_root=piwigo_export_path,
        target_root=target_path,
    )


if __name__ == "__main__":
    main()
