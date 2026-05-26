"""
OS Memory Management Simulator
操作系统内存管理模拟 — 主入口
"""

import sys

# Windows 终端 UTF-8 兼容
sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_banner():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]操作系统内存管理模拟[/bold cyan]\n"
            "OS Memory Management Simulator",
            border_style="cyan",
        )
    )


def show_menu() -> str:
    table = Table(show_header=False, box=None, padding=(0, 4))
    table.add_column(style="dim")
    table.add_column(style="white")
    table.add_row("1", "动态分区分配模拟  (First Fit / Best Fit)")
    table.add_row("2", "请求调页存储管理模拟  (FIFO / LRU)")
    table.add_row("3", "全部运行 (对比展示)")
    table.add_row("0", "退出")
    console.print(table)
    return console.input("\n[dim]请选择:[/dim] ").strip()


def main():
    show_banner()
    while True:
        choice = show_menu()
        console.print()

        if choice == "1":
            from src.dynamic_partition import run
            run()
        elif choice == "2":
            from src.paging import run
            run()
        elif choice == "3":
            from src.dynamic_partition import run as run_dp
            from src.paging import run as run_pg
            run_dp()
            run_pg()
        elif choice == "0":
            console.print("[dim]再见。[/dim]\n")
            break
        else:
            console.print("[red]无效选择，请重试。[/red]")

        console.print()


if __name__ == "__main__":
    main()
