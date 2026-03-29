# 测试新求解方法工具

此工具用于验证你编写的连续最佳匹配问题求解器是否正确。

## 文件说明

- `test_runner.py` - 测试运行器核心代码
- `your_solver.py` - 你的求解器示例文件（在此实现你的算法）
- `__init__.py` - 包初始化

## 使用方法

### 方法一：命令行运行

```bash
cd real_problems/continuous_best_matching

# 使用默认测试用例（testcase_generator/testcases.json）
python test_new_func/test_runner.py --solver test_new_func/your_solver.py

# 指定自定义测试用例文件
python test_new_func/test_runner.py --solver test_new_func/your_solver.py --testcases testcase_generator/testcases.json

# 设置超时时间（每个用例5秒）
python test_new_func/test_runner.py --solver test_new_func/your_solver.py --timeout 5.0
```

### 方法二：Python 代码中调用

```python
from test_new_func.test_runner import run_tests
from test_new_func.your_solver import solve

# 运行所有测试
results = run_tests(solve)

# 或者带参数
results = run_tests(
    solve_func=solve,
    testcases_path="testcase_generator/testcases.json",
    timeout=5.0,
    verbose=True
)

# 获取统计信息
print(f"通过率: {results['pass_rate']*100:.1f}%")
print(f"通过: {results['passed']}/{results['total']}")
```

## 编写你的求解器

在 `your_solver.py` 中实现 `solve` 函数：

```python
from typing import List, Tuple, Optional, Callable

def solve(n: int, m: int, weights: List[List[int]],
          check_timeout: Optional[Callable[[], bool]] = None) -> Tuple[List[List[int]], int]:
    """
    实现你的算法

    参数:
        n: U 集合大小
        m: V 集合大小
        weights: n×m 边权矩阵
        check_timeout: 超时检查函数（可选）

    返回:
        (matches, max_segment_weight)
    """
    # 你的算法代码
    matches = [...]  # [[u1, v1], [u2, v2], ...]
    max_segment_weight = ...  # 整数

    return matches, max_segment_weight
```

### 超时处理

如果你的算法可能运行较长时间，请实现超时检查：

```python
def solve(n, m, weights, check_timeout=None):
    for ... in ...:  # 你的循环
        if check_timeout and check_timeout():
            return [], -1  # 返回 -1 表示超时
        # 继续计算
```

## 测试用例格式

测试用例文件为 JSON 格式：

```json
{
  "testcases": [
    {
      "id": "test_001",
      "description": "最小规模: n=2, m=2",
      "input": {
        "n": 2,
        "m": 2,
        "weights": [[22, 77], [32, 99]]
      },
      "expected_output": {
        "matches": [[0, 0], [1, 1]],
        "max_segment_weight": 121
      }
    }
  ]
}
```

## 验证逻辑

测试工具会：

1. 调用你的 `solve` 函数获取输出
2. 验证返回的 `max_segment_weight` 是否等于期望值
3. 验证你返回的 `matches` 计算出的权值与你报告的 `max_segment_weight` 是否一致

注意：不要求 `matches` 完全相同，因为可能存在多个最优解。

## 测试报告示例

```
======================================================================
测试报告
======================================================================

总体统计:
  总用例数: 100
  通过: 85 (85.0%)
  失败: 15 (15.0%)
  总用时: 12.345s
  平均用时: 123.45ms

失败用例详情:
----------------------------------------------------------------------

[test_042] 随机测试: n=10, m=8
  期望权值: 5234567
  实际权值: 5123456
  用时: 45.67ms
  错误: 期望权值 5234567，实际权值 5123456

======================================================================
```
