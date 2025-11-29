"""
Module for generating interactive visualizations using JSXGraph.
"""
import json
from typing import Dict, Optional
import os
import numpy as np
from jinja2 import Template

# Template for the HTML visualization
VISUALIZATION_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>UAGO-3C Visualization</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/jsxgraph@1.7.0/distrib/jsxgraph.css" />
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        #jxgbox { width: {{ width }}px; height: {{ height }}px; margin: 20px auto; }
        .container { max-width: 800px; margin: 0 auto; }
        .info { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
    <div id="jxgbox" class="jxgbox"></div>
        <h1>UAGO-3C Visualization</h1>
        <div class="info">
            <p><strong>Formula:</strong> {{ formula }}</p>
            <p><strong>Dimensionality:</strong> {{ "%.3f"|format(invariants.dimensionality) }}</p>
            <p><strong>Symmetry:</strong> {{ invariants.symmetry_approx }}</p>
        </div>
        
    </div>

    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/jsxgraph@1.7.0/distrib/jsxgraphcore.js"></script>
    <script type="text/javascript">
        (function() {
            const board = JXG.JSXGraph.initBoard('jxgbox', {
                boundingbox: [-5, 5, 5, -5],
                axis: true,
                showCopyright: false,
                showNavigation: true
            });

            // Visualization logic will be inserted here
            {{ visualization_script|safe }}
        })();
    </script>
</body>
</html>
"""

def generate_jsx_visualization(formula: str, invariants: Dict, width: int = 500, height: int = 500) -> str:
    """
    Generate an interactive JSXGraph visualization based on the formula and invariants.
    
    Args:
        formula: The symbolic formula to visualize
        invariants: Dictionary containing geometric invariants
        width: Width of the visualization in pixels
        height: Height of the visualization in pixels
        
    Returns:
        str: HTML content as a string
    """
    # Determine the visualization type based on invariants
    vis_type = _determine_visualization_type(invariants)
    
    # Generate the appropriate visualization script
    vis_script = _generate_visualization_script(vis_type, formula, invariants)
    
    # Render the template
    template = Template(VISUALIZATION_TEMPLATE)
    html = template.render(
        width=width,
        height=height,
        formula=formula,
        invariants=invariants,
        visualization_script=vis_script
    )
    
    return html

def _determine_visualization_type(invariants: Dict) -> str:
    """
    Determine the appropriate visualization type based on invariants.
    
    Args:
        invariants: Dictionary containing geometric invariants
        
    Returns:
        str: Visualization type identifier
    """
    dim = invariants.get('dimensionality', 0)
    symmetry = invariants.get('symmetry_approx', 'C1')
    rep_score = invariants.get('repetition_score', 0)
    connectivity = invariants.get('connectivity', 1)
    
    # Sierpiński pattern
    if 1.55 <= dim <= 1.60 and symmetry == "C3":
        return "sierpinski"
    
    # Koch curve
    elif 1.24 <= dim <= 1.28 and "D" in symmetry:
        return "koch"
    
    # Mandelbrot/Julia set
    elif 1.95 <= dim <= 2.05 and rep_score > 0.85:
        return "julia"
    
    # Dragon curve
    elif 1.95 <= dim <= 2.05 and invariants.get('branching', {}).get('angles') == [90.0]:
        return "dragon"
    
    # Leaf/Tree
    elif 1.80 <= dim <= 1.90 and ("C5" in symmetry or "C∞" in symmetry):
        return "tree"
    
    # Menger sponge
    elif 2.70 <= dim <= 2.75 and symmetry == "Oh":
        return "menger"
    
    # Cellular automaton
    elif 1.4 <= dim <= 2.0 and rep_score < 0.7:
        return "automaton"
    
    # Parametric spiral
    elif 1.0 <= dim <= 1.2 and symmetry == "C∞":
        return "spiral"
    
    # Algebraic fractal
    elif 1.6 <= dim <= 2.0 and connectivity == 1:
        return "algebraic"
    
    # Default to Cantor set
    else:
        return "cantor"

def _generate_visualization_script(vis_type: str, formula: str, invariants: Dict) -> str:
    """
    Generate the JavaScript code for the specified visualization type.
    
    Args:
        vis_type: Type of visualization to generate
        formula: The formula to visualize
        invariants: Dictionary containing geometric invariants
        
    Returns:
        str: JavaScript code as a string
    """
    if vis_type == "sierpinski":
        return """
            function sierpinski(points, depth) {
                if (depth <= 0) {
                    return [points[0], points[1], points[2]];
                }
                
                const p1 = [(points[0][0] + points[1][0]) / 2, 
                           (points[0][1] + points[1][1]) / 2];
                const p2 = [(points[1][0] + points[2][0]) / 2, 
                           (points[1][1] + points[2][1]) / 2];
                const p3 = [(points[0][0] + points[2][0]) / 2, 
                           (points[0][1] + points[2][1]) / 2];
                
                return [
                    ...sierpinski([points[0], p1, p3], depth - 1),
                    ...sierpinski([p1, points[1], p2], depth - 1),
                    ...sierpinski([p3, p2, points[2]], depth - 1)
                ];
            }
            
            const depth = 5;
            const triangles = sierpinski([[-4, -4], [4, -4], [0, 4]], depth);
            
            for (let i = 0; i < triangles.length; i += 3) {
                board.create('polygon', [
                    triangles[i], triangles[i+1], triangles[i+2]
                ], {fillColor: 'blue', fillOpacity: 0.3});
            }
        """
    
    elif vis_type == "koch":
        return """
            function koch(p1, p2, depth) {
                if (depth <= 0) {
                    return board.create('line', [p1, p2], {strokeColor: 'blue', strokeWidth: 1});
                }
                
                const dx = p2[0] - p1[0];
                const dy = p2[1] - p1[1];
                
                const pA = [p1[0] + dx/3, p1[1] + dy/3];
                const pC = [p1[0] + 2*dx/3, p1[1] + 2*dy/3];
                
                // Calculate the new point to form an equilateral triangle
                const angle = Math.PI / 3; // 60 degrees
                const pB = [
                    pA[0] + Math.cos(angle) * (pC[0] - pA[0]) - Math.sin(angle) * (pC[1] - pA[1]),
                    pA[1] + Math.sin(angle) * (pC[0] - pA[0]) + Math.cos(angle) * (pC[1] - pA[1])
                ];
                
                return [
                    ...koch(p1, pA, depth - 1),
                    ...koch(pA, pB, depth - 1),
                    ...koch(pB, pC, depth - 1),
                    ...koch(pC, p2, depth - 1)
                ];
            }
            
            const depth = 4;
            koch([-4, 0], [4, 0], depth);
        """
    
    # Add more visualization types as needed...
    
    else:
        # Default visualization (Cantor set)
        return """
            function cantor(x, y, len, depth) {
                if (depth <= 0) return;
                
                board.create('line', [[x, y], [x + len, y]], 
                    {strokeColor: 'blue', strokeWidth: 2});
                
                cantor(x, y - 1, len/3, depth - 1);
                cantor(x + 2*len/3, y - 1, len/3, depth - 1);
            }
            
            cantor(-4, 0, 8, 5);
        """