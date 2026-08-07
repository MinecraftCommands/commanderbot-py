from typing import Optional, overload

import cv2
import numpy as np
from cv2.typing import MatLike
from tesserocr import OEM, PSM, RIL, PyResultIterator, PyTessBaseAPI, iterate_level

from commanderbot.lib.types import AttachmentID

__all__ = ("get_text",)


@overload
def get_text(image_data: bytes, lang: str) -> Optional[str]: ...


@overload
def get_text(
    image_data: bytes, lang: str, attachment_id: AttachmentID
) -> Optional[tuple[str, AttachmentID]]: ...


def get_text(
    image_data: bytes, lang: str, attachment_id: Optional[AttachmentID] = None
) -> Optional[str | tuple[str, AttachmentID]]:
    # Turn the bytes into a Numpy array
    buffer = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR_RGB)
    assert image is not None

    # Process the image to make the text stand out more
    processed = preprocess(image)
    processed = unskew(processed)
    processed = reorient(processed)

    # OCR the processed image
    with PyTessBaseAPI(oem=OEM.LSTM_ONLY, lang=lang) as api:
        height, width = processed.shape[:2]
        bytes_per_pixel = 1
        bytes_per_line = width * bytes_per_pixel
        api.SetImageBytes(
            imagedata=processed.tobytes(),  # type: ignore[ty:invalid-argument-type] - Why is this even expecting a string
            width=width,
            height=height,
            bytes_per_pixel=bytes_per_pixel,
            bytes_per_line=bytes_per_line,
        )
        api.Recognize()

        # Iterate over every word in the image (in order) and add them to an array
        words: list[str] = []
        page_iter = api.GetIterator()
        for word_iter in iterate_level(page_iter, RIL.WORD):
            try:
                assert isinstance(word_iter, PyResultIterator)
                if word := word_iter.GetUTF8Text(RIL.WORD).strip():
                    words.append(word)
            except:
                pass

        # Return any words we found as a string
        if words:
            text = " ".join(words)
            if attachment_id:
                return (text, attachment_id)
            return text


def preprocess(image: MatLike) -> MatLike:
    """
    Preprocess an image by making it strictly black and white (binarized)
    while trying to keep as much detail in the text as possible.
    """

    # Upscale
    processed = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # Make grayscale
    processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

    # Invert dark images
    if processed.mean() < 128:
        processed = cv2.bitwise_not(processed)

    # Denoise
    processed = cv2.bilateralFilter(processed, 9, 30, 30)

    # Binarize
    return cv2.adaptiveThreshold(
        processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 7
    )


