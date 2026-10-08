# 成都二手房智能分析与预测系统

基于 Python 的二手房数据分析、价格预测与可视化平台。项目由 Vue 3 前端和 Django REST 后端组成，面向成都二手房数据提供房源浏览、筛选、收藏推荐、价格预测与智能问答等功能。

> 本项目为毕业设计项目，仅用于学习、研究和功能演示。数据与图片请遵循其来源平台的使用规范。

## 项目目标

二手房价格受区域、面积、户型、楼层、装修、建筑类型与市场供需等多种因素共同影响。本项目将房源数据处理、可视化分析、机器学习预测和检索增强问答整合到同一套 Web 系统中，帮助用户从数据角度了解成都二手房市场。

系统输出仅用于学习与研究演示，不构成交易、估值或投资建议。

## 功能

- 房源列表、条件筛选、详情查看和收藏管理
- 基于用户收藏记录的房源推荐
- 区域房价数据分析与可视化
- 多模型房价预测
- 基于 RAG 的房产数据智能问答（可选配置）
- 用户注册、登录与 JWT 鉴权

## 系统架构

```text
房源 CSV / 数据处理脚本
          │
          ├── 数据清洗、字段标准化、地理编码
          │
          ├── Django REST API ────────────── Vue 3 可视化界面
          │        │                                  │
          │        ├── 房源、收藏、推荐、认证          ├── 图表与筛选
          │        ├── 价格预测服务                    └── 预测与问答交互
          │        └── RAG / AI 问答服务
          │
          └── 模型文件与 FAISS 向量索引
```

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Naive UI、ECharts
- 后端：Django、Django REST Framework、Simple JWT
- 数据与模型：Pandas、scikit-learn、XGBoost、FAISS、LangChain

## 数据处理与特征

`backend/data/` 提供原始房源数据、清洗脚本和导入工具。处理流程包括：

1. 统一价格、面积、户型、朝向、楼层、装修、建筑类型等字段格式。
2. 对缺失值和异常值进行清理，并保留区域、地址、图片链接等房源信息。
3. 可选地调用地图地理编码服务补充经纬度；该功能需要自行配置 `AMAP_API_KEY`。
4. 将处理后的 CSV 导入系统，供房源筛选、统计图表、模型训练和 RAG 检索使用。

仓库中的数据仅作为功能演示样本。部署到生产或发布衍生数据前，应先确认数据来源、授权范围与隐私合规性。

## 机器学习价格预测

价格预测模块位于 `backend/prediction/`。系统以区域为单位训练候选回归模型，并使用交叉验证结果选择适合该区域的数据模型；样本不足时会回退到全局 Ridge 回归或区域均价，避免小样本导致不稳定预测。

候选模型包括：

- Ridge 回归：作为稳健的线性基线与小样本回退模型。
- 决策树回归：刻画特征的非线性分段关系。
- 随机森林与梯度提升：降低单一树模型的方差并增强拟合能力。
- XGBoost：在环境安装 `xgboost` 且样本量满足条件时参与比较。

训练过程会记录训练集 MAE、R²、交叉验证 R²，以及测试集 MAE、RMSE、R² 等指标；推理时还会进行合理范围校验，异常预测会回退到区域统计基线。训练结果和模型文件位于 `backend/model_results/`。

> 模型表现受样本量、采集时间、字段质量和区域分布影响。预测结果应被理解为数据驱动的参考值，而不是实际成交价承诺。

## RAG 智能问答

RAG 模块位于 `backend/houserag/`，用于让问答回答尽量基于本地房源数据，而非仅依赖通用语言模型知识。

1. 使用 `CSVLoader` 读取处理后的房源数据。
2. 按固定大小切分文本记录，并通过 HuggingFace Embeddings 生成向量。
3. 使用 FAISS 持久化向量索引，按用户问题检索相关房源片段。
4. 将检索结果与用户问题一并交给 OpenAI 兼容模型接口生成回答。

项目使用 `ChatOpenAI` 作为兼容客户端；配置 `MODELSCOPE_API_KEY`、`MODELSCOPE_BASE_URL` 和 `MODELSCOPE_MODEL_ID` 后可启用模型回答。未配置模型密钥时，房源浏览、可视化和价格预测等功能仍可独立使用。

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

## 主要接口

| 模块 | 示例地址 | 说明 |
| --- | --- | --- |
| 认证与用户 | `/api/auth/` | 注册、登录、JWT、个人资料与用户管理 |
| 房源与收藏 | `/api/listings/houses/` | 房源列表、筛选、详情、收藏与推荐 |
| 价格预测 | `/api/prediction/predict/` | 根据房源特征返回预测总价、单价与模型信息 |
| 模型状态 | `/api/prediction/status/` | 查询已加载模型与预测服务状态 |
| RAG 问答 | `/api/rag/ask/` | 基于向量检索的房源数据问答 |
| AI 助手 | `/api/assistant/chat/` | 通用房产分析辅助问答 |

接口详情可从各应用目录中的 `urls.py`、`serializers.py` 与 `views.py` 查看。

## 可选环境变量

复制 [backend/.env.example](backend/.env.example) 作为本地参考。项目不会自动读取 `.env`；可在启动前通过系统环境变量注入：

```powershell
$env:DJANGO_SECRET_KEY = 'replace-with-a-long-random-secret'
$env:MODELSCOPE_API_KEY = 'your-model-service-key' # 仅 AI 问答功能需要
$env:AMAP_API_KEY = 'your-amap-key'                # 仅数据地理编码脚本需要
```

不要将真实密钥、Cookie、数据库导出或含个人信息的数据提交到 Git。

## 常见问题

**为什么 AI 问答无法使用？**  请确认已在启动后端的同一终端中设置 `MODELSCOPE_API_KEY`，并且网络可访问配置的模型服务地址。

**为什么预测接口返回区域均价？**  这通常表示该区域样本不足、模型文件未加载，或模型预测结果超出合理范围。系统会优先返回可解释且相对稳健的回退结果。

**为什么前端无法请求后端？**  请确认 Django 服务运行在 `127.0.0.1:8000`，而 Vite 开发服务运行在 `127.0.0.1:5137`。

## 安全说明

- 仓库不含模型服务、地图服务或爬虫登录凭据。
- `DJANGO_SECRET_KEY`、`MODELSCOPE_API_KEY` 和 `AMAP_API_KEY` 均应仅通过部署环境配置。
- 若仓库曾提交过密钥，请先在服务商后台作废或轮换该密钥，再重写 Git 历史后公开仓库。

## 许可

当前未附带开源许可证。若计划允许他人复用，请在公开前补充合适的 LICENSE 文件。
