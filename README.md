# 成都二手房智能分析与预测系统

基于 Python 的二手房数据分析、价格预测与可视化平台。项目由 Vue 3 前端和 Django REST 后端组成，面向成都二手房数据提供房源浏览、筛选、收藏推荐、价格预测与智能问答等功能。

> 本项目为毕业设计项目，仅用于学习、研究和功能演示。数据与图片请遵循其来源平台的使用规范。

## 功能

- 房源列表、条件筛选、详情查看和收藏管理
- 基于用户收藏记录的房源推荐
- 区域房价数据分析与可视化
- 多模型房价预测
- 基于 RAG 的房产数据智能问答（可选配置）
- 用户注册、登录与 JWT 鉴权

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Naive UI、ECharts
- 后端：Django、Django REST Framework、Simple JWT
- 数据与模型：Pandas、scikit-learn、XGBoost、FAISS、LangChain

## 目录

```text
.
├── frontend/                  # Vue 3 前端
├── backend/
│   ├── second_house_analysis/ # Django 项目配置
│   ├── listings/              # 房源与收藏
│   ├── prediction/            # 价格预测
│   ├── assistant/             # AI 问答接口
│   ├── houserag/              # RAG 问答逻辑
│   └── data/                  # 数据处理与导入脚本
└── README.md
```

## 本地运行

### 1. 启动后端

建议使用 Python 3.10 或更高版本，并在虚拟环境中安装依赖：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter pandas numpy scikit-learn xgboost joblib requests lxml sqlalchemy openai langchain-community langchain-core langchain-openai langchain-huggingface langchain-text-splitters faiss-cpu
python manage.py migrate
python manage.py runserver
```

后端默认运行在 `http://127.0.0.1:8000`。

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端开发服务器默认地址为 `http://127.0.0.1:5137`，并会将 `/api` 与 `/media` 请求代理到后端。

## 可选环境变量

复制 [backend/.env.example](backend/.env.example) 作为本地参考。项目不会自动读取 `.env`；可在启动前通过系统环境变量注入：

```powershell
$env:DJANGO_SECRET_KEY = 'replace-with-a-long-random-secret'
$env:MODELSCOPE_API_KEY = 'your-model-service-key' # 仅 AI 问答功能需要
$env:AMAP_API_KEY = 'your-amap-key'                # 仅数据地理编码脚本需要
```

不要将真实密钥、Cookie、数据库导出或含个人信息的数据提交到 Git。

## 安全说明

- 仓库不含模型服务、地图服务或爬虫登录凭据。
- `DJANGO_SECRET_KEY`、`MODELSCOPE_API_KEY` 和 `AMAP_API_KEY` 均应仅通过部署环境配置。
- 若仓库曾提交过密钥，请先在服务商后台作废或轮换该密钥，再重写 Git 历史后公开仓库。

## 许可

当前未附带开源许可证。若计划允许他人复用，请在公开前补充合适的 LICENSE 文件。
