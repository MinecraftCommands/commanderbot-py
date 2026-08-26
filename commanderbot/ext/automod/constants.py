from mime_enum import MimeType

__all__ = ("IMAGE_MIME_TYPES",)

IMAGE_MIME_TYPES: tuple[MimeType, ...] = (
    MimeType.IMAGE_AVIF,
    MimeType.IMAGE_AVIF_SEQUENCE,
    MimeType.IMAGE_BMP,
    MimeType.IMAGE_GIF,
    MimeType.IMAGE_HEIC,
    MimeType.IMAGE_JPEG,
    MimeType.IMAGE_PJPEG,
    MimeType.IMAGE_PNG,
    MimeType.IMAGE_TIFF,
    MimeType.IMAGE_WEBP,
)
