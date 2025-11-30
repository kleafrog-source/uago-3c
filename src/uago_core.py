"""
Main module for the UAGO-3C engine.
Implements the three-cycle core: Discovery → Embodiment → Validation.
"""
import json
import os
import time
from typing import Dict, List
from pathlib import Path
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Correct relative imports (uago_core.py is inside src/)
from .invariant_measurer import measure_invariants
from .symbolic_regressor import generate_formula_from_invariants, _generate_mmss_explanation
from .jsx_visualizer import generate_jsx_visualization


class UAGO3CEngine:
    """
    Main engine for the Universal Adaptive Geometric Observer - Three-Cycle Core.
    """
    
    def __init__(self):
        """
        Initialize the UAGO-3C engine.
        """
        self.config = {}
        self.driver = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_directories(self):
        """Create necessary output directories if they don't exist."""
        output_dir = self.config.get('visualization', {}).get('output_dir', 'output/visualizations')
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs('output/reports', exist_ok=True)
    
    def _setup_selenium(self):
        """Initialize Selenium WebDriver for HTML visualization capture."""
        if self.driver:
            return

        vis_config = self.config.get('visualization', {})
        width = vis_config.get('width', 800)
        height = vis_config.get('height', 800)

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'window-size={width}x{height}')
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        except Exception as e:
            print(f"Could not initialize Selenium WebDriver: {e}")
            self.driver = None
    
    def run(self, image_path: str) -> Dict:
        """
        Run the full UAGO-3C pipeline on the input image.
        
        Args:
            image_path: Path to the input image file
            
        Returns:
            Dictionary containing the analysis results
        """
        result = {
            'status': 'failure',
            'formula': None,
            'attempts': 0,
            'history': []
        }
        
        try:
            # Load the main MMSS config
            self.config = self._load_config('uago_mmss_config.json')
            mmss_config = self.config.get("SYNTHESIZED_MMSS_SYSTEM", {})
            self._setup_directories()
            self._setup_selenium()

            # Load the image using PIL and convert to numpy array
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Ensure image is in the correct format (H, W) or (H, W, 3)
            if len(img_array.shape) == 3:
                if img_array.shape[2] == 4:  # RGBA to RGB
                    img_array = img_array[..., :3]
                elif img_array.shape[2] == 1:  # Grayscale with channel
                    img_array = img_array[..., 0]
            
            # Cycle 1: Discovery
            print("Cycle 1/3: Discovery - Analyzing image invariants...")
            invariants = measure_invariants(img_array)
            formula = generate_formula_from_invariants(
                invariants,
                use_mistral=mmss_config.get('use_mistral_api', False),
                mistral_model=mmss_config.get('mistral_model', 'mistral-large-latest')
            )
            
            # Generate MMSS explanation
            explanation_policy = mmss_config.get("EXPLANATION_POLICY", {})
            mistral_api_key = os.getenv("MISTRAL_API_KEY") # Use environment variable for key
            explanation = _generate_mmss_explanation(
                invariants,
                formula,
                policy=explanation_policy,
                api_key=mistral_api_key,
                model=mmss_config.get('mistral_model', 'mistral-large-latest')
            )
            result['mmss_explanation'] = explanation

            result['history'].append({
                'attempt': 1,
                'formula': formula,
                'invariants': invariants,
                'explanation': explanation
            })
            
            # Set up for cycles 2 and 3
            max_cycles = mmss_config.get('max_cycles', 1) # Default to 1 cycle in MMSS mode
            similarity_threshold = mmss_config.get('similarity_threshold', 0.95)
            
            # If only one cycle is requested, skip validation
            if max_cycles == 1:
                # Generate final visualization for the single cycle
                print("Generating final visualization...")
                html_content = generate_jsx_visualization(
                    formula,
                    invariants,
                    width=self.config.get('visualization', {}).get('width', 800),
                    height=self.config.get('visualization', {}).get('height', 800),
                    mmss_explanation=explanation,
                    config=self.config
                )
                html_path = os.path.join(
                    self.config.get('visualization', {}).get('output_dir', 'output/visualizations'),
                    'final_visualization.html'
                )
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                result['final_visualization'] = html_path

                result['status'] = 'success'
                result['formula'] = formula
                result['attempts'] = 1
                return result
            
            current_formula = formula
            current_invariants = invariants
            
            for attempt in range(2, max_cycles + 1):
                # Cycle 2: Embodiment
                print(f"Cycle {attempt}/3: Embodiment - Generating visualization...")
                html_content = generate_jsx_visualization(
                    current_formula,
                    current_invariants,
                    width=self.config.get('visualization', {}).get('width', 800),
                    height=self.config.get('visualization', {}).get('height', 800),
                    mmss_explanation=explanation, # Carry over explanation
                    config=self.config
                )
                
                # Save HTML and capture screenshot
                html_path = os.path.join(
                    self.config['visualization']['output_dir'],
                    f'attempt_{attempt}.html'
                )
                png_path = html_path.replace('.html', '.png')
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                self._capture_screenshot(html_path, png_path)
                
                # Cycle 3: Validation
                print(f"Cycle {attempt}/3: Validation - Analyzing visualization...")
                new_invariants = measure_invariants(png_path)
                new_formula = generate_formula_from_invariants(
                    new_invariants,
                    use_mistral=self.config.get('use_mistral_api', False),
                    mistral_model=self.config.get('mistral_model', 'mistral-large-latest')
                )
                
                # Calculate similarity (now exact string match for canonical formulas)
                similarity = self._calculate_formula_similarity(current_formula, new_formula)
                
                # Update result
                result['history'].append({
                    'attempt': attempt,
                    'formula': new_formula,
                    'visualization': html_path,
                    'invariants': new_invariants,
                    'similarity_score': similarity
                })
                
                # Check if we've converged
                if similarity >= similarity_threshold:
                    result['status'] = 'success'
                    result['formula'] = new_formula
                    result['attempts'] = attempt
                    break
                
                # Prepare for next iteration
                current_formula = new_formula
                current_invariants = new_invariants
            
            # If we get here without success
            if result['status'] != 'success':
                result['attempts'] = max_cycles
            
        except Exception as e:
            print(f"Error during UAGO-3C execution: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _capture_screenshot(self, html_path: str, output_path: str):
        """Capture a screenshot of the HTML visualization."""
        try:
            self.driver.get(f'file://{os.path.abspath(html_path)}')
            time.sleep(2)  # Wait for JS to execute
            self.driver.save_screenshot(output_path)
        except Exception as e:
            print(f"Warning: Failed to capture screenshot: {str(e)}")
    
    def _calculate_formula_similarity(self, formula1: str, formula2: str) -> float:
        """
        Calculate similarity between two formulas.
        Since formulas are now canonical (e.g., 'IFS_Sierpinski: ...'),
        we use exact string matching after normalizing whitespace.
        """
        # Normalize: remove extra whitespace and compare
        norm1 = ' '.join(formula1.split())
        norm2 = ' '.join(formula2.split())
        return 1.0 if norm1 == norm2 else 0.0
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()