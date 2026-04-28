---
name: code-generator
description: 代码生成规范和最佳实践，用于生成高质量、可维护的代码
metadata:
  author: one-person-company
  version: "1.0"
---

## 代码生成指南

当生成代码时，遵循以下原则：

### 1. 代码质量标准
- **可读性优先**: 使用清晰的变量名和函数名
- **注释适度**: 只在复杂逻辑处添加注释，代码应自解释
- **错误处理**: 所有可能失败的操作都要有错误处理
- **类型安全**: 使用类型注解（Python）或类型声明（TypeScript/Java）

### 2. 文件组织
- 每个文件只负责一个主要功能
- 相关的类/函数放在同一个模块
- 使用清晰的目录结构

### 3. 代码风格
- **Python**: 遵循 PEP 8，使用 Black 格式化
- **Java**: 遵循 Google Java Style Guide
- **JavaScript/TypeScript**: 使用 Prettier + ESLint

### 4. 安全性
- 永远不要硬编码敏感信息（API Key、密码等）
- 验证所有外部输入
- 使用参数化查询防止 SQL 注入

### 5. 性能考虑
- 避免 N+1 查询问题
- 合理使用缓存
- 大数据量处理使用流式处理或分页

## 生成代码时的输出格式

生成的代码应包含：
1. 文件路径（相对于项目根目录）
2. 完整的代码内容
3. 必要的依赖说明
4. 简短的使用说明

示例：
```
文件: src/services/user_service.py

代码:
[完整代码内容]

依赖: 
- pydantic>=2.0.0
- sqlalchemy>=2.0.0

使用说明:
[简短说明]
```
