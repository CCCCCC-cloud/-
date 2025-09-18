#!/usr/bin/env python
"""
串口监视器工具
实时显示串口数据，支持HEX和ASCII显示
"""

import os
import sys

# 修复Qt平台插件问题
if sys.platform == "win32":
    os.environ['QT_DEBUG_PLUGINS'] = '1'
    import PyQt5
    plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = plugin_path

# 现在导入其他模块
import time
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import struct
class SerialWorker(QThread):
    """串口工作线程"""
    data_received = pyqtSignal(bytes, str)  # 数据, 时间戳
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_running = False

    def connect_port(self, port, baudrate):
        """连接串口"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            return True
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False

    def disconnect_port(self):
        """断开串口"""
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

    def run(self):
        """工作线程主循环"""
        self.is_running = True

        while self.is_running:
            if self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        self.data_received.emit(data, timestamp)
                except Exception as e:
                    self.error_occurred.emit(str(e))

            self.msleep(10)  # 10ms轮询

    def send_data(self, data):
        """发送数据"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(data)
                return True
            except Exception as e:
                self.error_occurred.emit(str(e))
                return False
        return False

    def stop(self):
        """停止线程"""
        self.is_running = False


class SerialMonitor(QMainWindow):
    """串口监视器主窗口"""

    def __init__(self):
        super().__init__()
        self.serial_worker = SerialWorker()
        self.rx_count = 0
        self.tx_count = 0
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("串口监视器 - AdaptiveGraspControl")
        self.setGeometry(100, 100, 1200, 800)

        # 主Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 端口选择
        self.port_combo = QComboBox()
        self.refresh_ports()
        toolbar_layout.addWidget(QLabel("端口:"))
        toolbar_layout.addWidget(self.port_combo)

        # 波特率选择
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '230400'])
        self.baud_combo.setCurrentText('115200')
        toolbar_layout.addWidget(QLabel("波特率:"))
        toolbar_layout.addWidget(self.baud_combo)

        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        toolbar_layout.addWidget(self.connect_btn)

        # 刷新按钮
        refresh_btn = QPushButton("刷新端口")
        refresh_btn.clicked.connect(self.refresh_ports)
        toolbar_layout.addWidget(refresh_btn)

        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear_display)
        toolbar_layout.addWidget(clear_btn)

        toolbar_layout.addStretch()

        # 显示格式
        self.hex_checkbox = QCheckBox("HEX显示")
        self.hex_checkbox.setChecked(True)
        toolbar_layout.addWidget(self.hex_checkbox)

        # 自动滚动
        self.autoscroll_checkbox = QCheckBox("自动滚动")
        self.autoscroll_checkbox.setChecked(True)
        toolbar_layout.addWidget(self.autoscroll_checkbox)

        main_layout.addLayout(toolbar_layout)

        # 分割器
        splitter = QSplitter(Qt.Vertical)

        # 接收区域
        rx_group = QGroupBox("接收数据")
        rx_layout = QVBoxLayout(rx_group)

        self.rx_text = QTextEdit()
        self.rx_text.setReadOnly(True)
        self.rx_text.setFont(QFont("Consolas", 10))
        rx_layout.addWidget(self.rx_text)

        splitter.addWidget(rx_group)

        # 发送区域
        tx_group = QGroupBox("发送数据")
        tx_layout = QVBoxLayout(tx_group)

        # 发送输入框和按钮
        tx_input_layout = QHBoxLayout()

        self.tx_input = QLineEdit()
        self.tx_input.setFont(QFont("Consolas", 10))
        self.tx_input.returnPressed.connect(self.send_data)
        tx_input_layout.addWidget(self.tx_input)

        self.hex_send_checkbox = QCheckBox("HEX发送")
        self.hex_send_checkbox.setChecked(True)
        tx_input_layout.addWidget(self.hex_send_checkbox)

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_data)
        tx_input_layout.addWidget(send_btn)

        tx_layout.addLayout(tx_input_layout)

        # 快速命令按钮
        quick_cmd_layout = QHBoxLayout()

        # 握手包
        handshake_btn = QPushButton("握手包")
        handshake_btn.clicked.connect(lambda: self.send_quick_cmd("AA01000000000010026B55"))
        quick_cmd_layout.addWidget(handshake_btn)

        # 心跳包
        heartbeat_btn = QPushButton("心跳包")
        heartbeat_btn.clicked.connect(lambda: self.send_quick_cmd("AA0190000000000100A255"))
        quick_cmd_layout.addWidget(heartbeat_btn)

        # 紧急停止
        estop_btn = QPushButton("紧急停止")
        estop_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; }")
        estop_btn.clicked.connect(lambda: self.send_quick_cmd("AA01500000000001005255"))
        quick_cmd_layout.addWidget(estop_btn)

        quick_cmd_layout.addStretch()
        tx_layout.addLayout(quick_cmd_layout)

        # 发送历史
        self.tx_history = QTextEdit()
        self.tx_history.setReadOnly(True)
        self.tx_history.setFont(QFont("Consolas", 10))
        self.tx_history.setMaximumHeight(100)
        tx_layout.addWidget(QLabel("发送历史:"))
        tx_layout.addWidget(self.tx_history)

        splitter.addWidget(tx_group)
        splitter.setSizes([500, 300])

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = self.statusBar()
        self.update_status("未连接")

        # 连接信号
        self.serial_worker.data_received.connect(self.on_data_received)
        self.serial_worker.error_occurred.connect(self.on_error)

    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

    def toggle_connection(self):
        """切换连接状态"""
        if self.connect_btn.text() == "连接":
            port_text = self.port_combo.currentText()
            if not port_text:
                QMessageBox.warning(self, "警告", "请选择串口!")
                return

            port = port_text.split(" - ")[0]
            baudrate = int(self.baud_combo.currentText())

            if self.serial_worker.connect_port(port, baudrate):
                self.serial_worker.start()
                self.connect_btn.setText("断开")
                self.connect_btn.setStyleSheet("QPushButton { background-color: #44ff44; }")
                self.update_status(f"已连接: {port} @ {baudrate}")

                # 禁用端口和波特率选择
                self.port_combo.setEnabled(False)
                self.baud_combo.setEnabled(False)
            else:
                QMessageBox.critical(self, "错误", "无法打开串口!")
        else:
            self.serial_worker.stop()
            self.serial_worker.wait()
            self.serial_worker.disconnect_port()
            self.connect_btn.setText("连接")
            self.connect_btn.setStyleSheet("")
            self.update_status("未连接")

            # 启用端口和波特率选择
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)

    def on_data_received(self, data, timestamp):
        """处理接收到的数据"""
        self.rx_count += len(data)

        # 格式化显示
        if self.hex_checkbox.isChecked():
            # HEX显示
            hex_str = ' '.join([f'{b:02X}' for b in data])
            display_text = f"[{timestamp}] ← {hex_str}"

            # 尝试解析协议
            if len(data) > 10 and data[0] == 0xAA and data[-1] == 0x55:
                packet_type = data[2]
                display_text += f" (Type: 0x{packet_type:02X})"
        else:
            # ASCII显示
            try:
                ascii_str = data.decode('utf-8', errors='replace')
                display_text = f"[{timestamp}] ← {ascii_str}"
            except:
                display_text = f"[{timestamp}] ← [Binary Data]"

        # 添加到显示
        self.rx_text.append(display_text)

        # 自动滚动
        if self.autoscroll_checkbox.isChecked():
            self.rx_text.moveCursor(QTextCursor.End)

        # 更新状态
        self.update_status(f"已连接 | RX: {self.rx_count} bytes | TX: {self.tx_count} bytes")

    def send_data(self):
        """发送数据"""
        text = self.tx_input.text()
        if not text:
            return

        try:
            if self.hex_send_checkbox.isChecked():
                # HEX发送
                text = text.replace(' ', '')
                data = bytes.fromhex(text)
            else:
                # ASCII发送
                data = text.encode('utf-8')

            if self.serial_worker.send_data(data):
                self.tx_count += len(data)

                # 显示发送历史
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                if self.hex_send_checkbox.isChecked():
                    display = ' '.join([f'{b:02X}' for b in data])
                else:
                    display = text

                self.tx_history.append(f"[{timestamp}] → {display}")

                # 清空输入
                self.tx_input.clear()

                # 更新状态
                self.update_status(f"已连接 | RX: {self.rx_count} bytes | TX: {self.tx_count} bytes")
            else:
                QMessageBox.warning(self, "警告", "串口未连接!")
        except ValueError:
            QMessageBox.warning(self, "警告", "无效的HEX格式!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def send_quick_cmd(self, hex_cmd):
        """发送快速命令"""
        self.tx_input.setText(hex_cmd)
        self.hex_send_checkbox.setChecked(True)
        self.send_data()

    def clear_display(self):
        """清除显示"""
        self.rx_text.clear()
        self.tx_history.clear()
        self.rx_count = 0
        self.tx_count = 0

    def on_error(self, error_msg):
        """处理错误"""
        QMessageBox.critical(self, "串口错误", error_msg)

    def update_status(self, msg):
        """更新状态栏"""
        self.status_bar.showMessage(msg)

    def closeEvent(self, event):
        """关闭事件"""
        if self.connect_btn.text() == "断开":
            self.toggle_connection()
        event.accept()


def main():
    app = QApplication(sys.argv)
    monitor = SerialMonitor()
    monitor.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()