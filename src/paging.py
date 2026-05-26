"""请求调页存储管理模拟 — FIFO & LRU 页面置换算法。

- 每页 10 条指令, 共 32 页 (320 条指令)
- 4 个物理内存块
- 初始所有页均不在内存
- 输出每次缺页时的调入/置换情况
- 最终给出缺页率
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

from src.instruction_gen import generate_instructions

# 常量
PAGE_SIZE = 10        # 每页指令数
TOTAL_INSTRUCTIONS = 320
TOTAL_PAGES = 32
BLOCK_COUNT = 4


# 页表条目
@dataclass
class PageEntry:
    page_no: int
    valid: bool = False           # 是否在内存中
    block_no: int = -1            # 占用的物理块号, -1 表示不在内存
    load_time: int = -1           # 调入时刻 (FIFO 用)
    last_access: int = -1         # 最近访问时刻 (LRU 用)


# 页面置换算法接口
class ReplacementAlgo(Protocol):
    name: str

    def access(self, page_no: int, page_table: list[PageEntry], clock: int) -> bool:
        """访问一页, 返回是否缺页。"""
        ...

    def _replace(self, page_table: list[PageEntry], clock: int) -> int:
        """选出要换出的 block_no。"""
        ...


# FIFO
class FIFO:
    name = "FIFO (先进先出)"

    def __init__(self):
        self.queue: deque[int] = deque()  # block_no 的入队顺序

    def access(self, page_no: int, page_table: list[PageEntry], clock: int) -> bool:
        entry = page_table[page_no]
        if entry.valid:
            return False  # 已在内存, 无缺页

        # 缺页
        if len(self.queue) < BLOCK_COUNT:
            # 有空闲块
            block = len(self.queue)
            self.queue.append(block)
            entry.valid = True
            entry.block_no = block
            entry.load_time = clock
        else:
            # 置换
            victim_block = self.queue.popleft()
            self.queue.append(victim_block)
            # 找到占用该块的旧页
            for pe in page_table:
                if pe.block_no == victim_block:
                    pe.valid = False
                    pe.block_no = -1
                    pe.load_time = -1
                    break
            entry.valid = True
            entry.block_no = victim_block
            entry.load_time = clock

        return True


# ---------------------------------------------------------------------------
# LRU
# ---------------------------------------------------------------------------

class LRU:
    name = "LRU (最近最少使用)"

    def access(self, page_no: int, page_table: list[PageEntry], clock: int) -> bool:
        entry = page_table[page_no]

        if entry.valid:
            entry.last_access = clock
            return False

        # 缺页
        in_memory = [pe for pe in page_table if pe.valid]
        if len(in_memory) < BLOCK_COUNT:
            block = len(in_memory)
            entry.valid = True
            entry.block_no = block
            entry.last_access = clock
        else:
            # 找最近最少使用的页
            victim = min(in_memory, key=lambda pe: pe.last_access)
            victim_block = victim.block_no
            victim.valid = False
            victim.block_no = -1
            victim.last_access = -1
            entry.valid = True
            entry.block_no = victim_block
            entry.last_access = clock

        return True


# ---------------------------------------------------------------------------
# 格式化
# ---------------------------------------------------------------------------

def _pad_memory(page_table: list[PageEntry]) -> str:
    """格式化显示 4 个物理块的占用情况。"""
    parts = []
    for b in range(BLOCK_COUNT):
        occupant = next((pe for pe in page_table if pe.valid and pe.block_no == b), None)
        if occupant:
            parts.append(f"块{b}: 页{occupant.page_no}")
        else:
            parts.append(f"块{b}: 空")
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# 模拟运行
# ---------------------------------------------------------------------------

def simulate(algo_cls: type[FIFO | LRU], seed: int | None = None) -> None:
    """用指定置换算法模拟执行 320 条指令, 输出过程并统计缺页率。"""
    algo = algo_cls()
    page_table = [PageEntry(page_no=i) for i in range(TOTAL_PAGES)]
    instructions = generate_instructions(seed)
    page_faults = 0

    print(f"\n{'=' * 60}")
    print(f"  页面置换算法: {algo.name}")
    print(f"  物理块数: {BLOCK_COUNT}  |  每页 {PAGE_SIZE} 条指令  |  共 {TOTAL_PAGES} 页")
    print(f"{'=' * 60}")
    print(f"  {'序号':>4}  {'指令':>5}  {'页号':>4}  {'页内偏移':>6}  {'物理地址':>8}  {'状态':>8}  {_pad_memory(page_table)}")
    print(f"  {'-' * 4}  {'-' * 5}  {'-' * 4}  {'-' * 6}  {'-' * 8}  {'-' * 8}  {'-' * 35}")

    for tick, addr in enumerate(instructions):
        page_no = addr // PAGE_SIZE
        offset = addr % PAGE_SIZE
        entry = page_table[page_no]
        is_fault = algo.access(page_no, page_table, tick)

        if is_fault:
            page_faults += 1
            status = f"缺页→块{entry.block_no}"
        else:
            status = "命中"

        phys_addr = entry.block_no * PAGE_SIZE + offset if entry.valid else "—"

        print(
            f"  {tick + 1:>4}  "
            f"{addr:>5}  "
            f"{page_no:>4}  "
            f"{offset:>6}  "
            f"{str(phys_addr):>8}  "
            f"{status:>8}  "
            f"{_pad_memory(page_table)}"
        )

    rate = page_faults / TOTAL_INSTRUCTIONS * 100
    print(f"\n  ▶ 缺页次数: {page_faults} / {TOTAL_INSTRUCTIONS}")
    print(f"  ▶ 缺页率:   {rate:.2f}%")
    print()


def run():
    """依次运行 FIFO 和 LRU 并对比。"""
    seed = 42  # 固定种子便于对比
    simulate(FIFO, seed)
    simulate(LRU, seed)
