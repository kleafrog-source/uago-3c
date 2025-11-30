"""
Module for generating symbolic formulas from geometric invariants.
Uses a rule-based approach for known fractal types, with optional Mistral API fallback.
"""
import json
import requests
from typing import Dict, Optional


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
    # First, try rule-based matching (deterministic and accurate)
    formula = _generate_with_rule_based(invariants)
    
    # Optionally refine or replace using Mistral API
    if use_mistral and mistral_api_key:
        try:
            mistral_formula = _generate_with_mistral(invariants, mistral_api_key, mistral_model)
            # Use Mistral result only if it's not obviously worse
            if "formula" not in mistral_formula.lower() and len(mistral_formula) > 5:
                formula = mistral_formula
        except Exception as e:
            print(f"Mistral API call failed, using rule-based formula: {str(e)}")
    
    return formula


def _generate_with_rule_based(invariants: Dict) -> str:
    """
    Generate formula using a deterministic rule-based system for known fractal types.
    """
    dim = invariants.get('dimensionality', 0)
    sym = invariants.get('symmetry_approx', 'C1')
    rep = invariants.get('repetition_score', 0)
    connectivity = invariants.get('connectivity', 1)
    branching = invariants.get('branching', {})
    angles = branching.get('angles', [])
    
    # Sierpiński triangle
    if 1.55 <= dim <= 1.60 and sym == "C3":
        return "IFS_Sierpinski: f1(x,y)=(x/2,y/2), f2(x,y)=(x/2+0.5,y/2), f3(x,y)=(x/2,y/2+0.5)"
    
    # Koch snowflake / curve
    elif 1.24 <= dim <= 1.28 and ("D" in sym or sym in ["C6", "C12"]):
        return "L-system_Koch: F -> F+F--F+F, angle=60°"
    
    # Mandelbrot/Julia set
    elif 1.95 <= dim <= 2.05 and rep > 0.85:
        return "Julia_Set: z_{n+1} = z_n^2 + c"
    
    # Heighway dragon curve
    elif 1.95 <= dim <= 2.05 and angles == [90.0]:
        return "Dragon_Curve: iterated 90° folding, seed=(0,0)->(1,0)"
    
    # Maple leaf / tree (L-system based)
    elif 1.80 <= dim <= 1.90 and ("C5" in sym or "C∞" in sym):
        return "L-system_Tree: A -> F[+A][-A]F, angle=36°, scale=0.7"
    
    # Menger sponge (2D projection)
    elif 2.70 <= dim <= 2.75 and sym == "Oh":
        return "IFS_Menger: divide cube into 3x3x3, remove 7 central subcubes"
    
    # Cellular automaton (Rule 30, 110, etc.)
    elif 1.4 <= dim <= 2.0 and rep < 0.7:
        return "Cellular_Automaton: 1D rule with binary states and local update"
    
    # Logarithmic spiral
    elif 1.0 <= dim <= 1.2 and sym == "C∞":
        return "Parametric_Spiral: r(θ) = a * exp(b * θ)"
    
    # Newton fractal or other algebraic
    elif 1.6 <= dim <= 2.0 and connectivity == 1:
        return "Algebraic_Fractal: root-finding iteration for complex polynomial"
    
    # Cantor set (1D, disconnected)
    elif dim < 1.0:
        return "Cantor_Set: remove middle third recursively"
    
    # Fallback for unknown patterns
    else:
        return f"Unknown_fractal: dimensionality={dim:.3f}, symmetry={sym}, repetition={rep:.2f}"


def _generate_with_mistral(
    invariants: Dict,
    api_key: str,
    model: str,
    timeout: int = 10
) -> str:
    """
    Generate formula using Mistral API.
    """
    prompt = (
        "Given the following geometric invariants extracted from an image, "
        "provide the most likely generative formula in a standard mathematical form. "
        "Respond with just the formula, without any additional text or explanation.\n\n"
        f"Invariants: {json.dumps(invariants, indent=2)}\n\n"
        "Formula: "
    )
    
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
    
    formula = response.json()['choices'][0]['message']['content'].strip()
    
    # Clean markdown code blocks
    if formula.startswith('```') and formula.endswith('```'):
        formula = formula[3:-3].strip()
    
    return formula

def _generate_mmss_explanation(
    invariants: Dict,
    formula: str,
    policy: Dict,
    api_key: Optional[str] = None,
    model: str = "mistral-large-latest",
    timeout: int = 15
) -> str:
    """
    Generates a human-readable explanation using a policy-driven prompt.
    """
    if not policy.get("generate_explanation", False) or not api_key:
        return ""

    try:
        prompt = policy["prompt_template"].format(invariants=json.dumps(invariants, indent=2), formula=formula)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a fractal geometry expert providing insightful analysis."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 250
        }

        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )

        if response.status_code != 200:
            return f"Error: Mistral API returned status {response.status_code}. {response.text}"

        explanation = response.json()['choices'][0]['message']['content'].strip()
        return explanation

    except Exception as e:
        return f"Error generating explanation: {str(e)}"
