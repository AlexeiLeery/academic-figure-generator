# 开源 | AI 学术论文配图生成器 —— 上传论文一键出图

大家好！分享一个我做的开源项目：**Academic Figure Generator**，一个 AI 驱动的学术论文配图生成平台。

## 它能做什么？

简单来说：**上传论文 → AI 自动分析 → 一键生成科研配图**

写论文时最头疼的就是配图了，手动画费时费力，AI 画又不知道怎么描述。这个工具把整个流程串起来了：

1. 上传你的论文（PDF / DOCX / TXT）
2. Claude AI 自动阅读论文，理解内容，生成专业的配图 Prompt
3. 你可以直接用，也可以微调 Prompt
4. 一键生成高质量配图，支持 1K/2K/4K 多种分辨率

## 主要特性

- **智能 Prompt** — Claude 分析论文内容，生成贴合语境的配图描述
- **多分辨率** — 1K / 2K / 4K，16:9 / 4:3 / 1:1 等比例自由选择
- **50+ 学术配色** — 预设多种期刊风格配色，含色盲友好方案，也支持自定义
- **图生图编辑** — 对已有图片用文字指令二次修改
- **项目管理** — 按论文/项目组织所有配图
- **实时进度** — SSE 流式推送生成状态，不用干等
- **BYOK** — 可以用自己的 API Key，也可以用平台统一配置的 Key
- **Linux DO 登录** — 支持 Linux DO OAuth 一键登录
- **积分充值** — 接入了 Linux DO EasyPay，用积分自助充值余额

## 技术栈

| | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy (Async) + Celery |
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS |
| 数据库 | PostgreSQL 16 + Redis 7 |
| 存储 | MinIO |
| AI | Claude API + NanoBanana API |
| 部署 | Docker Compose 一键部署 |

## 部署超简单

```bash
git clone https://github.com/LigphiDonk/academic-figure-generator.git
cd academic-figure-generator
cp .env.docker.example .env
# 编辑 .env 填入密码和密钥
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

5 分钟搞定，所有服务（PostgreSQL、Redis、MinIO、后端、前端、Celery）一条命令全部拉起。

## 截图预览

> （建议在这里贴几张截图：项目工作台、配图生成过程、管理后台等）

## 开源地址

GitHub：https://github.com/你的用户名/academic-figure-generator

欢迎 Star、Fork、提 Issue！

---

如果你也在写论文被配图折磨，欢迎试试。有问题可以直接在帖子里回复，或者去 GitHub 提 Issue。
