"""电机配置"""


class Motor:
    """电机配置类"""

    def __init__(self, pulse_per_rev, divisor):
        self.pulse_per_rev = pulse_per_rev
        self.divisor = divisor


class MotorConfig:
    """电机配置管理"""

    def __init__(self):
        self.configs = {
            0: Motor(96000, 30),  # 电机1
            1: Motor(160000, 50),  # 电机2
            2: Motor(96000, 30),  # 电机3
            3: Motor(96000, 30),  # 电机4
            4: Motor(96000, 30),  # 电机5
            5: Motor(96000, 30),  # 电机6
        }

    def get_motor_config(self, motor_id):
        return self.configs.get(motor_id, Motor(96000, 30))
