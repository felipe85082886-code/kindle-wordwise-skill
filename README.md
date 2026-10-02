# Kindle Word Wise Codex Skill

[English](README.en.md) · [Skill 指令](skills/kindle-wordwise/SKILL.md) · [已验证案例](skills/kindle-wordwise/references/confirmed-case.md)

把英文电子书制作成可在 Kindle 正文上方显示中文生词释义的 USB 版本，由 Codex 代为完成转换、注释检查、封面准备和传输。

这个仓库也记录了一种实际解决的故障：**菜单已经开启 Word Wise，但正文没有提示，右下角只有阅读百分比。** 在已验证的 Paperwhite 5 / 5.19.2 上，原因是缺少首次启用完成标记 `ftuxShown`。补上该标记并**手动重启**后，用户确认中文释义正常显示。

这项修复只在检查证据支持时执行，通常不需要每本书重复处理。其他型号或固件尚未由本案例验证。修复内部设置需要设备已有可用的 SH Integration 等授权访问方式；本 skill 不安装越狱。

## 安装到 Codex

将以下请求发给 Codex，让其使用 skill-installer 安装：

> 从 https://github.com/felipe85082886-code/kindle-wordwise-skill 安装 skills/kindle-wordwise 这个 skill。

也可以手动安装（macOS / Linux）：

```sh
git clone https://github.com/felipe85082886-code/kindle-wordwise-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R kindle-wordwise-skill/skills/kindle-wordwise "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Windows：把仓库中的 `skills/kindle-wordwise` 文件夹复制到 `%USERPROFILE%\.codex\skills\`，或指定的 `CODEX_HOME` 下的 `skills` 目录。已有同名 skill 时，先比较更新内容并备份，再更新。安装后在后续轮次使用。

## 日常使用

准备可转换的英文 EPUB，告诉 Codex：

> 使用 $kindle-wordwise 把这本英文书做成 Kindle 中文生词提示版，保留原文和封面，并代我检查和 USB 传输。

Codex 会：

1. 保留原文件，核对作者、书名、语言、正文与图片。
2. 用 Calibre 制作 AZW3，用 WordDumb 生成对应的 `.kll` 注释。
3. 验证书籍标识、注释位置，以及与现有中文 Word Wise 词库的对应关系。
4. 准备书库封面缩略图，备份后将匹配的文件合并传到 USB 设备。
5. 安全弹出，请你在正文和书库确认实际显示。

优先使用可重排、无 DRM 的英文 EPUB；扫描 PDF 需先 OCR。普通新书制作不要求修改 Kindle 内部设置。Kindle 自带的普通查词词典与 Word Wise 词库不同。这个 USB sidecar 流程需要把书与配套文件一起传入。

## 工具与文件

- 上游依赖：[Calibre](https://calibre-ebook.com/download)、[WordDumb](https://github.com/xxyzz/WordDumb)。本仓库不捆绑它们。
- `inspect_package.py`：只读核对 AZW3、配套注释及可选的原生词库；Python 3.10+，无第三方依赖。
- `extract_kf8.py`：在 Calibre 环境下重建注释使用的正文 bytes。
- `make_cover.py`：生成与最终 ASIN 对应的两个封面缓存；这个可选工具需要 Pillow。
- `device_probe.sh`：通过已有 launcher 读取实际开关、词库清单及相关错误记录。
- `build_first_use_repair.py`：从真实设置快照生成修复和撤销脚本。仅修改一个标记，保留备份，设置变化时拒绝覆盖，要求手动重启。

具体步骤见 [制作流程](skills/kindle-wordwise/references/production.md) 和 [诊断与修复](skills/kindle-wordwise/references/diagnostics.md)。脚本执行权限遵循使用者的 Codex 与设备环境。

## 验证与边界

真实书籍验证：7,016 条注释通过书籍标识、正文位置和中文词库编号检查；用户在设备上确认中文释义出现。封面文件已写入，但该案例的书库封面显示尚未获用户确认。

仓库测试使用自建数据，不需要书籍或 Kindle：

```sh
python3 -m unittest discover -s tests -v
```

测试覆盖正确文件、错误版本、缺少词义编号、错误位置、加密文件、重复设置、修复与精确撤销，以及设置变化后的拒绝覆盖。真实设备与其他固件仍需屏幕验证。

**不发布书籍、亚马逊词库、设备设置、日志、内容目录或固件文件。** 诊断导出和生成的个案修复文件保留在本地私有目录。通用脚本与说明采用 MIT License；上游工具遵循各自许可证。
