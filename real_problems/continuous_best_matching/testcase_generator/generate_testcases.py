"""
连续最佳匹配问题 - 测试用例生成编排控制器

模拟简单 OJ 平台的编排逻辑：
1. 调用 generator 生成批量测试场景（输入数据）
2. 对每个测试场景调用 solver 进行求解（带超时控制）
3. 整合输入和期望输出，生成完整测试用例
4. 输出到 testcases.json

架构：
    generator.py -> 生成批量测试场景
    solver.py    -> 单个问题求解（内置超时控制）
    generate_testcases.py -> 编排整合
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 添加当前目录到路径以导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from generator import generate_all_scenarios
from solver import solve_from_dict

# 超时时间（秒）
SOLVER_TIMEOUT = 5


def run_testcase(scenario: Dict[str, Any], index: int, total: int) -> Dict[str, Any]:
    """
    运行单个测试用例（类似 OJ 的单次评测）
    """
    testcase_id = scenario["id"]
    description = scenario["description"]
    input_data = scenario["input"]
    n = input_data["n"]
    m = input_data["m"]

    # 打印运行信息
    print(f"  [{index}/{total}] 正在求解: {testcase_id}")
    print(f"         描述: {description}")
    print(f"         规模: n={n}, m={m}")

    # 调用 solver（带超时控制）
    start_time = time.time()
    result = solve_from_dict(input_data, timeout=SOLVER_TIMEOUT)
    elapsed_time = time.time() - start_time

    # 检查是否超时
    if "error" in result and result["error"] == "timeout":
        print(f"         结果: ✗ 超时（超过{SOLVER_TIMEOUT}秒）")
        print(f"         耗时: {elapsed_time:.3f}s")

        return {
            "id": testcase_id,
            "description": description,
            "input": input_data,
            "expected_output": None,
            "generator_info": {
                "status": "failed",
                "fail_reason": "timeout",
                "elapsed_time": round(elapsed_time, 3)
            }
        }
    elif "error" in result:
        # 其他错误
        print(f"         结果: ✗ 错误")
        print(f"         消息: {result['error']}")
        print(f"         耗时: {elapsed_time:.3f}s")

        return {
            "id": testcase_id,
            "description": description,
            "input": input_data,
            "expected_output": None,
            "generator_info": {
                "status": "failed",
                "fail_reason": result["error"],
                "elapsed_time": round(elapsed_time, 3)
            }
        }
    else:
        # 成功
        print(f"         结果: ✓ 成功")
        print(f"         最大子图权值: {result['max_segment_weight']}")
        print(f"         匹配数: {len(result['matches'])}")
        print(f"         耗时: {elapsed_time:.3f}s")

        return {
            "id": testcase_id,
            "description": description,
            "input": input_data,
            "expected_output": result,
            "generator_info": {
                "status": "success",
                "elapsed_time": round(elapsed_time, 3)
            }
        }


def run_all_testcases(scenarios: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    运行所有测试用例（模拟 OJ 的批量评测）
    """
    testcases = []
    total = len(scenarios)

    stats = {
        "total": total,
        "success": 0,
        "timeout": 0,
        "error": 0
    }

    print(f"\n开始批量求解 {total} 个测试用例...")
    print(f"超时时间: {SOLVER_TIMEOUT}秒")
    print("-" * 60)

    for i, scenario in enumerate(scenarios, 1):
        testcase = run_testcase(scenario, i, total)
        testcases.append(testcase)

        # 更新统计
        status = testcase.get("generator_info", {}).get("status", "unknown")
        fail_reason = testcase.get("generator_info", {}).get("fail_reason", "")
        if status == "success":
            stats["success"] += 1
        elif fail_reason == "timeout":
            stats["timeout"] += 1
        else:
            stats["error"] += 1

        print()  # 空行分隔

    print("-" * 60)
    print(f"批量求解完成!")
    print(f"  成功: {stats['success']}/{total}")
    print(f"  超时: {stats['timeout']}/{total}")
    print(f"  错误: {stats['error']}/{total}")

    return testcases, stats


def save_testcases(testcases: List[Dict[str, Any]], output_file: str = "testcases.json"):
    """保存测试用例到 JSON 文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"testcases": testcases}, f, indent=2, ensure_ascii=False)


def print_statistics(testcases: List[Dict[str, Any]], stats: Dict[str, int]):
    """打印测试用例统计信息"""
    successful_testcases = [tc for tc in testcases if tc.get("generator_info", {}).get("status") == "success"]

    print(f"\n========== 测试用例统计 ==========")
    print(f"总测试用例数: {stats['total']}")
    print(f"  成功: {stats['success']}")
    print(f"  超时: {stats['timeout']}")
    print(f"  错误: {stats['error']}")

    if successful_testcases:
        n_values = [tc["input"]["n"] for tc in successful_testcases]
        m_values = [tc["input"]["m"] for tc in successful_testcases]
        weight_values = [tc["expected_output"]["max_segment_weight"] for tc in successful_testcases]

        print(f"\n成功用例统计:")
        print(f"  n 范围: [{min(n_values)}, {max(n_values)}]")
        print(f"  m 范围: [{min(m_values)}, {max(m_values)}]")
        print(f"  平均 n: {sum(n_values)/len(n_values):.1f}")
        print(f"  平均 m: {sum(m_values)/len(m_values):.1f}")
        print(f"  最大子图权值范围: [{min(weight_values)}, {max(weight_values)}]")


def main():
    """主函数 - OJ 风格的编排流程"""
    print("=" * 60)
    print("连续最佳匹配问题 - 测试用例生成器 (OJ 编排模式)")
    print("=" * 60)

    # 步骤 1: 生成测试场景
    print("\n[步骤 1] 生成测试场景...")
    scenarios = generate_all_scenarios(total_count=100)
    print(f"         已生成 {len(scenarios)} 个测试场景")

    # 步骤 2: 批量求解
    print("\n[步骤 2] 调用 Solver 批量求解...")
    testcases, stats = run_all_testcases(scenarios)

    # 步骤 3: 保存结果
    print("\n[步骤 3] 保存测试用例到文件...")
    output_file = "testcases.json"
    save_testcases(testcases, output_file)
    print(f"         已保存到: {output_file}")

    # 打印统计
    print_statistics(testcases, stats)

    print("\n" + "=" * 60)
    if stats["success"] == stats["total"]:
        print("测试用例生成完成! (全部成功)")
    else:
        print(f"测试用例生成完成! ({stats['success']}/{stats['total']} 成功)")
    print("=" * 60)


if __name__ == "__main__":
    main()
