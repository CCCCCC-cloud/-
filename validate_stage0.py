#!/usr/bin/env python
"""
Stage 0 综合验证脚本
验证所有基础组件是否正常工作
"""

import os
import sys
import time
import importlib
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List


class SystemValidator:
    """系统验证器"""

    def __init__(self):
        self.test_results = {}
        self.project_root = Path.cwd()

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("AdaptiveGraspControl - Stage 0 验证")
        print("=" * 60)

        # 1. 环境检查
        print("\n[1/5] 检查Python环境...")
        self.check_python_environment()

        # 2. 依赖检查
        print("\n[2/5] 检查依赖包...")
        self.check_dependencies()

        # 3. 目录结构检查
        print("\n[3/5] 检查项目结构...")
        self.check_project_structure()

        # 4. 配置文件检查
        print("\n[4/5] 检查配置文件...")
        self.check_config_files()

        # 5. 模块导入测试
        print("\n[5/5] 测试模块导入...")
        self.test_imports()

        # 生成报告
        self.generate_report()

    def check_python_environment(self) -> Tuple[bool, str]:
        """检查Python环境"""
        success = True
        messages = []

        # Python版本
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            messages.append(f"✓ Python版本: {sys.version.split()[0]}")
        else:
            success = False
            messages.append(f"✗ Python版本不符合要求: {sys.version.split()[0]} (需要3.8+)")

        # 虚拟环境
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            messages.append("✓ 虚拟环境已激活")
        else:
            messages.append("⚠ 建议使用虚拟环境")

        # 操作系统
        import platform
        messages.append(f"✓ 操作系统: {platform.system()} {platform.release()}")

        self.test_results['environment'] = (success, messages)
        for msg in messages:
            print(f"  {msg}")

        return success, "\n".join(messages)

    def check_dependencies(self) -> Tuple[bool, str]:
        """检查依赖包"""
        required_packages = {
            'serial': 'pyserial',
            'numpy': 'numpy',
            'yaml': 'pyyaml',
            'PyQt5': 'PyQt5',
            'pyqtgraph': 'pyqtgraph',
        }

        success = True
        messages = []

        for module_name, package_name in required_packages.items():
            try:
                module = importlib.import_module(module_name)
                version = getattr(module, '__version__', 'unknown')
                messages.append(f"✓ {package_name}: {version}")
            except ImportError:
                success = False
                messages.append(f"✗ {package_name}: 未安装")

        # 检查串口工具
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            messages.append(f"✓ 发现 {len(ports)} 个串口")
            for port in ports:
                messages.append(f"    - {port.device}: {port.description}")
        except:
            messages.append("⚠ 无法列出串口")

        self.test_results['dependencies'] = (success, messages)
        for msg in messages:
            print(f"  {msg}")

        return success, "\n".join(messages)

    def check_project_structure(self) -> Tuple[bool, str]:
        """检查项目目录结构"""
        required_dirs = [
            'tests',
            'tools',
            'config',
            'logs',
            'data',
            'data/raw',
            'data/processed',
        ]

        required_files = [
            'requirements.txt',
            '.gitignore'
        ]

        success = True
        messages = []

        # 检查目录
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                messages.append(f"✓ 目录存在: {dir_name}/")
            else:
                success = False
                messages.append(f"✗ 目录缺失: {dir_name}/")
                # 尝试创建
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    messages.append(f"  → 已自动创建: {dir_name}/")
                except:
                    messages.append(f"  → 创建失败: {dir_name}/")

        # 检查文件
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                messages.append(f"✓ 文件存在: {file_name}")
            else:
                messages.append(f"⚠ 文件缺失: {file_name}")

        self.test_results['structure'] = (success, messages)
        for msg in messages:
            print(f"  {msg}")

        return success, "\n".join(messages)

    def check_config_files(self) -> Tuple[bool, str]:
        """检查配置文件"""
        config_files = [
            'config/system_config.yaml',
            'config/control_params.yaml'
        ]

        success = True
        messages = []

        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                # 尝试加载配置
                try:
                    import yaml
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    messages.append(f"✓ 配置文件有效: {config_file}")
                except Exception as e:
                    success = False
                    messages.append(f"✗ 配置文件错误: {config_file}")
                    messages.append(f"    错误: {str(e)}")
            else:
                messages.append(f"⚠ 配置文件缺失: {config_file}")
                messages.append(f"    请从项目文档复制配置文件")

        self.test_results['config'] = (success, messages)
        for msg in messages:
            print(f"  {msg}")

        return success, "\n".join(messages)

    def test_imports(self) -> Tuple[bool, str]:
        """测试模块导入"""
        test_scripts = [
            'tests/test_serial.py',
            'tests/test_protocol.py',
            'tools/serial_monitor.py',
            'tools/data_plotter.py'
        ]

        success = True
        messages = []

        for script in test_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                # 检查语法
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, script, 'exec')
                    messages.append(f"✓ 脚本语法正确: {script}")
                except SyntaxError as e:
                    success = False
                    messages.append(f"✗ 脚本语法错误: {script}")
                    messages.append(f"    行 {e.lineno}: {e.msg}")
            else:
                messages.append(f"⚠ 脚本不存在: {script}")

        self.test_results['imports'] = (success, messages)
        for msg in messages:
            print(f"  {msg}")

        return success, "\n".join(messages)

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("验证报告")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for success, _ in self.test_results.values() if success)

        # 统计
        print(f"\n测试通过: {passed_tests}/{total_tests}")

        # 问题汇总
        issues = []
        for test_name, (success, messages) in self.test_results.items():
            if not success:
                issues.append(f"- {test_name}: 存在问题")
                for msg in messages:
                    if msg.startswith("✗"):
                        issues.append(f"    {msg}")

        if issues:
            print("\n需要解决的问题:")
            for issue in issues:
                print(issue)
        else:
            print("\n✅ 所有测试通过! Stage 0 环境配置完成!")
            print("\n下一步:")
            print("1. 运行串口测试: python tests/test_serial.py")
            print("2. 启动串口监视器: python tools/serial_monitor.py")
            print("3. 启动数据绘图器: python tools/data_plotter.py")

        # 保存报告
        report_file = self.project_root / 'validation_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Stage 0 验证报告\n")
            f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 60 + "\n\n")

            for test_name, (success, messages) in self.test_results.items():
                f.write(f"{test_name}: {'通过' if success else '失败'}\n")
                for msg in messages:
                    f.write(f"  {msg}\n")
                f.write("\n")

        print(f"\n报告已保存到: {report_file}")


def main():
    """主函数"""
    validator = SystemValidator()
    validator.run_all_tests()


if __name__ == "__main__":
    main()