项目根目录/
├── main.py                # 主程序
├── control.py             # UI界面（PySide6）
├── motor_config.py        # 电机配置
├── requirements.txt       # 依赖清单
├── config/               # 配置目录
│   └── motor_config.yaml # YAML配置
├── stepper/              # 步进电机驱动库
│   ├── commands/         # 命令模块
│   ├── device/           # 设备管理
│   ├── serial_utilities/ # 串口工具
│   ├── stepper_core/     # 核心参数
│   └── setup.py          # 安装脚本
└── venv/                 # 虚拟环境