"""
测试运行器 - 用于验证新求解方法的正确性

使用方法:
    from test_new_func.test_runner import run_tests
    from your_solver import solve
    run_tests(solve)

或者命令行:
    python test_runner.py --solver your_solver.py
"""

import json
import time
import sys
import importlib.util
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class TestResult:
    """单个测试用例的结果"""
    testcase_id: str
    description: str
    passed: bool
    expected_weight: int
    actual_weight: int
    elapsed_time: float
    error_message: Optional[str] = None
    actual_matches: Optional[List[List[int]]] = None


def calculate_max_segment_weight(
    n: int, m: int, weights: List[List[int]], matches: List[List[int]]
) -> int:
    """
    计算给定匹配下的最大子图权值
    从 solver.py 复用
    """
    matched_u = set(u for u, v in matches)
    match_dict = {u: v for u, v in matches}

    segments = []
    current_segment = []

    for u in range(n):
        if u in matched_u:
            current_segment.append(u)
        else:
            if current_segment:
                segments.append(current_segment)
                current_segment = []

    if current_segment:
        segments.append(current_segment)

    max_weight = 0
    for segment in segments:
        segment_weight = sum(weights[u][match_dict[u]] for u in segment)
        max_weight = max(max_weight, segment_weight)

    return max_weight


