# Ordo · 知序 — 官方发行

此仓库用于公开发布 Ordo 安装包、版本说明和更新清单。应用源码不包含在此仓库中。

- [下载安装包](https://github.com/roverway/ordo-releases/releases)
- [应用更新清单](https://roverway.github.io/ordo-releases/updates.json)

## 发布渠道

正式版和 Beta 分别维护。Beta 可能含尚未稳定的功能，升级前建议备份数据。没有发布的渠道在清单中标记为 `null`。

## 安装

Android 下载 universal APK，按系统提示安装；Windows 下载 ZIP，退出旧版后解压运行；Linux 根据 CPU 架构选择 AppImage。安装和替换由用户确认。

历史 Android Debug 签名版本无法覆盖升级到固定 Ordo 签名。请先导出数据备份，再卸载旧版、安装新版并恢复。卸载会删除本地应用数据。

## 自动更新清单

发布、编辑或删除 Release 后，GitHub Actions 自动部署 Pages。也可以手动运行 Publish Update Feed。清单中包含安装包大小、SHA-256 和下载来源；JSON 不包含访问私有仓库的凭据。

此仓库的工作流只读取本仓库的公开发行内容，不访问私有源码仓库。
