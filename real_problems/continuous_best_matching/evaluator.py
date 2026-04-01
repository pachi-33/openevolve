"""
Evaluator for Continuous Best Matching Problem

Evaluates programs on three dimensions:
1. Correctness (60%): Pass rate on test cases
2. Time Efficiency (25%): Bytecode instruction count
3. Space Efficiency (15%): Peak memory usage

Uses cascade evaluation:
- Stage 1: Quick validation (5 simple cases, threshold 70%)
- Stage 2: Medium validation (15 medium cases, threshold 85%)
- Stage 3: Full evaluation (all cases)
"""

import importlib.util
import json
import os
import sys
import tracemalloc
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

from openevolve.evaluation_result import EvaluationResult


class InstructionCounter:
    """Counts Python bytecode instructions using sys.settrace"""

    def __init__(self):
        self.count = 0
        self._original_trace = None

    def trace_fn(self, frame, event, arg):
        if event == 'line' or event == 'call' or event == 'return':
            self.count += 1
        return self.trace_fn

    def start(self):
        self.count = 0
        self._original_trace = sys.gettrace()
        sys.settrace(self.trace_fn)

    def stop(self):
        sys.settrace(self._original_trace)
        return self.count


class ContinuousBestMatchingEvaluator:
    """
    Multi-dimensional evaluator for continuous best matching problem.

    Evaluates solve(n, m, weights, check_timeout) -> (matches, max_segment_weight)
    """

    def __init__(
        self,
        testcases_path: Optional[str] = None,
        baseline_path: Optional[str] = None,
        cascade_thresholds: List[float] = None,
    ):
        """
        Initialize evaluator.

        Args:
            testcases_path: Path to testcases.json, defaults to testcase_generator/testcases.json
            baseline_path: Path to baseline_metrics.json, defaults to ./baseline_metrics.json
            cascade_thresholds: Thresholds for stage transitions [stage1, stage2]
        """
        if testcases_path is None:
            testcases_path = os.path.join(
                os.path.dirname(__file__), "testcase_generator", "testcases.json"
            )
        self.testcases_path = testcases_path
        self.testcases = self._load_testcases(testcases_path)

        if baseline_path is None:
            baseline_path = os.path.join(os.path.dirname(__file__), "baseline_metrics.json")
        self.baseline_path = baseline_path
        self.baseline_metrics = self._load_or_compute_baseline()

        # Cascade thresholds: Stage 1 -> 2 -> 3
        self.cascade_thresholds = cascade_thresholds or [0.70, 0.85]

    def _load_testcases(self, path: str) -> List[Dict]:
        """Load test cases from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get('testcases', [])

    def _load_or_compute_baseline(self) -> Dict[str, Any]:
        """Load baseline metrics or compute from initial program."""
        if os.path.exists(self.baseline_path):
            with open(self.baseline_path, 'r') as f:
                return json.load(f)

        # Compute baseline using initial_program.py
        initial_program_path = os.path.join(os.path.dirname(__file__), "initial_program.py")
        if os.path.exists(initial_program_path):
            print(f"Computing baseline metrics from {initial_program_path}...")
            baseline = self._compute_baseline_metrics(initial_program_path)
            # Save for future use
            with open(self.baseline_path, 'w') as f:
                json.dump(baseline, f, indent=2)
            return baseline

        # Default baseline if no initial program
        return {
            "avg_instructions": 1000000,
            "avg_memory_bytes": 10 * 1024 * 1024,  # 10 MB
            "pass_rate": 1.0,
        }

    def _compute_baseline_metrics(self, program_path: str) -> Dict[str, Any]:
        """Compute baseline metrics by running initial program."""
        program = self._load_program(program_path)

        total_instructions = 0
        total_memory = 0
        passed = 0
        count = 0

        # Sample test cases for baseline (use all for accuracy)
        for testcase in self.testcases:
            result = self._run_single_test(program, testcase, measure_perf=True)
            if result['passed']:
                passed += 1
                total_instructions += result['instructions']
                total_memory += result['memory_bytes']
                count += 1

        if count == 0:
            return {
                "avg_instructions": 1000000,
                "avg_memory_bytes": 10 * 1024 * 1024,
                "pass_rate": 0.0,
            }

        return {
            "avg_instructions": total_instructions / count,
            "avg_memory_bytes": total_memory / count,
            "pass_rate": passed / len(self.testcases),
        }

    def _load_program(self, program_path: str) -> Any:
        """Load a Python program from file path."""
        spec = importlib.util.spec_from_file_location("program", program_path)
        program = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(program)
        return program

    def _validate_matches(
        self, n: int, m: int, weights: List[List[int]], matches: List[List[int]],
        expected_max_weight: int
    ) -> Tuple[bool, str]:
        """
        Validate the solution matches.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(matches, list):
            return False, f"matches should be a list, got {type(matches)}"

        if len(matches) != m:
            return False, f"Expected {m} matches, got {len(matches)}"

        # Check each V vertex is matched exactly once
        used_v = set()
        used_u = set()

        for match in matches:
            if not isinstance(match, (list, tuple)) or len(match) != 2:
                return False, f"Invalid match format: {match}"

            u, v = match

            if v in used_v:
                return False, f"V vertex {v} matched multiple times"
            if u in used_u:
                return False, f"U vertex {u} matched multiple times"

            if not (0 <= u < n):
                return False, f"U vertex {u} out of range [0, {n})"
            if not (0 <= v < m):
                return False, f"V vertex {v} out of range [0, {m})"

            used_v.add(v)
            used_u.add(u)

        if len(used_v) != m:
            return False, f"Expected {m} unique V vertices, got {len(used_v)}"

        # Validate max_segment_weight matches the computed value
        computed_weight = sum(weights[u][v] for u, v in matches)
        if computed_weight != expected_max_weight:
            return False, f"max_segment_weight mismatch: computed={computed_weight}, returned={expected_max_weight}"

        return True, ""

    def _run_single_test(
        self, program: Any, testcase: Dict, measure_perf: bool = False, timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Run a single test case.

        Args:
            program: Loaded program module
            testcase: Test case dict with input and expected_output
            measure_perf: Whether to measure instruction count and memory
            timeout: Timeout in seconds

        Returns:
            Dict with passed, instructions, memory_bytes, error
        """
        result = {
            'passed': False,
            'instructions': 0,
            'memory_bytes': 0,
            'error': None,
        }

        try:
            # Check for solve function
            if not hasattr(program, 'solve'):
                result['error'] = "Missing solve function"
                return result

            solve_fn = program.solve
            input_data = testcase['input']
            n, m = input_data['n'], input_data['m']
            weights = input_data['weights']

            # Setup timeout check using a simple counter approach
            max_iterations = 1000000  # Fallback safety limit
            iteration_count = [0]

            def check_timeout():
                iteration_count[0] += 1
                return iteration_count[0] > max_iterations

            if measure_perf:
                # Measure memory
                tracemalloc.start()

                # Measure instructions
                counter = InstructionCounter()

                try:
                    counter.start()
                    matches, max_weight = solve_fn(n, m, weights, check_timeout)
                    instruction_count = counter.stop()

                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    result['instructions'] = instruction_count
                    result['memory_bytes'] = peak

                except Exception as e:
                    counter.stop()
                    tracemalloc.stop()
                    result['error'] = str(e)
                    return result

            else:
                # Run without performance measurement
                try:
                    matches, max_weight = solve_fn(n, m, weights, check_timeout)
                except Exception as e:
                    result['error'] = str(e)
                    return result

            # Validate result
            is_valid, error_msg = self._validate_matches(
                n, m, weights, matches, max_weight
            )

            if is_valid:
                result['passed'] = True
            else:
                result['error'] = error_msg

        except Exception as e:
            result['error'] = f"{type(e).__name__}: {str(e)}"

        return result

    def _calculate_instruction_score(self, avg_instructions: float) -> float:
        """Calculate instruction efficiency score (0.0 to 1.0+)."""
        baseline = self.baseline_metrics['avg_instructions']

        if avg_instructions <= baseline:
            # Better than baseline: bonus up to 1.5
            return 1.0 + (1.0 - avg_instructions / baseline) * 0.5
        else:
            # Worse than baseline: 0.0 to 1.0
            return baseline / avg_instructions

    def _calculate_memory_score(self, avg_memory: float) -> float:
        """Calculate memory efficiency score (0.0 to 1.0+)."""
        baseline = self.baseline_metrics['avg_memory_bytes']

        if avg_memory <= baseline:
            # Better than baseline: bonus up to 1.5
            return 1.0 + (1.0 - avg_memory / baseline) * 0.5
        else:
            # Worse than baseline: 0.0 to 1.0
            return baseline / avg_memory

    def _calculate_combined_score(
        self, correctness: float, instruction_score: float, memory_score: float
    ) -> float:
        """Calculate combined weighted score."""
        if correctness < 1.0:
            # Some tests failed: reduce other dimensions' weight
            instruction_weight = 0.15
            memory_weight = 0.10
            correctness_weight = 0.75
        else:
            instruction_weight = 0.25
            memory_weight = 0.15
            correctness_weight = 0.60

        return (
            correctness * correctness_weight +
            instruction_score * instruction_weight +
            memory_score * memory_weight
        )

    def evaluate(self, program_path: str) -> EvaluationResult:
        """
        Main evaluation function with cascade stages.

        Args:
            program_path: Path to the program file to evaluate

        Returns:
            EvaluationResult with metrics and artifacts
        """
        try:
            # Load program
            program = self._load_program(program_path)
        except Exception as e:
            traceback.print_exc()
            return EvaluationResult(
                metrics={
                    "combined_score": 0.0,
                    "correctness_score": 0.0,
                    "instruction_score": 0.0,
                    "memory_score": 0.0,
                    "passed_cases": 0,
                    "total_cases": 0,
                },
                artifacts={
                    "error_type": "LoadError",
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                }
            )

        # Check for required function
        if not hasattr(program, 'solve'):
            return EvaluationResult(
                metrics={
                    "combined_score": 0.0,
                    "correctness_score": 0.0,
                    "instruction_score": 0.0,
                    "memory_score": 0.0,
                    "passed_cases": 0,
                    "total_cases": 0,
                },
                artifacts={
                    "error_type": "MissingFunction",
                    "error_message": "Program must define a 'solve' function",
                }
            )

        # Sort test cases by difficulty (n * m as proxy)
        sorted_testcases = sorted(
            self.testcases,
            key=lambda t: t['input']['n'] * t['input']['m']
        )

        # Stage 1: Quick validation (5 simplest cases, threshold 70%)
        stage1_cases = sorted_testcases[:5]
        stage1_passed = 0
        failed_cases = []

        for testcase in stage1_cases:
            result = self._run_single_test(program, testcase, measure_perf=False)
            if result['passed']:
                stage1_passed += 1
            else:
                failed_cases.append(f"{testcase['id']}: {result['error']}")

        stage1_pass_rate = stage1_passed / len(stage1_cases) if stage1_cases else 0

        if stage1_pass_rate < self.cascade_thresholds[0]:
            # Failed stage 1
            return EvaluationResult(
                metrics={
                    "combined_score": stage1_pass_rate * 0.3,  # Low score for failing early
                    "correctness_score": stage1_pass_rate,
                    "instruction_score": 0.0,
                    "memory_score": 0.0,
                    "passed_cases": stage1_passed,
                    "total_cases": len(stage1_cases),
                },
                artifacts={
                    "stage": "stage1_failed",
                    "failed_cases": failed_cases[:10],
                    "avg_instructions": 0,
                    "avg_memory_mb": 0.0,
                }
            )

        # Stage 2: Medium validation (next 10 cases, threshold 85%)
        stage2_cases = sorted_testcases[5:15]
        stage2_passed = 0

        for testcase in stage2_cases:
            result = self._run_single_test(program, testcase, measure_perf=False)
            if result['passed']:
                stage2_passed += 1
            else:
                failed_cases.append(f"{testcase['id']}: {result['error']}")

        stage2_pass_rate = stage2_passed / len(stage2_cases) if stage2_cases else 1.0

        if stage2_pass_rate < self.cascade_thresholds[1]:
            # Failed stage 2
            total_passed = stage1_passed + stage2_passed
            total_cases = len(stage1_cases) + len(stage2_cases)
            correctness = total_passed / total_cases

            return EvaluationResult(
                metrics={
                    "combined_score": correctness * 0.5,  # Medium score
                    "correctness_score": correctness,
                    "instruction_score": 0.0,
                    "memory_score": 0.0,
                    "passed_cases": total_passed,
                    "total_cases": total_cases,
                },
                artifacts={
                    "stage": "stage2_failed",
                    "failed_cases": failed_cases[:10],
                    "avg_instructions": 0,
                    "avg_memory_mb": 0.0,
                }
            )

        # Stage 3: Full evaluation with performance measurement
        remaining_cases = sorted_testcases[15:]
        stage3_passed = 0
        total_instructions = 0
        total_memory = 0
        perf_measured_count = 0

        # Also measure performance on stage 1 and 2 passed cases
        all_cases = stage1_cases + stage2_cases + remaining_cases
        for testcase in all_cases:
            result = self._run_single_test(program, testcase, measure_perf=True)
            if result['passed']:
                stage3_passed += 1

                if result['instructions'] > 0:
                    total_instructions += result['instructions']
                    total_memory += result['memory_bytes']
                    perf_measured_count += 1
            else:
                testcase_id = testcase['id']
                if testcase_id not in [f.split(':')[0] for f in failed_cases]:
                    failed_cases.append(f"{testcase_id}: {result['error']}")

        total_passed = stage3_passed
        total_cases = len(self.testcases)
        correctness = total_passed / total_cases

        # Calculate performance scores
        if perf_measured_count > 0:
            avg_instructions = total_instructions / perf_measured_count
            avg_memory = total_memory / perf_measured_count
            instruction_score = self._calculate_instruction_score(avg_instructions)
            memory_score = self._calculate_memory_score(avg_memory)
        else:
            avg_instructions = float('inf')
            avg_memory = float('inf')
            instruction_score = 0.0
            memory_score = 0.0

        # Calculate combined score
        combined_score = self._calculate_combined_score(
            correctness, instruction_score, memory_score
        )

        return EvaluationResult(
            metrics={
                "combined_score": combined_score,
                "correctness_score": correctness,
                "instruction_score": instruction_score,
                "memory_score": memory_score,
                "passed_cases": total_passed,
                "total_cases": total_cases,
            },
            artifacts={
                "stage": "full_evaluation",
                "avg_instructions": int(avg_instructions) if avg_instructions != float('inf') else 0,
                "avg_memory_mb": avg_memory / (1024 * 1024) if avg_memory != float('inf') else 0.0,
                "failed_cases": failed_cases[:20],
                "baseline_comparison": {
                    "instruction_ratio": avg_instructions / self.baseline_metrics['avg_instructions']
                    if avg_instructions != float('inf') else float('inf'),
                    "memory_ratio": avg_memory / self.baseline_metrics['avg_memory_bytes']
                    if avg_memory != float('inf') else float('inf'),
                }
            }
        )


def evaluate(program_path: str) -> EvaluationResult:
    """
    Standalone evaluate function for OpenEvolve compatibility.

    Args:
        program_path: Path to the program file

    Returns:
        EvaluationResult
    """
    evaluator = ContinuousBestMatchingEvaluator()
    return evaluator.evaluate(program_path)