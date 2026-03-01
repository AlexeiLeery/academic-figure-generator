# VPS 部署（Docker + GitHub 更新）

## 1) VPS 准备

- 安装 Docker / Docker Compose（按你的发行版官方文档即可）
- 开放端口：`80`（可选 `443`）

## 2) 首次部署

```bash
git clone <你的仓库地址> academic-figure-generator
cd academic-figure-generator

# 复制 docker 环境变量模板
cp .env.docker.example .env

# 编辑 .env：至少改 POSTGRES_PASSWORD / MINIO_SECRET_KEY / SECRET_KEY / ENCRYPTION_MASTER_KEY
```

启动：

```bash
docker compose up -d --build
```

访问：
- Web: `http://<VPS_IP>/`
- API: `http://<VPS_IP>/api/v1/docs`（如果 DEBUG=true 才开放）

## 3) 常用运维

查看日志：

```bash
docker compose logs -f --tail=200 backend
docker compose logs -f --tail=200 celery-worker
docker compose logs -f --tail=200 minio
```

重启服务：

```bash
docker compose restart
```

## 4) 通过 GitHub 快速更新

每次你 push 到 GitHub 后，在 VPS 上执行：

```bash
cd academic-figure-generator
git pull
docker compose up -d --build
```

说明：
- 这会重新 build 前端（在 `nginx` 镜像里多阶段构建）并重启相关容器。
- 数据（Postgres/Redis/MinIO）都在 Docker volume 里，不会因为更新丢失。

