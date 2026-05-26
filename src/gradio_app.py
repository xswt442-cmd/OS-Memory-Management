"""Gradio Web UI — 动态分区分配 & 请求调页模拟。"""

from __future__ import annotations

import random

import gradio as gr

from src.dynamic_partition import (
    REQUESTS,
    FreeBlock,
    AllocatedBlock,
    first_fit_alloc,
    best_fit_alloc,
    _do_free,
    format_free_list,
)
from src.instruction_gen import generate_instructions
from src.paging import (
    PAGE_SIZE,
    TOTAL_INSTRUCTIONS,
    TOTAL_PAGES,
    PageEntry,
    FIFO,
    LRU,
)


# 动态分区，数据收集
def _run_dp(alloc_fn) -> list[dict]:
    free_list = [FreeBlock(0, 640)]
    allocated: dict[int, AllocatedBlock] = {}
    steps: list[dict] = []

    for op, arg, job_id in REQUESTS:
        if op == "A":
            addr = alloc_fn(free_list, arg)
            ok = addr >= 0
            if ok:
                allocated[job_id] = AllocatedBlock(job_id, addr, arg)
            step = {
                "操作": f"作业{job_id} 申请 {arg}K",
                "结果": f"成功 @{addr}K" if ok else "失败",
                "空闲分区链": format_free_list(free_list),
            }
        else:
            ok = _do_free(free_list, allocated, job_id)
            step = {
                "操作": f"作业{job_id} 回收",
                "结果": "成功" if ok else "失败",
                "空闲分区链": format_free_list(free_list),
            }
        steps.append(step)
    return steps


def dp_table() -> tuple[list[list], list[list]]:
    """返回 FF 和 BF 的步骤数据供 Gradio DataFrame 使用。"""
    ff_steps = _run_dp(first_fit_alloc)
    bf_steps = _run_dp(best_fit_alloc)

    def to_rows(steps):
        return [[s["操作"], s["结果"], s["空闲分区链"]] for s in steps]

    return to_rows(ff_steps), to_rows(bf_steps)


# 请求调页，数据收集版
def _run_paging(algo_cls, seed: int, blocks: int) -> dict:
    algo = algo_cls()
    # 动态设置块数
    page_table = [PageEntry(page_no=i) for i in range(TOTAL_PAGES)]
    seq = generate_instructions(seed)
    page_faults = 0
    trace: list[dict] = []

    in_memory_count = 0  # 替代 len(queue)

    class _FIFO_blocks:
        """FIFO with configurable block count."""
        def __init__(self):
            self.queue: list[int] = []

        def access(self, page_no, pt, clock):
            nonlocal page_faults, in_memory_count
            entry = pt[page_no]
            if entry.valid:
                return False
            page_faults += 1
            if len(self.queue) < blocks:
                block = len(self.queue)
                self.queue.append(block)
            else:
                victim_block = self.queue.pop(0)
                self.queue.append(victim_block)
                for pe in pt:
                    if pe.block_no == victim_block:
                        pe.valid = False
                        pe.block_no = -1
                        pe.load_time = -1
                        break
                block = victim_block
            entry.valid = True
            entry.block_no = block
            entry.load_time = clock
            return True

    class _LRU_blocks:
        def __init__(self):
            pass

        def access(self, page_no, pt, clock):
            nonlocal page_faults
            entry = pt[page_no]
            if entry.valid:
                entry.last_access = clock
                return False
            page_faults += 1
            in_mem = [pe for pe in pt if pe.valid]
            if len(in_mem) < blocks:
                block = len(in_mem)
            else:
                victim = min(in_mem, key=lambda pe: pe.last_access)
                block = victim.block_no
                victim.valid = False
                victim.block_no = -1
                victim.last_access = -1
            entry.valid = True
            entry.block_no = block
            entry.last_access = clock
            return True

    Algo = _FIFO_blocks if algo_cls is FIFO else _LRU_blocks
    algo = Algo()

    for tick, addr in enumerate(seq):
        page_no = addr // PAGE_SIZE
        offset = addr % PAGE_SIZE
        entry_before = page_table[page_no].valid
        is_fault = algo.access(page_no, page_table, tick)
        entry = page_table[page_no]
        phys = entry.block_no * PAGE_SIZE + offset if entry.valid else None
        trace.append({
            "序号": tick + 1,
            "指令地址": addr,
            "页号": page_no,
            "页内偏移": offset,
            "物理地址": phys if phys is not None else "—",
            "缺页": "✓" if is_fault else "",
        })

    return {
        "page_faults": page_faults,
        "total": TOTAL_INSTRUCTIONS,
        "rate": page_faults / TOTAL_INSTRUCTIONS * 100,
        "trace": trace,
    }


