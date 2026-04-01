# Continuous Best Matching - Evaluator 设计方案

## 1. 概述

本设计文档描述针对连续最佳匹配问题的多维度评估器（Evaluator）实现方案。评估器将从三个维度综合评价进化出的算法：

1. **正确性维度**：用例通过率
2. **时间维度**：算法运行指令数
3. **空间维度**：算法内存消耗

## 2. 设计目标

- **正确性优先**：算法必须首先保证正确性，否则其他维度无意义
- **细粒度评估**：能够区分不同优化程度的算法
- **可复现性**：评估结果稳定，不受系统负载影响
- **OpenEvolve兼容**：符合 OpenEvolve 框架的 EvaluationResult 接口规范

## 3. 评估维度详解

### 3.1 用例通过率 (Correctness Score)

#### 3.1.1 测试用例来源
- 使用 `testcase_generator/testcases.json` 中的约 100 个测试用例
- 涵盖边界情况、随机情况、特殊模式等

#### 3.1.2 评估方法
```python
def evaluate_correctness(program_path, testcases):
    """
    评估算法正确性

    Returns:
        - passed_count: 通过测试用例数量
        - total_count: 总测试用例数量
        - pass_rate: 通过率 (0.0 ~ 1.0)
        - failed_cases: 失败用例ID列表（用于调试）
    """
```

#### 3.1.3 通过标准
对于每个测试用例，验证以下条件：
1. **返回值格式正确**：`solve()` 返回 `(matches, max_segment_weight)`
2. **匹配合法性**：
   - 每个 V 顶点最多匹配一个 U 顶点
   - 每个 U 顶点最多匹配一个 V 顶点
   - 匹配总数等于 m（V集合大小）
3. **max_segment_weight 正确**：根据 matches 计算出的最大段权值等于返回值

#### 3.1.4 得分计算
```python
correctness_score = passed_count / total_count
```

### 3.2 算法运行指令数 (Instruction Count Score)

#### 3.2.1 设计思路
由于 Python 的 `time` 测量受系统负载影响，采用**指令数**作为时间复杂度的代理指标。

#### 3.2.2 实现方案
使用 `dis` 模块统计：

**方案：使用 bytecode 分析（更精确）**
```python
import dis
import types

def count_bytecode_instructions(func, *args, **kwargs):
    """
    通过字节码级跟踪统计实际执行的指令数
    更精确但实现复杂度较高
    """
    # 使用 line_profiler 或 memory_profiler 类似思路
    pass
```

#### 3.2.3 归一化处理
由于不同规模的问题指令数基数不同，采用**相对优化比**进行归一化：

```python
# 基准：原始算法的平均指令数
baseline_instructions = get_baseline_instructions(testcases)

# 当前算法的平均指令数
current_instructions = get_current_instructions(program_path, testcases)

# 指令效率得分 (越高越好，范围 0.0 ~ 1.0+)
if current_instructions <= baseline_instructions:
    instruction_score = 1.0 + (1.0 - current_instructions / baseline_instructions) * 0.5
else:
    instruction_score = baseline_instructions / current_instructions
```

### 3.3 算法内存消耗 (Memory Usage Score)

#### 3.3.1 测量方法
使用 `tracemalloc` 模块精确测量峰值内存：

```python
import tracemalloc

def measure_memory(func, *args, **kwargs):
    """
    测量函数执行的峰值内存消耗

    Returns:
        peak_memory_bytes: 峰值内存（字节）
    """
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, peak
```

#### 3.3.2 归一化处理
类似指令数，采用相对优化比：

```python
# 基准：原始算法的平均内存消耗
baseline_memory = get_baseline_memory(testcases)

# 当前算法的平均内存消耗
current_memory = get_current_memory(program_path, testcases)

# 内存效率得分 (越高越好，范围 0.0 ~ 1.0+)
if current_memory <= baseline_memory:
    memory_score = 1.0 + (1.0 - current_memory / baseline_memory) * 0.5
else:
    memory_score = baseline_memory / current_memory
```

## 4. 综合得分计算

### 4.1 加权公式

