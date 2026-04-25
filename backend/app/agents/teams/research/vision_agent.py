from __future__ import annotations

import base64
from typing import Any


async def process_base64_images(base64_images: list[str]) -> list[dict[str, Any]]:
    """Validate and summarize incoming Base64 images for multimodal routing."""

    summaries: list[dict[str, Any]] = []
    for index, image_blob in enumerate(base64_images):
        normalized = image_blob
        if "," in image_blob and image_blob.lower().startswith("data:"):
            normalized = image_blob.split(",", 1)[1]

        try:
            decoded = base64.b64decode(normalized, validate=True)
            summaries.append(
                {
                    "image_index": index,
                    "bytes": len(decoded),
                    "status": "valid_base64",
                }
            )
        except (ValueError, base64.binascii.Error):
            summaries.append(
                {
                    "image_index": index,
                    "bytes": 0,
                    "status": "invalid_base64",
                }
            )

    return summaries
