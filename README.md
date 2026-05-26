# OS Memory Management

操作系统内存管理模拟 — 动态分区分配 & 请求调页存储管理。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

启动后选择运行模式：

- `1` — Console 控制台版
- `2` — Web 浏览器版 (Gradio)

## 功能

| 模块 | 算法 | 说明 |
|---|---|---|
| 动态分区分配 | First Fit / Best Fit | 640K 内存，模拟分配回收，展示空闲分区链变化 |
| 请求调页管理 | FIFO / LRU | 32 页 / 4 个物理块，320 条指令，统计缺页率 |

## 结构

```
├── main.py          # 入口
├── src/
│   ├── dynamic_partition.py
│   ├── paging.py
│   ├── instruction_gen.py
│   └── gradio_app.py
└── dist/            # 打包输出
```

## 打包

```bash
pyinstaller --name os_mm --onedir --add-data "src;src" --collect-all gradio main.py
```
