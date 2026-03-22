from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import proxy.tg_ws_proxy as tg_ws_proxy

APP_SLUG = "tg-ws-proxy-android"
APP_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_SLUG
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "proxy.log"

DEFAULT_CONFIG: Dict[str, Any] = {
    "port": 1080,
    "host": "127.0.0.1",
    "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
    "verbose": False,
    "log_max_mb": 5,
    "log_backups": 1,
    "buf_kb": 256,
    "pool_size": 4,
    "wake_lock": False,
}

log = logging.getLogger("tg-ws-proxy-android")


def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("config root must be an object")
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            if not isinstance(merged.get("dc_ip"), list):
                merged["dc_ip"] = list(DEFAULT_CONFIG["dc_ip"])
            return merged
        except Exception as exc:
            raise RuntimeError(f"Не удалось прочитать {CONFIG_FILE}: {exc}")
    return dict(DEFAULT_CONFIG)


def save_config(cfg: Dict[str, Any], overwrite: bool = True) -> None:
    ensure_dirs()
    if CONFIG_FILE.exists() and not overwrite:
        raise FileExistsError(str(CONFIG_FILE))
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def setup_logging(verbose: bool, log_max_mb: float, log_backups: int) -> None:
    ensure_dirs()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-5s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-5s  %(message)s",
        datefmt="%H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(console_formatter)
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=max(32 * 1024, int(log_max_mb * 1024 * 1024)),
        backupCount=max(0, int(log_backups)),
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def add_bool_toggle(
    parser: argparse.ArgumentParser,
    name: str,
    *,
    help_enable: str,
    help_disable: str,
) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(f"--{name}", dest=name.replace("-", "_"), action="store_true", default=None, help=help_enable)
    group.add_argument(f"--no-{name}", dest=name.replace("-", "_"), action="store_false", help=help_disable)


def add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--port", type=int, default=None, help="Порт локального SOCKS5-прокси")
    parser.add_argument("--host", type=str, default=None, help="Хост для bind (обычно 127.0.0.1)")
    parser.add_argument(
        "--dc-ip",
        metavar="DC:IP",
        action="append",
        default=None,
        help="Переопределение целевого IP для Telegram DC, можно указывать несколько раз",
    )
    parser.add_argument("--log-max-mb", type=float, default=None, help="Максимальный размер лог-файла в МБ")
    parser.add_argument("--log-backups", type=int, default=None, help="Сколько архивов логов хранить")
    parser.add_argument("--buf-kb", type=int, default=None, help="Размер send/recv буфера в КБ")
    parser.add_argument("--pool-size", type=int, default=None, help="Размер пула WS-соединений на DC")
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument("-v", "--verbose", dest="verbose", action="store_true", default=None, help="Включить DEBUG-логирование")
    verbose_group.add_argument("--no-verbose", dest="verbose", action="store_false", help="Отключить DEBUG-логирование")

    wake_group = parser.add_mutually_exclusive_group()
    wake_group.add_argument("-w", "--wake-lock", dest="wake_lock", action="store_true", default=None, help="Перед запуском попытаться взять termux-wake-lock")
    wake_group.add_argument("--no-wake-lock", dest="wake_lock", action="store_false", help="Не брать wake-lock перед запуском")


