#!/usr/bin/env python3
"""
Main entry point for the MMSS-Alpha-Formula (v2.0) application.
"""
import sys
import os
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from mmss.mmss_engine import MMSS_Engine

def main():
    """
    Main function to run the MMSS-Alpha-Formula application.
    """
    # Create a dummy image file for testing
    dummy_image_path = "dummy_image.jpg"
    with open(dummy_image_path, "w") as f:
        f.write("This is a dummy image file.")

    try:
        # The new engine does not require a config file in the same way,
        # but we could load one here if needed in the future.
        config = {}
        engine = MMSS_Engine(config)
        
        # Run the analysis
        result = engine.run(dummy_image_path)
        
        # Save the result
        os.makedirs('output/reports', exist_ok=True)
        report_path = os.path.join('output', 'reports', 'mmss_alpha_formula_result.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nAnalysis complete! Report saved to: {report_path}")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up the dummy image file
        if os.path.exists(dummy_image_path):
            os.remove(dummy_image_path)

if __name__ == "__main__":
    main()