# Gradio UI
CSS = """
.gradio-container { max-width: 1100px !important; }
.fault { color: #e74c3c; font-weight: bold; }
h3 { margin-top: 0.5em; margin-bottom: 0.3em; }
"""


def create_ui() -> gr.Blocks:
    with gr.Blocks(title="OS 内存管理模拟", css=CSS) as demo:
        gr.Markdown(
            """
            # 🖥 操作系统内存管理模拟
            ### 动态分区分配 / 请求调页存储管理
            """
        )

        with gr.Tabs():
            # ── Tab 1: 动态分区分配 ──
            with gr.TabItem("动态分区分配"):
                gr.Markdown("#### 内存请求序列")
                req_table = gr.Dataframe(
                    headers=["操作", "大小(K)", "作业号"],
                    values=[list(r) for r in REQUESTS],
                    interactive=False,
                )

                gr.Markdown("#### 模拟结果")
                btn_dp = gr.Button("运行模拟", variant="primary")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**首次适应 (First Fit)**")
                        ff_table = gr.Dataframe(
                            headers=["操作", "结果", "空闲分区链"],
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Column():
                        gr.Markdown("**最佳适应 (Best Fit)**")
                        bf_table = gr.Dataframe(
                            headers=["操作", "结果", "空闲分区链"],
                            interactive=False,
                            wrap=True,
                        )

                btn_dp.click(fn=dp_table, outputs=[ff_table, bf_table])

            # ── Tab 2: 请求调页 ──
            with gr.TabItem("请求调页存储管理"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### 参数设置")
                        algo_radio = gr.Radio(
                            choices=["FIFO", "LRU"],
                            value="FIFO",
                            label="页面置换算法",
                        )
                        blocks_slider = gr.Slider(
                            minimum=1, maximum=10, value=4, step=1,
                            label="物理内存块数",
                        )
                        seed_input = gr.Number(
                            value=42, label="随机种子", precision=0,
                        )
                        btn_pg = gr.Button("运行模拟", variant="primary")

                    with gr.Column(scale=2):
                        gr.Markdown("#### 结果")
                        with gr.Row():
                            fault_num = gr.Label(label="缺页次数", value="—")
                            fault_rate = gr.Label(label="缺页率", value="—")
                        gr.Markdown("#### 执行过程 (前 100 条)")
                        trace_table = gr.Dataframe(
                            headers=["序号", "指令地址", "页号", "页内偏移", "物理地址", "缺页"],
                            interactive=False,
                            max_rows=100,
                        )

                def on_run_pg(algo_name, blocks, seed):
                    cls = FIFO if algo_name == "FIFO" else LRU
                    result = _run_paging(cls, int(seed), int(blocks))
                    trace_rows = [[
                        t["序号"], t["指令地址"], t["页号"],
                        t["页内偏移"], t["物理地址"], t["缺页"],
                    ] for t in result["trace"]]
                    return (
                        str(result["page_faults"]),
                        f"{result['rate']:.2f}%",
                        trace_rows,
                    )

                btn_pg.click(
                    fn=on_run_pg,
                    inputs=[algo_radio, blocks_slider, seed_input],
                    outputs=[fault_num, fault_rate, trace_table],
                )

    return demo


def launch():
    demo = create_ui()
    demo.launch(show_error=True)
