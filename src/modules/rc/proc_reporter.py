import psutil

hl2_pid: int = 0


def is_hl2_running() -> bool:
    global hl2_pid
    for proc in psutil.process_iter():
        if "hl2" in proc.name():
            hl2_pid = proc.pid
            return True
    return False


def get_hl2_pid() -> int:
    global hl2_pid
    return hl2_pid


if __name__ == "__main__":
    print("Is hl2 running? ", is_hl2_running())
