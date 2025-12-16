"""
Core engine for the MMSS-Alpha-Formula (v2.0) architecture.
Orchestrates the bi-directional, iterative control loop.
"""
import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from mistralai import Mistral

from .openflexure_mock import MockOpenFlexureAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MMSS_Engine:
    """
    The MMSS-Engine orchestrates the iterative control loop for meta-formula synthesis.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the MMSS-Engine.

        Args:
            config: A dictionary containing the configuration for the engine.
        """
        self.config = config
        self.safety_mode_active = os.getenv('MMSS_SAFETY_MODE_ACTIVE', 'False').lower() == 'true'
        self.microscope = MockOpenFlexureAPI()
        self.max_iterations = 3

        # Initialize Mistral client
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        if self.mistral_api_key:
            self.mistral_client = Mistral(api_key=self.mistral_api_key)
        else:
            self.mistral_client = None
            logger.warning("MISTRAL_API_KEY not found. Mistral API calls will be simulated.")

        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader('src/mmss/'))

        if self.safety_mode_active:
            logger.info("MMSS_SAFETY_MODE_ACTIVE is True. Microscope commands will be simulated.")

    def run(self, initial_image_path: str) -> Dict[str, Any]:
        """
        Runs the iterative control loop to derive a meta-formula.

        Args:
            initial_image_path: The path to the initial image for analysis.

        Returns:
            A dictionary containing the final result of the analysis.
        """
        logger.info("Starting MMSS-Alpha-Formula (v2.0) run.")

        current_image_path = initial_image_path
        v_stability_counter = 0
        last_v = 0.0
        candidate_formula = "N/A"

        for i in range(self.max_iterations):
            logger.info(f"--- Iteration {i + 1}/{self.max_iterations} ---")

            # Step A: Capture & Atomization (simulated for now)
            mmss_atoms = self._capture_and_atomize(current_image_path)

            # Step B: Hypothesis Generation (Mistral API call)
            mistral_response = self._generate_hypothesis(mmss_atoms)
            candidate_formula = mistral_response.get("formula")
            refinement_command = mistral_response.get("command")

            # Step C: Safety & Validation
            command_validated = False
            if self.safety_mode_active:
                logger.info(f"Command '{refinement_command}' simulated and skipped.")
            else:
                command_validated = self._validate_command(refinement_command, mmss_atoms)

            # Step D: Execution & Iteration
            if not self.safety_mode_active and command_validated:
                if refinement_command.startswith('MOVE_Z'):
                    value = int(refinement_command.split('(')[1].split(')')[0])
                    current_image_path = self.microscope.execute_command(refinement_command, value=value)

            # Step E: Termination Check
            current_v = self._calculate_semantic_value(mmss_atoms)
            if current_v >= 0.999:
                logger.info(f"Termination criteria met: V ({current_v}) >= 0.999")
                break

            if abs(current_v - last_v) < 0.001:
                v_stability_counter += 1
                if v_stability_counter >= 3:
                    logger.info("Termination criteria met: V stability over 3 iterations.")
                    break
            else:
                v_stability_counter = 0

            last_v = current_v

        final_metrics = {
            "V": last_v,
            "S": mmss_atoms.get("S"),
            "D_f": mmss_atoms.get("D_f"),
            "R_T": mmss_atoms.get("R_T")
        }
        final_result = self._generate_final_output(candidate_formula, final_metrics)
        logger.info("MMSS-Alpha-Formula run finished.")
        return final_result

    def _capture_and_atomize(self, image_path: str) -> Dict[str, Any]:
        """
        Performs the MMSS atomization process (based on MIX_055 and MIX_073).
        """
        logger.info(f"Atomizing image: {image_path}")
        return {
            "V": 0.95 + (0.01 * (3 - self.max_iterations)),
            "S": 0.05,
            "D_f": 9.0,
            "R_T": 2.618,
            "language_atoms": ["atom1", "atom2", "atom3"],
            "structural_relations": ["rel1", "rel2"]
        }

    def _generate_hypothesis(self, mmss_atoms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a hypothesis using the Mistral API with a Jinja2 template.
        """
        if not self.mistral_client:
            logger.warning("Mistral client not available. Using simulated response.")
            return self._get_simulated_hypothesis()

        try:
            template = self.jinja_env.get_template('mistral_prompt.jinja2')
            prompt = template.render(mmss_atoms=mmss_atoms)

            chat_response = self.mistral_client.chat(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = chat_response.choices[0].message.content
            return json.loads(response_text)

        except Exception as e:
            logger.error(f"Mistral API call failed: {e}. Using simulated response.")
            return self._get_simulated_hypothesis()

    def _get_simulated_hypothesis(self) -> Dict[str, Any]:
        """
        Returns a simulated hypothesis for fallback.
        """
        iteration = self.max_iterations - (self.max_iterations - 1)
        command = f"MOVE_Z({100 * iteration})"
        return {
            "formula": f"SIMULATED_FORMULA_ITER_{iteration}",
            "command": command
        }

    def _validate_command(self, command: str, current_metrics: Dict[str, Any]) -> bool:
        """
        Validates the command from Mistral against the MMSS metrics.
        """
        logger.info(f"Validating command: {command}")

        r_t = current_metrics.get("R_T")
        d_f = current_metrics.get("D_f")

        if not (2.617 <= r_t <= 2.619):
            logger.warning(f"Command validation failed: R_T ({r_t}) is out of bounds [2.617, 2.619].")
            return False

        if not (8.9 <= d_f <= 9.1):
            logger.warning(f"Command validation failed: D_f ({d_f}) is out of bounds [8.9, 9.1].")
            return False

        try:
            self.microscope._validate_command(command)
        except ValueError as e:
            logger.warning(f"Command validation failed: {e}")
            return False

        logger.info("Command validation successful.")
        return True

    def _calculate_semantic_value(self, mmss_atoms: Dict[str, Any]) -> float:
        """
        Calculates the semantic value (V) from the MMSS atoms.
        """
        return mmss_atoms.get("V", 0.0)

    def _generate_final_output(self, formula: str, final_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the final output in the specified JSON format.
        """
        with open("MMSS-Blockly.json", "r") as f:
            blockly_data = json.load(f)

        return {
            "final_meta_formula": formula,
            "object_description": "A description of the derived formula and structure.",
            "light_spectrums_used": ["BLUE_450nm"],
            "final_mmss_module": {
                "system_name": blockly_data["system_name"],
                "version": blockly_data["version"],
                "description": blockly_data["description"],
                "workflow_blocks": blockly_data["workflow_blocks"],
                "control_flow": blockly_data["control_flow"],
                "current_metrics": final_metrics
            }
        }
