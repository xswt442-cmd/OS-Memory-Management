"""指令流生成器 — 按题目要求的分布比例生成 320 条指令地址序列。"""

import random


def generate_instructions(seed: int | None = None) -> list[int]:
    """生成 320 条指令地址序列。

    分布: 50% 顺序执行, 25% 向前跳转, 25% 向后跳转。
    """
    if seed is not None:
        random.seed(seed)

    seq: list[int] = []

    m = random.randint(0, 318)  # 确保 m+1 ≤ 319
    seq.append(m)
    pos = m

    if len(seq) < 320:
        seq.append(pos + 1)
        pos += 1

    while len(seq) < 320:
        # 向前跳转: [0, pos-1]
        if pos > 0:
            forward = random.randint(0, pos - 1)
            seq.append(forward)
            if len(seq) >= 320:
                break
            seq.append(forward + 1)
            pos = forward + 1

        if len(seq) >= 320:
            break

        # 向后跳转: [pos+1, 318] (确保 backward+1 ≤ 319)
        if pos + 1 <= 318:
            backward = random.randint(pos + 1, 318)
            seq.append(backward)
            if len(seq) >= 320:
                break
            seq.append(backward + 1)
            pos = backward + 1

    return seq[:320]


def classify_sequence(seq: list[int]) -> dict[str, float]:
    """统计指令序列的分布比例 (验证用)。"""
    total = len(seq)
    sequential = 0
    forward_jump = 0
    backward_jump = 0

    for i in range(1, total):
        if seq[i] == seq[i - 1] + 1:
            sequential += 1
        elif seq[i] < seq[i - 1]:
            forward_jump += 1
        else:
            backward_jump += 1

    return {
        "sequential": sequential / total * 100,
        "forward": forward_jump / total * 100,
        "backward": backward_jump / total * 100,
    }
