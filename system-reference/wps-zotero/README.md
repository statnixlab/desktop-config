# WPS / Zotero 本机兼容参考

这些文件不由默认恢复流程安装。先在目标机器安装 WPS、Zotero 及兼容插件，再合并本机调整。

插件来源为 [danielhluna/WPS-Zotero](https://github.com/danielhluna/WPS-Zotero/tree/fix/zotero7-compatibility)，
固定提交 `83867d199a6ef947b7f7d0cf8ef966388d6e88fe`，安装目录版本为 `wps-zotero_0.2.0`。
`LOCAL-INSTALL.txt` 记录本机验证版本与调整；`LICENSE.txt` 保留上游 GPL-3.0 许可证。

- `proxy.py`、`js/ribbon.js`、`js/i18n.js` 是该版本的本机源文件覆盖项，保留仅由 systemd
  管理代理生命周期、日志写入 `XDG_STATE_HOME/wps-zotero` 及中文界面回退。先取得完整上游
  源码并核对提交，再覆盖对应文件；本目录不是完整插件，也不运行上游安装器。
- `lang.cfg` 保存界面语言。代理用户单元在
  `../user-home/config/systemd/user/wps-zotero-proxy.service`，使用前展开其中的 `@HOME@`，
  并确认 `~/.local/share/Kingsoft/wps/jsaddons/wps-zotero_0.2.0/proxy.py` 已就绪。
- Zotero 启动器仍保留共用 Windows 文献库的挂载和可读写检查，见 `../user-home/bin/zotero`。
  文献库、附件、WPS 文档、插件缓存及账户信息不在此快照中。

本机曾在 WPS 12.1.2.29183 / Zotero 10.0.6 中，用独立临时文献库验证引文与参考文献插入。
此记录不代表其他版本的兼容性；更新插件或办公软件后应重新验证。
