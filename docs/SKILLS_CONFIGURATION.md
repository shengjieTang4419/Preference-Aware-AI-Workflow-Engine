# Skills 配置指南

## 概述

本项目支持两种 Skills 来源：
1. **外部 Skills** - 从宿主机挂载的 skills 目录（如 `~/.claude/skills`）
2. **项目内置 Skills** - 项目 `./skills` 目录下的 skills

## 配置外部 Skills

### 方法 1: 使用默认路径（推荐）

如果你的 skills 存放在 `~/.claude/skills`，无需任何配置，devcontainer 会自动挂载。

### 方法 2: 自定义路径

1. **在宿主机设置环境变量**

   ```bash
   # Linux/macOS - 添加到 ~/.bashrc 或 ~/.zshrc
   export EXTERNAL_SKILLS_DIR=/path/to/your/skills
   
   # Windows - 在系统环境变量中设置
   # 变量名: EXTERNAL_SKILLS_DIR
   # 变量值: C:\path\to\your\skills
   ```

2. **重启 VS Code** 使环境变量生效

3. **重建容器**
   - 按 `F1` 或 `Ctrl+Shift+P`
   - 输入 `Dev Containers: Rebuild Container`

### 方法 3: 不使用外部 Skills

如果不想加载外部 skills，只使用项目内置的：

1. 在宿主机设置环境变量为空路径：
   ```bash
   export EXTERNAL_SKILLS_DIR=/tmp/empty_skills
   mkdir -p /tmp/empty_skills  # 创建空目录
   ```

2. 或者直接注释掉 `devcontainer.json` 中的 mounts 配置

## 工作原理

### 挂载机制

```json
// .devcontainer/devcontainer.json
"mounts": [
  "source=${localEnv:EXTERNAL_SKILLS_DIR:-${localEnv:HOME}/.claude/skills},target=/workspace/external_skills,type=bind,consistency=cached"
]
```

- `${localEnv:EXTERNAL_SKILLS_DIR}` - 读取宿主机环境变量
- `:-${localEnv:HOME}/.claude/skills` - 如果未设置，使用默认路径
- `target=/workspace/external_skills` - 挂载到容器内的固定路径

### 加载逻辑

```python
# crewai_web/core/tools/skills/config.py
def get_skills_directories():
    dirs = []
    
    # 1. 检查外部 skills (如果挂载目录非空)
    if Path("/workspace/external_skills").exists():
        dirs.append(Path("/workspace/external_skills"))
    
    # 2. 项目内置 skills
    if Path("./skills").exists():
        dirs.append(Path("./skills"))
    
    return dirs
```

## 验证配置

运行测试脚本检查 skills 加载情况：

```bash
python test_skills_loader.py
```

输出示例：
```
📁 搜索目录:
  - /workspace/external_skills
  - /workspaces/one_person_company/skills

📚 发现的 Skills (5 个):
  ✅ mysql-query (external)
  ✅ design-guide (external)
  ✅ code-generator (internal)
  ...
```

## 常见问题

### Q: 外部 skills 没有加载？

**A:** 检查以下几点：
1. 宿主机环境变量是否设置正确
2. 路径是否存在且包含 SKILL.md 文件
3. 是否重启了 VS Code 和重建了容器

### Q: 如何只使用项目内置 skills？

**A:** 设置 `EXTERNAL_SKILLS_DIR` 为不存在的路径，或注释掉 mounts 配置。

### Q: 可以同时使用多个外部 skills 目录吗？

**A:** 当前不支持。如需多个目录，建议：
- 在宿主机创建一个统一目录
- 使用符号链接将其他目录链接到这个统一目录

## 示例配置

### 示例 1: macOS 用户

```bash
# ~/.zshrc
export EXTERNAL_SKILLS_DIR="$HOME/.claude/skills"
```

### 示例 2: Windows 用户

```powershell
# 系统环境变量
EXTERNAL_SKILLS_DIR=C:\Users\YourName\.claude\skills
```

### 示例 3: 团队共享 skills

```bash
# 使用团队共享目录
export EXTERNAL_SKILLS_DIR="/mnt/team-shared/skills"
```
