# -*- coding: utf-8 -*-
"""国际贸易上市公司一站式智能服务平台 —— 一键启动器 v2

用法：
    python launcher.py            # 交互菜单（双击 start.bat 进入）
    python launcher.py start      # 启动前后端（已运行则直接打开页面）
    python launcher.py stop       # 停止前后端服务
    python launcher.py restart    # 重启
    python launcher.py status     # 查看服务状态

v2 改进（相对 v1）：
    1. 依赖缓存：requirements.txt / package.json 未变化时跳过安装，秒级启动
    2. 一键停止：按端口反查 PID 并结束进程，不再需要手关窗口
    3. 端口占用自动处理：被其他程序占用时可一键释放
    4. 彩色输出 + 服务状态自检（status 命令）
"""
import argparse
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "国际贸易上市公司一站式智能服务平台"
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
IS_WINDOWS = os.name == "nt"
VENV_PY = BACKEND_DIR / ".venv" / (Path("Scripts") / "python.exe" if IS_WINDOWS else Path("bin") / "python")

BACKEND_PORT = 8009
FRONTEND_PORT = 5173
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

# ------------ 输出样式（Windows 下先启用 ANSI） ------------
if IS_WINDOWS:
    os.system("")  # 激活 ANSI 转义支持
C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "cyan": "\033[36m", "gray": "\033[90m",
}


def say(msg: str = "", color: str = "") -> None:
    print(f"{C.get(color, '')}{msg}{C['reset']}")


def banner() -> None:
    say("=" * 62, "cyan")
    say(f"  {APP_NAME}", "bold")
    say("  一键启动器 v2  |  start / stop / restart / status", "dim")
    say("=" * 62, "cyan")


# ------------ 基础检测 ------------
def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def health_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def pids_on_port(port: int) -> list[int]:
    """按端口反查监听进程的 PID 列表。"""
    pids: list[int] = []
    try:
        if IS_WINDOWS:
            # 中文 Windows 下 netstat 输出为 GBK 编码，统一按字节读取再容错解码
            out = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"], capture_output=True
            ).stdout.decode("utf-8", "ignore")
            for line in out.splitlines():
                parts = line.split()
                # 形如 TCP 0.0.0.0:8009 ... LISTENING <pid>
                if len(parts) >= 5 and parts[3] == "LISTENING" and parts[1].endswith(f":{port}"):
                    pid = int(parts[4])
                    if pid and pid not in pids:
                        pids.append(pid)
        else:
            out = subprocess.run(
                ["lsof", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True
            ).stdout
            pids = [int(x) for x in out.split() if x.strip().isdigit()]
    except Exception:
        pass
    return pids


def pid_cmdline(pid: int) -> str:
    try:
        if IS_WINDOWS:
            # wmic 在新版 Windows 已弃用，改用 PowerShell CIM 查询完整命令行
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"],
                capture_output=True,
            ).stdout.decode("gbk", "ignore").strip()  # Windows 控制台默认 GBK 输出
            if out:
                return out[:90]
            return "(未知进程)"
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().decode("utf-8", "ignore").replace("\0", " ")[:90]
    except Exception:
        return "(未知进程)"


def kill_pids(pids: list[int]) -> None:
    for pid in pids:
        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, text=True)
            else:
                os.kill(pid, 9)
        except Exception:
            pass


def run(cmd, cwd: Path, shell: bool = False) -> bool:
    try:
        return subprocess.run(cmd, cwd=str(cwd), shell=shell).returncode == 0
    except Exception as e:  # noqa: BLE001
        say(f"  [错误] 执行失败: {e}", "red")
        return False


def spawn(cmd, cwd: Path, shell: bool = False) -> None:
    """在独立终端窗口启动子进程（Windows 弹新控制台，POSIX 脱离会话后台运行）。"""
    kwargs = {"cwd": str(cwd), "shell": shell}
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def wait_health(url: str, timeout: int = 90) -> bool:
    for _ in range(timeout * 2):
        if health_ok(url):
            return True
        time.sleep(0.5)
    return False


def pause_exit(code: int) -> int:
    if IS_WINDOWS:
        input("按回车退出...")
    return code


