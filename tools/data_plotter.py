#!/usr/bin/env python
"""
实时数据绘图工具
显示力矩、位置等传感器数据的实时曲线
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
import numpy as np
from collections import deque
from datetime import datetime
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 设置pyqtgraph
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class DataBuffer:
    """数据缓冲区"""

    def __init__(self, max_length=1000):
        self.max_length = max_length
        self.time_buffer = deque(maxlen=max_length)
        self.force_buffer = deque(maxlen=max_length)
        self.position_buffer = deque(maxlen=max_length)
        self.velocity_buffer = deque(maxlen=max_length)
        self.force_gradient_buffer = deque(maxlen=max_length)

        self.start_time = None

    def add_data(self, force=None, position=None, velocity=None):
        """添加数据点"""
        current_time = datetime.now()

        if self.start_time is None:
            self.start_time = current_time

        # 计算相对时间（秒）
        elapsed_time = (current_time - self.start_time).total_seconds()
        self.time_buffer.append(elapsed_time)

        # 添加数据
        if force is not None:
            self.force_buffer.append(force)

            # 计算力梯度
            if len(self.force_buffer) > 1:
                gradient = (self.force_buffer[-1] - self.force_buffer[-2]) * 50  # 50Hz
                self.force_gradient_buffer.append(gradient)
            else:
                self.force_gradient_buffer.append(0)

        if position is not None:
            self.position_buffer.append(position)

        if velocity is not None:
            self.velocity_buffer.append(velocity)

    def get_data(self, data_type):
        """获取指定类型的数据"""
        if data_type == 'force':
            return list(self.time_buffer), list(self.force_buffer)
        elif data_type == 'position':
            return list(self.time_buffer), list(self.position_buffer)
        elif data_type == 'velocity':
            return list(self.time_buffer), list(self.velocity_buffer)
        elif data_type == 'gradient':
            return list(self.time_buffer), list(self.force_gradient_buffer)
        else:
            return [], []

    def clear(self):
        """清空缓冲区"""
        self.time_buffer.clear()
        self.force_buffer.clear()
        self.position_buffer.clear()
        self.velocity_buffer.clear()
        self.force_gradient_buffer.clear()
        self.start_time = None


class DataSimulator(QThread):
    """虚假数据（用于测试）目前没有连接 可在图形化界面操作"""
    data_generated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.time_step = 0

    def run(self):
        """生成模拟数据"""
        self.is_running = True

        while self.is_running:
            # 生成模拟数据
            t = self.time_step * 0.02  # 50Hz

            # 模拟抓取过程的力曲线
            if t < 2:  # 接近阶段
                force = 0
            elif t < 3:  # 接触阶段
                force = 0.2 * (t - 2)
            elif t < 5:  # 抓取阶段
                force = 0.2 + 1.8 * (1 - np.exp(-2 * (t - 3)))
            else:  # 保持阶段
                force = 2.0 + 0.1 * np.sin(2 * np.pi * t)

            # 添加噪声
            force += np.random.normal(0, 0.02)

            # 位置数据
            if t < 2:
                position = 100 - 30 * t
            else:
                position = 40

            position += np.random.normal(0, 0.5)

            # 速度数据
            if t < 2:
                velocity = -30
            else:
                velocity = 0

            velocity += np.random.normal(0, 2)

            # 发送数据
            data = {
                'force': force,
                'position': position,
                'velocity': velocity,
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3]
            }

            self.data_generated.emit(data)

            self.time_step += 1
            self.msleep(20)  # 50Hz更新率

    def stop(self):
        self.is_running = False


class RealTimePlotter(QMainWindow):
    """实时数据绘图主窗口"""

    def __init__(self):
        super().__init__()
        self.data_buffer = DataBuffer(max_length=1000)
        self.data_simulator = DataSimulator()

        # 绘图定时器
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)

        # 统计信息
        self.stats = {
            'force_max': 0,
            'force_min': 0,
            'force_avg': 0,
            'position_current': 0
        }

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("实时数据监控 - AdaptiveGraspControl")
        self.setGeometry(100, 100, 1400, 900)

        # 主Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # 开始/停止按钮
        self.start_btn = QAction("▶ 开始", self)
        self.start_btn.triggered.connect(self.toggle_plotting)
        toolbar.addAction(self.start_btn)

        # 清除按钮
        clear_action = QAction("清除", self)
        clear_action.triggered.connect(self.clear_data)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # 模拟数据开关
        self.simulate_checkbox = QCheckBox("模拟数据")
        self.simulate_checkbox.setChecked(True)
        toolbar.addWidget(self.simulate_checkbox)

        toolbar.addSeparator()

        # 显示选项
        toolbar.addWidget(QLabel("显示选项:"))

        self.show_force_checkbox = QCheckBox("力矩")
        self.show_force_checkbox.setChecked(True)
        toolbar.addWidget(self.show_force_checkbox)

        self.show_position_checkbox = QCheckBox("位置")
        self.show_position_checkbox.setChecked(True)
        toolbar.addWidget(self.show_position_checkbox)

        self.show_velocity_checkbox = QCheckBox("速度")
        self.show_velocity_checkbox.setChecked(False)
        toolbar.addWidget(self.show_velocity_checkbox)

        self.show_gradient_checkbox = QCheckBox("力梯度")
        self.show_gradient_checkbox.setChecked(False)
        toolbar.addWidget(self.show_gradient_checkbox)

        # 创建绘图区域
        self.create_plots()
        main_layout.addWidget(self.graphics_layout_widget)

        # 统计信息面板
        stats_group = QGroupBox("统计信息")
        stats_layout = QHBoxLayout(stats_group)

        self.stats_labels = {}
        stats_items = [
            ('力矩最大值', 'force_max', 'N·m'),
            ('力矩最小值', 'force_min', 'N·m'),
            ('力矩平均值', 'force_avg', 'N·m'),
            ('当前位置', 'position_current', '度'),
            ('数据点数', 'data_points', ''),
            ('运行时间', 'run_time', 's')
        ]

        for label_text, key, unit in stats_items:
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(QLabel(label_text))
            value_label = QLabel("0.00")
            value_label.setFont(QFont("Arial", 14, QFont.Bold))
            value_label.setStyleSheet("color: #2196F3;")
            layout.addWidget(value_label)
            if unit:
                layout.addWidget(QLabel(unit))
            self.stats_labels[key] = value_label
            stats_layout.addWidget(container)

        main_layout.addWidget(stats_group)

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 连接信号
        self.data_simulator.data_generated.connect(self.on_data_received)

    def create_plots(self):
        """创建绘图区域"""
        self.graphics_layout_widget = pg.GraphicsLayoutWidget()

        # 力矩图
        self.force_plot = self.graphics_layout_widget.addPlot(row=0, col=0, title="力矩 (N·m)")
        self.force_plot.setLabel('left', '力矩', units='N·m')
        self.force_plot.setLabel('bottom', '时间', units='s')
        self.force_plot.showGrid(x=True, y=True, alpha=0.3)
        self.force_curve = self.force_plot.plot(pen=pg.mkPen(color='b', width=2))

        # 添加目标线
        self.force_target_line = pg.InfiniteLine(
            pos=2.5,
            angle=0,
            pen=pg.mkPen(color='r', width=1, style=Qt.DashLine),
            label='目标: 2.5 N·m',
            labelOpts={'position': 0.95, 'color': 'r'}
        )
        self.force_plot.addItem(self.force_target_line)

        # 位置图
        self.position_plot = self.graphics_layout_widget.addPlot(row=1, col=0, title="位置 (度)")
        self.position_plot.setLabel('left', '位置', units='度')
        self.position_plot.setLabel('bottom', '时间', units='s')
        self.position_plot.showGrid(x=True, y=True, alpha=0.3)
        self.position_curve = self.position_plot.plot(pen=pg.mkPen(color='g', width=2))

        # 速度图
        self.velocity_plot = self.graphics_layout_widget.addPlot(row=2, col=0, title="速度 (RPM)")
        self.velocity_plot.setLabel('left', '速度', units='RPM')
        self.velocity_plot.setLabel('bottom', '时间', units='s')
        self.velocity_plot.showGrid(x=True, y=True, alpha=0.3)
        self.velocity_curve = self.velocity_plot.plot(pen=pg.mkPen(color='m', width=2))

        # 力梯度图
        self.gradient_plot = self.graphics_layout_widget.addPlot(row=3, col=0, title="力梯度 (N·m/s)")
        self.gradient_plot.setLabel('left', '力梯度', units='N·m/s')
        self.gradient_plot.setLabel('bottom', '时间', units='s')
        self.gradient_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gradient_curve = self.gradient_plot.plot(pen=pg.mkPen(color='orange', width=2))

        # 链接X轴
        self.position_plot.setXLink(self.force_plot)
        self.velocity_plot.setXLink(self.force_plot)
        self.gradient_plot.setXLink(self.force_plot)

    def toggle_plotting(self):
        """开始/停止绘图"""
        if self.start_btn.text() == "▶ 开始":
            self.start_btn.setText("■ 停止")
            self.start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

            # 启动模拟器
            if self.simulate_checkbox.isChecked():
                self.data_simulator.start()

            # 启动绘图定时器
            self.plot_timer.start(50)  # 20Hz更新率

            self.status_bar.showMessage("正在记录数据...")
        else:
            self.start_btn.setText("▶ 开始")
            self.start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

            # 停止模拟器
            self.data_simulator.stop()

            # 停止绘图定时器
            self.plot_timer.stop()

            self.status_bar.showMessage("已停止")

    def on_data_received(self, data):
        """接收数据"""
        self.data_buffer.add_data(
            force=data.get('force'),
            position=data.get('position'),
            velocity=data.get('velocity')
        )

    def update_plots(self):
        """更新绘图"""
        # 更新力矩图
        if self.show_force_checkbox.isChecked():
            time_data, force_data = self.data_buffer.get_data('force')
            if time_data:
                self.force_curve.setData(time_data, force_data)
                self.force_plot.setVisible(True)

                # 更新统计
                self.stats['force_max'] = max(force_data) if force_data else 0
                self.stats['force_min'] = min(force_data) if force_data else 0
                self.stats['force_avg'] = np.mean(force_data) if force_data else 0
        else:
            self.force_plot.setVisible(False)

        # 更新位置图
        if self.show_position_checkbox.isChecked():
            time_data, position_data = self.data_buffer.get_data('position')
            if time_data:
                self.position_curve.setData(time_data, position_data)
                self.position_plot.setVisible(True)

                # 更新统计
                if position_data:
                    self.stats['position_current'] = position_data[-1]
        else:
            self.position_plot.setVisible(False)

        # 更新速度图
        if self.show_velocity_checkbox.isChecked():
            time_data, velocity_data = self.data_buffer.get_data('velocity')
            if time_data:
                self.velocity_curve.setData(time_data, velocity_data)
                self.velocity_plot.setVisible(True)
        else:
            self.velocity_plot.setVisible(False)

        # 更新力梯度图
        if self.show_gradient_checkbox.isChecked():
            time_data, gradient_data = self.data_buffer.get_data('gradient')
            if time_data:
                self.gradient_curve.setData(time_data, gradient_data)
                self.gradient_plot.setVisible(True)
        else:
            self.gradient_plot.setVisible(False)

        # 更新统计标签
        self.update_statistics()

    def update_statistics(self):
        """更新统计信息"""
        self.stats_labels['force_max'].setText(f"{self.stats.get('force_max', 0):.2f}")
        self.stats_labels['force_min'].setText(f"{self.stats.get('force_min', 0):.2f}")
        self.stats_labels['force_avg'].setText(f"{self.stats.get('force_avg', 0):.2f}")
        self.stats_labels['position_current'].setText(f"{self.stats.get('position_current', 0):.1f}")

        # 数据点数
        data_points = len(self.data_buffer.time_buffer)
        self.stats_labels['data_points'].setText(str(data_points))

        # 运行时间
        if self.data_buffer.time_buffer:
            run_time = self.data_buffer.time_buffer[-1]
            self.stats_labels['run_time'].setText(f"{run_time:.1f}")

    def clear_data(self):
        """清除数据"""
        self.data_buffer.clear()
        self.force_curve.clear()
        self.position_curve.clear()
        self.velocity_curve.clear()
        self.gradient_curve.clear()

        # 重置统计
        for key in self.stats:
            self.stats[key] = 0
        self.update_statistics()

        self.status_bar.showMessage("数据已清除")

    def closeEvent(self, event):
        """关闭事件"""
        self.data_simulator.stop()
        self.plot_timer.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    plotter = RealTimePlotter()
    plotter.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()