# 中文 presentation 运行说明

本目录保留严格 10 页的中文参考版本；正式交付与发布入口已经是 `slides.md` 英文版。中文版本不再维护独立的 Live Dash 演示。

## 演示前准备

在项目根目录重新导出可审计的静态数据：

```bash
uv run retail-rfm export-presentation \
  --csv "resource/Online Retail.csv" \
  --db artifacts/retail_rfm.sqlite \
  --output-dir presentation/public/static-demo
```

启动中文参考版：

```bash
cd presentation
pnpm install --frozen-lockfile
pnpm dev:zh
```

打开 `http://localhost:3030/`。第 8 页与英文终稿一样，直接使用浏览器静态交互版，不依赖 Dash、SQLite 或 localhost iframe。

## 第 8 页一分钟路径

1. 保持 `3D`，旋转一次模型空间。
2. 点击小窗内 `Customer 13777`。
3. 指出 `R=1`、`F=33`、`Net M=£25,748.35`、41 张记录 invoice 和 8 张取消。
4. 静态版本支持 3D、R–F/R–M/F–M 和 13777；左侧 slides 已展示四群画像，因此没有重复的 Profiles 按钮。

## 构建与导出

```bash
pnpm notes:zh
pnpm build:zh
pnpm export:zh
```

输出：

- `dist/zh/`：浏览器版；
- `dist/online-retail-rfm.zh-CN.pdf`：严格 10 页 PDF；
- `dist/speaker-notes.zh-CN.md`：中文逐页讲稿。

PDF 不运行 iframe，而使用 `public/images/slide8-demo.png` 的已验证静态图。

## 本地验收

当 Slidev 运行时：

```bash
pnpm smoke:browser
```

测试覆盖静态 WebGL、13777、三种二维切片、两个目标分辨率、标题姓名和远程请求。所有前端资源均来自本地，不加载 CDN 或在线字体。
