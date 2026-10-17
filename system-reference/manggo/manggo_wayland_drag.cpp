#include <QApplication>
#include <QMouseEvent>
#include <QWidget>
#include <QWindow>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>

// Local interoperability shim for Manggo 1.1.1's translation header.
// The original header uses QWidget::move, which cannot reposition a Wayland
// toplevel. Request an interactive compositor move on its left-button press.
// Match the exact receiver, so child buttons and text editors are untouched.
bool QApplication::notify(QObject *receiver, QEvent *event) {
    using Notify = bool (*)(QApplication *, QObject *, QEvent *);
    static const auto original = reinterpret_cast<Notify>(
        dlsym(RTLD_NEXT, "_ZN12QApplication6notifyEP7QObjectP6QEvent"));
    if (event->type() == QEvent::MouseButtonPress && receiver->isWidgetType()) {
        auto *widget = static_cast<QWidget *>(receiver);
        auto *mouse = static_cast<QMouseEvent *>(event);
        if (mouse->button() == Qt::LeftButton &&
            widget->objectName() == QStringLiteral("resultTitleBar") &&
            widget->window()->inherits("manggo::ui::windows::TranslationWindow") &&
            QGuiApplication::platformName().startsWith(QStringLiteral("wayland"))) {
            auto *window = widget->window()->windowHandle();
            if (window && window->startSystemMove()) {
                if (std::getenv("MANGGO_DRAG_TRACE"))
                    std::fputs("Manggo drag fix: compositor move accepted\n", stderr);
                event->accept();
                return true;
            }
        }
    }
    return original(this, receiver, event);
}
