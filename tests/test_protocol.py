#!/usr/bin/env python
"""
通信协议验证测试
测试数据包的编码、解码和校验
"""

import struct
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum


class PacketType(IntEnum):
    """数据包类型枚举"""
    # FPGA -> PC
    STATUS = 0x10
    ALERT = 0x20
    COMPLETE = 0x21
    RESPONSE = 0x80
    HEARTBEAT = 0x90

    # PC -> FPGA
    FORCE_CONTROL = 0x30
    POSITION_CONTROL = 0x31
    HYBRID_CONTROL = 0x32
    PARAMETER_SET = 0x40
    EMERGENCY_STOP = 0x50
    HANDSHAKE = 0x00


@dataclass
class Packet:
    """数据包结构"""
    packet_type: int
    timestamp: int
    payload: bytes


class ProtocolHandler:
    """协议处理器"""

    HEADER = 0xAA
    TAIL = 0x55

    def __init__(self):
        self.packet_counter = 0

    def calculate_crc16(self, data: bytes) -> int:
        """计算CRC16-MODBUS校验"""
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1

        return crc

    def encode_packet(self, packet_type: int, payload: Dict[str, Any]) -> bytes:
        """编码数据包"""
        # 根据类型编码payload
        if packet_type == PacketType.FORCE_CONTROL:
            payload_bytes = self._encode_force_control(payload)
        elif packet_type == PacketType.STATUS:
            payload_bytes = self._encode_status(payload)
        elif packet_type == PacketType.HEARTBEAT:
            payload_bytes = self._encode_heartbeat(payload)
        else:
            payload_bytes = bytes()

        # 构造完整数据包
        packet = bytearray()
        packet.append(self.HEADER)
        packet.append(len(payload_bytes))
        packet.append(packet_type)

        # 时间戳
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF
        packet.extend(struct.pack('<I', timestamp))

        # Payload
        packet.extend(payload_bytes)

        # CRC16
        crc = self.calculate_crc16(packet[1:])  # 不包括帧头
        packet.extend(struct.pack('<H', crc))

        # 帧尾
        packet.append(self.TAIL)

        self.packet_counter += 1
        return bytes(packet)

    def decode_packet(self, data: bytes) -> Optional[Tuple[int, Dict[str, Any]]]:
        """解码数据包"""
        if len(data) < 10:  # 最小包长度
            print(f"✗ 数据包太短: {len(data)} bytes")
            return None

        # 检查帧头帧尾
        if data[0] != self.HEADER or data[-1] != self.TAIL:
            print(f"✗ 帧头或帧尾错误: header={hex(data[0])}, tail={hex(data[-1])}")
            return None

        # 解析字段
        payload_len = data[1]
        packet_type = data[2]
        timestamp = struct.unpack('<I', data[3:7])[0]

        # 提取payload
        payload_end = 7 + payload_len
        if payload_end + 3 > len(data):  # 2字节CRC + 1字节帧尾
            print(f"✗ 数据包长度不匹配")
            return None

        payload_bytes = data[7:payload_end]

        # 验证CRC
        received_crc = struct.unpack('<H', data[payload_end:payload_end + 2])[0]
        calculated_crc = self.calculate_crc16(data[1:payload_end])

        if received_crc != calculated_crc:
            print(f"✗ CRC校验失败: received={hex(received_crc)}, calculated={hex(calculated_crc)}")
            return None

        # 解码payload
        if packet_type == PacketType.STATUS:
            payload = self._decode_status(payload_bytes)
        elif packet_type == PacketType.HEARTBEAT:
            payload = self._decode_heartbeat(payload_bytes)
        else:
            payload = {'raw': payload_bytes.hex()}

        payload['timestamp'] = timestamp
        return packet_type, payload

    def _encode_force_control(self, data: Dict) -> bytes:
        """编码力控制命令"""
        payload = struct.pack('<B', data.get('mode', 0))
        payload += struct.pack('<f', data.get('target_force', 0))
        payload += struct.pack('<f', data.get('force_rate', 0))
        payload += struct.pack('<f', data.get('max_force', 5.0))
        payload += struct.pack('<f', data.get('hold_time', 0))
        return payload

    def _encode_status(self, data: Dict) -> bytes:
        """编码状态数据"""
        payload = struct.pack('<f', data.get('force_value', 0))
        payload += struct.pack('<f', data.get('force_rate', 0))
        payload += struct.pack('<f', data.get('position', 0))
        payload += struct.pack('<f', data.get('velocity', 0))
        payload += struct.pack('<B', data.get('motor_enabled', 0))
        payload += struct.pack('<B', data.get('position_reached', 0))
        payload += struct.pack('<B', data.get('stall_detected', 0))
        payload += struct.pack('<B', data.get('emergency_stop', 0))
        payload += struct.pack('<B', data.get('error_code', 0))
        payload += bytes(3)  # 保留字节
        return payload

    def _encode_heartbeat(self, data: Dict) -> bytes:
        """编码心跳包"""
        payload = struct.pack('<I', data.get('timestamp', 0))
        payload += struct.pack('<B', data.get('status', 1))
        return payload

    def _decode_status(self, data: bytes) -> Dict:
        """解码状态数据"""
        if len(data) < 24:
            return {}

        result = {}
        offset = 0

        result['force_value'] = struct.unpack('<f', data[offset:offset + 4])[0]
        offset += 4
        result['force_rate'] = struct.unpack('<f', data[offset:offset + 4])[0]
        offset += 4
        result['position'] = struct.unpack('<f', data[offset:offset + 4])[0]
        offset += 4
        result['velocity'] = struct.unpack('<f', data[offset:offset + 4])[0]
        offset += 4

        result['motor_enabled'] = data[offset]
        offset += 1
        result['position_reached'] = data[offset]
        offset += 1
        result['stall_detected'] = data[offset]
        offset += 1
        result['emergency_stop'] = data[offset]
        offset += 1
        result['error_code'] = data[offset]

        return result

    def _decode_heartbeat(self, data: bytes) -> Dict:
        """解码心跳包"""
        if len(data) < 5:
            return {}

        return {
            'timestamp': struct.unpack('<I', data[0:4])[0],
            'status': data[4]
        }


