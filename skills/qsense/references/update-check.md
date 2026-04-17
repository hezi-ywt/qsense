# 更新检查

qsense 有两种安装方式,更新方式不同。先判断用户是哪种再动手。

## 先看当前版本和安装模式

```bash
qsense --version
pipx list --short 2>/dev/null | grep qsense-cli
pip show qsense-cli 2>/dev/null | grep -E "^(Location|Editable project location)"
```

判断:
- `pipx list` 有 `qsense-cli` → **pipx 安装(主路径)**,走 PyPI 更新。
- `pip show` 输出含 `Editable project location` → **editable 安装**,走 git 更新(那个路径就是 git 工作目录)。
- 都没命中 → 要么没装,要么走了非标准路径;先按 SKILL.md `Setup` 重装。

## pipx(PyPI)用户

**检查最新版:**

```bash
curl -s https://pypi.org/pypi/qsense-cli/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

把输出和 `qsense --version` 比,不同就是有更新。

**升级:**

```bash
pipx upgrade qsense-cli
```

验证:`qsense --version` 应显示新版本号。

## editable / git clone 用户

仓库里三样东西更新方式不同:

| 组件 | 内容 | 更新方式 |
|---|---|---|
| **Skill** | `skills/qsense/` 下 SKILL.md + references | `git pull` 即生效 |
| **Python 代码** | `src/qsense/` | `git pull` 即生效(editable 直接指源码) |
| **CLI 元数据** | 版本号、依赖、entry point(`pyproject.toml`) | `git pull` 后需要 `pip install -e .` |

**检查:**

```bash
cd <qsense 所在目录>
git fetch origin main
git log HEAD..origin/main --oneline
```

无输出 = 已是最新。有输出 = 列出的就是待更新的 commit。

**执行:**

```bash
git pull origin main
# 若 pyproject.toml 有改动(版本号/依赖/entry point):
pip install -e .
```

快速判断是否需要重装:

```bash
git diff HEAD~..HEAD -- pyproject.toml
```

有 diff → 跑 `pip install -e .`。

## 注意

- 用户本地有未提交修改时,`git pull` 前先确认是否需要 `git stash`。
- 升级后如果 `qsense --version` 仍是旧号,说明还有一个旧副本在 PATH 前面 — 用 `which -a qsense` 定位。
- `~/.qsense/.env` 不受升级影响,API key / base_url / 默认模型会保留。
