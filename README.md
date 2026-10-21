# terminal-widget

ターミナルの隅に置ける小さなウィジェット。macOS 専用。

```
  󰥔 11:05:08
  󰌌 roBa  C 󰁹 92%  P 󰁾 75%
```

- 現在時刻（秒まで、毎秒更新）
- 接続中の Bluetooth LE 機器の電池残量（キーボードなど）。取得できないときは「取得できません」と表示

## 起動

```sh
./run
```

初回だけ `.venv` を作って依存（`rich`, `bleak`）を入れます。終了は Ctrl-C。
どこからでも起動したい場合は `alias tw='~/Development/terminal-widget/run'` などを `~/.zshrc` に。

Nerd Font（JetBrainsMono Nerd Font など）が必要です。

## 必要なもの

- macOS 14 以降、Python 3.10 以降
- ターミナルへの Bluetooth 権限（初回にダイアログが出ます。出ない／拒否した場合は
  システム設定 > プライバシーとセキュリティ > Bluetooth でターミナルを許可）

## 電池残量の取得方法

`system_profiler SPBluetoothDataType` や `ioreg`（`BatteryPercent`）には BLE キーボードの
電池情報が出ません（ZMK の roBa で確認）。そのため、
[ZMK Battery Bar](https://github.com/itouuuuuuuuu/zmk-battery-bar) と同じく、
CoreBluetooth で接続中の機器から BLE Battery Service (0x180F) の Battery Level (0x2A19) を
GATT で直接読んでいます。60 秒ごとに更新します。

- ZMK の分割キーボードは Battery Level が 2 つあり、`C`（中央側）と `P`（周辺側）で表示します。
  どちらが左右かは見分けられません。
- 周辺側が出ない場合は、中央側の `.conf` に次を追加してください。

  ```ini
  CONFIG_ZMK_BATTERY_REPORTING=y
  CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=y
  CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y
  ```

## 注意

- bleak の公開 API では「接続済み機器の取得」ができないため、内部クラス
  （`CentralManagerDelegate`）を使っています。bleak を更新すると動かなくなる可能性があるので
  `requirements.txt` で `bleak==3.0.2` に固定しています。
- 電池残量の取得に失敗した場合は、次の更新（60 秒後）まで「取得できません」を表示します。

## 構成

| ファイル | 内容 |
|---|---|
| `widget.py` | 表示（rich）と電池取得スレッド |
| `battery.py` | BLE Battery Service の読み取り |
| `run` | venv 作成と起動 |