def unskew(image: MatLike) -> MatLike:
    """
    Use the lines in the image to straighten it out. It doesn't
    have to be perfect since Tesseract can fix it.
    """

    # Merge the text into lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 5))
    processed = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    # Try to find the skew angle
    angle = find_skew_angle(processed)
    if angle is None:
        return image

    # Rotate the image without cutting the corners off
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Get the absolute values of the sine and cosine of the rotation
    abs_cos = abs(mat[0, 0])
    abs_sin = abs(mat[0, 1])

    # Find the new width and height
    new_width = int(height * abs_sin + width * abs_cos)
    new_height = int(height * abs_cos + width * abs_sin)

    # Update the center
    mat[0, 2] += (new_width / 2) - center[0]
    mat[1, 2] += (new_height / 2) - center[1]

    return cv2.warpAffine(
        image,
        mat,
        (new_width, new_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def reorient(image: MatLike) -> MatLike:
    """
    Use Tesseract OSD to make the image right side up.
    """

    orientation: int = 0
    with PyTessBaseAPI(psm=PSM.OSD_ONLY) as api:
        height, width = image.shape[:2]
        bytes_per_pixel = 1
        bytes_per_line = width * bytes_per_pixel
        api.SetImageBytes(
            imagedata=image.tobytes(),  # type: ignore[ty:invalid-argument-type] - Why is this even expecting a string
            width=width,
            height=height,
            bytes_per_pixel=bytes_per_pixel,
            bytes_per_line=bytes_per_line,
        )
        if os := api.DetectOrientationScript():
            orientation = os.get("orient_deg", 0)

    match orientation:
        case 90:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        case 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        case 270:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        case _:
            return image


def find_skew_angle(
    image_array: MatLike,
    sigma: float = 3.0,
    num_peaks: int = 20,
    angle_pm_90: bool = False,
    min_angle: Optional[float] = None,
    max_angle: Optional[float] = None,
    min_deviation: float = 1.0,
    gradient_percentile: float = 99.0,
    canny_threshold_low: Optional[float] = None,
    canny_threshold_high: Optional[float] = None,
    hough_rho: float = 1.0,
    hough_threshold: int = 30,
) -> Optional[np.float64]:
    """
    From: https://github.com/HOZHENWAI/fast_deskew

    Estimate the skew angle (in degrees) of a (grayscale) document image.

    The pipeline follows the classical Hough-transform skew-detection method:
    blur -> Canny edges -> Hough line transform -> fold each line orientation
    into the canonical skew interval -> return the most frequent (modal) angle.
    The rho (offset) dimension carries no skew information and is ignored.

    Thresholds are derived relative to the image (rather than fixed constants) so
    the same defaults work across document sizes and contrasts: the Canny
    thresholds come from a percentile of the gradient magnitude, and the dominant
    orientation is taken from the strongest ``num_peaks`` Hough lines.

    image_array: :class:`MatLike`
        8-bit single-channel image.
    sigma: :class:`float`
        Standard deviation of the Gaussian pre-blur.
    num_peaks: :class:`int`
        Number of strongest Hough lines to vote with.
    angle_pm_90: :class:`bool`
        Fold into `[-90, 90)` instead of `[-45, 45)`.
    min_angle: :class:`Optional[float]`
        Lower bound (degrees) on the reported skew; `None` disables it.
    max_angle: :class:`Optional[float]`
        Upper bound (degrees) on the reported skew; `None` disables it.
    min_deviation: :class:`float`
        Strictly positive angular resolution in degrees; also the
        voting bin width used to find the modal angle.
    gradient_percentile: :class:`float`
        Percentile of the gradient magnitude used as the
        high Canny threshold when the Canny thresholds are auto-derived.
    canny_threshold_low: :class:`Optional[float]`
        Explicit low Canny threshold; `None` auto-derives it.
    canny_threshold_high: :class:`Optional[float]`
        Explicit high Canny threshold; `None` auto-derives it.
    hough_rho: :class:`float`
        Distance resolution of the accumulator in pixels.
    hough_threshold: :class:`int`
        Minimum Hough votes for a line to be considered. It acts
        as a floor only; the dominant orientation is chosen from the strongest
        `num_peaks` lines, so peak selection stays relative to the image.
    :return: :class:`Optional[np.float64]`
        The skew angle in degrees, or `None` if no dominant line is found.
    """
    if min_deviation <= 0:
        raise ValueError("min_deviation must be strictly positive")

    theta_resolution = np.deg2rad(min_deviation)
    blurred_image = cv2.GaussianBlur(image_array, (0, 0), sigma)

    if canny_threshold_low is None or canny_threshold_high is None:
        # Derive Canny thresholds from this image's gradient magnitude instead of
        # using fixed constants, so faint or heavily blurred documents still yield
        # edges (mirrors scikit-image's gradient-relative Canny).
        grad_x = cv2.Sobel(blurred_image, cv2.CV_16S, 1, 0, ksize=3)
        grad_y = cv2.Sobel(blurred_image, cv2.CV_16S, 0, 1, ksize=3)
        magnitude = cv2.magnitude(grad_x.astype(np.float32), grad_y.astype(np.float32))
        high = max(float(np.percentile(magnitude, gradient_percentile)), 1.0)
        edges = cv2.Canny(grad_x, grad_y, 0.5 * high, high)
    else:
        edges = cv2.Canny(blurred_image, canny_threshold_low, canny_threshold_high)

    lines = cv2.HoughLines(edges, hough_rho, theta_resolution, hough_threshold)
    if lines is None:
        return None

    # cv2.HoughLines returns lines ordered by descending vote count, so the first
    # `num_peaks` are the strongest peaks. theta is the orientation of each line's
    # normal in [0, pi).
    theta = lines[:num_peaks, 0, 1]

    # Fold every orientation into the canonical skew interval BEFORE counting, so
    # that text baselines and vertical strokes (which differ by ~90 deg) reinforce
    # the same skew estimate.
    if angle_pm_90:
        folded = theta % np.pi - np.pi / 2  # [-pi/2, pi/2)
    else:
        folded = (theta + np.pi / 4) % (np.pi / 2) - np.pi / 4  # [-pi/4, pi/4)

    folded_deg = np.rad2deg(folded)

    # Restrict the reported skew to the requested output range, if any.
    if min_angle is not None:
        folded_deg = folded_deg[folded_deg >= min_angle]
    if max_angle is not None:
        folded_deg = folded_deg[folded_deg <= max_angle]
    if folded_deg.size == 0:
        return None

    # Most frequent angle: quantize to the min_deviation grid to group nearby
    # peaks, pick the densest bin, then average its members for sub-bin precision.
    bins = np.round(folded_deg / min_deviation)
    values, counts = np.unique(bins, return_counts=True)
    best_bin = values[np.argmax(counts)]
    best_angle = folded_deg[bins == best_bin].mean()

    return np.float64(best_angle)
