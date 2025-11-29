"""
Main module for the UAGO-3C engine.
"""
import json
import os
import time
from typing import Dict, List, Optional
from pathlib import Path
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.invariant_measurer import measure_invariants
from src.symbolic_regressor import generate_formula_from_invariants
from src.jsx_visualizer import generate_jsx_visualization


class UAGO3CEngine:
    """
    Main engine for the Universal Adaptive Geometric Observer - Three-Cycle Core.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the UAGO-3C engine.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_directories()
        self._setup_selenium()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _setup_directories(self):
        """Create necessary output directories if they don't exist."""
        os.makedirs(self.config['visualization']['output_dir'], exist_ok=True)
        os.makedirs('output/reports', exist_ok=True)
    
    def _setup_selenium(self):
        """Initialize Selenium WebDriver for HTML visualization capture."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'window-size={self.config["visualization"]["width"]}x{self.config["visualization"]["height"]}')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    
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
            # Cycle 1: Discovery
            print("Cycle 1/3: Discovery - Analyzing image invariants...")
            
            # Load the image using PIL and convert to numpy array
            try:
                img = Image.open(image_path)
                img_array = np.array(img)
                
                # Ensure image is in the correct format (H, W) or (H, W, 3) or (H, W, 4)
                if len(img_array.shape) == 3:
                    if img_array.shape[2] == 4:  # RGBA to RGB
                        img_array = img_array[..., :3]
                
                invariants = measure_invariants(img_array)
                formula = generate_formula_from_invariants(
                    invariants,
                    use_mistral=self.config.get('use_mistral_api', False),
                    mistral_model=self.config.get('mistral_model', 'mistral-large-latest')
                )
            except Exception as e:
                print(f"Error loading/processing image: {str(e)}")
                raise
            
            result['history'].append({
                'attempt': 1,
                'formula': formula,
                'invariants': invariants
            })
            
            # Set up for cycles 2 and 3
            max_cycles = self.config.get('max_cycles', 3)
            similarity_threshold = self.config.get('similarity_threshold', 0.95)
            
            for attempt in range(2, max_cycles + 1):
                # Cycle 2: Embodiment
                print(f"Cycle {attempt}/3: Embodiment - Generating visualization...")
                html_content = generate_jsx_visualization(
                    formula,
                    invariants,
                    width=self.config['visualization']['width'],
                    height=self.config['visualization']['height']
                )
                
                # Save HTML and capture screenshot
                html_path = os.path.join(
                    self.config['visualization']['output_dir'],
                    f'attempt_{attempt}.html'
                )
                png_path = html_path.replace('.html', '.png')
                
                with open(html_path, 'w') as f:
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
                
                # Calculate similarity
                similarity = self._calculate_formula_similarity(formula, new_formula)
                
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
                formula = new_formula
                invariants = new_invariants
            
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
        
        This is a simplified implementation. In a real system, you would want
        to use a more sophisticated method for comparing mathematical expressions.
        """
        # Simple token-based similarity
        tokens1 = set(formula1.lower().replace(' ', ''))
        tokens2 = set(formula2.lower().replace(' ', ''))
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()