import shutil
from pathlib import Path
from typing import Optional

import unicodedata
from pydantic import BaseModel, Field

from components._utils import get_data_from_json_dump
from components.image import Image


def _sanitize_directory_name(value: str, allow_unicode: bool = False) -> str:
    """Makes directory name Windows compliant"""
    # https://github.com/django/django/blob/b47bdb4cd9149ee2a39bf1cc9996a36a940bd7d9/django/utils/text.py#L454-L472
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    import re

    value = re.sub(r"[^\w\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-_")


class Category(BaseModel):
    id: int
    name: str
    id_uppercat: int | None
    parent: Optional["Category"] = Field(exclude=True, default=None)

    @property
    def directory_name(self) -> str:
        return _sanitize_directory_name(self.name)

    def set_parent(self, parent: "Category") -> None:
        self.parent = parent

    @classmethod
    def from_json(cls, file_path: Path) -> dict[int, "Category"]:
        data = get_data_from_json_dump(file_path)

        categories: dict[int, Category] = {}
        for entry in data:
            category = cls(
                id=int(entry["id"]),
                name=entry["name"],
                id_uppercat=int(id_u) if (id_u := entry.get("id_uppercat")) else None,
            )

            categories[category.id] = category

        return categories


class CategoryTree(BaseModel):
    __slots__ = ["__weakref__"]
    root: Category
    children: list["CategoryTree"] = []

    @classmethod
    def from_dict(cls, categories_dict: dict[int, Category]) -> list["CategoryTree"]:
        categories = list(categories_dict.values())

        root_trees = {
            cat.id: cls(root=cat)
            for cat in filter(lambda cat: cat.id_uppercat is None, categories)
        }
        trees = root_trees.copy()

        unparsed_ids = set(categories_dict) - set(root_trees)
        while unparsed_ids:
            for cat_id in list(unparsed_ids):
                cat = categories_dict[cat_id]

                if (not cat.id_uppercat) or (
                    not (parent_cat := trees.get(cat.id_uppercat))
                ):
                    continue

                child_tree = cls(root=cat)
                cat.set_parent(parent_cat.root)
                parent_cat.children.append(child_tree)
                trees[cat.id] = child_tree

                unparsed_ids.discard(cat_id)

        return list(root_trees.values())

    def create_directory_tree(self, root_path: Path) -> None:
        for child_cat in self.children:
            path = root_path / child_cat.root.directory_name
            path.mkdir(parents=True, exist_ok=True)
            child_cat.create_directory_tree(path)


class GalleryTree(BaseModel):
    root_categories: list[CategoryTree]
    categories_mapping: dict[int, Category] = Field(..., exclude=True)

    @classmethod
    def from_dict(cls, categories_dict: dict[int, Category]) -> "GalleryTree":
        return cls(
            root_categories=CategoryTree.from_dict(categories_dict),
            categories_mapping=categories_dict,
        )

    @classmethod
    def from_json(cls, file_path: Path) -> "GalleryTree":
        return cls.from_dict(Category.from_json(file_path))

    def create_directory_tree(self, root_path: Path) -> None:
        for root_cat in self.root_categories:
            path = root_path / root_cat.root.directory_name
            path.mkdir(parents=True, exist_ok=True)
            root_cat.create_directory_tree(path)

    def get_path_for_category(self, root_path: Path, category: int | Category) -> Path:
        effective_category = self.categories_mapping[
            category if isinstance(category, int) else Category.id
        ]
        dir_names = []
        while effective_category is not None:
            dir_names.append(effective_category.directory_name)
            effective_category = effective_category.parent

        return root_path.joinpath(*reversed(dir_names))

    def move_image(self, image: Image, export_root: Path, target_root: Path) -> None:
        old_path = image.path
        new_path = (
            self.get_path_for_category(target_root, image.category_id) / image.file
        )
        new_path.parent.mkdir(parents=True, exist_ok=True)

        if new_path.is_file():
            return

        try:
            shutil.copyfile(export_root / old_path, new_path)
        except FileNotFoundError:
            print(f"File not found: {export_root / old_path} | {image.file} - skipping")

    def move_images(
        self, images: list[Image], export_root: Path, target_root: Path
    ) -> None:
        for image in images:
            self.move_image(image, export_root, target_root)
