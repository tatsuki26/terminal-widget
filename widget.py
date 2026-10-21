"""ターミナル用の小さなウィジェット: 時計 + Bluetooth 機器の電池残量。"""

import asyncio
import os
import threading
import time
from datetime import datetime

from rich.console import Group
from rich.live import Live
from rich.text import Text

from battery import BatteryReader, DeviceBattery

BATTERY_POLL_SECONDS = 60

ICON_CLOCK = ""
ICON_KEYBOARD = ""
# nf-fa-battery_0 .. battery_4
ICON_BATTERY = ["", "", "", "", ""]


class BatteryPoller(threading.Thread):
    """別スレッドで電池残量を定期取得する。失敗時は devices=None になる。"""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.devices: list[DeviceBattery] | None = None
        self.loaded = False

    def run(self) -> None:
        asyncio.run(self._loop())

    async def _loop(self) -> None:
        reader = BatteryReader()
        while True:
            try:
                devices = await reader.read()
            except Exception:
                devices = []
            self.devices = devices or None
            self.loaded = True
            await asyncio.sleep(BATTERY_POLL_SECONDS)


def level_style(level: int) -> str:
    if level <= 15:
        return "bold red"
    if level <= 30:
        return "yellow"
    return "green"


def battery_icon(level: int) -> str:
    return ICON_BATTERY[min(4, level * 5 // 100)]


def render(poller: BatteryPoller) -> Group:
    clock = Text(f" {ICON_CLOCK} {datetime.now():%H:%M:%S}", style="bold green")
    lines = [clock]
    devices = poller.devices
    if not poller.loaded:
        lines.append(Text(f" {ICON_KEYBOARD} 取得中…", style="dim green"))
    elif not devices:
        lines.append(Text(f" {ICON_KEYBOARD} 取得できません", style="dim"))
    else:
        for dev in devices:
            line = Text(f" {ICON_KEYBOARD} {dev.name}", style="green")
            for label, level in dev.levels.items():
                line.append(f"  {label} " if label else "  ", style="dim green")
                line.append(f"{battery_icon(level)} {level}%", style=level_style(level))
            lines.append(line)
    return Group(*lines)


def main() -> None:
    poller = BatteryPoller()
    poller.start()
    try:
        with Live(render(poller), refresh_per_second=4, screen=False) as live:
            while True:
                live.update(render(poller))
                time.sleep(1 - time.time() % 1)  # 秒の切り替わりに合わせる
    except KeyboardInterrupt:
        pass
    # CoreBluetooth 待機中のスレッドが通常終了を妨げることがあるため即終了する
    os._exit(0)


if __name__ == "__main__":
    main()
