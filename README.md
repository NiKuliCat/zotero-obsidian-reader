# Zotero Obsidian Reader

一个面向 `Codex + Zotero + Obsidian` 工作流的本地 skill。

它的目标是：

- 从本地 Zotero 数据目录读取文献元数据、标签、批注、附件和可用全文缓存
- 按单篇、批量、综述三种模式生成 Obsidian Markdown 笔记
- 首次使用时自动识别工作区中的 Obsidian 仓库和 Zotero 数据目录
- 在正式读文献前先检查研究画像，避免“写到一半才发现配置不完整”

## 目录结构

```text
zotero-obsidian-reader/
├─ SKILL.md
├─ README.md
├─ .gitignore
├─ agents/
├─ assets/
│  └─ templates/
├─ references/
├─ scripts/
└─ examples/
```

## 核心特性

- `single`：单篇论文精读并生成一篇详细笔记
- `batch`：对一个 Zotero 集合 / 标签 / 主题批量生成笔记
- `synthesis`：对一组论文生成综述型笔记
- `preflight`：在读取文献前先检查工作区配置与研究画像

## 安装方式

把整个仓库目录放到你的 Codex skill 目录下，例如：

```text
.codex/skills/zotero-obsidian-reader
```

要求根目录中保留 `SKILL.md`，不要再额外套一层目录。

## 首次使用行为

第一次运行时会优先执行预检查：

1. 读取本地配置文件 `.zotero-obsidian-reader.json`
2. 如果缺少 `vault_dir`，自动搜索工作区中的 `.obsidian`
3. 如果缺少 `zotero_dir`，自动搜索包含 `zotero.sqlite` 的目录
4. 将识别结果写回 `.zotero-obsidian-reader.json`
5. 如果缺少研究领域信息，立即暂停，不进入读文献和写笔记阶段

如果是首次自动识别，会提示类似：

- `自动识别到当前的 Obsidian 仓库位置：...`
- `自动识别到当前的 Zotero 数据目录：...`

## 本地配置文件

默认配置文件名：

```text
.zotero-obsidian-reader.json
```

可参考 [examples/zotero-obsidian-reader.example.json](./examples/zotero-obsidian-reader.example.json)。

## 主要脚本

- `scripts/preflight_workspace.py`：先检查工作区配置和研究画像
- `scripts/extract_zotero_item.py`：提取单篇文献数据
- `scripts/collect_zotero_items.py`：按标题 / 标签 / 集合批量检索
- `scripts/render_paper_note.py`：生成单篇论文笔记
- `scripts/render_synthesis_note.py`：生成综述笔记
- `scripts/set_research_profile.py`：写入研究领域、研究重点、关键词

## 推荐发布说明

如果你准备公开发布到 Git：

- 建议补一个许可证文件
- 建议在仓库描述里明确说明这是“本地 Zotero 数据驱动”的 skill
- 建议附一张工作流示意图或示例笔记截图

## 兼容说明

- 当前版本默认走“本地 skill + Python 脚本”方案
- 不依赖 Zotero MCP
- 使用 Python 标准库，无额外第三方依赖
