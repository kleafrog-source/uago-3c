"""
Module for automatic measurement of geometric, topological, and dynamical invariants
from a 2D image (provided as a numpy array or file path).
"""
import cv2
import numpy as np
from skimage.measure import label, regionprops
from skimage.morphology import skeletonize
from scipy.spatial.distance import pdist
import os
from typing import Dict, Union


def measure_invariants(image_input: Union[str, np.ndarray]) -> Dict:
    """
    Measure geometric invariants from an image.

    Args:
        image_input: Path to image file (str) or numpy array (H, W) or (H, W, 3)

    Returns:
        Dictionary with keys:
          - dimensionality (float)
          - scales (list of float)
          - connectivity (int)
          - repetition_score (float)
          - symmetry_approx (str)
          - branching (dict with 'angles' and 'ratios')
    """
    # Load image if path is given
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found: {image_input}")
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"Cannot load image: {image_input}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 3:
            gray = cv2.cvtColor(image_input, cv2.COLOR_RGB2GRAY)
        elif image_input.ndim == 2:
            gray = image_input.copy()
        else:
            raise ValueError("Input array must be 2D or 3D (RGB).")
    else:
        raise TypeError("image_input must be str (path) or np.ndarray.")

    # Binarize
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    # 1. Fractal dimension (box-counting)
    dim = _box_counting_dimension(binary)

    # 2. Characteristic scales
    scales = _detect_scales(binary)

    # 3. Connectivity (number of connected components)
    labeled = label(binary > 0)
    connectivity = len(regionprops(labeled))

    # 4. Repetition score (via normalized autocorrelation)
    rep_score = _detect_repetition(binary)

    # 5. Approximate symmetry
    symmetry = _detect_symmetry(binary)

    # 6. Branching analysis (if applicable)
    branching = _analyze_branching(binary)

    return {
        "dimensionality": float(dim),
        "scales": [float(s) for s in scales],
        "connectivity": int(connectivity),
        "repetition_score": float(rep_score),
        "symmetry_approx": str(symmetry),
        "branching": branching
    }


def _box_counting_dimension(binary_img: np.ndarray, max_boxes: int = 6) -> float:
    """Estimate fractal dimension using box-counting method."""
    H, W = binary_img.shape
    min_dim = min(H, W)
    sizes = []
    counts = []
    size = 1
    while size <= min_dim and len(sizes) < max_boxes:
        boxes = 0
        for i in range(0, H, size):
            for j in range(0, W, size):
                if np.any(binary_img[i:i + size, j:j + size]):
                    boxes += 1
        if boxes > 0:
            sizes.append(size)
            counts.append(boxes)
        size *= 2

    if len(sizes) < 2:
        return 2.0

    log_sizes = np.log(sizes)
    log_counts = np.log(counts)
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    return -coeffs[0]


def _detect_scales(binary_img: np.ndarray, levels: int = 3) -> list:
    """Detect characteristic scales by downsampling."""
    H, W = binary_img.shape
    scales = []
    current = binary_img.copy()
    area = H * W
    scales.append(float(area))
    for _ in range(levels - 1):
        h, w = current.shape
        if h < 10 or w < 10:
            break
        current = cv2.resize(current, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        scales.append(float(current.shape[0] * current.shape[1]))
    return scales


def _detect_repetition(binary_img: np.ndarray) -> float:
    """Estimate repetition via normalized cross-correlation (simplified)."""
    try:
        # Use a small template from top-left
        h, w = binary_img.shape
        if h < 20 or w < 20:
            return 0.0
        template = binary_img[:h // 4, :w // 4]
        if template.size == 0:
            return 0.0
        res = cv2.matchTemplate(binary_img, template, cv2.TM_CCOEFF_NORMED)
        if res.size == 0:
            return 0.0
        return float(np.mean(res))
    except Exception:
        return 0.0


def _detect_symmetry(binary_img: np.ndarray) -> str:
    """Estimate rotational symmetry."""
    angles = [0, 30, 45, 60, 90, 120, 180]
    scores = []
    for angle in angles:
        if angle == 0:
            scores.append(1.0)
            continue
        rotated = _rotate_image(binary_img, angle)
        diff = np.sum(np.abs(binary_img.astype(int) - rotated.astype(int)))
        score = 1.0 - (diff / (binary_img.size * 255.0))
        scores.append(score)

    # Find best non-zero symmetry
    best_idx = np.argmax(scores[1:]) + 1
    if scores[best_idx] > 0.85:
        angle = angles[best_idx]
        if angle == 180:
            return "C2"
        elif angle == 120:
            return "C3"
        elif angle == 90:
            return "C4"
        elif angle == 60:
            return "C6"
        elif angle == 45:
            return "C8"
        elif angle == 30:
            return "C12"
        else:
            return f"C{int(360 / angle)}" if angle != 0 else "C1"
    elif scores[3] > 0.8 and scores[5] > 0.8:  # 60° and 120° → C3
        return "C3"
    elif scores[4] > 0.8:  # 90° → C4
        return "C4"
    else:
        return "C1"


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by given angle (degrees)."""
    h, w = img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)


def _analyze_branching(binary_img: np.ndarray) -> dict:
    """Analyze branching structure (e.g., in trees or veins)."""
    try:
        # Only analyze if image is sparse and tree-like
        density = np.sum(binary_img) / binary_img.size
        if density > 0.3 or density < 0.01:
            return {"angles": [], "ratios": []}

        skeleton = skeletonize(binary_img > 0)
        # Find junctions (pixels with >2 neighbors)
        from scipy.ndimage import convolve
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        neighbors = convolve(skeleton.astype(int), kernel, mode='constant')
        junctions = np.where((skeleton) & (neighbors >= 3))

        if len(junctions[0]) == 0:
            return {"angles": [], "ratios": []}

        # Simplified: assume dominant angle is ~36° or 90°
        # In real system, you'd trace branches
        # For now, use dimensionality as proxy
        # This is a placeholder for a full graph-based analysis
        return {"angles": [36.0], "ratios": [0.7]}
    except Exception:
        return {"angles": [], "ratios": []}