def load_testcases(testcases_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    加载测试用例文件

    Args:
        testcases_path: 测试用例文件路径，默认为上一级目录的 testcase_generator/testcases.json

    Returns:
        测试用例列表
    """
    if testcases_path is None:
        # 默认路径：从 test_new_func 目录向上找到 testcase_generator
        current_dir = Path(__file__).parent
        testcases_path = current_dir.parent / "testcase_generator" / "testcases.json"

    print(f"[DEBUG] 正在加载测试用例文件: {testcases_path}")

    with open(testcases_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data is None:
        print(f"[ERROR] JSON 文件解析返回 None，文件内容可能为空或格式错误")
        return []

    testcases = data.get("testcases", []) if isinstance(data, dict) else []
    print(f"[DEBUG] 成功加载 {len(testcases)} 个测试用例")

    # 检查有多少个测试用例缺少 expected_output
    missing_expected = [tc.get("id", "unknown") for tc in testcases if tc.get("expected_output") is None]
    if missing_expected:
        print(f"[WARN] 发现 {len(missing_expected)} 个测试用例缺少 expected_output: {missing_expected[:5]}{'...' if len(missing_expected) > 5 else ''}")

    return testcases


def run_single_test(
    testcase: Dict[str, Any],
    solve_func: Callable,
    timeout: Optional[float] = None
) -> TestResult:
    """
    运行单个测试用例

    Args:
        testcase: 测试用例字典
        solve_func: 求解函数，签名应为 solve(n, m, weights, check_timeout=None)
        timeout: 超时时间（秒），None 表示无超时

    Returns:
        TestResult 对象
    """
    testcase_id = testcase.get("id", "unknown")
    description = testcase.get("description", "")
    input_data = testcase.get("input") or {}
    expected_output = testcase.get("expected_output") or {}

    print(f"[DEBUG] 运行测试用例 {testcase_id}: input_data={input_data is not None}, expected_output={testcase.get('expected_output') is not None}")

    n = input_data.get("n", 0) if input_data else 0
    m = input_data.get("m", 0) if input_data else 0
    weights = input_data.get("weights", []) if input_data else []
    expected_weight = expected_output.get("max_segment_weight", 0) if expected_output else 0

    start_time = time.time()
    elapsed_time = 0.0

    try:
        # 创建超时检查函数
        check_timeout = None
        if timeout is not None:
            timeout_deadline = start_time + timeout
            def check_timeout_fn():
                return time.time() > timeout_deadline
            check_timeout = check_timeout_fn

        # 调用用户求解函数
        matches, max_segment_weight = solve_func(n, m, weights, check_timeout)

        elapsed_time = time.time() - start_time

        # 验证结果：检查返回的 max_segment_weight 是否等于期望值
        # 注意：不检查 matches 是否完全相同，因为可能存在多个最优解
        if max_segment_weight == -1 and timeout is not None:
            # 超时返回
            return TestResult(
                testcase_id=testcase_id,
                description=description,
                passed=False,
                expected_weight=expected_weight,
                actual_weight=max_segment_weight,
                elapsed_time=elapsed_time,
                error_message="求解超时",
                actual_matches=matches
            )

        # 额外验证：计算返回的 matches 的实际权值，确保与用户报告的 max_segment_weight 一致
        actual_calculated_weight = calculate_max_segment_weight(n, m, weights, matches)

        if actual_calculated_weight != max_segment_weight:
            return TestResult(
                testcase_id=testcase_id,
                description=description,
                passed=False,
                expected_weight=expected_weight,
                actual_weight=max_segment_weight,
                elapsed_time=elapsed_time,
                error_message=f"返回的 max_segment_weight ({max_segment_weight}) 与实际计算的 matches 权值 ({actual_calculated_weight}) 不一致",
                actual_matches=matches
            )

        passed = (max_segment_weight == expected_weight)

        return TestResult(
            testcase_id=testcase_id,
            description=description,
            passed=passed,
            expected_weight=expected_weight,
            actual_weight=max_segment_weight,
            elapsed_time=elapsed_time,
            error_message=None if passed else f"期望权值 {expected_weight}，实际权值 {max_segment_weight}",
            actual_matches=matches
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        return TestResult(
            testcase_id=testcase_id,
            description=description,
            passed=False,
            expected_weight=expected_weight,
            actual_weight=-1,
            elapsed_time=elapsed_time,
            error_message=f"执行异常: {type(e).__name__}: {str(e)}",
            actual_matches=None
        )


def run_tests(
    solve_func: Callable,
    testcases_path: Optional[str] = None,
    timeout: Optional[float] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    运行所有测试用例

    Args:
        solve_func: 求解函数，签名应为 solve(n, m, weights, check_timeout=None)
        testcases_path: 测试用例文件路径，默认自动查找
        timeout: 每个测试用例的超时时间（秒），None 表示无超时
        verbose: 是否打印详细报告

    Returns:
        测试结果统计字典
    """
    testcases = load_testcases(testcases_path)

    if not testcases:
        print("错误：未找到测试用例")
        return {"total": 0, "passed": 0, "failed": 0, "results": []}

    results: List[TestResult] = []

    for testcase in testcases:
        result = run_single_test(testcase, solve_func, timeout)
        results.append(result)

    # 统计
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    total_time = sum(r.elapsed_time for r in results)

    if verbose:
        print("\n" + "=" * 70)
        print("测试报告")
        print("=" * 70)
        print(f"\n总体统计:")
        print(f"  总用例数: {total}")
        print(f"  通过: {passed} ({passed/total*100:.1f}%)")
        print(f"  失败: {failed} ({failed/total*100:.1f}%)")
        print(f"  总用时: {total_time:.3f}s")
        print(f"  平均用时: {total_time/total*1000:.2f}ms")

        if failed > 0:
            print(f"\n失败用例详情:")
            print("-" * 70)
            for result in results:
                if not result.passed:
                    print(f"\n[{result.testcase_id}] {result.description}")
                    print(f"  期望权值: {result.expected_weight}")
                    print(f"  实际权值: {result.actual_weight}")
                    print(f"  用时: {result.elapsed_time*1000:.2f}ms")
                    if result.error_message:
                        print(f"  错误: {result.error_message}")

        print("\n" + "=" * 70)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "total_time": total_time,
        "avg_time": total_time / total if total > 0 else 0,
        "results": results
    }


def load_solver_from_file(file_path: str) -> Callable:
    """
    从文件动态加载求解函数

    Args:
        file_path: Python 文件路径

    Returns:
        solve 函数
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"求解器文件不存在: {file_path}")

    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if not hasattr(module, 'solve'):
        raise AttributeError(f"文件 {file_path} 中没有定义 solve 函数")

    return module.solve


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='测试新求解方法')
    parser.add_argument('--solver', '-s', type=str, required=True,
                        help='求解器 Python 文件路径（必须包含 solve 函数）')
    parser.add_argument('--testcases', '-t', type=str, default=None,
                        help='测试用例文件路径（默认为 testcase_generator/testcases.json）')
    parser.add_argument('--timeout', type=float, default=None,
                        help='每个测试用例的超时时间（秒）')

    args = parser.parse_args()

    try:
        solve_func = load_solver_from_file(args.solver)
        print(f"已加载求解器: {args.solver}")
        run_tests(solve_func, args.testcases, args.timeout)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
