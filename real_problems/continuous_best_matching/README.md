# Continuous Best Matching

一个真实工作中遇到的场景，抽象成一个带有连续性约束的带权二分图匹配问题。

## Problem Description

有一个二分图 -> (U, V, E)。其中，U是左侧顶点、V是右侧顶点，E是U到V的边集合。
|U| 大于 |V|，且 |E| == |U|*|V|
E中的每条边都有一个大于等于0的边权。
经典的KM算法可以求解：二分图匹配下的最大权值之和的最优匹配。
本场景不同之处在于，U是一个有偏序性的集合。且，|U| 大于 |V| 则必然有左侧顶点没有匹配的对向顶点，我们把没有匹配的点看作断点，
沿着U的顺序看，有断点把U切分成N个集合，即 二分图 (U, V, E) 被拆成了N个子图。现在我们定义 权值之和最大的子图为目标子图，
要求解一种匹配，使得目标子图的总权值最大。

现在有一个基础的程序，要求 演化出一个 时间、空间复杂度 综合最优，且能通过所有测试用例的算法:

real_problems/continuous_best_matching/initial_program.py

## Getting Started

To run this evolve-task:

```bash
cd real_problems/continuous_best_matching
python ../../openevolve-run.py initial_program.py evaluator.py --config config.yaml
```

## evaluator

### 运行测试用例

```python
pass
```

### 评估实际空间/内存占用 (Space Profiling)

```python
import tracemalloc

# 开始追踪内存分配
tracemalloc.start()

# 这里运行你的目标程序
# ...

current, peak = tracemalloc.get_traced_memory()
print(f"当前内存使用: {current / 1024 / 1024:.2f} MB")
print(f"峰值内存占用: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

### 评估实际运行时间 (Time Profiling)

```python
import time

start_time = time.perf_counter()

# 这里运行你的目标程序
# ...

end_time = time.perf_counter()
print(f"程序运行耗时: {end_time - start_time:.6f} 秒")
```
