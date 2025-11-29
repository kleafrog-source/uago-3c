import numpy as np
from typing import Dict

def _box_count(img, box_size):
    """Count non-empty boxes in the image."""
    lx, ly = img.shape
    # Adjust image size to be divisible by box_size
    lx = lx // box_size * box_size
    ly = ly // box_size * box_size
    img = img[:lx, :ly]
    
    # Split the image into boxes
    boxes = img.reshape(lx // box_size, box_size, ly // box_size, box_size)
    # Count boxes with at least one white pixel
    return np.count_nonzero(np.any(boxes, axis=(1, 3)))

def calculate_fractal_dimension(img, box_sizes=None):
    """Calculate the fractal dimension using box counting method."""
    if box_sizes is None:
        box_sizes = [2**i for i in range(1, 7)]
    
    counts = []
    for size in box_sizes:
        # Skip if size is larger than image dimensions
        if size > min(img.shape[0], img.shape[1]):
            continue
        count = _box_count(img, size)
        if count > 0:  # Only add non-zero counts
            counts.append(count)
    
    if len(counts) < 2:  # Need at least 2 points for linear regression
        return 0.0
    
    # Convert to numpy arrays
    box_sizes = np.array(box_sizes[:len(counts)])
    counts = np.array(counts)
    
    # Filter out any zeros to avoid log(0)
    valid = counts > 0
    if np.sum(valid) < 2:  # Need at least 2 valid points
        return 0.0
        
    box_sizes = box_sizes[valid]
    counts = counts[valid]
    
    # Add small epsilon to avoid log(0)
    coeffs = np.polyfit(np.log(box_sizes), np.log(counts + 1e-10), 1)
    return -coeffs[0]

def calculate_repetition_score(img):
    """Calculate repetition/self-similarity score using FFT."""
    f = np.fft.fft2(img)
    acorr = np.fft.ifft2(f * np.conj(f)).real
    acorr = acorr / (acorr.max() + 1e-10)  # Add small epsilon to prevent division by zero
    return np.mean(acorr)

def measure_invariants(img: np.ndarray) -> Dict:
    """Calculate geometric invariants from an image."""
    if len(img.shape) > 2:
        img = img.mean(axis=2)  # Convert to grayscale if needed
    
    # Convert to binary (black and white)
    img = (img > 128).astype(np.uint8)
    
    # Calculate fractal dimension
    dimensionality = calculate_fractal_dimension(img)
    
    # Calculate repetition/self-similarity score
    repetition_score = calculate_repetition_score(img)
    
    # Calculate symmetry score (simple horizontal symmetry)
    h, w = img.shape
    half = w // 2
    left_half = img[:, :half]
    right_half = img[:, -half:][:, ::-1]  # Flip right half
    symmetry = np.mean(left_half == right_half)
    
    # Determine symmetry approximation
    if symmetry > 0.9:
        symmetry_approx = "D2"
    elif symmetry > 0.7:
        symmetry_approx = "C2"
    else:
        symmetry_approx = "C1"
    
    # Calculate connectivity (Euler characteristic)
    from scipy.ndimage import label
    labeled, num_features = label(img)
    connectivity = num_features / (img.shape[0] * img.shape[1])
    
    # Simple branching analysis
    from skimage.measure import regionprops
    regions = regionprops(labeled)
    angles = []
    for region in regions:
        if hasattr(region, 'orientation') and region.orientation is not None:
            angles.append(np.degrees(region.orientation))
    
    return {
        'dimensionality': float(dimensionality),
        'symmetry': float(symmetry),
        'symmetry_approx': symmetry_approx,
        'repetition_score': float(repetition_score),
        'connectivity': float(connectivity),
        'branching': {
            'count': len(regions),
            'angles': [float(a) for a in angles],
            'mean_angle': float(np.mean(angles)) if angles else 0.0
        }
    }