# 微信云函数接入说明

本小程序当前采用：

- 本地前端完成起卦、本卦/变卦分析
- 云函数 `yijingAi` 完成 AI 深度解卦

## 1. 配置云开发环境 ID

编辑 [utils/cloud-config.js](/E:/chowey/miniapp/utils/cloud-config.js:1)：

```js
const CLOUD_ENV_ID = "chowi-d6gxkipu118055650";
```

## 2. 配置云函数密钥

在微信开发者工具中：

1. 打开“云开发”面板
2. 选择你的环境
3. 打开 `yijingAi` 云函数
4. 在云函数环境变量中新增：

`LLM_API_KEY=你的模型密钥`

如果后续需要切模型，也可以把 [cloudfunctions/yijingAi/index.js](/E:/chowey/miniapp/cloudfunctions/yijingAi/index.js:1) 里的：

- `LLM_BASE_URL`
- `LLM_MODEL`

改成新的值。

## 3. 安装并上传云函数

在微信开发者工具中对 `cloudfunctions/yijingAi`：

1. 右键
2. 选择“在终端中打开”
3. 执行 `npm install`
4. 再右键选择“上传并部署：云端安装依赖”

## 4. 本地调试

完成后直接运行小程序页面：

- `起一卦`：本地完成
- `请求 AI 解卦`：走云函数

## 5. 发布说明

这套结构适合正式发布，因为：

- 小程序本身不依赖你本机电脑在线
- 不需要本地反代
- 不需要开放你自己的 Python 服务

后续如果你想继续增强：

- 可以把卦例记录写入云数据库
- 可以把 AI 解读历史保存到用户维度
- 可以加入每日一卦、分享卡片等功能
