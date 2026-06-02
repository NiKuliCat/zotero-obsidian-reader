# Zotero Obsidian Reader

一个面向 `Codex + Zotero + Obsidian` 的本地研究工作流 skill。

它的目标不是只“读出一篇文献的元数据”，而是把这条链路打通：

- 从本地 Zotero 数据目录读取论文元数据、标签、批注、附件和可用全文缓存
- 根据单篇、批量、综述三种模式生成 Obsidian Markdown 笔记
- 自动识别工作区中的 Obsidian vault 与 Zotero 数据目录
- 在正式读文献前先检查本地配置与研究画像，避免“写到一半才发现前置条件不完整”

## 适用场景

这个 skill 适合下面几类任务：

- 精读一篇 Zotero 中的论文，并生成结构化 Obsidian 笔记
- 批量处理一个集合、标签或主题下的多篇文献
- 对一组论文生成综述型笔记
- 围绕自己的研究方向，持续沉淀“论文笔记 -> 综述 -> 课题关联”的知识库

## 核心能力

- `single`
  一篇论文 -> 一篇详细精读笔记
- `batch`
  一个集合 / 标签 / 主题 -> 多篇论文笔记
- `synthesis`
  多篇论文 -> 一篇交叉比较综述
- `preflight`
  在读取文献前先检查工作区配置、自动补全路径、确认研究画像

## 特点

- 不依赖 Zotero MCP
- 默认走“本地 skill + Python 脚本”方案
- 使用 Python 标准库，无额外第三方依赖
- 支持自动识别 Zotero 数据目录和 Obsidian vault
- 笔记输出路径可继承 Zotero 集合结构
- 缺少研究画像时，会在最开始暂停，而不是读到一半再回头补问

## 目录结构

```text
zotero-obsidian-reader/
├─ SKILL.md
├─ README.md
├─ .gitignore
├─ agents/
├─ assets/
│  └─ templates/
├─ examples/
├─ references/
└─ scripts/
```

## 安装方式

把整个目录放到你的 Codex skill 目录下，保持 `SKILL.md` 位于 skill 根目录。

例如：

```text
.codex/skills/zotero-obsidian-reader
```

不要额外再套一层目录，否则 Codex 可能无法正确识别这个 skill。

## 环境要求

- Python 3.10+
- 本地工作区内可访问：
  - 一个 Obsidian vault
  - 一个 Zotero 数据目录

Zotero 数据目录通常包含：

- `zotero.sqlite`
- `storage/`

Obsidian vault 通常包含：

- `.obsidian/`

## 首次运行行为

第一次运行时，会优先执行预检查：

1. 读取本地配置文件 `.zotero-obsidian-reader.json`
2. 如果缺少 `vault_dir`，自动搜索工作区中的 `.obsidian`
3. 如果缺少 `zotero_dir`，自动搜索包含 `zotero.sqlite` 的目录
4. 将识别结果写回 `.zotero-obsidian-reader.json`
5. 检查是否已经设置研究领域
6. 如果缺少研究画像，立即暂停，不进入读文献和写笔记阶段

首次自动识别成功时，会提示类似：

- `自动识别到当前的 Obsidian 仓库位置：...`
- `自动识别到当前的 Zotero 数据目录：...`

## 本地配置文件

默认配置文件名：

```text
.zotero-obsidian-reader.json
```

可参考：

- [examples/zotero-obsidian-reader.example.json](./examples/zotero-obsidian-reader.example.json)

示例字段说明：

- `vault_dir`
  Obsidian 仓库根目录
- `zotero_dir`
  Zotero 数据目录
- `paper_relative_dir`
  单篇笔记默认输出子目录，可留空
- `synthesis_relative_dir`
  综述笔记默认输出子目录，可留空
- `paper_filename_suffix`
  单篇笔记文件名后缀
- `synthesis_filename_suffix`
  综述笔记文件名后缀
- `research_domain`
  研究领域
- `research_focus`
  当前研究重点
- `research_keywords`
  研究关键词列表

## 快速开始

### 1. 先运行预检查

```bash
python scripts/preflight_workspace.py
```

它会：

- 检查本地配置
- 自动识别 Zotero / Obsidian 路径
- 检查研究画像是否存在

