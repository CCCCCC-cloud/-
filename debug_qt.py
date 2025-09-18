import os
import sys

# 启用Qt调试输出
os.environ['QT_DEBUG_PLUGINS'] = '1'
os.environ['QT_LOGGING_RULES'] = '*.debug=true'

# 明确设置插件路径
import PyQt5
plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
os.environ['QT_PLUGIN_PATH'] = plugin_path

print(f"Python: {sys.version}")
print(f"PyQt5 路径: {PyQt5.__file__}")
print(f"插件路径: {plugin_path}")
print(f"平台插件: {os.path.join(plugin_path, 'platforms')}")

try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("✓ Qt初始化成功!")
except Exception as e:
    print(f"✗ 错误详情: {e}")
    import traceback
    traceback.print_exc()