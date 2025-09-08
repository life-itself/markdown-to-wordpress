#!/usr/bin/env python3
"""
ETL Pipeline Runner
Orchestrates all migration steps in sequence.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import subprocess


class PipelineRunner:
    """Orchestrates the ETL pipeline steps."""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.steps = [
            {
                'name': '0-image-processing',
                'description': 'Analyze images and create rename dictionary',
                'required': True
            },
            {
                'name': '1-prepare-content',
                'description': 'Clean up front-matter and markdown',
                'required': False  # Not implemented yet
            },
            {
                'name': '2-decide-mappings', 
                'description': 'Map content to WordPress types',
                'required': False  # Not implemented yet
            },
            {
                'name': '3-upload-media',
                'description': 'Upload images to WordPress',
                'required': False  # Not implemented yet
            },
            {
                'name': '4-rewrite-links',
                'description': 'Update image and internal links',
                'required': False  # Not implemented yet
            },
            {
                'name': '5-create-content',
                'description': 'Create posts/pages in WordPress',
                'required': False  # Not implemented yet
            },
            {
                'name': '6-verify',
                'description': 'Verify migration results',
                'required': False  # Not implemented yet
            }
        ]
    
    def run_step(self, step_name: str, input_source: str = None) -> bool:
        """Run a single pipeline step."""
        step_dir = self.base_dir / step_name
        
        if not step_dir.exists():
            print(f"ERROR: Step directory not found: {step_dir}")
            return False
        
        main_script = step_dir / "main.py"
        if not main_script.exists():
            print(f"ERROR: main.py not found in {step_dir}")
            return False
        
        print(f"\n{'='*60}")
        print(f"RUNNING STEP: {step_name}")
        step_info = next((s for s in self.steps if s['name'] == step_name), {})
        print(f"DESCRIPTION: {step_info.get('description', 'No description')}")
        print(f"{'='*60}")
        
        # Prepare arguments
        cmd = [sys.executable, "main.py"]
        
        if step_name == "0-image-processing":
            input_dir = input_source if input_source else "input"
            cmd.extend(["--input-dir", input_dir, "--output-dir", "output"])
        
        # Run the step
        try:
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=step_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print("STDOUT:")
                print(result.stdout)
                print(f"\nSUCCESS: Step completed in {duration:.1f}s")
                return True
            else:
                print("STDOUT:")
                print(result.stdout)
                print("STDERR:")
                print(result.stderr)
                print(f"\nFAILED: Step failed after {duration:.1f}s (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to run step: {e}")
            return False
    
    def run_pipeline(self, input_source: str = None, steps_to_run: list = None):
        """Run the complete pipeline."""
        print("MARKDOWN TO WORDPRESS ETL PIPELINE")
        print("=" * 60)
        
        # Determine which steps to run
        if steps_to_run:
            steps = [s for s in self.steps if s['name'] in steps_to_run]
        else:
            steps = [s for s in self.steps if s['required']]
        
        if not steps:
            print("No steps to run!")
            return False
        
        print("PIPELINE PLAN:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step['name']}: {step['description']}")
        
        # Run each step
        success_count = 0
        total_steps = len(steps)
        
        for i, step in enumerate(steps, 1):
            print(f"\n[{i}/{total_steps}] Starting step: {step['name']}")
            
            if self.run_step(step['name'], input_source):
                success_count += 1
                
                # Copy output to next step's input (if needed)
                self._copy_outputs_to_next_step(step['name'], i, steps)
            else:
                print(f"Step {step['name']} failed. Stopping pipeline.")
                break
        
        # Summary
        print(f"\n{'='*60}")
        print("PIPELINE SUMMARY")
        print(f"{'='*60}")
        print(f"Steps completed: {success_count}/{total_steps}")
        
        if success_count == total_steps:
            print("STATUS: SUCCESS - All steps completed!")
        else:
            print("STATUS: FAILED - Pipeline stopped due to errors")
        
        return success_count == total_steps
    
    def _copy_outputs_to_next_step(self, current_step: str, current_index: int, steps: list):
        """Copy outputs from current step to next step's input."""
        # This is a placeholder for now
        # In a full implementation, we'd copy files between step directories
        pass
    
    def list_steps(self):
        """List all available steps."""
        print("AVAILABLE PIPELINE STEPS:")
        print("-" * 40)
        
        for i, step in enumerate(self.steps, 1):
            status = "READY" if step['required'] else "NOT IMPLEMENTED"
            print(f"{i:2d}. {step['name']:<20} {status:<15} {step['description']}")
    
    def test_step(self, step_name: str):
        """Run unit tests for a specific step."""
        step_dir = self.base_dir / step_name
        tests_dir = step_dir / "tests"
        
        if not tests_dir.exists():
            print(f"No tests found for step: {step_name}")
            return False
        
        print(f"Running tests for step: {step_name}")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd=step_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            print("TEST OUTPUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("TESTS PASSED!")
                return True
            else:
                print("TESTS FAILED!")
                return False
                
        except Exception as e:
            print(f"Error running tests: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run ETL Pipeline')
    parser.add_argument('--input', type=str, 
                       help='Input source directory')
    parser.add_argument('--steps', nargs='+',
                       help='Specific steps to run (e.g., 0-image-processing 1-prepare-content)')
    parser.add_argument('--list', action='store_true',
                       help='List all available steps')
    parser.add_argument('--test', type=str,
                       help='Run tests for specific step')
    
    args = parser.parse_args()
    
    runner = PipelineRunner()
    
    if args.list:
        runner.list_steps()
    elif args.test:
        runner.test_step(args.test)
    else:
        runner.run_pipeline(args.input, args.steps)


if __name__ == '__main__':
    main()