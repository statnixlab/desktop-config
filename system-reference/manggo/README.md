# Manggo 翻译窗口拖动兼容

`manggo_wayland_drag.cpp` 是本机编写的独立 Qt 兼容层，只在 Wayland 下拦截
`TranslationWindow` 中名为 `resultTitleBar` 的空白区域左键按下事件，调用
`QWindow::startSystemMove()`；按钮、文本编辑及其他窗口不改变。
已在官方 Manggo 1.1.1 的自带 Qt 库上验证。原应用二进制没有被修改。

在安装了 Manggo 与 Qt 6 开发头文件的 CachyOS / Arch 上可编译到用户目录：

```sh
mkdir -p "$HOME/.local/lib/manggo-drag-fix"
c++ -std=c++17 -O2 -Wall -Wextra -DQT_NO_VERSION_TAGGING -fPIC -shared \
  system-reference/manggo/manggo_wayland_drag.cpp \
  -o "$HOME/.local/lib/manggo-drag-fix/libmanggo-wayland-drag.so" \
  $(pkg-config --cflags Qt6Widgets) -L/usr/lib/manggo \
  -l:libQt6Widgets.so.6 -l:libQt6Gui.so.6 -l:libQt6Core.so.6 -ldl
```

`system-reference/user-home/bin/Manggo` 是配套启动器，安装时将其中 `@HOME@` 替换成
目标用户的绝对 Home 路径，并放到 `~/.local/bin/Manggo`。对应的 `.desktop` 文件
位于同一参考树的 `config/autostart/` 和 `share/applications/`，也需要展开占位符。
原配置应先备份，退出 Manggo 后再使用新入口启动。
启动器校验官方应用哈希；升级后不会盲目加载旧补丁。不要把 `LD_PRELOAD` 设置成全局变量。
