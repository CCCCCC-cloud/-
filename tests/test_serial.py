#!/usr/bin/env python
"""
串口连接测试脚本
测试与FPGA的基础通信
"""

import serial
import serial.tools.list_ports
import time
import struct
import sys
from typing import Optional, List, Tuple


class SerialTester:
    """串口测试类"""

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.HEADER = 0xAA
        self.TAIL = 0x55

    def list_available_ports(self) -> List[Tuple[str, str]]:
        """列出所有可用串口"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append((port.device, port.description))
        return ports

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """连接串口"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )
            print(f"✓ Connected to {port} at {baudrate} bps")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False

    def send_handshake(self) -> bool:
        """发送握手包"""
        if not self.serial_port:
            print("✗ Serial port not connected")
            return False

        # 构造握手包: [0xAA][0x01][0x00][0x10][0x00][0x00][0x00][CRC16][0x55]
        packet = bytearray([self.HEADER, 0x01, 0x00])  # 头部
        packet.extend(struct.pack('<I', 0))  # 时间戳 (4字节)
        packet.append(0x10)  # 协议版本

        # 计算CRC16 (简化版，实际项目需要完整CRC16)
        crc = sum(packet[1:]) & 0xFFFF
        packet.extend(struct.pack('<H', crc))
        packet.append(self.TAIL)

        try:
            self.serial_port.write(packet)
            print(f"→ Sent handshake: {packet.hex()}")
            return True
        except Exception as e:
            print(f"✗ Failed to send handshake: {e}")
            return False

    def receive_data(self, timeout: float = 2.0) -> Optional[bytes]:
        """接收数据"""
        if not self.serial_port:
            return None

        self.serial_port.timeout = timeout
        start_time = time.time()
        buffer = bytearray()

        while time.time() - start_time < timeout:
            if self.serial_port.in_waiting > 0:
                byte = self.serial_port.read(1)
                if byte:
                    buffer.append(byte[0])

                    # 检查是否收到完整数据包
                    if len(buffer) >= 2 and buffer[0] == self.HEADER:
                        if buffer[-1] == self.TAIL:
                            print(f"← Received: {buffer.hex()}")
                            return bytes(buffer)

        if buffer:
            print(f"← Partial data: {buffer.hex()}")
        else:
            print("← No data received")
        return None

    def test_loopback(self, data: bytes = b"Hello FPGA!") -> bool:
        """测试回环"""
        if not self.serial_port:
            return False

        try:
            # 发送测试数据
            self.serial_port.write(data)
            print(f"→ Sent loopback: {data}")

            # 接收回显
            received = self.serial_port.read(len(data))
            if received == data:
                print(f"✓ Loopback successful: {received}")
                return True
            else:
                print(f"✗ Loopback failed. Expected: {data}, Got: {received}")
                return False
        except Exception as e:
            print(f"✗ Loopback error: {e}")
            return False

    def continuous_test(self, duration: int = 10):
        """连续测试 (发送心跳包)"""
        if not self.serial_port:
            return

        print(f"\n开始连续测试 ({duration}秒)...")
        start_time = time.time()
        packet_count = 0
        error_count = 0

        while time.time() - start_time < duration:
            # 构造心跳包
            packet = bytearray([self.HEADER, 0x01, 0x90])  # 心跳类型
            timestamp = int((time.time() - start_time) * 1000)
            packet.extend(struct.pack('<I', timestamp))
            packet.append(0x01)  # 状态: 正常

            # 简单校验和
            checksum = sum(packet[1:]) & 0xFF
            packet.append(checksum)
            packet.append(self.TAIL)

            try:
                self.serial_port.write(packet)
                packet_count += 1
                print(f"→ Heartbeat #{packet_count}: {packet.hex()}")

                # 等待响应
                response = self.serial_port.read(10)
                if response:
                    print(f"← Response: {response.hex()}")
                else:
                    error_count += 1
                    print(f"✗ No response (errors: {error_count})")

            except Exception as e:
                error_count += 1
                print(f"✗ Error: {e}")

            time.sleep(0.5)  # 2Hz发送频率

        # 统计结果
        print(f"\n测试完成!")
        print(f"- 发送包数: {packet_count}")
        print(f"- 错误次数: {error_count}")
        print(f"- 成功率: {(packet_count - error_count) / packet_count * 100:.1f}%")

    def close(self):
        """关闭串口"""
        if self.serial_port:
            self.serial_port.close()
            print("✓ Serial port closed")


def main():
    """主测试函数"""
    print("=" * 60)
    print("AdaptiveGraspControl - 串口连接测试")
    print("=" * 60)

    tester = SerialTester()

    # 1. 列出可用串口
    print("\n1. 可用串口列表:")
    ports = tester.list_available_ports()
    if not ports:
        print("✗ 没有发现可用串口!")
        print("请检查:")
        print("  - USB转TTL模块是否已连接")
        print("  - 驱动程序是否已安装")
        print("  - 是否有权限访问串口")
        sys.exit(1)

    for i, (port, desc) in enumerate(ports):
        print(f"  [{i}] {port}: {desc}")

    # 2. 选择串口
    if len(ports) == 1:
        selected_port = ports[0][0]
        print(f"\n自动选择唯一可用串口: {selected_port}")
    else:
        try:
            idx = int(input("\n请选择串口编号: "))
            selected_port = ports[idx][0]
        except:
            print("✗ 无效选择")
            sys.exit(1)

    # 3. 连接测试
    print(f"\n2. 连接到 {selected_port}...")
    if not tester.connect(selected_port):
        sys.exit(1)

    # 4. 基础测试菜单
    while True:
        print("\n" + "=" * 40)
        print("测试菜单:")
        print("  1. 发送握手包")
        print("  2. 回环测试")
        print("  3. 连续测试(10秒)")
        print("  4. 自定义数据发送")
        print("  0. 退出")

        try:
            choice = input("\n请选择: ")

            if choice == '1':
                tester.send_handshake()
                time.sleep(0.5)
                tester.receive_data()

            elif choice == '2':
                tester.test_loopback()

            elif choice == '3':
                tester.continuous_test()

            elif choice == '4':
                data = input("输入要发送的数据(HEX格式,如AA5501): ")
                try:
                    data_bytes = bytes.fromhex(data)
                    tester.serial_port.write(data_bytes)
                    print(f"→ Sent: {data_bytes.hex()}")
                    time.sleep(0.5)
                    response = tester.receive_data(1.0)
                except:
                    print("✗ 无效的HEX格式")

            elif choice == '0':
                break

        except KeyboardInterrupt:
            print("\n\n中断测试...")
            break

    # 关闭串口
    tester.close()
    print("\n测试结束!")


if __name__ == "__main__":
    main()