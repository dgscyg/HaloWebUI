# HaloWebUI

![GitHub stars](https://img.shields.io/github/stars/ztx888/HaloWebUI?style=social)
![GitHub forks](https://img.shields.io/github/forks/ztx888/HaloWebUI?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/ztx888/HaloWebUI?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/ztx888/HaloWebUI)
![GitHub language count](https://img.shields.io/github/languages/count/ztx888/HaloWebUI)
![GitHub top language](https://img.shields.io/github/languages/top/ztx888/HaloWebUI)
![GitHub last commit](https://img.shields.io/github/last-commit/ztx888/HaloWebUI?color=red)

**HaloWebUI 是一个功能丰富、可扩展、用户友好的自托管 AI 平台，支持完全离线运行。** 兼容 **Ollama** 和 **OpenAI 兼容 API** 等多种 LLM 运行时，内置 RAG 推理引擎，是强大的 AI 部署方案。

## 核心特性

- **极简部署**：通过 Docker 一键安装，支持 `:ollama` 和 `:cuda` 标签镜像。

- **多 API 集成**：无缝对接 OpenAI 兼容 API，可连接 LMStudio、GroqCloud、Mistral、OpenRouter 等服务。

- **精细权限管理**：支持管理员创建详细的用户角色和权限分组，确保安全的多用户环境。

- **响应式设计**：在桌面、笔记本和移动设备上均有流畅体验，支持 PWA 离线访问。

- **Markdown 和 LaTeX**：完整支持 Markdown 和 LaTeX 渲染，丰富对话内容展示。

- **语音/视频通话**：集成免提语音和视频通话功能，打造动态交互的对话体验。

- **模型构建器**：通过 Web 界面轻松创建 Ollama 模型，支持自定义角色/Agent 和聊天元素。

- **Python 函数调用**：内置代码编辑器，支持自带纯 Python 函数（BYOF），无缝集成 LLM 工具调用。

- **本地 RAG**：支持检索增强生成，将文档直接加载到对话中，或通过 `#` 命令引用文档库。

- **联网搜索**：支持 SearXNG、Google PSE、Brave Search、DuckDuckGo、Tavily 等搜索引擎，将搜索结果注入对话。

- **网页浏览**：使用 `#` 加 URL 将网页内容整合到对话中。

- **图像生成**：集成 AUTOMATIC1111 API、ComfyUI（本地）和 OpenAI DALL-E（外部）。

- **多模型并行对话**：同时与多个模型交互，充分利用不同模型的优势。

- **多语言支持**：支持国际化（i18n），可使用多种语言界面。

- **Pipeline 插件系统**：通过 Pipeline 框架集成自定义逻辑和 Python 库，支持函数调用、速率限制、用量监控、实时翻译等。

## 安装方式

### Docker 安装（推荐）

> [!NOTE]
> 请确保 Docker 命令中包含 `-v open-webui:/app/backend/data` 以正确挂载数据库，防止数据丢失。

> [!TIP]
> 如需 CUDA 加速，请先安装 [Nvidia CUDA container toolkit](https://docs.nvidia.com/dgx/nvidia-container-runtime-upgrade/)。

**Ollama 在本机：**

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:main
```

**Ollama 在其他服务器：**

```bash
docker run -d -p 3000:8080 -e OLLAMA_BASE_URL=https://example.com -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:main
```

**GPU 加速：**

```bash
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:cuda
```

**仅使用 OpenAI API：**

```bash
docker run -d -p 3000:8080 -e OPENAI_API_KEY=your_secret_key -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:main
```

**内置 Ollama（GPU）：**

```bash
docker run -d -p 3000:8080 --gpus=all -v ollama:/root/.ollama -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:ollama
```

**内置 Ollama（仅 CPU）：**

```bash
docker run -d -p 3000:8080 -v ollama:/root/.ollama -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/ztx888/halowebui:ollama
```

安装完成后访问 [http://localhost:3000](http://localhost:3000) 即可使用。

### Python pip 安装

需要 **Python 3.11**：

```bash
pip install open-webui
open-webui serve
```

访问 [http://localhost:8080](http://localhost:8080)。

### 常见问题

如果遇到连接问题（容器无法访问 Ollama 服务器），可使用 `--network=host`：

```bash
docker run -d --network=host -v open-webui:/app/backend/data -e OLLAMA_BASE_URL=http://127.0.0.1:11434 --name open-webui --restart always ghcr.io/ztx888/halowebui:main
```

### 更新 Docker 版本

```bash
docker run --rm --volume /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower --run-once open-webui
```

### 离线模式

```bash
export HF_HUB_OFFLINE=1
```

## 许可证

本项目基于 [BSD-3-Clause License](LICENSE) 许可协议。

## Star History

<a href="https://star-history.com/#ztx888/HaloWebUI&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=ztx888/HaloWebUI&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=ztx888/HaloWebUI&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=ztx888/HaloWebUI&type=Date" />
  </picture>
</a>
