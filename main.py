"""步进电机控制主程序"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
import serial.tools.list_ports
import re
from serial import Serial

from stepper.commands.move import Enable, Move
from stepper.commands.get import GetSysStatus
from stepper.stepper_core.parameters import PositionParams, DeviceParams
from stepper.stepper_core.configs import Direction, Speed, Acceleration, PulseCount, AbsoluteFlag, Address
from stepper.device import Device

import control
from motor_config import MotorConfig


class MotorController(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = control.Ui_super_student_clap()
        self.ui.setupUi(self)

        # 初始化变量
        self.serial = None
        self.devices = []
        self.motors = []
        self.config = MotorConfig()

        # 初始化串口列表
        self._refresh_ports()

    def _refresh_ports(self):
        """刷新串口列表"""
        self.ui.chuankou.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.chuankou.addItem(f"{port.device} - {port.description}")

    def on_dakaichuankou_clicked(self):
        """打开串口"""
        # 解析串口号
        match = re.search(r'COM\d+', self.ui.chuankou.currentText())
        if not match:
            QMessageBox.warning(self, "错误", "无效的串口")
            return

        port = match.group()
        baudrate = int(self.ui.botelv.currentText())
        motor_count = int(self.ui.dianjishu.currentText())

        try:
            # 打开串口
            self.serial = Serial(port, baudrate, timeout=0.1)

            # 创建设备
            self.devices = []
            self.motors = []
            for i in range(motor_count):
                device_params = DeviceParams(
                    serial_connection=self.serial,
                    address=Address(0x01 + i)
                )
                device = Device(device_params=device_params)
                motor = self.config.get_motor_config(i)

                self.devices.append(device)
                self.motors.append(motor)

            # 更新界面
            self.ui.dakaichuankou.setEnabled(False)
            self.ui.chuankou.setEnabled(False)
            self.ui.botelv.setEnabled(False)
            self.ui.dianjishu.setEnabled(False)

            # 读取初始角度
            self._update_angles()

            QMessageBox.information(self, "成功", "串口打开成功")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"串口打开失败: {str(e)}")

    def on_guanbichuankou_clicked(self):
        """关闭串口"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()

            self.devices.clear()
            self.motors.clear()

            # 恢复界面
            self.ui.dakaichuankou.setEnabled(True)
            self.ui.chuankou.setEnabled(True)
            self.ui.botelv.setEnabled(True)
            self.ui.dianjishu.setEnabled(True)

            self._refresh_ports()
            QMessageBox.information(self, "成功", "串口已关闭")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"关闭失败: {str(e)}")

    def on_kaishi_clicked(self):
        """开始运动"""
        displays = [
            self.ui.xianshijiaodu1, self.ui.xianshijiaodu2, self.ui.xianshijiaodu3,
            self.ui.xianshijiaodu4, self.ui.xianshijiaodu5, self.ui.xianshijiaodu6
        ]
        directions = [self.ui.fangxiang1, self.ui.fangxiang2, self.ui.fangxiang3,
                      self.ui.fangxiang4, self.ui.fangxiang5, self.ui.fangxiang6]
        speeds = [self.ui.sudu1, self.ui.sudu2, self.ui.sudu3,
                  self.ui.sudu4, self.ui.sudu5, self.ui.sudu6]
        accels = [self.ui.jiasudu1, self.ui.jiasudu2, self.ui.jiasudu3,
                  self.ui.jiasudu4, self.ui.jiasudu5, self.ui.jiasudu6]
        angles = [self.ui.jiaodu1, self.ui.jiaodu2, self.ui.jiaodu3,
                  self.ui.jiaodu4, self.ui.jiaodu5, self.ui.jiaodu6]

        for i in range(len(self.devices)):
            try:
                motor = self.motors[i]
                direction = directions[i].currentText()
                speed = speeds[i].value()
                accel = accels[i].value()
                angle = angles[i].value()

                # 计算脉冲数
                pulse = angle / 360 * motor.pulse_per_rev

                # 使能电机
                Enable(device=self.devices[i]).status

                # 创建运动参数
                if direction == "CW":
                    params = PositionParams(
                        direction=Direction.CW,
                        speed=Speed(speed),
                        acceleration=Acceleration(accel),
                        pulse_count=PulseCount(pulse),
                        absolute=AbsoluteFlag.RELATIVE
                    )
                elif direction == "CCW":
                    params = PositionParams(
                        direction=Direction.CCW,
                        speed=Speed(speed),
                        acceleration=Acceleration(accel),
                        pulse_count=PulseCount(pulse),
                        absolute=AbsoluteFlag.RELATIVE
                    )
                else:  # 逆解
                    status = GetSysStatus(device=self.devices[i]).raw_data.data_dict
                    current_deg = status.get('stepper_real_time_position (deg)') / motor.divisor

                    if current_deg <= angle:
                        dir_val = Direction.CW
                    else:
                        dir_val = Direction.CCW

                    pulse = abs(current_deg - angle) / 360 * motor.pulse_per_rev
                    params = PositionParams(
                        direction=dir_val,
                        speed=Speed(speed),
                        acceleration=Acceleration(accel),
                        pulse_count=PulseCount(pulse),
                        absolute=AbsoluteFlag.RELATIVE
                    )

                # 执行运动
                Move(device=self.devices[i], params=params).status

                # 更新显示
                status = GetSysStatus(device=self.devices[i]).raw_data.data_dict
                target_deg = status.get('stepper_target_position (deg)') / motor.divisor
                displays[i].setText(f'{target_deg:.2f}°')

            except Exception as e:
                QMessageBox.warning(self, "警告", f"电机{i + 1}运动失败: {str(e)}")

    def on_stop_clicked(self):
        """停止运动"""
        for i, device in enumerate(self.devices):
            try:
                Enable(device=device).status
                params = PositionParams(
                    direction=Direction.CW,
                    speed=Speed(0),
                    acceleration=Acceleration(0),
                    pulse_count=PulseCount(0),
                    absolute=AbsoluteFlag.RELATIVE
                )
                Move(device=device, params=params).status
            except Exception as e:
                print(f"电机{i + 1}停止失败: {str(e)}")

        self._update_angles()

    def on_huiling_clicked(self):
        """回零"""
        displays = [
            self.ui.xianshijiaodu1, self.ui.xianshijiaodu2, self.ui.xianshijiaodu3,
            self.ui.xianshijiaodu4, self.ui.xianshijiaodu5, self.ui.xianshijiaodu6
        ]

        for i, device in enumerate(self.devices):
            try:
                Enable(device=device).status
                params = PositionParams(
                    direction=Direction.CW,
                    speed=Speed(100),
                    acceleration=Acceleration(0),
                    pulse_count=PulseCount(0),
                    absolute=AbsoluteFlag.ABSOLUTE
                )
                Move(device=device, params=params).status

                motor = self.motors[i]
                status = GetSysStatus(device=device).raw_data.data_dict
                target_deg = status.get('stepper_target_position (deg)') / motor.divisor
                displays[i].setText(f'{target_deg:.2f}°')

            except Exception as e:
                QMessageBox.warning(self, "警告", f"电机{i + 1}回零失败: {str(e)}")

    def _update_angles(self):
        """更新角度显示"""
        displays = [
            self.ui.xianshijiaodu1, self.ui.xianshijiaodu2, self.ui.xianshijiaodu3,
            self.ui.xianshijiaodu4, self.ui.xianshijiaodu5, self.ui.xianshijiaodu6
        ]

        for i, device in enumerate(self.devices):
            try:
                motor = self.motors[i]
                status = GetSysStatus(device=device).raw_data.data_dict
                current_deg = status.get('stepper_real_time_position (deg)') / motor.divisor
                displays[i].setText(f'{current_deg:.2f}°')
            except:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorController()
    window.show()
    sys.exit(app.exec())