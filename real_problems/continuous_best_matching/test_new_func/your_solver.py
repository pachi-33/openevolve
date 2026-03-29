"""
你的求解器示例文件

请在此文件中实现你的 solve 函数，然后使用 test_runner 测试

函数签名:
    def solve(n: int, m: int, weights: List[List[int]],
              check_timeout: Optional[Callable[[], bool]] = None) -> Tuple[List[List[int]], int]:

参数:
    n: U 集合的大小 (2 <= n <= 12)
    m: V 集合的大小 (2 <= m <= 10, m < n)
    weights: n×m 的边权矩阵，weights[i][j] 表示 U[i] 到 V[j] 的边权
    check_timeout: 可选的超时检查函数，返回 True 表示需要终止

返回:
    (matches, max_segment_weight)
    - matches: 匹配列表，每个元素是 [u, v] 表示 U[u] 匹配到 V[v]
    - max_segment_weight: 最优匹配下的最大子图权值

示例:
    n=3, m=2, weights=[[1,2], [3,4], [5,6]]
    可能返回: ([[1,0], [2,1]], 9)
    解释: U[1]匹配V[0], U[2]匹配V[1]，形成连续段[1,2]，权值=4+6=10
          但更优解可能是 [[0,0], [2,1]]，形成段[0]和[2]，最大权值=max(1,6)=6
          最优解是 [[1,0], [2,1]]，最大子图权值=9

测试方法:
    1. 在命令行运行:
       python test_runner.py --solver your_solver.py

    2. 或在 Python 中调用:
       from test_runner import run_tests
       from your_solver import solve
       run_tests(solve)
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
                segment_matches = [[i + r, c] for r, c in zip(row_ind, col_ind)]

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

    return best_matches, best_max_segment_weight

# 本地测试代码
if __name__ == "__main__":
    # 简单测试
    n, m = 3, 2
    weights = [[1, 2], [3, 4], [5, 6]]

    matches, max_weight = solve(n, m, weights)
    print(f"输入: n={n}, m={m}, weights={weights}")
    print(f"输出: matches={matches}, max_segment_weight={max_weight}")

    # 完整测试
    print("\n运行完整测试...")
    from test_runner import run_tests
    run_tests(solve, timeout=5.0)
