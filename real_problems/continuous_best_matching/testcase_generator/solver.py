"""
连续最佳匹配问题 - 暴力求解器

问题描述：
- 二分图 (U, V, E)，n=|U|, m=|V|, n > m
- 每个 V 顶点最多匹配一个 U 顶点
- 未匹配的 U 顶点形成断点，将 U 分割成多个连续子集
- 目标：找到一种匹配，使得权值之和最大的子图的权值最大

使用方法：
    命令行: python solver.py --input input.json --output output.json
    函数调用: solve(n, m, weights) -> (matches, max_segment_weight)
"""

import argparse
import json
import time
import numpy as np
from itertools import combinations, permutations
from typing import List, Tuple, Optional, Dict, Any, Callable
from scipy.optimize import linear_sum_assignment

def solve(n: int, m: int, weights: List[List[int]],
          check_timeout: Optional[Callable[[], bool]] = None) -> Tuple[List[List[int]], int]:
    """
    基于 KM 算法（匈牙利算法）优化的连续最佳匹配求解器

    Args:
        n: U 集合的大小
        m: V 集合的大小
        weights: n×m 的边权矩阵
        check_timeout: 可选的超时检查函数，返回 True 表示需要终止

    Returns:
        (matches, max_segment_weight)
    """
    if m == 0 or n == 0:
        return [], 0

    best_max_segment_weight = -1
    best_matches = []

    # 转换为 numpy 数组以加速切片和矩阵运算
    weights_np = np.array(weights)

    # 1. 穷举所有可能的连续段长度 L (从 1 到 m)
    for L in range(1, m + 1):
        # 2. 穷举该连续段的所有可能起点 i
        for i in range(n - L + 1):
            if check_timeout and check_timeout():
                return [], -1

            # --- 阶段 A: 拓扑合法性校验 ---
            # 计算为了保证当前段独立，必须预留的“空断点”数量
            breakpoints = 0
            if i > 0:
                breakpoints += 1
            if i + L < n:
                breakpoints += 1

            # 计算剩余可用的 U 顶点数量 和 需要被匹配的剩余 V 顶点数量
            available_u = n - L - breakpoints
            remaining_v = m - L

            # 如果剩下的 U 空间不足以容纳剩下的 V（即必定会破坏当前段的独立性），则跳过
            if available_u < remaining_v:
                continue

            # --- 阶段 B: 构建并求解 KM 子问题 ---
            # 提取当前段对应的权重子矩阵 (L 行 m 列)
            sub_weights = weights_np[i : i + L, :]

            # scipy 的 linear_sum_assignment 默认求最小权值匹配
            # 我们要求最大权值，因此将权重矩阵取反
            cost_matrix = -sub_weights
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            # 计算出当前段在最优匹配下的权值之和
            current_weight = int(sub_weights[row_ind, col_ind].sum())

            # --- 阶段 C: 维护全局最优解并重构完整匹配 ---
            if current_weight > best_max_segment_weight:
                best_max_segment_weight = current_weight

                # 记录主段的精确匹配情况
                # row_ind 是相对索引，需要加上起点 i 还原为真实的 U 索引
                segment_matches = [[i + r, c] for r, c in zip(row_ind.tolist(), col_ind.tolist())]

                # 为了返回完整的合法匹配方案，我们需要将剩余的 V 随便“塞”进剩余合法的 U 中
                used_v = set(c for r, c in segment_matches)
                forbidden_u = set(range(i, i + L))
                if i > 0:
                    forbidden_u.add(i - 1)  # 封锁左断点
                if i + L < n:
                    forbidden_u.add(i + L)  # 封锁右断点

                remaining_vs = [v for v in range(m) if v not in used_v]
                available_us = [u for u in range(n) if u not in forbidden_u]

                # 缝合: 核心最佳段匹配 + 剩余顶点的随意合法匹配
                additional_matches = [[u, v] for u, v in zip(available_us[:len(remaining_vs)], remaining_vs)]
                best_matches = segment_matches + additional_matches

    return best_matches, int(best_max_segment_weight)


def solve_with_timeout(n: int, m: int, weights: List[List[int]],
                       timeout_seconds: float = 5.0) -> Tuple[List[List[int]], int, str]:
    """
    带超时控制的求解函数

    Args:
        n, m, weights: 问题输入
        timeout_seconds: 超时时间（秒）

    Returns:
        (matches, max_segment_weight, status)
        status: "success" 或 "timeout"
    """
    start_time = time.time()

    def check_timeout() -> bool:
        return time.time() - start_time > timeout_seconds

    if m == 0 or n == 0:
        return [], 0

    rslt = solve(n, m, weights, check_timeout)
    
    return *rslt, "success"

def solve_from_dict(input_data: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
    """
    从字典输入求解问题

    Args:
        input_data: 包含 n, m, weights 的字典
        timeout: 可选的超时时间（秒）

    Returns:
        包含 matches 和 max_segment_weight 的字典
        如果超时，返回 {"error": "timeout"}
    """
    n = input_data["n"]
    m = input_data["m"]
    weights = input_data["weights"]

    if timeout:
        matches, max_segment_weight, status = solve_with_timeout(n, m, weights, timeout)
        if status == "timeout":
            return {"error": "timeout"}
    else:
        matches, max_segment_weight = solve(n, m, weights)

    return {
        "matches": matches,
        "max_segment_weight": max_segment_weight
    }


def solve_from_file(input_file: str, output_file: Optional[str] = None,
                    timeout: Optional[float] = None) -> Dict[str, Any]:
    """
    从文件读取输入并求解

    Args:
        input_file: 输入文件路径 (JSON格式)
        output_file: 输出文件路径 (JSON格式)，为None则不写入文件
        timeout: 可选的超时时间（秒）

    Returns:
        求解结果字典
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    result = solve_from_dict(input_data, timeout)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='连续最佳匹配问题求解器')
    parser.add_argument('--input', '-i', type=str, help='输入文件路径 (JSON)')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径 (JSON)')
    parser.add_argument('--n', type=int, help='U集合大小')
    parser.add_argument('--m', type=int, help='V集合大小')
    parser.add_argument('--weights', type=str, help='边权矩阵 (JSON字符串)')
    parser.add_argument('--timeout', '-t', type=float, default=None, help='超时时间（秒）')

    args = parser.parse_args()

    if args.input:
        result = solve_from_file(args.input, args.output, args.timeout)
        if not args.output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.n is not None and args.m is not None and args.weights:
        weights = json.loads(args.weights)
        result = solve_from_dict({"n": args.n, "m": args.m, "weights": weights}, args.timeout)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
