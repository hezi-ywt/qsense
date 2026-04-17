# 更新检查

qsense 从 git 源安装(不发 PyPI)。仓库里有三样东西,更新方式不同:

| 组件 | 内容 | 更新方式 |
|---|---|---|
| **Skill** | `skills/qsense/` 下 SKILL.md 和 references | `git pull` 即生效 |
| **Python 代码** | `src/qsense/` | `git pull` 即生效(editable install 直接指源码) |
| **CLI 元数据** | 版本号、依赖、entry point(`pyproject.toml`) | `git pull` 后需要 `pip install -e .` |

## 检查是否有更新

```bash
cd <qsense 源码目录>
git fetch origin main
git log HEAD..origin/main --oneline
```

无输出 = 已是最新。有输出 = 列出的就是待更新的 commit。

找不到源码目录时:

```bash
# 如果装的是 pip editable
pip show qsense-cli 2>/dev/null | grep -E "^(Location|Editable project location)"
# 如果装的是 pipx editable
pipx show qsense-cli 2>/dev/null | grep "Editable project location"
```

## 执行更新

```bash
git pull origin main
```

大多数情况到这就够了 — skill 文件和库代码立即生效。

如果 `git diff HEAD@{1}..HEAD -- pyproject.toml` 有改动(版本号、依赖、entry point 变了),再跑:

```bash
pip install -e .
# 或 pipx editable 装的:
pipx reinstall qsense-cli
```

## 验证

```bash
qsense --version
```

## 注意

- 本地有未提交修改时,`git pull` 前先确认是否需要 `git stash`。
- 升级后 `qsense --version` 仍是旧号 → PATH 上可能有多份 qsense;`which -a qsense` 定位,删旧的或调 PATH。
- `~/.qsense/.env` 不受升级影响,API key / base_url / 默认模型会保留。
- qsense 当前没发 PyPI(2026-04),所以**没有** `pipx upgrade` 这条路。要么 `git pull`,要么 `pipx reinstall` 重建 editable 链接。
