#!/usr/bin/env python3
"""
Simple system monitoring script for VoiceFrame
Checks disk space, memory, and container health
"""

import psutil
import docker
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any

class VoiceFrameMonitor:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.voiceframe_containers = [
            'voiceframe-api-1',
            'voiceframe-db-1',
            'voiceframe-redis-1',
            'voiceframe-celery-worker-1',
            'voiceframe-celery-beat-1'
        ]

    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage"""
        disk_usage = psutil.disk_usage('/')
        total_gb = disk_usage.total / (1024**3)
        used_gb = disk_usage.used / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        usage_percent = (used_gb / total_gb) * 100

        status = "OK"
        if usage_percent > 90:
            status = "CRITICAL"
        elif usage_percent > 80:
            status = "WARNING"

        return {
            "status": status,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "usage_percent": round(usage_percent, 2)
        }

    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        used_gb = memory.used / (1024**3)
        available_gb = memory.available / (1024**3)
        usage_percent = memory.percent

        status = "OK"
        if usage_percent > 90:
            status = "CRITICAL"
        elif usage_percent > 80:
            status = "WARNING"

        return {
            "status": status,
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "available_gb": round(available_gb, 2),
            "usage_percent": usage_percent
        }

    def check_containers(self) -> Dict[str, Any]:
        """Check Docker container status"""
        container_status = {}

        for container_name in self.voiceframe_containers:
            try:
                container = self.docker_client.containers.get(container_name)
                status = container.status
                health = "unknown"

                # Get health status if available
                if container.attrs.get('State', {}).get('Health'):
                    health = container.attrs['State']['Health']['Status']

                container_status[container_name] = {
                    "status": status,
                    "health": health,
                    "running": status == "running"
                }
            except docker.errors.NotFound:
                container_status[container_name] = {
                    "status": "not_found",
                    "health": "unknown",
                    "running": False
                }
            except Exception as e:
                container_status[container_name] = {
                    "status": f"error: {str(e)}",
                    "health": "unknown",
                    "running": False
                }

        # Overall status
        running_containers = sum(1 for c in container_status.values() if c["running"])
        total_containers = len(self.voiceframe_containers)

        if running_containers == total_containers:
            overall_status = "OK"
        elif running_containers > 0:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"

        return {
            "status": overall_status,
            "running": running_containers,
            "total": total_containers,
            "containers": container_status
        }

    def check_api_health(self) -> Dict[str, Any]:
        """Check VoiceFrame API health"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "OK",
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "status_code": response.status_code
                }
            else:
                return {
                    "status": "WARNING",
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "status_code": response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "CRITICAL",
                "error": str(e),
                "response_time_ms": None,
                "status_code": None
            }

    def check_metrics_endpoint(self) -> Dict[str, Any]:
        """Check if metrics endpoint is accessible"""
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "OK",
                    "metrics_available": True,
                    "content_length": len(response.content)
                }
            else:
                return {
                    "status": "WARNING",
                    "metrics_available": False,
                    "status_code": response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                "status": "CRITICAL",
                "metrics_available": False,
                "error": str(e)
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Get overall system information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": psutil.os.uname().nodename,
            "platform": psutil.os.uname().sysname,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }

    def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check"""
        print(f"🔍 Running VoiceFrame health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        health_report = {
            "system_info": self.get_system_info(),
            "disk_space": self.check_disk_space(),
            "memory": self.check_memory(),
            "containers": self.check_containers(),
            "api_health": self.check_api_health(),
            "metrics": self.check_metrics_endpoint()
        }

        # Overall status
        critical_issues = []
        warnings = []

        if health_report["disk_space"]["status"] == "CRITICAL":
            critical_issues.append(f"Disk usage: {health_report['disk_space']['usage_percent']}%")
        elif health_report["disk_space"]["status"] == "WARNING":
            warnings.append(f"Disk usage: {health_report['disk_space']['usage_percent']}%")

        if health_report["memory"]["status"] == "CRITICAL":
            critical_issues.append(f"Memory usage: {health_report['memory']['usage_percent']}%")
        elif health_report["memory"]["status"] == "WARNING":
            warnings.append(f"Memory usage: {health_report['memory']['usage_percent']}%")

        if health_report["containers"]["status"] == "CRITICAL":
            critical_issues.append("Containers not running")
        elif health_report["containers"]["status"] == "WARNING":
            warnings.append(f"Only {health_report['containers']['running']}/{health_report['containers']['total']} containers running")

        if health_report["api_health"]["status"] == "CRITICAL":
            critical_issues.append("API not responding")
        elif health_report["api_health"]["status"] == "WARNING":
            warnings.append("API responding with warnings")

        if health_report["metrics"]["status"] == "CRITICAL":
            critical_issues.append("Metrics endpoint not accessible")

        # Determine overall status
        if critical_issues:
            overall_status = "CRITICAL"
        elif warnings:
            overall_status = "WARNING"
        else:
            overall_status = "OK"

        health_report["overall_status"] = overall_status
        health_report["critical_issues"] = critical_issues
        health_report["warnings"] = warnings

        return health_report

    def print_report(self, report: Dict[str, Any]):
        """Print formatted health report"""
        print("\n" + "="*60)
        print("🎯 VOICEFRAME HEALTH REPORT")
        print("="*60)

        # Overall status
        status_emoji = {"OK": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}
        print(f"\n📊 Overall Status: {status_emoji[report['overall_status']]} {report['overall_status']}")

        # System info
        print(f"\n🖥️  System: {report['system_info']['hostname']} ({report['system_info']['platform']})")
        print(f"💻 CPU: {report['system_info']['cpu_count']} cores, {report['system_info']['cpu_percent']}% usage")

        # Disk space
        disk = report["disk_space"]
        print(f"\n💾 Disk Space: {disk['usage_percent']}% used ({disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB)")
        print(f"   Status: {status_emoji[disk['status']]} {disk['status']}")

        # Memory
        memory = report["memory"]
        print(f"\n🧠 Memory: {memory['usage_percent']}% used ({memory['used_gb']:.1f}GB / {memory['total_gb']:.1f}GB)")
        print(f"   Status: {status_emoji[memory['status']]} {memory['status']}")

        # Containers
        containers = report["containers"]
        print(f"\n🐳 Containers: {containers['running']}/{containers['total']} running")
        print(f"   Status: {status_emoji[containers['status']]} {containers['status']}")

        for name, info in containers["containers"].items():
            container_emoji = "✅" if info["running"] else "❌"
            print(f"   {container_emoji} {name}: {info['status']} ({info['health']})")

        # API Health
        api = report["api_health"]
        print(f"\n🌐 API Health: {status_emoji[api['status']]} {api['status']}")
        if api.get("response_time_ms"):
            print(f"   Response time: {api['response_time_ms']}ms")

        # Metrics
        metrics = report["metrics"]
        print(f"\n📈 Metrics: {status_emoji[metrics['status']]} {metrics['status']}")
        if metrics.get("metrics_available"):
            print(f"   Metrics available: {metrics['content_length']} bytes")

        # Issues
        if report["critical_issues"]:
            print(f"\n🚨 Critical Issues:")
            for issue in report["critical_issues"]:
                print(f"   • {issue}")

        if report["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in report["warnings"]:
                print(f"   • {warning}")

        print("\n" + "="*60)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="VoiceFrame System Monitor")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="Watch mode with refresh interval")
    parser.add_argument("--save", type=str, metavar="FILE", help="Save report to file")

    args = parser.parse_args()

    monitor = VoiceFrameMonitor()

    def run_check():
        report = monitor.run_health_check()

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            monitor.print_report(report)

        if args.save:
            with open(args.save, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Report saved to {args.save}")

        return report

    if args.watch:
        print(f"👀 Watching system health (refresh every {args.watch} seconds)")
        print("Press Ctrl+C to stop")
        try:
            while True:
                run_check()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    else:
        run_check()

if __name__ == "__main__":
    main()