# ------------ 依赖缓存 ------------
def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deps_up_to_date(lock_file: Path, source_file: Path) -> bool:
    """lock 文件中记录的哈希与源文件一致则认为依赖已是最新。"""
    if not (lock_file.exists() and source_file.exists()):
        return False
    return lock_file.read_text(encoding="utf-8").strip() == file_sha256(source_file)


def mark_deps(lock_file: Path, source_file: Path) -> None:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(file_sha256(source_file), encoding="utf-8")


def ensure_deps() -> bool:
    """创建虚拟环境 + 安装依赖（带缓存，内容未变则跳过）。"""
    # 后端依赖
    req = BACKEND_DIR / "requirements.txt"
    req_lock = BACKEND_DIR / ".venv" / ".deps_hash"
    if not VENV_PY.exists():
        say("[1/3] 创建虚拟环境 backend\\.venv ...", "blue")
        if not run(["python", "-m", "venv", str(BACKEND_DIR / ".venv")], BASE_DIR):
            say("[错误] 虚拟环境创建失败，请检查 Python 安装是否完整。", "red")
            return False
    if deps_up_to_date(req_lock, req):
        say("[1/3] 后端依赖未变化，跳过安装", "gray")
    else:
        say("[1/3] 安装/更新后端依赖 ...", "blue")
        if not run([str(VENV_PY), "-m", "pip", "install", "-r", str(req)], BACKEND_DIR):
            say("[错误] 后端依赖安装失败，请检查网络后重试。", "red")
            return False
        mark_deps(req_lock, req)

    # 前端依赖
    pkg = FRONTEND_DIR / "package.json"
    pkg_lock = FRONTEND_DIR / "node_modules" / ".deps_hash"
    if not (FRONTEND_DIR / "node_modules").exists():
        say("[2/3] 安装前端依赖（首次运行，可能需要几分钟）...", "blue")
        if not run("npm install", FRONTEND_DIR, shell=True):
            say("[错误] 前端依赖安装失败，请确认已安装 Node.js 18+ 后重试。", "red")
            return False
        mark_deps(pkg_lock, pkg)
    elif deps_up_to_date(pkg_lock, pkg):
        say("[2/3] 前端依赖未变化，跳过安装", "gray")
    else:
        say("[2/3] 检测到 package.json 有变更，更新前端依赖 ...", "blue")
        if not run("npm install", FRONTEND_DIR, shell=True):
            say("[错误] 前端依赖更新失败。", "red")
            return False
        mark_deps(pkg_lock, pkg)
    return True


