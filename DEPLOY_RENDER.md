# Render 部署说明

当前项目已经适合直接作为 Render Web Service 部署：

- `api.py` 提供 FastAPI 应用
- `/` 返回网页入口
- `/health` 可用于健康检查

## 1. 上传到 Git 仓库

先把 `E:\chowey` 推到 GitHub 或 GitLab。

## 2. 在 Render 创建 Web Service

在 Render 后台：

1. New
2. Web Service
3. 连接你的代码仓库
4. 选择本项目

如果 Render 识别到 [render.yaml](/E:/chowey/render.yaml:1)，它会自动带出配置。

关键配置如下：

- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

## 3. 配置环境变量

在 Render 的 Environment 页面设置：

- `LLM_API_KEY`: 你的模型 key
- `LLM_BASE_URL`: `https://wgooold.cn`
- `LLM_MODEL`: `Qwen3.6-27B`

## 4. 绑定自定义域名

部署成功后：

1. 打开 Render 服务
2. 进入 Settings -> Custom Domains
3. 添加你的域名
4. 按 Render 提示去你的域名 DNS 后台添加记录

通常：

- 子域名：加 `CNAME`
- 根域名：按 Render 提供的 `A` / `ALIAS` 记录配置

## 5. 验证

部署完成后可测试：

- `https://你的域名/`
- `https://你的域名/health`

## 6. 注意事项

- 如果你的“免费域名”DNS 功能不完整，可能无法成功绑定。
- `LLM_API_KEY` 不要写进代码仓库。
- 当前模型响应偏慢，正式环境建议后续换更快的模型或缩短提示词。
