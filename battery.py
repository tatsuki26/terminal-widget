"""接続中の BLE 機器から Battery Service (0x180F) の電池残量を読む。

ZMK Battery Bar と同じ方法。接続済みの機器は広告を出さないため、スキャンではなく
CoreBluetooth の retrieveConnectedPeripheralsWithServices を使う。bleak の公開 API には
この機能がないので、内部の CentralManagerDelegate を使っている（bleak は固定版）。
"""

import asyncio
from dataclasses import dataclass, field

import CoreBluetooth as CB
from bleak import BleakClient
from bleak.backends.corebluetooth.CentralManagerDelegate import CentralManagerDelegate
from bleak.backends.device import BLEDevice

BATTERY_SERVICE = "0000180f"
USER_DESCRIPTION = "00002901"


@dataclass
class DeviceBattery:
    name: str
    # 役割ラベル ("C" = 中央 / "P" = 周辺 / "" = 単体) -> 残量 %
    levels: dict[str, int] = field(default_factory=dict)


async def _read_device(delegate, peripheral) -> DeviceBattery:
    device = BLEDevice(str(peripheral.identifier()), peripheral.name(), (peripheral, delegate))
    result = DeviceBattery(name=peripheral.name() or "unknown")
    async with BleakClient(device, timeout=10) as client:
        chars = [
            c
            for s in client.services
            if s.uuid.startswith(BATTERY_SERVICE)
            for c in s.characteristics
            if c.uuid.startswith("00002a19")
        ]
        for i, char in enumerate(chars):
            level = (await client.read_gatt_char(char))[0]
            desc = ""
            for d in char.descriptors:
                if d.uuid.startswith(USER_DESCRIPTION):
                    desc = bytes(await client.read_gatt_descriptor(d.handle)).decode(errors="ignore")
            if len(chars) == 1:
                label = ""
            else:
                # ZMK: 周辺側は "Peripheral N"、中央側は説明なし
                label = "P" if desc.startswith("Peripheral") else "C"
                if label in result.levels:
                    label = f"{label}{i}"
            result.levels[label] = level
    return result


class BatteryReader:
    """asyncio ループ上で使う。電池残量を読めた機器のリストを返す。"""

    def __init__(self) -> None:
        self._delegate: CentralManagerDelegate | None = None

    async def read(self) -> list[DeviceBattery]:
        if self._delegate is None:
            self._delegate = CentralManagerDelegate()
        await self._delegate.wait_until_ready()
        uuid = CB.CBUUID.UUIDWithString_("180F")
        peripherals = self._delegate.central_manager.retrieveConnectedPeripheralsWithServices_([uuid])
        results = []
        for p in peripherals:
            try:
                dev = await asyncio.wait_for(_read_device(self._delegate, p), timeout=20)
            except Exception:
                continue
            if dev.levels:
                results.append(dev)
        return results
