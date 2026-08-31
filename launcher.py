# -*- coding: utf-8 -*-
"""国际贸易上市公司一站式智能服务平台 —— 一键启动器（源码运行，不打包）

启动流程：
检查 Python -> 创建虚拟环境 -> 安装后端依赖 -> 安装前端依赖
-> 检测端口占用 -> 分别弹出独立窗口启动前后端 -> 健康检查 -> 打开浏览器。
"""
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

# 项目根目录：脚本所在目录
BASE_DIR = Path(__file__).resolve().parent

BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
IS_WINDOWS = os.name == "nt"
VENV_PY = BACKEND_DIR / ".venv" / (Path("Scripts") / "python.exe" if IS_WINDOWS else Path("bin") / "python")

BACKEND_PORT = 8009
FRONTEND_PORT = 5173


def spawn(cmd, cwd: Path, shell: bool = False) -> None:
    """在独立终端窗口启动子进程（Windows 弹新控制台，POSIX 脱离会话后台运行）。"""
    kwargs = {"cwd": str(cwd), "shell": shell}
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def banner() -> None:
    print("=" * 62)
    print(f"  {APP_NAME}  · 一键启动")
    print("=" * 62)


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


def wait_health(url: str, timeout: int = 90) -> bool:
    for _ in range(timeout * 2):
        if health_ok(url):
            return True
        time.sleep(0.5)
    return False


def run(cmd, cwd: Path, shell: bool = False) -> bool:
    try:
        return subprocess.run(cmd, cwd=str(cwd), shell=shell).returncode == 0
    except Exception as e:  # noqa: BLE001
        print(f"  [错误] 执行失败: {e}")
        return False


def main() -> int:
    banner()

    # 0) Python 环境检查
    if shutil.which("python") is None:
        print("[错误] 未检测到 Python。请安装 Python 3.11+，并勾选 'Add to PATH'。")
        input("按回车退出...")
        return 1

    # 1) 虚拟环境
    if not VENV_PY.exists():
        print("[1/4] 创建虚拟环境 backend\\.venv ...")
        if not run(["python", "-m", "venv", str(BACKEND_DIR / ".venv")], BASE_DIR):
            print("[错误] 虚拟环境创建失败，请检查 Python 安装是否完整。")
            input("按回车退出...")
            return 1
    else:
        print("[1/4] 虚拟环境已存在，跳过")

    # 2) 后端依赖
    print("[2/4] 安装/更新后端依赖 ...")
    if not run([str(VENV_PY), "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")], BACKEND_DIR):
        print("[错误] 后端依赖安装失败，请检查网络后重试。")
        input("按回车退出...")
        return 1

    # 3) 前端依赖
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[3/4] 安装前端依赖（首次运行，可能需要几分钟）...")
        if not run("npm install", FRONTEND_DIR, shell=True):
            print("[错误] 前端依赖安装失败，请确认已安装 Node.js 18+ 后重试。")
            input("按回车退出...")
            return 1
    else:
        print("[3/4] 前端依赖已存在，跳过")

    # 4) 端口检查
    print("[4/4] 检查端口占用 ...")
    backend_running = port_in_use(BACKEND_PORT) and health_ok(
        f"http://localhost:{BACKEND_PORT}/health"
    )
    frontend_running = port_in_use(FRONTEND_PORT)
    if backend_running and frontend_running:
        print("  两个服务均已在运行，直接打开页面。")
    elif port_in_use(BACKEND_PORT) or port_in_use(FRONTEND_PORT):
        print(f"  [警告] 端口 {BACKEND_PORT}/{FRONTEND_PORT} 被占用但服务未就绪。")
        print("  请关闭占用端口的程序后重试（netstat -ano | findstr 8009）。")
        input("按回车退出...")
        return 1

    # 5) 启动服务（各自独立窗口，关闭窗口即停止）
    if not backend_running:
        print(f"  启动后端 (http://localhost:{BACKEND_PORT}) ...")
        spawn([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload",
               "--port", str(BACKEND_PORT)], BACKEND_DIR)
    if not frontend_running:
        print(f"  启动前端 (http://localhost:{FRONTEND_PORT}) ...")
        spawn("npm run dev", FRONTEND_DIR, shell=True)

    # 6) 等待服务就绪
    print("  等待服务就绪（最多 90 秒）...")
    backend_ok = wait_health(f"http://localhost:{BACKEND_PORT}/health")
    frontend_ok = wait_health(f"http://localhost:{FRONTEND_PORT}")
    if not backend_ok:
        print("[警告] 后端未在预期时间内就绪，请查看后端窗口中的日志。")
    if not frontend_ok:
        print("[警告] 前端未在预期时间内就绪，请查看前端窗口中的日志。")

    # 7) 打开浏览器
    url = f"http://localhost:{FRONTEND_PORT if frontend_ok else BACKEND_PORT}"
    if frontend_ok or backend_ok:
        webbrowser.open(url)
        print(f"  已打开浏览器: {url}")

    print()
    print("=" * 62)
    print("  启动完成！服务运行在独立窗口中，关闭对应窗口即可停止。")
    print(f"    前端页面  http://localhost:{FRONTEND_PORT}")
    print(f"    接口文档  http://localhost:{BACKEND_PORT}/docs")
    print("=" * 62)
    print()
    input("按回车关闭本窗口（不影响已启动的服务）...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
