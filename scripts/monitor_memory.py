#!/usr/bin/env python3
import psutil
import time
import sys
from datetime import datetime
import os

try:
    import torch
    import torch.backends.mps
    has_mps = torch.backends.mps.is_available()
except ImportError:
    has_mps = False


class MemoryMonitor:
    def __init__(self):
        self.memory_history = []
        self.log_file = f"memory_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._setup_log()
    
    def _setup_log(self):
        """设置日志文件"""
        with open(self.log_file, 'w') as f:
            f.write(f"# 内存监控日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("time,mem_total,mem_used,mem_free,mem_percent,swap_total,swap_used,swap_percent,cpu_percent,mps_memory\n")
    
    def get_mps_memory(self):
        """获取MPS显存使用情况"""
        if has_mps and torch.backends.mps.is_available():
            try:
                # 获取MPS内存使用
                memory_info = torch.mps.current_allocated_memory()
                return memory_info / 1024 / 1024  # 转换为MB
            except Exception as e:
                return 0.0
        return 0.0
    
    def get_memory_info(self):
        """获取完整的内存信息"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        mps_memory = self.get_mps_memory()
        
        info = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "mem_total": mem.total / 1024 / 1024,
            "mem_used": mem.used / 1024 / 1024,
            "mem_free": mem.free / 1024 / 1024,
            "mem_percent": mem.percent,
            "swap_total": swap.total / 1024 / 1024,
            "swap_used": swap.used / 1024 / 1024,
            "swap_percent": swap.percent,
            "cpu_percent": cpu,
            "mps_memory": mps_memory
        }
        
        # 记录历史数据
        self.memory_history.append(info)
        if len(self.memory_history) > 100:
            self.memory_history.pop(0)
        
        return info
    
    def print_memory_info(self):
        """打印内存信息"""
        info = self.get_memory_info()
        
        # 构建输出字符串
        output = f"[{info['time']}] "
        output += f"Memory: {info['mem_used']:.1f}/{info['mem_total']:.1f} MB ({info['mem_percent']:.1f}%) | "
        output += f"Swap: {info['swap_used']:.1f}/{info['swap_total']:.1f} MB ({info['swap_percent']:.1f}%) | "
        output += f"CPU: {info['cpu_percent']:.1f}%"
        
        if has_mps:
            output += f" | MPS: {info['mps_memory']:.1f} MB"
        
        print(output)
        
        # 写入日志文件
        self._write_log(info)
    
    def _write_log(self, info):
        """写入日志文件"""
        with open(self.log_file, 'a') as f:
            f.write(f"{info['time']},{info['mem_total']:.1f},{info['mem_used']:.1f},{info['mem_free']:.1f},{info['mem_percent']:.1f},{info['swap_total']:.1f},{info['swap_used']:.1f},{info['swap_percent']:.1f},{info['cpu_percent']:.1f},{info['mps_memory']:.1f}\n")
    
    def print_summary(self):
        """打印内存使用摘要"""
        if not self.memory_history:
            print("没有监控数据")
            return
        
        print("\n=== 内存监控摘要 ===")
        print(f"监控时间: {len(self.memory_history) * 5} 秒")
        
        # 计算最大值和平均值
        max_mem = max(item['mem_percent'] for item in self.memory_history)
        avg_mem = sum(item['mem_percent'] for item in self.memory_history) / len(self.memory_history)
        max_swap = max(item['swap_percent'] for item in self.memory_history)
        avg_swap = sum(item['swap_percent'] for item in self.memory_history) / len(self.memory_history)
        max_cpu = max(item['cpu_percent'] for item in self.memory_history)
        avg_cpu = sum(item['cpu_percent'] for item in self.memory_history) / len(self.memory_history)
        
        if has_mps:
            max_mps = max(item['mps_memory'] for item in self.memory_history)
            avg_mps = sum(item['mps_memory'] for item in self.memory_history) / len(self.memory_history)
            print(f"MPS 显存 - 最大值: {max_mps:.1f} MB, 平均值: {avg_mps:.1f} MB")
        
        print(f"内存使用 - 最大值: {max_mem:.1f}%, 平均值: {avg_mem:.1f}%")
        print(f"交换空间 - 最大值: {max_swap:.1f}%, 平均值: {avg_swap:.1f}%")
        print(f"CPU 使用率 - 最大值: {max_cpu:.1f}%, 平均值: {avg_cpu:.1f}%")
        print(f"日志文件: {self.log_file}")


def main():
    monitor = MemoryMonitor()
    print("=== 内存监控启动 ===")
    print("按 Ctrl+C 停止监控")
    print("=" * 80)
    
    try:
        while True:
            monitor.print_memory_info()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n=== 内存监控结束 ===")
        monitor.print_summary()


if __name__ == "__main__":
    main()
