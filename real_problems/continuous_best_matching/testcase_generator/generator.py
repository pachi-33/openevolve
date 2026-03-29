"""
连续最佳匹配问题 - 测试场景批量生成器

该模块负责生成各种测试场景的输入数据，不涉及问题求解。
可以生成多种类型的测试场景，包括边界情况、随机情况、特殊模式等。

使用方法:
    命令行: python generator.py --count 100 --output scenarios.json
    函数调用: generate_all_scenarios() -> List[Dict]
"""

import argparse
import json
import random
from typing import List, Dict, Any


def generate_random_weights(n: int, m: int, min_w: int = 0, max_w: int = 10**6) -> List[List[int]]:
    """生成随机边权矩阵"""
    return [[random.randint(min_w, max_w) for _ in range(m)] for _ in range(n)]


def generate_zero_weights(n: int, m: int) -> List[List[int]]:
    """生成全零边权矩阵"""
    return [[0 for _ in range(m)] for _ in range(n)]


def generate_max_weights(n: int, m: int, max_w: int = 10**6) -> List[List[int]]:
    """生成全最大值边权矩阵"""
    return [[max_w for _ in range(m)] for _ in range(n)]


def generate_ascending_weights(n: int, m: int, max_w: int = 10**6) -> List[List[int]]:
    """生成递增边权矩阵"""
    step = max_w // (n * m) if n * m > 0 else 1
    weights = []
    val = 0
    for _ in range(n):
        row = []
        for _ in range(m):
            row.append(min(val, max_w))
            val += step
        weights.append(row)
    return weights


def generate_descending_weights(n: int, m: int, max_w: int = 10**6) -> List[List[int]]:
    """生成递减边权矩阵"""
    step = max_w // (n * m) if n * m > 0 else 1
    weights = []
    val = max_w
    for _ in range(n):
        row = []
        for _ in range(m):
            row.append(max(val, 0))
            val -= step
        weights.append(row)
    return weights