```python
def calculate_combined_score(correctness, instruction_score, memory_score):
    """
    计算综合得分

    权重设计：
    - 正确性: 60%（必须优先保证）
    - 指令数: 25%（时间效率）
    - 内存: 15%（空间效率）

    正确性惩罚：如果正确性 < 1.0，其他维度得分大幅衰减
    """
    if correctness < 1.0:
        # 有测试用例失败，大幅降低其他维度权重
        instruction_weight = 0.15
        memory_weight = 0.10
        correctness_weight = 0.75
    else:
        instruction_weight = 0.25
        memory_weight = 0.15
        correctness_weight = 0.60

    combined_score = (
        correctness * correctness_weight +
        instruction_score * instruction_weight +
        memory_score * memory_weight
    )

    return combined_score
```

### 4.2 评分解释

| 得分范围 | 评价 |
|---------|------|
| 0.9 ~ 1.0+ | 优秀：完全正确且高效优化 |
| 0.7 ~ 0.9 | 良好：基本正确或中等优化 |
| 0.5 ~ 0.7 | 一般：部分正确或有明显优化空间 |
| 0.3 ~ 0.5 | 较差：较多错误或低效 |
| < 0.3 | 不合格：严重错误或无法运行 |

## 5. 实现架构

### 5.1 文件结构

```
real_problems/continuous_best_matching/
├── evaluator.py              # 主评估器
├── evaluator_design.md       # 本文档
├── baseline_metrics.json     # 基准算法指标缓存
└── testcase_generator/
    └── testcases.json        # 测试用例
```

### 5.2 类设计

```python
from openevolve.evaluation_result import EvaluationResult
import json
import importlib.util
import tracemalloc
import sys
from typing import List, Dict, Any, Tuple


class ContinuousBestMatchingEvaluator:
    """连续最佳匹配问题多维度评估器"""

    def __init__(self, testcases_path: str = None):
        """
        初始化评估器

        Args:
            testcases_path: 测试用例文件路径，默认使用 testcase_generator/testcases.json
        """
        if testcases_path is None:
            testcases_path = self._get_default_testcases_path()
        self.testcases = self._load_testcases(testcases_path)
        self.baseline_metrics = self._load_or_compute_baseline()

    def evaluate(self, program_path: str) -> EvaluationResult:
        """
        主评估函数

        Args:
            program_path: 待评估的程序文件路径

        Returns:
            EvaluationResult 包含 metrics 和 artifacts
        """
        # 1. 加载程序
        program = self._load_program(program_path)

        # 2. 评估正确性
        correctness_result = self._evaluate_correctness(program)

        # 3. 评估指令数（仅在正确性 > 0 时进行）
        if correctness_result['pass_rate'] > 0:
            instruction_result = self._evaluate_instructions(program)
        else:
            instruction_result = {'score': 0.0, 'avg_instructions': float('inf')}

        # 4. 评估内存（仅在正确性 > 0 时进行）
        if correctness_result['pass_rate'] > 0:
            memory_result = self._evaluate_memory(program)
        else:
            memory_result = {'score': 0.0, 'avg_memory_bytes': float('inf')}

        # 5. 计算综合得分
        combined_score = self._calculate_combined_score(
            correctness_result['pass_rate'],
            instruction_result['score'],
            memory_result['score']
        )

        # 6. 构建返回结果
        metrics = {
            'correctness_score': correctness_result['pass_rate'],
            'instruction_score': instruction_result['score'],
            'memory_score': memory_result['score'],
            'combined_score': combined_score,
            'passed_cases': correctness_result['passed_count'],
            'total_cases': correctness_result['total_count'],
        }

        artifacts = {
            'avg_instructions': instruction_result.get('avg_instructions', 0),
            'avg_memory_mb': memory_result.get('avg_memory_bytes', 0) / (1024 * 1024),
            'failed_cases': correctness_result.get('failed_cases', []),
            'baseline_comparison': {
                'instruction_ratio': instruction_result.get('avg_instructions', 0) / self.baseline_metrics['avg_instructions'],
                'memory_ratio': memory_result.get('avg_memory_bytes', 0) / self.baseline_metrics['avg_memory_bytes'],
            }
        }

        return EvaluationResult(metrics=metrics, artifacts=artifacts)

    def _evaluate_correctness(self, program) -> Dict[str, Any]:
        """评估算法正确性"""
        # 实现...
        pass

    def _evaluate_instructions(self, program) -> Dict[str, Any]:
        """评估指令数效率"""
        # 实现...
        pass

    def _evaluate_memory(self, program) -> Dict[str, Any]:
        """评估内存效率"""
        # 实现...
        pass
```
