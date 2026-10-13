# Ordo · 知序 — 官方发行

此仓库用于公开发布 Ordo 安装包、版本说明和更新清单。应用源码不包含在此仓库中。

- [下载安装包](https://github.com/roverway/ordo-releases/releases)
- [应用更新清单](https://roverway.github.io/ordo-releases/updates.json)

## 发布渠道

正式版和 Beta 分别维护。Beta 可能含尚未稳定的功能，升级前建议备份数据。没有发布的渠道在清单中标记为 `null`。

从 [1.1.0-beta.13](https://github.com/roverway/ordo-releases/releases/tag/v1.1.0-beta.13) 起，应用支持自动和手动检查正式版、Beta 两条发布线。用户确认后交由浏览器下载，安装仍由用户手动完成。

## 安装

Android 下载 universal APK，按系统提示安装；Windows 下载 ZIP，退出旧版后解压运行；Linux 根据 CPU 架构选择 AppImage。安装和替换由用户确认。

Android 新版系统包名为 `com.a40aldev.ordo`，使用固定 Ordo 签名；发行前会核验所有 APK 的包名和证书。

从旧 `com.example.todo` 应用迁移时：先在旧版导出备份，安装新版（可与旧版并存），在新版导入备份并核对任务、项目、标签和提醒。重新确认通知等系统权限及必要的同步配置，数据核对完成后再卸载旧版。旧应用的数据目录不会被新版自动读取。

## 自动更新清单

发布、编辑或删除 Release 后，GitHub Actions 自动部署 Pages。也可以手动运行 Publish Update Feed。清单中包含安装包大小、SHA-256 和下载来源；JSON 不包含访问私有仓库的凭据。

此仓库的工作流只读取本仓库的公开发行内容，不访问私有源码仓库。
