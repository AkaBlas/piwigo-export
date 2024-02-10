from pathlib import Path

from pydantic import BaseModel

from components._utils import get_data_from_json_dump


class ImageCatogery(BaseModel):
    image_id: int
    category_id: int

    @classmethod
    def from_json(cls, file_path: Path) -> dict[int, "ImageCatogery"]:
        data = get_data_from_json_dump(file_path)

        image_categories: dict[int, ImageCatogery] = {}
        for entry in data:
            image_category = cls(
                image_id=int(entry["image_id"]),
                category_id=int(entry["category_id"]),
            )

            image_categories[image_category.image_id] = image_category

        return image_categories


class Image(BaseModel):
    id: int
    file: str
    name: str
    category_id: int
    path: Path

    @classmethod
    def from_json(
        cls, images_path: Path, image_category_path: Path
    ) -> dict[int, "Image"]:
        image_data = get_data_from_json_dump(images_path)
        image_categories = ImageCatogery.from_json(image_category_path)

        images: dict[int, Image] = {}
        for entry in image_data:
            image_id = int(entry["id"])
            image = cls(
                id=image_id,
                file=entry["file"],
                name=entry["name"],
                path=Path(entry["path"]),
                category_id=image_categories[image_id].category_id,
            )

            images[image.id] = image

        return images
