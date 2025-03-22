import psutil
import sensors
import platform


def get_system_metrics() -> str:
    """
       Retrieves system metrics including CPU usage, memory usage, disk usage, and Linux version.
    
    Returns:
        str: A formatted string containing the system metrics.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        linux_version = platform.release()
        python_version = platform.python_version()

        # Format memory and disk in GB.
        mem_total = mem.total / 1024**3
        mem_used = mem.used / 1024**3
        disk_total = disk.total / 1024**3
        disk_used = disk.used / 1024**3

        result = (
            f"CPU Usage: {cpu_usage}%\n"
            f"Memory Usage: {mem_used:.2f}GB / {mem_total:.2f}GB ({mem.percent}%)\n"
            f"Disk Usage: {disk_used:.2f}GB / {disk_total:.2f}GB ({disk.percent}%)\n"
            f"Linux Version: {linux_version}\n"
            f"Python Version: {python_version}"
        )
    except Exception as e:
        result = f"Error retrieving system metrics: {str(e)}"
        
    return result

def get_system_sensors():
    """
    Retrieves system sensor data including temperature, fan speed, and voltage.
    
    Returns:
        str: A formatted string containing the system sensor data.
    """
    sensors.init()
    try:
        for chip in sensors.iter_detected_chips():
            print ('%s at %s' % (chip, chip.adapter_name))
            for feature in chip:
                print('  %s: %.2f' % (feature.label, feature.get_value()))
    finally:
        sensors.cleanup()


# Test cases
def test_get_system_metrics():
    print(get_system_metrics())

def test_get_system_sensors():
    print(get_system_sensors()) 
# Test the functions
#test_get_system_metrics()
#test_get_system_sensors()
