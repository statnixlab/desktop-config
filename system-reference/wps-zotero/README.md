# WPS / Zotero 本机兼容参考

这些文件不由默认恢复流程安装。先在目标机器安装 WPS、Zotero 及兼容插件，再合并本机调整。

插件来源为 [danielhluna/WPS-Zotero](https://github.com/danielhluna/WPS-Zotero/tree/fix/zotero7-compatibility)，
固定提交 `83867d199a6ef947b7f7d0cf8ef966388d6e88fe`，安装目录版本为 `wps-zotero_0.2.0`。
`LOCAL-INSTALL.txt` 记录本机验证版本与调整；`LICENSE.txt` 保留上游 GPL-3.0 许可证。

- `proxy.py`、`main.js` 和 `js/` 下文件是该版本的本机源文件覆盖项，保留仅由 systemd
  管理代理生命周期、日志写入 `XDG_STATE_HOME/wps-zotero` 及中文界面回退。先取得完整上游
  源码并核对提交，再覆盖对应文件；本目录不是完整插件，也不运行上游安装器。
- `lang.cfg` 保存界面语言。代理用户单元在
  `../user-home/config/systemd/user/wps-zotero-proxy.service`，使用前展开其中的 `@HOME@`，
  并确认 `~/.local/share/Kingsoft/wps/jsaddons/wps-zotero_0.2.0/proxy.py` 已就绪。
- Zotero 启动器仍保留共用 Windows 文献库的挂载和可读写检查，见 `../user-home/bin/zotero`。
  文献库、附件、WPS 文档、插件缓存及账户信息不在此快照中。

本机曾在 WPS 12.1.2.29183 / Zotero 10.0.6 中，用独立临时文献库验证引文与参考文献插入。
此记录不代表其他版本的兼容性；更新插件或办公软件后应重新验证。

## 在另一台电脑准备快捷引用适配

原版 Easier Citation 0.5.11 与 WPS 插件来源均固定并校验。只发布无认证信息的源码和补丁，
准备程序为每台电脑生成新的配对标记，写入配套 WPS bridge 和 XPI；不会复制本机的标记。

```bash
python3 scripts/prepare-wps-zotero.py \
  --output-dir "$HOME/.local/share/desktop-config/wps-zotero-prepared"
# 保存工作并退出 WPS、Zotero 后：
python3 scripts/install-wps-zotero.py \
  "$HOME/.local/share/desktop-config/wps-zotero-prepared" --apply
```

然后打开 Zotero：**工具 → 附加组件 → 齿轮 → 从文件安装附加组件**，选择准备目录中的
`easier-citation-wps-linux-0.5.11.1.xpi`。必须使用同一准备目录的一对文件。
本地适配版删除了官方自动更新地址，避免升级覆盖适配；其他 Zotero 插件更新不受影响。
更换版本前应重新验证。已有准备目录不会被覆盖；重新配对时指定新目录。

WPS 安装器只更新 `wps-zotero` 这一项注册，保留其他插件；原文件和注册表备份到
`~/.local/state/desktop-config-backups/wps-zotero-*`。不运行上游全量安装器，不迁移 Zotero
profile、文献库、附件、账户或 Windows 分区挂载设置。

使用方式：打开 WPS 文档并定位光标，在 Zotero 文献列表选中一篇或多篇文献，在英文输入
状态按单引号。仅适配快捷插入；未适配拖拽或 Windows Word 的文档名称探测。
首次选择引用格式的对话框仍需本人完成。目标机文献库位置由本人配置。

已在当前版本验证单篇、多选、重复请求保护及文档切换保护。配套两个 JavaScript 测试可运行：

```bash
node system-reference/wps-zotero/easy-cite/test-bridge.cjs
node system-reference/wps-zotero/easy-cite/test-wps-bridge.cjs
```
