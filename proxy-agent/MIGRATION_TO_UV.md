# 迁移到 uv 完成

proxy-agent 项目已成功迁移到使用 uv 包管理器。

## 变更内容

### 新增文件
- `pyproject.toml` - 项目配置文件，包含所有依赖和项目元数据
- `uv.lock` - 依赖锁定文件，确保环境一致性
- `.python-version` - Python 版本声明（3.12）
- `run.sh` - 便捷启动脚本

### 更新文件
- `.gitignore` - 添加了 `.venv/`、`uv.lock` 和 `.python-version`
- `README.md` - 更新了安装和运行说明

### 保留文件
- `requirements.txt` - 保留用于向后兼容

## 使用方法

### 安装依赖

```bash
uv sync
```

### 运行项目

方式1：使用 uv run
```bash
uv run python main.py
```

方式2：使用启动脚本
```bash
./run.sh
```

方式3：使用 uv run proxy-agent 命令（如果已安装为包）
```bash
uv run proxy-agent
```

### 添加新依赖

```bash
uv add package-name
```

### 移除依赖

```bash
uv remove package-name
```

## 优势

1. **更快的依赖解析** - uv 使用 Rust 编写，速度比 pip 快 10-100 倍
2. **可靠的锁定** - uv.lock 确保所有环境使用相同的依赖版本
3. **统一的项目配置** - pyproject.toml 是现代 Python 项目的标准
4. **更好的虚拟环境管理** - 自动创建和管理 .venv
5. **兼容性** - 完全兼容 pip 和 pyproject.toml 标准

## 常见问题

### Q: 如果我还想使用 pip 怎么办？
A: requirements.txt 文件仍然保留，你可以继续使用 `pip install -r requirements.txt`

### Q: .venv 目录可以删除吗？
A: 可以，uv sync 会自动重新创建

### Q: 如何更新所有依赖？
A: 运行 `uv lock --upgrade` 更新锁定文件，然后 `uv sync`

## 参考资料

- [uv 官方文档](https://github.com/astral-sh/uv)
- [pyproject.toml 规范](https://packaging.python.org/specifications/declaring-project-metadata/)
