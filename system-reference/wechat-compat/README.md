# 微信独立显示与文件剪贴板兼容

`source.json` 固定公开上游、完整源码补丁和校验值。补丁保留已有聊天兼容修复，并新增
`XWS_FILE_CLIPBOARD_EXE` 指定进程的文件格式视图。默认未设置时行为不变。

当 Wayland 剪贴板同时提供 `x-special/gnome-copied-files` 和 `text/uri-list`，且请求者的
XRes PID 对应指定可执行文件时，TARGETS 只返回文件 URL 类型。原始 Wayland offer 和数据
保持不变，X11 属性长度由服务端正常生成，普通文本和其他客户端不受此规则影响。
不会接管或重写全局剪贴板；不使用 LD_PRELOAD。

对应独立服务是 `xwayland-wechat.service`，显示为 `:4`，与 QQ／AB 的 `:2` 分离。
完整安装见 `../app-compat/README.md`。在本机完成了用户粘贴验证；测试为 88 项库测试、
37 项隔离集成测试通过，包括同一会话复制文件后再复制新文字。

上游许可证 MPL-2.0 随固定源码保留。只保存源码和配置，不包含剪贴板内容、聊天记录或账号。
