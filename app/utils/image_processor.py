import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image

from app.config import get_settings

settings = get_settings()


@dataclass
class QualityConfig:
    max_width: int
    max_height: int
    quality: int
    suffix: str


QUALITY_CONFIGS: Dict[str, QualityConfig] = {
    "original": QualityConfig(max_width=0, max_height=0, quality=100, suffix="original"),
    "standard": QualityConfig(max_width=1920, max_height=1080, quality=85, suffix="standard"),
    "low": QualityConfig(max_width=800, max_height=600, quality=60, suffix="low"),
    "icon": QualityConfig(max_width=200, max_height=200, quality=70, suffix="icon"),
}


def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        return img.size


def _resize_image(
    image: Image.Image,
    max_width: int,
    max_height: int,
) -> Image.Image:
    if max_width <= 0 or max_height <= 0:
        return image.copy()

    original_width, original_height = image.size

    if original_width <= max_width and original_height <= max_height:
        return image.copy()

    ratio = min(max_width / original_width, max_height / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized


def _save_image(
    image: Image.Image,
    output_path: Path,
    quality: int,
    format: Optional[str] = None,
) -> int:
    if format is None:
        format = image.format or "JPEG"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_kwargs = {}
    if format in ("JPEG", "JPG"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
        if image.mode == "RGBA":
            image = image.convert("RGB")
    elif format == "PNG":
        save_kwargs["optimize"] = True
        if quality < 100:
            pass
    elif format == "WEBP":
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6

    image.save(output_path, format=format, **save_kwargs)
    return output_path.stat().st_size


def process_image_sync(
    input_path: Path,
    base_filename: str,
    output_dir: Path,
) -> Dict[str, Tuple[Path, int]]:
    results: Dict[str, Tuple[Path, int]] = {}

    with Image.open(input_path) as original_img:
        original_format = original_img.format or "JPEG"
        original_ext = Path(original_img.format.lower()).suffix if original_img.format else ".jpg"

        for quality_name, config in QUALITY_CONFIGS.items():
            if quality_name == "original":
                output_path = output_dir / f"{base_filename}_{config.suffix}{original_ext}"
                resized_img = original_img.copy()
            else:
                output_path = output_dir / f"{base_filename}_{config.suffix}{original_ext}"
                resized_img = _resize_image(
                    original_img,
                    config.max_width,
                    config.max_height,
                )

            file_size = _save_image(resized_img, output_path, config.quality, original_format)
            results[quality_name] = (output_path, file_size)

            if quality_name != "original":
                resized_img.close()

    return results


async def process_image(
    input_path: Path,
    base_filename: str,
    output_dir: Path,
) -> Dict[str, Tuple[Path, int]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        process_image_sync,
        input_path,
        base_filename,
        output_dir,
    )


def get_image_info(image_path: Path) -> Tuple[int, int, str]:
    with Image.open(image_path) as img:
        width, height = img.size
        format = img.format or "JPEG"
        return width, height, format.lower()
