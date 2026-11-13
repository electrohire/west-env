# J-Link Flashing — west-env

`west-env` supports firmware flashing using **host-side J-Link tools** as the
default strategy. Build artifacts are synced from the container to the host
filesystem, then flashed with the native J-Link installation. No USB
passthrough into the container is required.

## Default flow (host mode)

```
[container] west build → zephyr.elf / zephyr.hex
       ↓  west env sync --back
[host]  artifacts/build/zephyr/zephyr.hex
       ↓  west env flash artifacts/build/zephyr/zephyr.hex
[host]  JLinkExe (Windows) / JLinkExe (Linux/macOS)
       ↓
[target board via USB J-Link]
```

No USB passthrough into the container. No Zephyr runner inside the container.

---

## Configuration

```yaml
jlink:
  mode: host        # (default) flash with host J-Link tools
  # mode: tcp-server  # start GDB server on host; GDB connects from container
  # mode: none        # disable flash/debug via west-env
  serial: 69656048  # optional: pin one probe by serial (-SelectEmuBySN)
  interface: SWD    # SWD (default) or JTAG
```

On a bench with more than one probe attached, set `serial`: without it
J-Link connects to an arbitrary probe. `interface` selects the target
interface in the commander script (`si SWD` / `si JTAG`).

---

## Prerequisites

1. Install [SEGGER J-Link](https://www.segger.com/downloads/jlink/).
2. Connect the target board via a J-Link probe.
3. `west env doctor` reports `[PASS] J-Link host tools: /path/to/JLinkExe`.

Default search paths:
- **Windows:** `C:\Program Files\SEGGER\JLink\JLink.exe` (also checks PATH)
- **Linux:** `/opt/SEGGER/JLink/JLinkExe`, `/usr/bin/JLinkExe`
- **macOS:** `/Applications/SEGGER/JLink/JLinkExe`

---

## Flashing

```sh
# After building and syncing artifacts:
west env flash artifacts/build/zephyr/zephyr.hex

# Specify J-Link device explicitly:
west env flash artifacts/build/zephyr/zephyr.hex -- --device nRF52840_xxAA

# Or pin the probe for one run (overrides jlink.serial):
west env flash artifacts/build/zephyr/zephyr.hex -- --serial 69656048
```

The commander script is written to a temporary file and passed with
`-CommanderScript` (no `/dev/stdin`, which does not exist on Windows).
The flash verdict reads the captured J-Link output: J-Link exits 0 for
many script failures, so known failure markers in the output (for
example "Cannot connect to target") fail the flash even on exit code 0.

`west env flash` automatically calls `west env sync --back` if
`workspace_mode` is `sync` or `copy`, so you do not need to run sync separately.

---

## TCP GDB server mode

For debugging inside the container, start a J-Link GDB server on the host and
connect from a container-side GDB session over TCP.

```yaml
jlink:
  mode: tcp-server
```

```sh
# Start GDB server (blocks until killed)
west env debug nRF52840_xxAA

# In another terminal or inside the container:
arm-none-eabi-gdb zephyr.elf
(gdb) target remote host.docker.internal:2331
```

The default GDB port is 2331.

---

## Windows-specific notes

- J-Link for Windows installs as `JLink.exe` and `JLinkExe.exe` (both probed).
- The board connects via USB to the Windows host — no passthrough into any VM
  or WSL instance required.
- Build artifacts are synced to a Windows path by `west env sync --back` and
  flashed directly from there.

---

## Disabling flash

```yaml
jlink:
  mode: none
```

`west env flash` and `west env debug` will exit with an error when `mode: none`.
Use this when you flash via a different tool (e.g. OpenOCD, pyOCD, or a custom
runner script).
