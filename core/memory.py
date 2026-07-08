import re


def get_ram():

    with open("/proc/meminfo", "r") as f:
        text = f.read()

    total = int(re.search(r"MemTotal:\s+(\d+)", text).group(1))
    available = int(re.search(r"MemAvailable:\s+(\d+)", text).group(1))

    used = total - available

    return (
        used / 1024 / 1024,
        total / 1024 / 1024,
    )


def get_ram_percent():

    used, total = get_ram()

    return round((used / total) * 100)