### 2. 如果还没设置研究画像

```bash
python scripts/set_research_profile.py
```

### 3. 提取单篇文献

按唯一键提取：

```bash
python scripts/extract_zotero_item.py --item-key 87ULUC2F --pretty
```

按标题查找候选：

```bash
python scripts/extract_zotero_item.py --find "三维高斯泼溅技术的GIS应用探索"
```

### 4. 生成单篇笔记

```bash
python scripts/render_paper_note.py --input item.json
```

### 5. 生成综述笔记

```bash
python scripts/render_synthesis_note.py --input items.json --title "高斯泼溅相关文献综述"
```

## 在 Codex 中的使用方式

这是一个给 Codex 调用的 skill，所以更推荐直接用自然语言触发，而不是手动串所有脚本。

### 单篇笔记示例

```text
精读 Zotero 中《三维高斯泼溅技术的GIS应用探索》这篇论文，并生成 Obsidian 笔记
```

```text
按 item key 87ULUC2F 读取论文并生成精读笔记
```

### 批量笔记示例

```text
批量精读高斯泼溅集合下的所有论文，并生成 Obsidian 笔记
```

```text
读取 Zotero 中标签为 3DGS 的所有论文，跳过已有笔记，只生成缺失部分
```

### 综述示例

```text
对高斯泼溅集合下的论文生成一篇综述笔记，重点比较方法差异和应用场景
```

## 输出路径规则

默认情况下：

- 如果配置里写了 `paper_relative_dir` / `synthesis_relative_dir`，优先使用配置
- 如果没写，单篇笔记默认继承该论文的第一个 Zotero 集合路径
- 如果论文没有集合，单篇笔记回退到 vault 根目录
- 综述笔记默认写到 vault 根目录

例如：

- Zotero 集合路径：`高斯泼溅`
- 论文标题：`三维高斯泼溅技术的GIS应用探索`

默认输出可能是：

```text
Obsidian根目录/高斯泼溅/三维高斯泼溅技术的GIS应用探索_精读笔记.md
```

## 笔记生成原则

这个 skill 的目标不是机械搬运摘要，而是帮助你形成“可继续研究”的笔记。

因此它强调：

- Frontmatter 需要提炼，不能整段复制摘要
- `theme` / `study_area` / `data_source` / `methodology` / `core_variable` / `key_finding` / `relevance` 都应短、准、可复用
- 如果研究画像缺失，先停下来问用户，不进入正文分析
- 如果元数据不全，也会生成可补写的笔记骨架，而不是直接失败

## 主要脚本

- `scripts/preflight_workspace.py`
  先检查工作区配置和研究画像
- `scripts/extract_zotero_item.py`
  提取单篇文献数据
- `scripts/collect_zotero_items.py`
  按标题 / 标签 / 集合批量检索
- `scripts/render_paper_note.py`
  生成单篇论文笔记
- `scripts/render_synthesis_note.py`
  生成综述笔记
- `scripts/set_research_profile.py`
  写入研究领域、研究重点、关键词
- `scripts/show_workspace_config.py`
  查看当前识别到的工作区配置

## 工作流概览

标准顺序是：

1. 运行 `preflight`
2. 检查或写入研究画像
3. 定位目标文献
4. 提取元数据、批注、全文缓存
5. 生成 Markdown 笔记
6. 写入 Obsidian

这个顺序是刻意设计的。
它避免了先读论文、再发现配置缺失、再中途打断的体验问题。

## 已知边界

- 当前默认基于本地 Zotero 数据目录，不依赖云端 Zotero API
- 如果附件没有全文缓存，分析会更多依赖元数据、摘要、标签和批注
- 如果同名论文很多，最好提供 item key、精确标题或集合范围，避免歧义

## 适合公开发布时补充的内容

如果你准备继续把这个仓库打磨成公开项目，建议后续再补：

- `LICENSE`
- 示例截图
- 一篇真实生成结果的样例笔记
- 更新日志或 roadmap

## 相关文件

- 技能入口：[SKILL.md](./SKILL.md)
- 示例配置：[examples/zotero-obsidian-reader.example.json](./examples/zotero-obsidian-reader.example.json)
