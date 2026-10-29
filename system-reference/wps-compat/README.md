# 已确认的 WPS 显示与工具栏修复

`source.json` 固定 XWayland Satellite 上游提交和 `xwayland-wps.patch` 校验值。
该补丁是相对原始上游的完整差异，包含光标、最小化／最大化、WPS 工具栏分类和对应测试。
不需要按历史顺序叠加多个试验补丁。

`sticky-toolbar.c` 是文字和表格的选区工具栏常驻 hook。`sticky-toolbar.json` 记录已验证的
WPS 版本与库哈希。启动器另做哈希检查，hook 自身也验证指令字节；不匹配时不应用。

配套用户单元、启动器和新机器安装步骤见 `../app-compat/README.md`。
已废弃的 Expose 自动重绘试验不包含在本目录。

XWayland Satellite 上游许可证为 MPL-2.0，完整许可证与源码从固定上游获取。
