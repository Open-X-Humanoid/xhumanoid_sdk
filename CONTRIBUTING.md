# 贡献指南

感谢您对本项目的关注！本文档提供参与具身天工 3.0 SDK 示例项目贡献的指南。

## 如何贡献

### 报告 Bug

1. 先查看已有 [Issues](https://github.com/Open-X-Humanoid/xhumanoid_sdk/issues)，避免重复提交。
2. 使用 **Bug Report** 模板创建新 Issue。
3. 请包含：
   - 复现步骤
   - 期望行为与实际行为
   - 环境信息（操作系统、ROS 2 版本、硬件型号）
   - 相关日志或截图

### 功能建议

1. 使用 **Feature Request** 模板提交 Issue。
2. 描述使用场景和期望行为。

### 提交代码

1. **Fork** 本仓库。
2. 从 `main` 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 按照下方编码规范进行开发。
4. 在目标平台上 **测试** 您的修改。
5. 使用清晰的提交信息 **Commit**：
   ```bash
   git commit -m "feat: 为单关节控制增加新的控制模式"
   ```
6. **Push** 并向 `main` 提交 Pull Request。

## 编码规范

### 通用

- 保持代码简洁、可读、结构清晰。
- 每个示例应同时提供 Python 和 C++ 版本。
- 遵循已有示例的包目录结构。

### Python

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 代码风格。
- 适当使用类型注解。
- 统一使用 `rclpy` API。

### C++

- 遵循 [ROS 2 C++ 代码风格指南](https://docs.ros.org/en/rolling/The-ROS2-Project/Contributing/Code-Style-Language-Versions.html)。
- 使用 C++17 特性。
- 统一使用 `rclcpp` API。

### Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

| 前缀 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修复 |
| `docs:` | 仅文档修改 |
| `refactor:` | 代码重构 |
| `test:` | 增加或更新测试 |
| `chore:` | 构建、CI 或工具链变更 |

### 文档

- 修改功能时同步更新对应示例的 `README.md`。
- 包含参数说明和使用示例。
- 记录预期输出和常见错误。

## Pull Request 规范

- 每个 PR 对应一个功能或修复。
- 关联相关 Issue（如 `Closes #42`）。
- PR 描述需说明 **改了什么** 和 **为什么改**。
- 所有 CI 检查通过后方可合并。

## 行为准则

请保持尊重和建设性的态度。我们致力于为所有人提供一个友好和包容的社区环境。

## 许可证

参与贡献即表示您同意您的贡献将按照 [Apache License 2.0](LICENSE) 进行授权。
