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


def show_version_chooser() -> str:
    """选择 Console 版还是 Web 版。"""
    table = Table(show_header=False, box=None, padding=(0, 4))
    table.add_column(style="dim")
    table.add_column(style="white")
    table.add_row("1", "Console 控制台版")
    table.add_row("2", "Web 浏览器版 (Gradio)")
    table.add_row("0", "退出")
    console.print(table)
    return console.input("\n[dim]请选择版本:[/dim] ").strip()


def run_console():
    """原有控制台菜单。"""
    from rich.table import Table as T

    def show_menu() -> str:
        table = T(show_header=False, box=None, padding=(0, 4))
        table.add_column(style="dim")
        table.add_column(style="white")
        table.add_row("1", "动态分区分配模拟  (First Fit / Best Fit)")
        table.add_row("2", "请求调页存储管理模拟  (FIFO / LRU)")
        table.add_row("3", "全部运行 (对比展示)")
        table.add_row("0", "返回上级")
        console.print(table)
        return console.input("\n[dim]请选择:[/dim] ").strip()

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
            break
        else:
            console.print("[red]无效选择，请重试。[/red]")

        console.print()


def run_web():
    """启动 Gradio Web 版。"""
    from src.gradio_app import create_ui
    console.print("\n[cyan]正在启动 Web 服务...[/cyan]")
    console.print("[dim]浏览器打开后即可使用，Ctrl+C 停止。[/dim]\n")
    demo = create_ui()
    demo.launch(show_error=True)


def main():
    show_banner()
    while True:
        choice = show_version_chooser()
        if choice == "1":
            run_console()
        elif choice == "2":
            run_web()
            break  # Gradio 有自己的事件循环，退出后返回
        elif choice == "0":
            console.print("[dim]再见。[/dim]\n")
            break
        else:
            console.print("[red]无效选择，请重试。[/red]")


if __name__ == "__main__":
    main()
