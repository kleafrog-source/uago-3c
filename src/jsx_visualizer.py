"""
Module for generating interactive visualizations using JSXGraph.
Supports 10+ fractal types based on measured invariants.
"""
import json
from typing import Dict
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

            // Visualization logic
            {{ visualization_script|safe }}
        })();
    </script>
</body>
</html>
"""


def generate_jsx_visualization(formula: str, invariants: Dict, width: int = 500, height: int = 500) -> str:
    """
    Generate an interactive JSXGraph visualization based on the formula and invariants.
    """
    vis_type = _determine_visualization_type(invariants)
    vis_script = _generate_visualization_script(vis_type, formula, invariants)
    template = Template(VISUALIZATION_TEMPLATE)
    return template.render(
        width=width,
        height=height,
        formula=formula,
        invariants=invariants,
        visualization_script=vis_script
    )


def _determine_visualization_type(invariants: Dict) -> str:
    dim = invariants.get('dimensionality', 0)
    symmetry = invariants.get('symmetry_approx', 'C1')
    rep_score = invariants.get('repetition_score', 0)
    connectivity = invariants.get('connectivity', 1)
    branching = invariants.get('branching', {})
    angles = branching.get('angles', [])

    if 1.55 <= dim <= 1.60 and symmetry == "C3":
        return "sierpinski"
    elif 1.24 <= dim <= 1.28 and ("D" in symmetry or symmetry in ["C6", "C12"]):
        return "koch"
    elif 1.95 <= dim <= 2.05 and rep_score > 0.85:
        return "julia"
    elif 1.95 <= dim <= 2.05 and angles == [90.0]:
        return "dragon"
    elif 1.80 <= dim <= 1.90 and ("C5" in symmetry or "C∞" in symmetry):
        return "tree"
    elif 2.70 <= dim <= 2.75 and symmetry == "Oh":
        return "menger"
    elif 1.4 <= dim <= 2.0 and rep_score < 0.7:
        return "automaton"
    elif 1.0 <= dim <= 1.2 and symmetry == "C∞":
        return "spiral"
    elif 1.6 <= dim <= 2.0 and connectivity == 1:
        return "algebraic"
    elif dim < 1.0:
        return "cantor"
    else:
        return "generic"


def _generate_visualization_script(vis_type: str, formula: str, invariants: Dict) -> str:
    scripts = {
        "sierpinski": """
            function sierpinski(points, depth) {
                if (depth <= 0) {
                    board.create('polygon', points, {fillColor: 'lightblue', strokeColor: 'navy'});
                    return;
                }
                const p12 = [(points[0][0]+points[1][0])/2, (points[0][1]+points[1][1])/2];
                const p23 = [(points[1][0]+points[2][0])/2, (points[1][1]+points[2][1])/2];
                const p31 = [(points[2][0]+points[0][0])/2, (points[2][1]+points[0][1])/2];
                sierpinski([points[0], p12, p31], depth-1);
                sierpinski([p12, points[1], p23], depth-1);
                sierpinski([p31, p23, points[2]], depth-1);
            }
            sierpinski([[-4,-3.464],[4,-3.464],[0,3.464]], 4);
        """,
        "koch": """
            function koch(a, b, depth) {
                if (depth === 0) {
                    board.create('line', [a, b], {strokeWidth: 1.5});
                    return;
                }
                const dx = b[0] - a[0], dy = b[1] - a[1];
                const p1 = [a[0] + dx/3, a[1] + dy/3];
                const p3 = [a[0] + 2*dx/3, a[1] + 2*dy/3];
                const angle = Math.PI/3;
                const p2 = [
                    p1[0] + (p3[0]-p1[0])*Math.cos(angle) - (p3[1]-p1[1])*Math.sin(angle),
                    p1[1] + (p3[0]-p1[0])*Math.sin(angle) + (p3[1]-p1[1])*Math.cos(angle)
                ];
                koch(a, p1, depth-1);
                koch(p1, p2, depth-1);
                koch(p2, p3, depth-1);
                koch(p3, b, depth-1);
            }
            koch([-4,0], [4,0], 4);
            koch([4,0], [0,3.464], 4);
            koch([0,3.464], [-4,0], 4);
        """,
        "julia": """
            // Simplified Julia set approximation (grid-based)
            const maxIter = 50;
            for (let x = -2; x <= 2; x += 0.05) {
                for (let y = -2; y <= 2; y += 0.05) {
                    let zx = x, zy = y, iter = 0;
                    while (zx*zx + zy*zy < 4 && iter < maxIter) {
                        const tmp = zx*zx - zy*zy + -0.7; // c = -0.7 (example)
                        zy = 2*zx*zy + 0.27015;          // c = 0.27015i
                        zx = tmp;
                        iter++;
                    }
                    if (iter === maxIter) {
                        board.create('point', [x, y], {size: 1, color: 'black', withLabel: false});
                    }
                }
            }
        """,
        "dragon": """
            function dragon(points, depth, flip) {
                if (depth === 0) {
                    board.create('line', points, {strokeWidth: 1});
                    return;
                }
                const mid = [(points[0][0]+points[1][0])/2, (points[0][1]+points[1][1])/2];
                const dx = points[1][0] - points[0][0];
                const dy = points[1][1] - points[0][1];
                const len = Math.sqrt(dx*dx + dy*dy) / 2;
                const angle = Math.atan2(dy, dx) + (flip ? Math.PI/2 : -Math.PI/2);
                const newPoint = [mid[0] + len*Math.cos(angle), mid[1] + len*Math.sin(angle)];
                dragon([points[0], newPoint], depth-1, false);
                dragon([newPoint, points[1]], depth-1, true);
            }
            dragon([[-3,0], [3,0]], 10, false);
        """,
        "tree": """
            function drawBranch(x, y, angle, length, depth) {
                if (depth <= 0) return;
                const endX = x + length * Math.cos(angle);
                const endY = y + length * Math.sin(angle);
                board.create('line', [[x,y], [endX,endY]], {strokeWidth: depth});
                drawBranch(endX, endY, angle - 0.6, length * 0.7, depth - 1);
                drawBranch(endX, endY, angle + 0.6, length * 0.7, depth - 1);
            }
            drawBranch(0, -4, Math.PI/2, 2, 6);
        """,
        "menger": """
            function menger(x, y, size, depth) {
                if (depth === 0) {
                    board.create('polygon', [
                        [x, y], [x+size, y], [x+size, y+size], [x, y+size]
                    ], {fillColor: 'lightgray', strokeColor: 'gray'});
                    return;
                }
                const step = size / 3;
                for (let i = 0; i < 3; i++) {
                    for (let j = 0; j < 3; j++) {
                        if (i === 1 && j === 1) continue; // center hole
                        menger(x + i*step, y + j*step, step, depth - 1);
                    }
                }
            }
            menger(-4, -4, 8, 3);
        """,
        "automaton": """
            // Rule 30 approximation (1D cellular automaton)
            const rule30 = (a, b, c) => (a ^ (b || c)) ? 1 : 0;
            const width = 101;
            const steps = 50;
            let current = new Array(width).fill(0);
            current[Math.floor(width/2)] = 1;
            for (let t = 0; t < steps; t++) {
                for (let i = 0; i < width; i++) {
                    if (current[i]) {
                        board.create('point', [i - width/2, -t], {size: 1, color: 'black', withLabel: false});
                    }
                }
                let next = [];
                for (let i = 0; i < width; i++) {
                    const left = i > 0 ? current[i-1] : 0;
                    const center = current[i];
                    const right = i < width-1 ? current[i+1] : 0;
                    next.push(rule30(left, center, right));
                }
                current = next;
            }
        """,
        "spiral": """
            const curve = board.create('curve', [
                (t) => 0.5 * Math.exp(0.2 * t) * Math.cos(t),
                (t) => 0.5 * Math.exp(0.2 * t) * Math.sin(t),
                0, 10
            ], {strokeColor: 'darkgreen', strokeWidth: 2});
        """,
        "algebraic": """
            // Newton fractal for f(z) = z^3 - 1
            const maxIter = 20;
            for (let x = -2; x <= 2; x += 0.1) {
                for (let y = -2; y <= 2; y += 0.1) {
                    let zx = x, zy = y;
                    let iter = 0;
                    while (iter < maxIter) {
                        const x2 = zx*zx, y2 = zy*zy;
                        const denom = (x2 + y2) * (x2 + y2);
                        if (denom === 0) break;
                        const nx = zx - (x2*x2 - 6*x2*y2 + y2*y2 + x2 - y2) / (3*denom);
                        const ny = zy - (4*zx*zy*(x2 - y2) + 2*zx*zy) / (3*denom);
                        if (Math.abs(zx - nx) < 0.01 && Math.abs(zy - ny) < 0.01) break;
                        zx = nx; zy = ny;
                        iter++;
                    }
                    const color = iter % 3 === 0 ? 'red' : (iter % 3 === 1 ? 'green' : 'blue');
                    board.create('point', [x, y], {size: 1, color: color, withLabel: false});
                }
            }
        """,
        "cantor": """
            function cantor(x, y, len, depth) {
                if (depth <= 0) {
                    board.create('line', [[x, y], [x + len, y]], {strokeWidth: 2});
                    return;
                }
                cantor(x, y - 0.8, len/3, depth - 1);
                cantor(x + 2*len/3, y - 0.8, len/3, depth - 1);
            }
            cantor(-4, 0, 8, 5);
        """,
        "generic": """
            board.create('text', [0, 0, 'Unknown fractal structure'], {fontSize: 16});
        """
    }
    return scripts.get(vis_type, scripts["generic"])