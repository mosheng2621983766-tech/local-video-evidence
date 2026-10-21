# Local Video Evidence

本地视频取证小工具：镜头切分、关键帧导出、离线语音转写，以及逐帧时间戳检查。

A small CLI toolkit for local shot detection, keyframe export, offline speech transcription, and video timestamp comparison. Initial public version: **0.1.0**.

## 功能 / Features

- `analyze.py scenes`: 调用 PySceneDetect 自适应检测，输出镜头 CSV 和每个镜头的代表帧。
- `analyze.py speech`: 调用 MLX Whisper，使用你已经下载的本地模型，输出字幕、文字和时间戳。
- `video_check.py`: 用 ffprobe 检查画幅、帧数、逐帧时间戳、音轨数量和旋转信息，可比较两个视频。
- 已存在的输出目录或报告不会被覆盖；处理记录写入 `execution.json`。

这些脚本是第三方工具的轻量封装，不是新的检测或语音模型。自动识别结果需要人工复核。时间戳一致不代表人物动作、画面或声音内容一致。

## 安装 / Installation

需要 Python 3.9+ 和系统可用的 FFmpeg / ffprobe。语音模块额外要求 Apple Silicon Mac；镜头与时间戳脚本未在 Windows/Linux 实机验证。建议使用 Python 3.11+ 的独立环境安装依赖：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-scenes.txt
# 仅在 Apple Silicon Mac 上需要语音转写时安装：
python -m pip install -r requirements-speech.txt
```

请从 [FFmpeg 官方站点](https://ffmpeg.org/download.html) 选择适合系统的安装方式，并确保 `ffmpeg`、`ffprobe` 位于 PATH 中。模型须按 [MLX Whisper 上游文档](https://github.com/ml-explore/mlx-examples/tree/main/whisper) 自行准备；脚本不会自动下载权重。`--model-dir` 指向包含 `config.json` 和 `weights.npz` 或 `weights.safetensors` 的模型文件夹。

## 使用 / Usage

```sh
python analyze.py scenes input.mp4 results/scenes-001
python analyze.py speech input.mp4 results/speech-001 --model-dir /path/to/whisper-model --language zh
python video_check.py input.mp4 --report results/source.json
python video_check.py input.mp4 --output-video processed.mp4 --report results/comparison.json
```

可用 `--scenedetect-bin`、`--whisper-bin`、`--ffprobe-bin` 指定可执行文件路径。语音语言可设为 `auto`。每次使用新的输出目录或报告文件名。

`video_check.py` 的退出码表示报告是否成功生成。比较是否通过请读取报告中的 `checks.timing_pass` 和 `checks.same_dimensions`；比较失败仍会成功生成报告。相对时间戳允许 1 毫秒误差，忽略两个视频的整体起始时间偏移。单帧视频不支持时间间隔判断。

## 可复现示例 / Synthetic demo

以下测试只生成纯色视频，不需要私人素材：

```sh
ffmpeg -f lavfi -i color=red:s=320x240:r=25:d=2 -f lavfi -i color=blue:s=320x240:r=25:d=2 -filter_complex '[0:v][1:v]concat=n=2:v=1:a=0' -c:v mpeg4 demo.mp4
python analyze.py scenes demo.mp4 results/demo-scenes
python video_check.py demo.mp4 --output-video demo.mp4 --report results/demo-check.json
python -m unittest -v test_tools
```

预期：两个各 2 秒的镜头、总计 100 帧、6 张代表帧；同一文件的时间戳比较通过。实际验证范围见 [VALIDATION.md](VALIDATION.md)。

## 隐私、限制和依赖

脚本处理本地文件，不调用付费 API。离线转写设置 Hugging Face 离线环境变量，仍需提前安装依赖和准备本地模型。执行记录包含输入和工具的本机绝对路径，字幕也可能包含私人信息；公开分享报告前请自行检查。

长视频检查会读取所有帧时间戳，因此耗时与内存随视频长度增长。自动切分可能漏检渐变或误判闪光。语音识别可能产生错字或幻觉；不能把转写当作已经核实的原话。

依赖：[PySceneDetect](https://github.com/Breakthrough/PySceneDetect)、[MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)、[FFmpeg](https://ffmpeg.org/)。这些工具和模型遵循各自许可证，本仓库不捆绑它们的代码、二进制文件或权重。

## 贡献 / Contributing

欢迎提交可复现的问题和修复。请附操作系统、Python/依赖版本、命令、预期与实际结果；尽量使用合成或获授权的素材，并去掉私人路径与内容。不要上传凭据或客户资料。

## License

本仓库自有代码与文档采用 [MIT License](LICENSE)。由个人视频工作流整理，使用 Codex 辅助开发。项目处于初始阶段，不声称已有外部用户、下载量或广泛采用。
