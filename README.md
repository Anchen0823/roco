# roco · 洛克王国属性工具

洛克王国手游相关的属性克制计算器、精灵与技能资料，以及用于更新精灵索引的 Python 脚本。

## 打开计算器

完整下载仓库后，用浏览器打开 [属性克制计算器.html](属性克制计算器.html)。页面通过相对路径加载 `data/pet-index.js` 和本地图标，请保留目录结构。

页面支持选择属性或精灵查看克制关系，并可按攻击技能系别计算倍率；本系加成的规则以页面说明为准。

也可以从仓库根目录启动本地静态服务，再在浏览器目录页中打开计算器：

```sh
python -m http.server 8000 --bind 127.0.0.1
```

访问 `http://127.0.0.1:8000`。仅使用计算器无需安装 Python 依赖或运行更新脚本。

## 内容导航

| 入口 | 内容 |
| --- | --- |
| [属性克制表.md](属性克制表.md) | 属性关系参考 |
| [data/pets.md](data/pets.md) | 精灵索引、来源与整理日期 |
| [data/技能图鉴.md](data/技能图鉴.md) | 技能资料 |
| [data/pet-index.js](data/pet-index.js) | 计算器加载的浏览器索引 |
| [assets/type-icons/manifest.json](assets/type-icons/manifest.json) | 图标来源记录 |
| [tools/update_pet_index.py](tools/update_pet_index.py) | 从 BWIKI 页面或本地 HTML 整理精灵资料 |

## 更新精灵资料

使用 Python 3，安装脚本依赖 `lxml` 后，在仓库根目录执行：

```sh
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python -m pip install lxml
.\.venv\Scripts\python tools/update_pet_index.py
# 已保存 Wiki HTML 时可以离线解析
.\.venv\Scripts\python tools/update_pet_index.py --input saved-page.html --out-dir data
```

Linux / macOS 将上述解释器路径替换为 `.venv/bin/python`。不传 `--input` 时脚本会联网获取页面，并覆盖输出目录中的精灵 JSON、CSV、Markdown 文件。

**脚本目前不会生成 `data/pet-index.js`，也不会更新技能数据或图标。** 更新资料后，还需单独同步计算器使用的浏览器索引并检查页面。

## 数据来源

已收录的精灵资料记录了 BWIKI 来源、页面更新日期和本地整理日期，见 [data/pets.md](data/pets.md)。其中标注的文本授权为 CC BY-NC-SA 4.0；图标来源及相关说明见 manifest。这里保留原有归属记录，不将文本授权扩展为整个仓库或全部图片的授权声明。

资料为仓库内的历史快照，更新脚本依赖源页面结构；当前游戏内容与本地数据可能不同。
