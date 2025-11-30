#!/usr/bin/env python3
"""
Main entry point for the UAGO-3C application.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from uago_core import UAGO3CEngine


def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    try:
        # Initialize the engine
        config_path = os.path.join('config', 'uago_config.json')
        engine = UAGO3CEngine(config_path)
        
        # Run the analysis
        print(f"Starting UAGO-3C analysis for: {image_path}")
        result = engine.run(image_path)
        
        # Save the result
        os.makedirs('output/reports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join('output', 'reports', f'result_{timestamp}.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nAnalysis complete! Report saved to: {report_path}")
        print(f"Status: {result['status'].upper()}")
        
        if result['status'] == 'success':
            print(f"Final formula: {result['formula']}")
        
        # Also update the latest.json
        latest_path = os.path.join('output', 'reports', 'latest.json')
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()