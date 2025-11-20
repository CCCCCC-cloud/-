import sys
import traceback
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import Slot
import control
from stepper.commands.move import Enable, Move
from stepper.stepper_core.parameters import PositionParams
from stepper.stepper_core.configs import (
    Direction, Speed,
    Acceleration, PulseCount, AbsoluteFlag
)
from motorclass import Motor
from stepper.commands.get import GetSysStatus
import serial.tools.list_ports
import re
from serial import Serial
from stepper.device import Device
from stepper.stepper_core.parameters import DeviceParams
from stepper.stepper_core.configs import Address

motormax=6
motors=[]
devices = []
xianshi=[]
Devices=[]

class Mywindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui= control.Ui_super_student_clap()
        self.ui.setupUi(self)
        self.chuankou = None
        self.botelv = None
        self.dianjishu = None
        self.serial = None
        self.serial_isopen=False
        try:
            self.ui.chuankou.clear()
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.ui.chuankou.addItem(f"{port.device} - {port.description}")
        except:
            print("更新串口失败")
    @Slot()#设备地址分配，串口打开（打开串口键）
    def on_dakaichuankou_clicked(self):
        global xianshi
        xianshi = [self.ui.xianshijiaodu1, self.ui.xianshijiaodu2, self.ui.xianshijiaodu3, self.ui.xianshijiaodu4,
                    self.ui.xianshijiaodu5, self.ui.xianshijiaodu6]
        match=re.search(r'COM\d+',self.ui.chuankou.currentText())
        self.chuankou=match.group()
        self.botelv=int(self.ui.botelv.currentText())
        self.dianjishu=int(self.ui.dianjishu.currentText())
        try:
            self.serial = Serial(self.chuankou, self.botelv, timeout=0.1)
            self.ui.dakaichuankou.setText("串口已打开")
            self.ui.guanbichuankou.setText('关闭串口')
            #  获取地址数量（或地址列表）
            self.ui.chuankou.setEnabled(False)
            self.ui.botelv.setEnabled(False)
            self.ui.dianjishu.setEnabled(False)
            self.serial_isopen=True
            self.ui.dakaichuankou.setEnabled(False)
        except:
            if self.serial_isopen==False:
                self.ui.dakaichuankou.setText("串口打开失败")
                self.ui.guanbichuankou.setText('关闭串口')

            else:
                self.ui.dakaichuankou.setText('串口已打开')
                self.ui.guanbichuankou.setText('关闭串口')
        try:
            addresses = [0x01 + i for i in range(self.dianjishu)]  # 生成连续地址，如0x01、0x02、0x03...
            #  动态创建device对象并存储到列表
            global devices,motors,Devices
            for addr in addresses:
                # 逐个创建device，配置不同的地址
                device = DeviceParams(
                    serial_connection=self.serial,
                    address=Address(addr)
                )
                Device1 = Device(
                     device_params=device
                 )
                devices.append(device)
                Devices.append(Device1)
                motor=Motor()
                motors.append(motor)
        except:
            print("分配设备地址失败")
            print(traceback.format_exc())
        try:
            for num in range(self.dianjishu):
                if num == 0:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 30:.10f}°')
                elif num == 1:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 50:.10f}°')
                else:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 30:.10f}°')
        except:
            print("设备角度获取失败")

    @Slot()
    def on_guanbichuankou_clicked(self):
        try:
            global devices,Devices
            devices=[]
            Devices=[]
        except:
            print("设备地址释放失败")
        try:
            self.serial.close()
            self.serial_isopen=False
            self.ui.guanbichuankou.setText('串口已关闭')
            self.ui.chuankou.setEnabled(True)
            self.ui.botelv.setEnabled(True)
            self.ui.dianjishu.setEnabled(True)
            self.ui.dakaichuankou.setText('打开串口')
            self.ui.dakaichuankou.setEnabled(True)
        except:
            print("串口关闭失败")
        self.ui.chuankou.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.chuankou.addItem(f"{port.device} - {port.description}")

    @Slot()#停止所有运动（停止工作键）
    def on_stop_clicked(self):
        try:
            self.dianjishu = int(self.ui.dianjishu.currentText())
            for num in range(self.dianjishu):
                Enable(device=devices[num]).status
                params = PositionParams(
                    direction=Direction.CW,
                    speed=Speed(0),
                    acceleration=Acceleration(0),
                    pulse_count=PulseCount(0),
                    absolute=AbsoluteFlag.RELATIVE
                )
        except:
            print('位置参数分配失败')
        try:
            Move(device=devices[num], params=params).status
        except:
            print("停止失败")
        try:
            for num in range(self.dianjishu):
                if num == 0:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_real_time_position (deg)') / 30 :.10f}°')
                elif num == 1:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_real_time_position (deg)') / 50:.10f}°')
                else:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_real_time_position (deg)') / 30:.10f}°')
        except:
            print("设备角度获取失败")
            print(traceback.format_exc())
    @Slot()#运动控制（开始工作键）
    def on_kaishi_clicked(self):
        fangxiang=[self.ui.fangxiang1,self.ui.fangxiang2,self.ui.fangxiang3,self.ui.fangxiang4,self.ui.fangxiang5,self.ui.fangxiang6]
        sudu=[self.ui.sudu1,self.ui.sudu2,self.ui.sudu3,self.ui.sudu4,self.ui.sudu5,self.ui.sudu6]
        jiasudu=[self.ui.jiasudu1,self.ui.jiasudu2,self.ui.jiasudu3,self.ui.jiasudu4,self.ui.jiasudu5,self.ui.jiasudu6]
        jiaodu=[self.ui.jiaodu1,self.ui.jiaodu2,self.ui.jiaodu3,self.ui.jiaodu4,self.ui.jiaodu5,self.ui.jiaodu6]
        pulse=[jiaodu[0].value()/360*96000,jiaodu[1].value()/360*160000,jiaodu[2].value()/360*96000,jiaodu[3].value()/360*96000,jiaodu[4].value()/360*96000,jiaodu[5].value()]
        global motors
        for num in range(self.dianjishu):
            try:
                motors[num].fangxiang=fangxiang[num].currentText()
                motors[num].sudu=sudu[num].value()
                motors[num].jiasudu=jiasudu[num].value()
                motors[num].jiaodu=jiaodu[num].value()

                if motors[num].fangxiang=='CW':
                    Enable(device=devices[num]).status
                    params = PositionParams(
                        direction=Direction.CW,
                        speed=Speed(motors[num].sudu),
                        acceleration=Acceleration(motors[num].jiasudu),
                        pulse_count=PulseCount(pulse[num]),
                        absolute=AbsoluteFlag.RELATIVE
                    )
                    # Move motor
                    Move(device=devices[num], params=params).status

                elif motors[num].fangxiang =='CCW':
                    Enable(device=devices[num]).status
                    params = PositionParams(
                        direction=Direction.CCW,
                        speed=Speed(motors[num].sudu),
                        acceleration=Acceleration(motors[num].jiasudu),
                        pulse_count=PulseCount(pulse[num]),
                        absolute=AbsoluteFlag.RELATIVE
                    )
                    # Move motor
                    Move(device=devices[num], params=params).status

                elif motors[num].fangxiang=='逆解':
                    Enable(device=devices[num]).status
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    if num==1:
                        motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                        if motors[num].recode.get('stepper_real_time_position (deg)') / 50 - jiaodu[
                            num].value() <= 0:
                            params = PositionParams(
                                direction=Direction.CW,
                                speed=Speed(motors[num].sudu),
                                acceleration=Acceleration(motors[num].jiasudu),
                                pulse_count=PulseCount(abs(motors[num].recode.get(
                                    'stepper_real_time_position (deg)') / 50 - jiaodu[num].value()) / 360 * 160000),
                                absolute=AbsoluteFlag.RELATIVE
                            )
                        else:
                            params = PositionParams(
                                direction=Direction.CCW,
                                speed=Speed(motors[num].sudu),
                                acceleration=Acceleration(motors[num].jiasudu),
                                pulse_count=PulseCount(abs(motors[num].recode.get(
                                    'stepper_real_time_position (deg)') / 50 - jiaodu[num].value()) / 360 * 160000),
                                absolute=AbsoluteFlag.RELATIVE
                            )
                    else:
                        motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                        if motors[num].recode.get('stepper_real_time_position (deg)') / 30 - jiaodu[
                            num].value() <= 0:
                            params = PositionParams(
                                direction=Direction.CW,
                                speed=Speed(motors[num].sudu),
                                acceleration=Acceleration(motors[num].jiasudu),
                                pulse_count=PulseCount(abs(motors[num].recode.get(
                                    'stepper_real_time_position (deg)') / 30 - jiaodu[num].value()) / 360 * 96000),
                                absolute=AbsoluteFlag.RELATIVE
                            )
                        else:
                            params = PositionParams(
                                direction=Direction.CCW,
                                speed=Speed(motors[num].sudu),
                                acceleration=Acceleration(motors[num].jiasudu),
                                pulse_count=PulseCount(abs(motors[num].recode.get(
                                    'stepper_real_time_position (deg)') / 30 - jiaodu[num].value()) / 360 * 96000),
                                absolute=AbsoluteFlag.RELATIVE
                            )
                    # Move motor
                    Move(device=devices[num], params=params).status
            except:
                print(f"设备{num+1}移动失败")
                print(traceback.format_exc())

            try:
                if num==0:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 30:.10f}°')
                elif num==1:
                    motors[num].recode=GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)')/50:.10f}°')
                else:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 30:.10f}°')
            except:
                print(f"设备{num+1}角度获取失败")

    @Slot()  # 回零（回到初始位置）
    def on_huiling_clicked(self):
        try:
            self.dianjishu = int(self.ui.dianjishu.currentText())
            for num in range(self.dianjishu):
                Enable(device=devices[num]).status
                params = PositionParams(
                    direction=Direction.CW,
                    speed=Speed(100),
                    acceleration=Acceleration(0),
                    pulse_count=PulseCount(0),
                    absolute=AbsoluteFlag.ABSOLUTE
                )
                Move(device=devices[num], params=params).status
                if num == 1:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 50:.10f}°')
                else:
                    motors[num].recode = GetSysStatus(device=devices[num]).raw_data.data_dict
                    xianshi[num].setText(f'{motors[num].recode.get('stepper_target_position (deg)') / 30:.10f}°')
        except:
            print("回零失败")

if __name__=="__main__":
    app=QApplication([])
    win=Mywindow()
    win.show()
    sys.exit((app.exec()))
