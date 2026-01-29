# K6 接口压测平台

基于 K6 的 API 接口压测平台，支持前端配置、一键执行、实时日志和结果展示。

## 技术栈

- **前端**: Vue 3 + Vite + NaiveUI + TypeScript
- **后端**: Python + FastAPI + SQLAlchemy
- **数据库**: MySQL 8.0
- **压测引擎**: K6

## 功能特性

- ✅ 前端表单配置接口和压测指标
- ✅ 支持多种 HTTP 方法 (GET/POST/PUT/DELETE/PATCH)
- ✅ 支持请求头和请求体配置
- ✅ 支持阶段配置（爬坡模式）
- ✅ 支持阈值配置
- ✅ 一键执行压测
- ✅ WebSocket 实时日志推送
- ✅ 压测结果可视化展示

## 快速开始

### 前置条件

1. **K6**: 确保已安装 K6
   ```bash
   # Windows
   winget install k6 --source winget
   # 或
   choco install k6
   
   # 验证安装
   k6 version
   ```

2. **Python 3.10+**: 确保已安装 Python

3. **Node.js 18+**: 确保已安装 Node.js

4. **MySQL 8.0**: 确保已安装并运行 MySQL

### 数据库初始化

```sql
CREATE DATABASE k6_perftest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档: http://localhost:8000/docs

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问: http://localhost:5173

## 项目结构

```
K6_PerfTest/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置
│   │   ├── database.py        # 数据库连接
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── api/               # API 路由
│   │   ├── services/          # 业务逻辑
│   │   └── websocket/         # WebSocket
│   ├── scripts/               # 生成的 K6 脚本
│   ├── results/               # 执行结果
│   ├── requirements.txt
│   └── .env
├── frontend/                  # 前端项目
│   ├── src/
│   │   ├── App.vue           # 主组件
│   │   ├── components/       # 子组件
│   │   ├── api/              # API 客户端
│   │   ├── types/            # 类型定义
│   │   └── styles/           # 样式
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## API 接口

### 配置管理

- `GET /api/configs` - 获取配置列表
- `POST /api/configs` - 创建配置
- `GET /api/configs/{id}` - 获取单个配置
- `PUT /api/configs/{id}` - 更新配置
- `DELETE /api/configs/{id}` - 删除配置

### 执行记录

- `GET /api/executions` - 获取执行记录列表
- `GET /api/executions/{id}` - 获取单个执行记录

### WebSocket

- `ws://localhost:8000/api/ws/test` - 压测执行 WebSocket

## 使用说明

1. 打开前端页面 http://localhost:5173
2. 在左侧表单中配置压测参数：
   - 配置名称
   - 请求 URL
   - HTTP 方法
   - 请求头
   - 请求体（POST/PUT/PATCH）
   - 虚拟用户数和持续时间
3. 点击「开始压测」按钮
4. 在右侧查看实时日志
5. 测试完成后查看结果展示

## License

MIT
