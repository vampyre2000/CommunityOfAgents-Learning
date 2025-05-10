import os
import psutil
import platform
import shutil
import subprocess
import logging
import json


def get_cpu_stats() -> dict:
    """Return detailed CPU information."""
    try:
        freq = psutil.cpu_freq()
        stats = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores":    psutil.cpu_count(logical=True),
            "max_frequency_mhz":  freq.max,
            "min_frequency_mhz":  freq.min,
            "current_frequency_mhz": freq.current,
            "cpu_percent_per_core":  psutil.cpu_percent(interval=1, percpu=True),
            "cpu_percentage_overall": psutil.cpu_percent(interval=None),
            "cpu_times_percent":     psutil.cpu_times_percent(interval=1)._asdict(),
            "load_average": {
                "1min":  os.getloadavg()[0],
                "5min":  os.getloadavg()[1],
                "15min": os.getloadavg()[2],
            }
        }
    except Exception as e:
        logging.error(f"Failed to gather CPU stats: {e}")
        stats = {"error": str(e)}
    return stats


def get_disk_status() -> dict:
    """Return usage stats for each mounted disk/partition."""
    disks = {}
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            logging.warning(f"Permission denied for {part.mountpoint}, skipping.")
            continue

        disks[part.device] = {
            "mountpoint": part.mountpoint,
            "fstype":     part.fstype,
            "total_gb":   round(usage.total / 1024**3, 2),
            "used_gb":    round(usage.used / 1024**3, 2),
            "free_gb":    round(usage.free / 1024**3, 2),
            "percent":    usage.percent
        }
    return disks


def get_ollama_version() -> str:
    """Return the installed ollama version, or an error message."""
    cmd = shutil.which("ollama")
    if not cmd:
        return "ollama not found on PATH"
    try:
        proc = subprocess.run([cmd, "--version"],
                              capture_output=True, text=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling ollama: {e.stderr.strip()}")
        return f"Error: {e.stderr.strip()}"


def gather_all_metrics() -> dict:
    """Combine all metrics into one dict."""
    return {
        "platform": {
            "os":     platform.system(),
            "release": platform.release(),
            "python": platform.python_version()
        },
        "cpu":    get_cpu_stats(),
        "disks":  get_disk_status(),
        "ollama": get_ollama_version()
    }


def get_system_metrics():
    """
       Retrieves system metrics including CPU usage, memory usage, disk usage, and Linux version.
       Parameters: "None"
       Returns:    str: A formatted string containing the system metrics.
    """
    metrics = gather_all_metrics()
    results = []
    results.append(f"OS:             {metrics['platform']['os']} {metrics['platform']['release']}")
    results.append(f"Python:         {metrics['platform']['python']}")
    results.append(f"Ollama version: {metrics['ollama']}")
    results.append(f"\nCPU:")
    
    for k, v in metrics["cpu"].items():
        results.append(f"  {k}: {v}")
    results.append(f"\nDisks:")
    for dev, info in metrics["disks"].items():
        results.append(f"  {dev} on {info['mountpoint']} ({info['fstype']}): "
                f"{info['used_gb']}GB/{info['total_gb']}GB ({info['percent']}%)")

    # human-readable fallback
    return "\n".join(results)
    
    
if __name__ == "__main__":
    print(get_system_metrics())
