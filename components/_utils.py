import json
from typing import Any


def get_data_from_json_dump(file_path) -> dict[str, Any]:
    json_data = json.loads(file_path.read_bytes())
    data: dict[str, Any] | None = None

    for entry in json_data:
        if entry.get("type") == "table":
            data = entry["data"]
            break

    if data is None:
        raise ValueError("data not found in JSON export")

    return data