def generate_diagonal_dominant_weights(n: int, m: int, max_w: int = 10**6) -> List[List[int]]:
    """生成对角线主导的边权矩阵（鼓励连续匹配）"""
    weights = []
    for i in range(n):
        row = []
        for j in range(m):
            if j == i % m:
                row.append(max_w)
            else:
                row.append(random.randint(0, max_w // 10))
        weights.append(row)
    return weights


def generate_sparse_high_weights(n: int, m: int, max_w: int = 10**6) -> List[List[int]]:
    """生成稀疏高权值边权矩阵（某些行权值特别高）"""
    weights = []
    high_rows = random.sample(range(n), min(m, n // 2))
    for i in range(n):
        row = []
        for j in range(m):
            if i in high_rows:
                row.append(random.randint(max_w // 2, max_w))
            else:
                row.append(random.randint(0, max_w // 10))
        weights.append(row)
    return weights


def generate_scenario(
    testcase_id: str,
    description: str,
    n: int,
    m: int,
    weights: List[List[int]]
) -> Dict[str, Any]:
    """生成单个测试场景（仅包含输入，不包含期望输出）"""
    return {
        "id": testcase_id,
        "description": description,
        "input": {
            "n": n,
            "m": m,
            "weights": weights
        }
    }


def generate_all_scenarios(total_count: int = 100) -> List[Dict[str, Any]]:
    """
    生成所有测试场景

    Args:
        total_count: 需要生成的测试用例总数

    Returns:
        测试场景列表（每个场景仅包含输入数据）
    """
    scenarios = []
    testcase_id = 0

    def next_id():
        nonlocal testcase_id
        testcase_id += 1
        return f"test_{testcase_id:03d}"

    # ============ 边界情况测试用例 ============

    # 1. 最小规模: n=2, m=2
    scenarios.append(generate_scenario(
        next_id(), "最小规模: n=2, m=2",
        2, 2, generate_random_weights(2, 2, 0, 100)
    ))

    # 2. 小规模: n=3, m=2
    scenarios.append(generate_scenario(
        next_id(), "小规模: n=3, m=2",
        3, 2, [[1, 2], [3, 4], [5, 6]]
    ))

    # 3. 最大规模: n=12, m=10
    scenarios.append(generate_scenario(
        next_id(), "最大规模: n=12, m=10",
        12, 10, generate_random_weights(12, 10, 0, 10**6)
    ))

    # 4. 全零边权
    scenarios.append(generate_scenario(
        next_id(), "全零边权",
        5, 3, generate_zero_weights(5, 3)
    ))

    # 5. 全最大边权
    scenarios.append(generate_scenario(
        next_id(), "全最大边权",
        5, 3, generate_max_weights(5, 3, 10**6)
    ))

    # 6. m=2 最小情况
    scenarios.append(generate_scenario(
        next_id(), "m=2 最小情况",
        8, 2, generate_random_weights(8, 2, 0, 1000)
    ))

    # 7. m接近n: n=5, m=4
    scenarios.append(generate_scenario(
        next_id(), "m接近n: n=5, m=4",
        5, 4, generate_random_weights(5, 4, 0, 10000)
    ))

    # 8. 递增边权
    scenarios.append(generate_scenario(
        next_id(), "递增边权",
        6, 3, generate_ascending_weights(6, 3, 1000)
    ))

    # 9. 递减边权
    scenarios.append(generate_scenario(
        next_id(), "递减边权",
        6, 3, generate_descending_weights(6, 3, 1000)
    ))

    # 10. 对角线主导（鼓励连续匹配）
    scenarios.append(generate_scenario(
        next_id(), "对角线主导（鼓励连续匹配）",
        7, 4, generate_diagonal_dominant_weights(7, 4, 10000)
    ))

    # 11. 稀疏高权值（某些行特别高）
    scenarios.append(generate_scenario(
        next_id(), "稀疏高权值（某些行特别高）",
        8, 3, generate_sparse_high_weights(8, 3, 100000)
    ))

    # ============ 随机测试用例 ============

    random_configs = [
        (4, 2, 100, "小规模随机"),
        (5, 3, 1000, "中等规模随机"),
        (6, 4, 10000, "中等规模随机"),
        (7, 3, 50000, "中等规模随机"),
        (8, 5, 100000, "较大规模随机"),
        (9, 4, 200000, "较大规模随机"),
        (10, 6, 500000, "大规模随机"),
        (11, 7, 800000, "大规模随机"),
        (12, 8, 10**6, "接近最大规模随机"),
    ]

    for n, m, max_w, desc in random_configs:
        if len(scenarios) >= total_count:
            break
        scenarios.append(generate_scenario(
            next_id(), f"{desc}: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, max_w)
        ))

    # ============ 特殊模式测试用例 ============

    # 前几行权值高
    if len(scenarios) < total_count:
        weights = [[10**6] * 3 for _ in range(3)] + [[1] * 3 for _ in range(3)]
        scenarios.append(generate_scenario(
            next_id(), "特定模式：前几行权值高",
            6, 3, weights
        ))

    # 后几行权值高
    if len(scenarios) < total_count:
        weights = [[1] * 3 for _ in range(3)] + [[10**6] * 3 for _ in range(3)]
        scenarios.append(generate_scenario(
            next_id(), "特定模式：后几行权值高",
            6, 3, weights
        ))

    # 中间行权值高
    if len(scenarios) < total_count:
        weights = [[1] * 3 for _ in range(2)] + [[10**6] * 3 for _ in range(2)] + [[1] * 3 for _ in range(2)]
        scenarios.append(generate_scenario(
            next_id(), "特定模式：中间行权值高",
            6, 3, weights
        ))

    # 交替高权值
    if len(scenarios) < total_count:
        weights = []
        for i in range(8):
            if i % 2 == 0:
                weights.append([10**6, 0, 0])
            else:
                weights.append([0, 0, 0])
        scenarios.append(generate_scenario(
            next_id(), "特定模式：交替高权值（偶数行高）",
            8, 3, weights
        ))

    # 小权值范围
    if len(scenarios) < total_count:
        scenarios.append(generate_scenario(
            next_id(), "小权值范围: 0-10",
            7, 4, generate_random_weights(7, 4, 0, 10)
        ))

    # 更多随机测试
    for i in range(5):
        if len(scenarios) >= total_count:
            break
        n = random.randint(5, 12)
        m = random.randint(2, min(n-1, 10))
        scenarios.append(generate_scenario(
            next_id(), f"随机规模测试 {i+1}: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, 10**6)
        ))

    # 极端情况：大量断点
    if len(scenarios) < total_count:
        scenarios.append(generate_scenario(
            next_id(), "极端情况：n=12, m=2（大量断点）",
            12, 2, generate_random_weights(12, 2, 0, 10**6)
        ))

    # 极端情况：极少断点
    if len(scenarios) < total_count:
        scenarios.append(generate_scenario(
            next_id(), "极端情况：n=12, m=10（极少断点）",
            12, 10, generate_random_weights(12, 10, 0, 10**6)
        ))

    # 补充随机测试
    for i in range(8):
        if len(scenarios) >= total_count:
            break
        n = random.randint(4, 12)
        m = random.randint(2, min(n-1, 10))
        max_w = random.choice([100, 1000, 10000, 100000, 10**6])
        scenarios.append(generate_scenario(
            next_id(), f"补充随机测试 {i+1}: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, max_w)
        ))

    # 多样模式测试
    patterns = [
        generate_random_weights,
        generate_ascending_weights,
        generate_descending_weights,
        generate_diagonal_dominant_weights,
        generate_sparse_high_weights,
    ]

    for i in range(20):
        if len(scenarios) >= total_count:
            break
        n = random.randint(3, 12)
        m = random.randint(2, min(n-1, 10))
        pattern = random.choice(patterns)
        if pattern == generate_random_weights:
            weights = pattern(n, m, 0, 10**6)
        elif pattern in [generate_ascending_weights, generate_descending_weights]:
            weights = pattern(n, m, 10**6)
        else:
            weights = pattern(n, m, 10**6)
        scenarios.append(generate_scenario(
            next_id(), f"多样模式测试 {i+1}: n={n}, m={m}",
            n, m, weights
        ))

    # 小规模密集测试
    for i in range(20):
        if len(scenarios) >= total_count:
            break
        n = random.randint(2, 6)
        m = random.randint(2, min(n, 4))
        scenarios.append(generate_scenario(
            next_id(), f"小规模密集测试 {i+1}: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, 10**6)
        ))

    # 中等规模测试
    for i in range(20):
        if len(scenarios) >= total_count:
            break
        n = random.randint(7, 12)
        m = random.randint(2, min(n-1, 10))
        scenarios.append(generate_scenario(
            next_id(), f"中等规模测试 {i+1}: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, 10**6)
        ))

    # 如果还不够，补充随机测试
    while len(scenarios) < total_count:
        n = random.randint(2, 12)
        m = random.randint(2, min(n-1, 10))
        scenarios.append(generate_scenario(
            next_id(), f"补充测试: n={n}, m={m}",
            n, m, generate_random_weights(n, m, 0, 10**6)
        ))

    return scenarios[:total_count]


def save_scenarios(scenarios: List[Dict[str, Any]], output_file: str):
    """保存测试场景到 JSON 文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"scenarios": scenarios}, f, indent=2, ensure_ascii=False)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='测试场景批量生成器')
    parser.add_argument('--count', '-c', type=int, default=100,
                        help='生成的测试用例数量 (默认: 100)')
    parser.add_argument('--output', '-o', type=str, default='scenarios.json',
                        help='输出文件路径 (默认: scenarios.json)')
    parser.add_argument('--seed', '-s', type=int, default=None,
                        help='随机种子 (可选)')

    args = parser.parse_args()

    # 设置随机种子
    if args.seed is not None:
        random.seed(args.seed)

    print(f"正在生成 {args.count} 个测试场景...")
    scenarios = generate_all_scenarios(args.count)

    save_scenarios(scenarios, args.output)
    print(f"已保存 {len(scenarios)} 个测试场景到: {args.output}")


if __name__ == "__main__":
    main()