def merge_config(base: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    merged = dict(base)
    for key in ("port", "host", "log_max_mb", "log_backups", "buf_kb", "pool_size", "verbose", "wake_lock"):
        value = getattr(args, key, None)
        if value is not None:
            merged[key] = value
    if getattr(args, "dc_ip", None) is not None:
        merged["dc_ip"] = args.dc_ip
    return merged


def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or prefix.startswith("/data/data/com.termux/")


def maybe_acquire_wake_lock(enabled: bool) -> None:
    if not enabled:
        return
    cmd = shutil.which("termux-wake-lock")
    if not cmd:
        log.warning("termux-wake-lock не найден; запускаю без него")
        return
    try:
        subprocess.run([cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("termux-wake-lock выполнен")
    except Exception as exc:
        log.warning("Не удалось вызвать termux-wake-lock: %s", exc)


def proxy_deep_links(host: str, port: int) -> List[str]:
    query = urlencode({"server": host, "port": str(port)})
    return [
        f"tg://socks?{query}",
        f"https://t.me/socks?{query}",
    ]


def open_url(url: str) -> bool:
    opener = shutil.which("termux-open-url")
    if opener:
        try:
            result = subprocess.run([opener, url], check=False)
            if result.returncode == 0:
                return True
        except Exception:
            pass

    am = shutil.which("am") or "/system/bin/am"
    if Path(am).exists() or shutil.which("am"):
        try:
            result = subprocess.run(
                [am, "start", "-a", "android.intent.action.VIEW", "-d", url],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False


def command_init(args: argparse.Namespace) -> int:
    if CONFIG_FILE.exists() and not args.overwrite:
        print(f"Конфиг уже существует: {CONFIG_FILE}")
        print("Используй --overwrite, если хочешь перезаписать его.")
        return 1
    save_config(dict(DEFAULT_CONFIG), overwrite=True)
    print(f"Создан конфиг: {CONFIG_FILE}")
    print(f"Логи будут писаться в: {LOG_FILE}")
    return 0


def command_paths(_: argparse.Namespace) -> int:
    print(f"APP_DIR={APP_DIR}")
    print(f"CONFIG_FILE={CONFIG_FILE}")
    print(f"LOG_FILE={LOG_FILE}")
    print(f"TERMUX={'yes' if is_termux() else 'no'}")
    return 0


def command_show_config(_: argparse.Namespace) -> int:
    cfg = load_config()
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
    return 0


def command_open(args: argparse.Namespace) -> int:
    cfg = load_config()
    port = args.port if args.port is not None else int(cfg.get("port", DEFAULT_CONFIG["port"]))
    host = args.host if args.host is not None else str(cfg.get("host", DEFAULT_CONFIG["host"]))
    urls = proxy_deep_links(host, port)

    for url in urls:
        if open_url(url):
            print(f"Открыта ссылка: {url}")
            return 0

    print("Не удалось автоматически открыть Telegram.")
    print("Скопируй одну из ссылок и открой вручную:")
    for url in urls:
        print(url)
    return 1


def command_start(args: argparse.Namespace) -> int:
    cfg = merge_config(load_config(), args)
    setup_logging(bool(cfg["verbose"]), float(cfg["log_max_mb"]), int(cfg["log_backups"]))

    maybe_acquire_wake_lock(bool(cfg["wake_lock"]))

    try:
        dc_opt = tg_ws_proxy.parse_dc_ip_list(list(cfg["dc_ip"]))
    except ValueError as exc:
        log.error(str(exc))
        return 2

    tg_ws_proxy._RECV_BUF = max(4, int(cfg["buf_kb"])) * 1024
    tg_ws_proxy._SEND_BUF = tg_ws_proxy._RECV_BUF
    tg_ws_proxy._WS_POOL_SIZE = max(0, int(cfg["pool_size"]))

    log.info("=" * 60)
    log.info("TG WS Proxy Android launcher")
    log.info("Config file: %s", CONFIG_FILE)
    log.info("Log file: %s", LOG_FILE)
    log.info("Termux detected: %s", "yes" if is_termux() else "no")
    log.info("Open Telegram proxy URL: %s", proxy_deep_links(str(cfg["host"]), int(cfg["port"]))[0])
    log.info("=" * 60)

    try:
        tg_ws_proxy.run_proxy(
            port=int(cfg["port"]),
            dc_opt=dc_opt,
            host=str(cfg["host"]),
        )
    except KeyboardInterrupt:
        log.info("Shutting down. Final stats: %s", tg_ws_proxy._stats.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Android/Termux launcher for TG WS Proxy",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="Создать дефолтный config.json")
    p_init.add_argument("--overwrite", action="store_true", help="Перезаписать существующий конфиг")
    p_init.set_defaults(func=command_init)

    p_start = subparsers.add_parser("start", help="Запустить прокси с конфигом из ~/.config")
    add_runtime_arguments(p_start)
    p_start.set_defaults(func=command_start)

    p_open = subparsers.add_parser("open", help="Открыть Telegram со ссылкой на локальный SOCKS5")
    p_open.add_argument("--port", type=int, default=None, help="Порт локального SOCKS5-прокси")
    p_open.add_argument("--host", type=str, default=None, help="Хост локального SOCKS5-прокси")
    p_open.set_defaults(func=command_open)

    p_paths = subparsers.add_parser("paths", help="Показать рабочие пути")
    p_paths.set_defaults(func=command_paths)

    p_show = subparsers.add_parser("show-config", help="Показать итоговый config.json")
    p_show.set_defaults(func=command_show_config)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = int(args.func(args))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        code = 2
    sys.exit(code)


if __name__ == "__main__":
    main()
