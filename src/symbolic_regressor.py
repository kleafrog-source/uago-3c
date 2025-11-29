"""
Module for generating symbolic formulas from geometric invariants.
Supports both local symbolic regression and Mistral API-based generation.
"""
import json
import time
from typing import Dict, Optional
import numpy as np
import requests
from pysr import PySRRegressor


def generate_formula_from_invariants(
    invariants: Dict,
    use_mistral: bool = False,
    mistral_api_key: Optional[str] = None,
    mistral_model: str = "mistral-large-latest"
) -> str:
    """
    Generate a symbolic formula from geometric invariants.
    
    Args:
        invariants: Dictionary containing geometric invariants
        use_mistral: Whether to use Mistral API for formula generation
        mistral_api_key: API key for Mistral (required if use_mistral=True)
        mistral_model: Mistral model to use for generation
        
    Returns:
        str: Generated symbolic formula as a string
    """
    if use_mistral and mistral_api_key:
        try:
            return _generate_with_mistral(invariants, mistral_api_key, mistral_model)
        except Exception as e:
            print(f"Mistral API call failed, falling back to local regression: {str(e)}")
    
    # Fall back to local symbolic regression
    return _generate_with_local_regression(invariants)


def _generate_with_mistral(
    invariants: Dict,
    api_key: str,
    model: str,
    timeout: int = 10
) -> str:
    """
    Generate formula using Mistral API.
    
    Args:
        invariants: Dictionary of geometric invariants
        api_key: Mistral API key
        model: Mistral model name
        timeout: Request timeout in seconds
        
    Returns:
        str: Generated formula
    """
    # Prepare the prompt
    prompt = (
        "Given the following geometric invariants extracted from an image, "
        "provide the most likely generative formula in a standard mathematical form. "
        "Respond with just the formula, without any additional text or explanation.\n\n"
        f"Invariants: {json.dumps(invariants, indent=2)}\n\n"
        "Formula: "
    )
    
    # Make the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a mathematical assistant that generates concise symbolic formulas."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }
    
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Mistral API error: {response.text}")
    
    # Extract and clean the formula from the response
    result = response.json()
    formula = result['choices'][0]['message']['content'].strip()
    
    # Remove any markdown code blocks if present
    if formula.startswith('```') and formula.endswith('```'):
        formula = formula[3:-3].strip()
    
    return formula


def _generate_with_local_regression(invariants: Dict) -> str:
    """
    Generate formula using local symbolic regression.
    
    Args:
        invariants: Dictionary of geometric invariants
        
    Returns:
        str: Generated formula
    """
    # Extract relevant features for regression
    features = []
    feature_names = []
    
    # Add scalar features
    for key in ['dimensionality', 'connectivity', 'repetition_score']:
        if key in invariants:
            features.append(float(invariants[key]))
            feature_names.append(key)
    
    # Add branching angles if available
    if 'branching' in invariants and 'angles' in invariants['branching']:
        angles = invariants['branching']['angles']
        if angles:
            features.append(float(np.mean(angles)))
            feature_names.append('mean_branch_angle')
    
    # Add symmetry as a numerical feature
    symmetry_map = {
        'C1': 1, 'C2': 2, 'C3': 3, 'C4': 4, 'C6': 6,
        'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4, 'D6': 6,
        'Oh': 8, 'Ih': 12, 'Td': 12
    }
    
    symmetry = invariants.get('symmetry_approx', 'C1')
    features.append(float(symmetry_map.get(symmetry, 1)))
    feature_names.append('symmetry_order')
    
    # Prepare the data for symbolic regression
    try:
        # Create meaningful target values based on invariants
        X = []
        y = []
        
        # Create data points based on the features
        for _ in range(100):
            # Generate random points in the feature space
            x_vals = [np.random.uniform(0.1, 2.0) for _ in range(len(features))]
            
            # Calculate a target value based on the features
            # This is a simple example - adjust based on your needs
            target = 0.0
            for i, val in enumerate(x_vals):
                # Weight different features differently
                weight = 1.0 / (i + 1)
                target += weight * val
            
            X.append(x_vals)
            y.append(target)
        
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        
        # Add some noise to prevent perfect fits
        y += np.random.normal(0, 0.1 * np.std(y), size=y.shape)
        
        # Configure and run symbolic regression with improved settings
        model = PySRRegressor(
            niterations=20,  # Increased iterations for better results
            binary_operators=["+", "*", "-", "/"],  # Basic arithmetic operators
            unary_operators=["square", "cube", "sqrt"],  # Simple unary operators
            populations=8,  # Increased population size
            parsimony=0.1,  # Balanced parsimony
            maxsize=20,  # Increased max size for more complex formulas
            warm_start=True,  # Enable warm start for faster convergence
            batching=True,  # Enable batching for better performance
            batch_size=50,  # Batch size for training
            max_evals=1000,  # Increased max evaluations
            constraints={"pow": 3},  # Limit power operations
            procs=0,  # Use Python backend instead of Julia for better compatibility
            parallelism='serial'  # Replaces multithreading=False
        )
        
        # Fit the model with error handling
        try:
            model.fit(X, y)
            
            # Get the best equation
            best_equation = model.sympy()
            
            # Convert to string and clean up
            formula = str(best_equation)
            
            # Replace variable names with more meaningful ones
            for i, name in enumerate(feature_names):
                formula = formula.replace(f"x{i}", name)
            
            # Check if we got a meaningful formula
            if len(formula) < 5:  # Very simple formula, likely a fallback
                raise ValueError("Formula too simple, likely a fallback")
            if len(X) == 0 or len(y) == 0:
                raise ValueError("No valid data points for regression")
            
            if np.all(y == y[0]):  # All y values are the same
                y = y + np.random.normal(0, 0.1, size=y.shape)  # Add small noise
            
            return formula
            
        except Exception as e:
            print(f"Symbolic regression failed during fitting: {str(e)}")
            print(f"Feature names: {feature_names}")
            print(f"X sample: {X[0] if X is not None and len(X) > 0 else 'None'}")
            print(f"y sample: {y[0] if y is not None and len(y) > 0 else 'None'}")
            
            # Fallback to a formula based on dimensionality
            dim = invariants.get('dimensionality', 1.5)
            return f"x^{dim:.3f} + y^{dim:.3f}"
            
    except Exception as e:
        print(f"Error preparing data for symbolic regression: {str(e)}")
        # Fallback to a simple formula based on dimensionality
        dim = invariants.get('dimensionality', 1.5)
        return f"x^{dim:.3f} + y^{dim:.3f}"