# ------------ 核心动作 ------------
def free_ports_interactive() -> bool:
    """端口被占用且服务未就绪时，展示占用进程并询问是否释放。"""
    for port in (BACKEND_PORT, FRONTEND_PORT):
        if port_in_use(port) and not health_ok(f"{BACKEND_URL}/health" if port == BACKEND_PORT else FRONTEND_URL):
            pids = pids_on_port(port)
            say(f"  [警告] 端口 {port} 被其他程序占用：", "yellow")
            for pid in pids:
                say(f"      PID {pid}  {pid_cmdline(pid)}", "yellow")
            if not pids:
                continue
            try:
                answer = input(f"  是否结束上述进程并释放端口 {port}？(y/N) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer == "y":
                kill_pids(pids)
                time.sleep(1)
                say(f"  端口 {port} 已释放。", "green")
            else:
                say("  已跳过。请手动关闭占用程序后重试。", "yellow")
                return False
    return True


def cmd_start() -> int:
    backend_running = port_in_use(BACKEND_PORT) and health_ok(f"{BACKEND_URL}/health")
    frontend_running = port_in_use(FRONTEND_PORT)

    if backend_running and frontend_running:
        say("[*] 两个服务均已在运行，直接打开页面。", "green")
        webbrowser.open(FRONTEND_URL)
        return pause_exit(0)

    if not ensure_deps():
        return pause_exit(1)

    say("[3/3] 检查端口 ...", "blue")
    if not free_ports_interactive():
        return pause_exit(1)

    if not backend_running:
        say(f"  启动后端 ({BACKEND_URL}) ...", "blue")
        spawn([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload",
               "--port", str(BACKEND_PORT)], BACKEND_DIR)
    else:
        say("  后端已在运行，跳过", "gray")
    if not frontend_running:
        say(f"  启动前端 ({FRONTEND_URL}) ...", "blue")
        spawn("npm run dev", FRONTEND_DIR, shell=True)
    else:
        say("  前端已在运行，跳过", "gray")

    say("  等待服务就绪（最多 90 秒）...", "dim")
    backend_ok = backend_running or wait_health(f"{BACKEND_URL}/health")
    frontend_ok = frontend_running or wait_health(FRONTEND_URL)
    if not backend_ok:
        say("[警告] 后端未在预期时间内就绪，请查看后端窗口中的日志。", "yellow")
    if not frontend_ok:
        say("[警告] 前端未在预期时间内就绪，请查看前端窗口中的日志。", "yellow")

    if backend_ok or frontend_ok:
        url = FRONTEND_URL if frontend_ok else BACKEND_URL
        webbrowser.open(url)
        say(f"  已打开浏览器: {url}", "green")

    say()
    say("=" * 62, "cyan")
    say("  启动完成！关闭对应窗口或运行 stop 命令即可停止服务。", "bold")
    say(f"    前端页面  {FRONTEND_URL}")
    say(f"    接口文档  {BACKEND_URL}/docs")
    say("=" * 62, "cyan")
    return pause_exit(0)


def cmd_stop() -> int:
    stopped_any = False
    for name, port, url in (("后端", BACKEND_PORT, f"{BACKEND_URL}/health"), ("前端", FRONTEND_PORT, FRONTEND_URL)):
        pids = pids_on_port(port)
        if not pids:
            say(f"  {name} (:{port}) 未在运行", "gray")
            continue
        for pid in pids:
            say(f"  停止 {name} (:{port})  PID {pid}  {pid_cmdline(pid)}", "yellow")
        kill_pids(pids)
        stopped_any = True
    if stopped_any:
        time.sleep(1)
        say("  已停止。", "green")
    else:
        say("  没有需要停止的服务。", "dim")
    return pause_exit(0)


def cmd_status() -> int:
    rows = [
        ("后端 API", BACKEND_URL, f"{BACKEND_URL}/health"),
        ("前端页面", FRONTEND_URL, FRONTEND_URL),
    ]
    say()
    for name, url, check in rows:
        running = health_ok(check)
        state = f"{C['green']}● 运行中{C['reset']}" if running else f"{C['red']}○ 未响应{C['reset']}"
        say(f"  {state}  {name:<8} {url}")
    if not any(health_ok(c) for _, _, c in rows):
        say("  提示：运行 python launcher.py start 启动服务。", "dim")
    say()
    return pause_exit(0)


def cmd_restart() -> int:
    cmd_stop_quiet()
    say()
    return cmd_start()


def cmd_stop_quiet() -> None:
    for port in (BACKEND_PORT, FRONTEND_PORT):
        pids = pids_on_port(port)
        if pids:
            kill_pids(pids)
    time.sleep(1)


def interactive_menu() -> int:
    while True:
        os.system("cls" if IS_WINDOWS else "clear")
        banner()
        say("  [1] 启动服务        (start)")
        say("  [2] 停止服务        (stop)")
        say("  [3] 重启服务        (restart)")
        say("  [4] 查看状态        (status)")
        say("  [0] 退出")
        say()
        try:
            choice = input("  请选择: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice in ("1", "start"):
            return cmd_start()
        if choice in ("2", "stop"):
            cmd_stop()
            input("按回车返回菜单...")
        elif choice in ("3", "restart"):
            return cmd_restart()
        elif choice in ("4", "status"):
            cmd_status()
            input("按回车返回菜单...")
        elif choice in ("0", "q", "exit"):
            return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} 一键启动器")
    parser.add_argument("command", nargs="?", choices=["start", "stop", "restart", "status"],
                        help="不传则进入交互菜单")
    args = parser.parse_args()

    if args.command is None:
        return interactive_menu()
    banner()
    return {"start": cmd_start, "stop": cmd_stop, "restart": cmd_restart, "status": cmd_status}[args.command]()


if __name__ == "__main__":
    sys.exit(main())
