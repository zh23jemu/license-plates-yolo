# 项目级 AGENTS.md

## 项目目标

本项目用于完成车牌定位对比实验：仅检测/定位车牌框，不进行车牌字符识别，也不对 YOLOv8n 或 YOLOv10n 做结构改进。实验目标是在相同数据、相同训练配置和相同评价流程下，对比 `yolov8n.pt` 与 `yolov10n.pt` 的车牌定位精度。

## 技术栈

- Python 3.10+（优先使用项目本地 `.venv`）
- Ultralytics YOLO
- OpenCV
- PyYAML
- Pandas
- Matplotlib
- Slurm（GPU 训练默认使用 `aws` 分区）

## 当前架构

- `scripts/prepare_ccpd_dataset.py`：将 CCPD 原始图片抽样并转换为 YOLO 单类别检测数据集。
- `scripts/check_dataset.py`：检查转换后的图片、标签和 `plates.yaml` 是否一致。
- `scripts/train_compare.py`：使用相同参数训练并验证 YOLOv8n 与 YOLOv10n。
- `scripts/generate_report.py`：从训练输出中汇总指标并生成 Markdown 实验报告。
- `slurm/train_compare.sbatch`：Slurm GPU 训练提交脚本。
- `reports/experiment_report.md`：实验报告模板。

## 开发规范

- 只做最小必要修改，不做无关重构。
- 新增 Python 代码保持中文注释，重点说明用途、关键逻辑、参数和异常处理。
- 所有 Python 命令优先使用 `.venv` 中的解释器，例如 Windows 使用 `.venv\Scripts\python.exe`，Linux/Slurm 使用 `.venv/bin/python`。
- 训练实验必须保证两个模型除权重名称外使用相同参数。
- 不直接删除文件；如需清理数据或输出，只给出建议命令或移动到临时目录。

## TODO

- 准备 CCPD 原始图片目录，并用 `scripts/prepare_ccpd_dataset.py` 生成几百张规模的 YOLO 数据集。
- 在 Slurm GPU 节点上运行 `slurm/train_compare.sbatch`。
- 训练完成后运行 `scripts/generate_report.py` 填充最终实验报告。

## 当前进度

已创建最小可复现实验工程骨架，包含数据转换、数据检查、训练对比、报告生成、Slurm 提交脚本和基础单元测试。当前本地 `.venv` 已创建并安装依赖，核心解析测试已通过，正在完成首次本地 Git 提交。

## 近期变更

- 新增 CCPD 到 YOLO 格式的数据准备脚本。
- 新增 YOLOv8n 与 YOLOv10n 同条件训练对比脚本。
- 新增 Markdown 报告模板与结果汇总脚本。
- 新增 Slurm GPU 训练脚本，默认使用 `aws` 分区。
- 新增 `.gitignore` 和依赖清单。
- 新增 CCPD 文件名解析与 YOLO 坐标归一化测试。
- 使用 `.venv` 完成依赖安装，并通过 `pytest tests` 验证。
- 初始化前确认 `.gitignore` 已覆盖 `.venv`、缓存、训练输出和本地数据目录。
- 同步全局 Codex 默认规则：Slurm 默认使用 `#SBATCH --account=gpo-ifv7xx` 与 `#SBATCH --qos=normal`。
- 更新车牌实验 Slurm 脚本，写入默认 account/qos，并移除作业内创建 `slurm_logs` 的步骤，避免集群计算节点权限限制导致任务提前失败。
- 修正 Slurm 项目根目录解析方式，改用 `SLURM_SUBMIT_DIR`，确保作业使用提交目录中的项目代码和 `.venv`，而不是计算节点 `/var/spool` 下的临时脚本目录。
- 同步全局 Codex 默认规则：当前集群 PyTorch GPU 环境默认使用 CUDA 12.x 兼容 wheel，优先安装 `cu126` 版 `torch torchvision`，避免误装 `cu130` 导致驱动不兼容。
- 修正训练脚本的权重路径获取逻辑：不再手写推断 `best.pt` 路径，而是使用 Ultralytics 实际训练输出目录，避免相对 `project` 被保存到 `runs/detect/...` 时后续验证找不到权重。
- 修正验证阶段 batch 处理：训练阶段仍允许 `batch=auto`，但验证和预测阶段改用正整数 batch，避免 Ultralytics DataLoader 收到 `-1` 报错。

## 下一步计划

- 下载或准备 CCPD 数据集原始图片。
- 生成 500 张左右的训练/验证/测试子集。
- 提交 Slurm 训练任务并记录日志。
- 根据训练结果更新报告中的指标、曲线和结论。
- 如需远端同步，添加远程仓库后再按需执行 `git push`。

## 风险问题

- CCPD 原始数据源体积较大，下载地址和镜像可能随时间变化，需要按实际可访问来源准备数据。
- YOLOv10n 支持依赖 Ultralytics 版本，若集群环境中版本过旧，需要升级项目 `.venv` 依赖。
- 几百张样本规模较小，最终结论只能代表该小样本实验，不应泛化为所有车牌场景。

## 架构决策

- 数据集只使用水平矩形框检测标签，不使用 OBB，也不解析字符类别。
- 模型保持原始 `yolov8n.pt` 与 `yolov10n.pt`，不做结构改进或额外调参搜索。
- 报告采用 Markdown，便于直接版本管理和引用训练输出图表。
- 当前集群 Slurm GPU 作业默认组合为 `partition=aws`、`account=gpo-ifv7xx`、`qos=normal`；如分区不匹配，应先用 `sacctmgr show assoc user=$USER format=User,Account,Partition,QOS` 确认可用组合。
- Slurm 脚本中项目根目录应优先使用 `SLURM_SUBMIT_DIR`，避免 `BASH_SOURCE[0]` 在计算节点临时目录中解析出错误路径。
- 当前集群 NVIDIA 驱动不适合 CUDA 13.0 PyTorch wheel；GPU 训练环境默认使用 `--index-url https://download.pytorch.org/whl/cu126` 安装 `torch torchvision`，并在提交前确认 `torch.cuda.is_available()` 为 `True`。
- Ultralytics 训练结果目录应以运行时返回的 `save_dir` 为准；脚本不要依赖手写路径推断来定位 `weights/best.pt`。
- Ultralytics 的 `batch=auto` 仅用于训练阶段；验证和预测阶段应传入正整数 batch。
