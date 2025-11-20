from setuptools import setup, find_packages

setup(
    name="stepper",  # 包名（pip安装时的名称）
    version="0.1.0",  # 版本号
    packages=find_packages(),  # 自动发现所有子包
    install_requires=[  # 该库依赖的第三方包
    ],
    author="你的名字",
    description="自定义步进电机控制库"
)
