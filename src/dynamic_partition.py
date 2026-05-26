"""动态分区分配模拟 — First Fit & Best Fit 算法。

初始可用内存: 640K。
每次分配/回收后显示空闲分区链的变化。
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class FreeBlock:
    start: int  # 起始地址 (K)
    size: int   # 大小 (K)


@dataclass
class AllocatedBlock:
    job_id: int
    start: int
    size: int


# ---------------------------------------------------------------------------
# 空闲分区合并与回收
# ---------------------------------------------------------------------------

def _merge(free_list: list[FreeBlock]) -> None:
    """合并相邻空闲分区并按地址排序。"""
    if not free_list:
        return
    free_list.sort(key=lambda b: b.start)
    i = 0
    while i < len(free_list) - 1:
        a = free_list[i]
        b = free_list[i + 1]
        if a.start + a.size == b.start:
            a.size += b.size
            free_list.pop(i + 1)
        else:
            i += 1


# ---------------------------------------------------------------------------
# First Fit — 返回分配起始地址, 失败返回 -1
# ---------------------------------------------------------------------------

def first_fit_alloc(free_list: list[FreeBlock], size: int) -> int:
    for blk in free_list:
        if blk.size >= size:
            addr = blk.start
            blk.start += size
            blk.size -= size
            if blk.size == 0:
                free_list.remove(blk)
            return addr
    return -1


# ---------------------------------------------------------------------------
# Best Fit
# ---------------------------------------------------------------------------

def best_fit_alloc(free_list: list[FreeBlock], size: int) -> int:
    best: FreeBlock | None = None
    for blk in free_list:
        if blk.size >= size and (best is None or blk.size < best.size):
            best = blk
    if best is None:
        return -1
    addr = best.start
    best.start += size
    best.size -= size
    if best.size == 0:
        free_list.remove(best)
    return addr


# ---------------------------------------------------------------------------
# 回收
# ---------------------------------------------------------------------------

def _do_free(free_list: list[FreeBlock], allocated: dict[int, AllocatedBlock], job_id: int) -> bool:
    if job_id not in allocated:
        return False
    blk = allocated.pop(job_id)
    free_list.append(FreeBlock(blk.start, blk.size))
    _merge(free_list)
    return True


# ---------------------------------------------------------------------------
# 格式化
# ---------------------------------------------------------------------------

def format_free_list(free_list: list[FreeBlock]) -> str:
    if not free_list:
        return "(全部已分配)"
    parts = [f"[{b.start}K–{b.start + b.size}K {b.size}K]" for b in sorted(free_list, key=lambda x: x.start)]
    return " → ".join(parts)


def format_allocated(allocated: dict[int, AllocatedBlock]) -> str:
    if not allocated:
        return "(无)"
    parts = []
    for b in sorted(allocated.values(), key=lambda b: b.start):
        parts.append(f"作业{b.job_id}: [{b.start}K–{b.start + b.size}K {b.size}K]")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# 预定义请求序列
# ---------------------------------------------------------------------------

REQUESTS: list[tuple[str, int, int]] = [
    # (操作, 大小/忽略, 作业号)  — 操作: 'A'=分配 'F'=回收
    ("A", 130, 1),
    ("A", 60,  2),
    ("A", 100, 3),
    ("F", 0,   2),
    ("A", 200, 4),
    ("F", 0,   3),
    ("F", 0,   1),
    ("A", 140, 5),
    ("A", 60,  6),
    ("A", 50,  7),
    ("F", 0,   6),
]


# ---------------------------------------------------------------------------
# 模拟运行
# ---------------------------------------------------------------------------

def simulate(algo_name: str, alloc_fn) -> None:
    free_list = [FreeBlock(0, 640)]
    allocated: dict[int, AllocatedBlock] = {}

    print(f"\n{'=' * 60}")
    print(f"  算法: {algo_name}  |  初始空闲: {format_free_list(free_list)}")
    print(f"{'=' * 60}")

    for op, arg, job_id in REQUESTS:
        if op == "A":
            addr = alloc_fn(free_list, arg)
            ok = addr >= 0
            if ok:
                allocated[job_id] = AllocatedBlock(job_id, addr, arg)
            action = f"作业{job_id} 申请 {arg}K"
            result = f"成功 @{addr}K" if ok else "失败(空间不足)"
        else:
            ok = _do_free(free_list, allocated, job_id)
            action = f"作业{job_id} 回收"
            result = "成功" if ok else "失败(未找到)"

        print(f"\n{action}: {result}")
        print(f"  空闲分区链: {format_free_list(free_list)}")
        print(f"  已分配:      {format_allocated(allocated)}")

    total_free = sum(b.size for b in free_list)
    frag = len(free_list)
    print(f"\n  总空闲: {total_free}K  |  碎片数: {frag}")


def run():
    simulate("首次适应 (First Fit)", first_fit_alloc)
    simulate("最佳适应 (Best Fit)", best_fit_alloc)
    print()