def test_protocol():
    """测试协议编解码"""
    print("=" * 60)
    print("协议编解码测试")
    print("=" * 60)

    handler = ProtocolHandler()

    # 测试1: 力控制命令编码
    print("\n1. 测试力控制命令编码:")
    force_cmd = {
        'mode': 2,  # 力递增模式
        'target_force': 2.5,
        'force_rate': 0.5,
        'max_force': 5.0,
        'hold_time': 2.0
    }

    packet = handler.encode_packet(PacketType.FORCE_CONTROL, force_cmd)
    print(f"编码后: {packet.hex()}")
    print(f"包长度: {len(packet)} bytes")

    # 测试2: 状态数据编解码
    print("\n2. 测试状态数据编解码:")
    status_data = {
        'force_value': 1.5,
        'force_rate': 0.2,
        'position': 45.0,
        'velocity': 10.0,
        'motor_enabled': 1,
        'position_reached': 0,
        'stall_detected': 0,
        'emergency_stop': 0,
        'error_code': 0
    }

    # 编码
    encoded = handler.encode_packet(PacketType.STATUS, status_data)
    print(f"编码后: {encoded.hex()}")

    # 解码
    decoded_type, decoded_data = handler.decode_packet(encoded)
    print(f"解码后类型: {hex(decoded_type)}")
    print(f"解码后数据: {decoded_data}")

    # 验证
    for key in ['force_value', 'position']:
        original = status_data[key]
        decoded = decoded_data[key]
        match = abs(original - decoded) < 0.001
        print(f"  {key}: {original} -> {decoded} {'✓' if match else '✗'}")

    # 测试3: CRC错误检测
    print("\n3. 测试CRC错误检测:")
    corrupted = bytearray(encoded)
    corrupted[10] ^= 0xFF  # 故意破坏一个字节

    result = handler.decode_packet(bytes(corrupted))
    if result is None:
        print("✓ 成功检测到CRC错误")
    else:
        print("✗ 未能检测到CRC错误")

    # 测试4: 批量测试
    print("\n4. 批量编解码测试:")
    success_count = 0
    test_count = 100

    for i in range(test_count):
        # 生成随机数据
        test_data = {
            'force_value': i * 0.1,
            'force_rate': i * 0.01,
            'position': i * 1.0,
            'velocity': i * 0.5,
            'motor_enabled': i % 2,
            'position_reached': (i + 1) % 2,
            'stall_detected': 0,
            'emergency_stop': 0,
            'error_code': 0
        }

        # 编解码
        encoded = handler.encode_packet(PacketType.STATUS, test_data)
        result = handler.decode_packet(encoded)

        if result:
            success_count += 1

    print(f"成功率: {success_count}/{test_count} ({success_count / test_count * 100:.1f}%)")

    print("\n✅ 协议测试完成!")


if __name__ == "__main__":
    test_protocol()