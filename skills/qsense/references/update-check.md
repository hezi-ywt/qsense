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
# pip editable(非 pipx 场景):
pip show qsense-cli 2>/dev/null | grep -E "^(Location|Editable project location)"

# pipx 场景(pipx 没有 show 子命令,得用 runpip):
pipx list --short 2>/dev/null | grep qsense-cli    # 确认存在
pipx runpip qsense-cli show qsense-cli 2>/dev/null | grep -E "^(Location|Editable project location)"
```

`Editable project location` 那行如果有,后面的路径就是 git 源码目录,`cd` 过去就能 `git pull`。

## 执行更新

qsense 有一个本地累积文件需要保护:`skills/qsense/references/user-notes.md` 是 agent 在使用中维护的用户偏好、经验、工作流。直接 `git pull` 可能会和本地改动冲突或被覆盖,所以走 stash 流程:

```bash
# 1. 如果 user-notes.md 有本地改动(含 staged),stash 出来
git diff --quiet HEAD -- skills/qsense/references/user-notes.md \
  || git stash push -m "qsense:user-notes" skills/qsense/references/user-notes.md

# 2. 拉取
git pull origin main

# 3. 恢复本地笔记 — 按 ref 弹,避免误弹其它 stash
ref=$(git stash list | awk -F: '/qsense:user-notes/{print $1; exit}')
[ -n "$ref" ] && git stash pop "$ref"
```

大多数情况到这就够了 — skill 文件和库代码立即生效。

`git stash pop` 有冲突时(罕见,说明 upstream 也动了 user-notes.md 的 skeleton/示例):读两份内容,**保留本地累积的个人偏好 / 经验 / 工作流**,同时采纳 upstream 对结构的更新,然后:

```bash
git add skills/qsense/references/user-notes.md
git stash drop
```

如果 `pyproject.toml` 也有改动(版本号、依赖、entry point 变了),再重装:

```bash
git diff HEAD@{1}..HEAD -- pyproject.toml   # 有 diff 才需要
pip install -e .
# 或 pipx editable 装的:
pipx reinstall qsense-cli
```

### 万一 user-notes.md 被覆盖了(没走 stash 流程)

通过 `git reflog` 找到 `pull` 前的 HEAD,把旧版本捞回来:

```bash
git reflog | head -10       # 找到 pull 前的 HEAD,比如 abc1234
git show abc1234:skills/qsense/references/user-notes.md > /tmp/rescued.md
# 把 /tmp/rescued.md 的本地累积内容手动 merge 回当前 user-notes.md
```

## 验证

```bash
qsense --version
```

## 注意

- 除 user-notes.md 外,其他本地未提交修改在 `git pull` 前也建议 `git stash`。
- 升级后 `qsense --version` 仍是旧号 → PATH 上可能有多份 qsense;用 `which -a qsense`(macOS/Linux)或 `where qsense`(Windows)定位,删旧的或调 PATH。
- `~/.qsense/.env` 不受升级影响,API key / base_url / 默认模型会保留。
- qsense 当前没发 PyPI(2026-04),所以**没有** `pipx upgrade` 这条路。要么 `git pull`,要么 `pipx reinstall` 重建 editable 链接。
