import psutil

hl2_pid: int = 0


def is_hl2_running() -> bool:
    global hl2_pid
    _pids = list(filter(lambda pid_: psutil.Process(pid_).name() == "hl2.exe", psutil.pids()))
    if _pids:
        hl2_pid = _pids[0]
        return True
    return False


def get_hl2_pid() -> int:
    global hl2_pid
    return hl2_pid


if __name__ == "__main__":
    print("Is hl2 running? ", is_hl2_running())
