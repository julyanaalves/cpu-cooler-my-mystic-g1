import hid
import psutil
import time

VENDOR_ID = 0xAA88
PRODUCT_ID = 0x8666


def get_cpu_temp() -> float:
    temps = psutil.sensors_temperatures()
    if not temps:
        raise RuntimeError("psutil não retornou sensores de temperatura.")

    if 'k10temp' in temps and temps['k10temp']:
        return temps['k10temp'][0].current

    for readings in temps.values():
        if readings:
            return readings[0].current

    raise RuntimeError("Não encontrei nenhum sensor de temperatura em psutil.")


def open_device(vendor_id: int, product_id: int) -> hid.device:
    matches = hid.enumerate(vendor_id, product_id)
    if not matches:
        raise RuntimeError(
            f"Não encontrei o dispositivo HID {vendor_id:04x}:{product_id:04x}. "
            "Confirme o VID/PID com lsusb e se a regra udev foi aplicada."
        )

    last_error: Exception | None = None
    for info in matches:
        path = info.get("path")
        if not path:
            continue
        dev = hid.device()
        try:
            dev.open_path(path)
            return dev
        except OSError as exc:
            last_error = exc

    raise RuntimeError(
        "Achei o dispositivo, mas não consegui abrir nenhuma interface HID. "
        "Tente executar o script como root para diagnosticar ou verifique permissões."
    ) from last_error


def write_to_cpu_fan_display(dev: hid.device) -> bool:
    try:
        cpu_temp = int(round(get_cpu_temp()))
    except RuntimeError as exc:
        print(f"Não consegui ler temperatura da CPU: {exc}")
        return False

    payload = bytes([0x00, max(0, min(cpu_temp, 255))])
    try:
        written = dev.write(payload)
    except OSError as exc:
        print(f"Erro escrevendo comando HID: {exc}")
        return False

    if written != len(payload):
        print(f"Escrevi {written} bytes, mas esperava {len(payload)}.")
        return False
    return True


def main() -> None:
    device = open_device(VENDOR_ID, PRODUCT_ID)
    print(f"Conectado ao dispositivo {PRODUCT_ID:04x}\n")
    interval = 1.0
    reconnect_delay = 2.0
    try:
        while True:
            ok = write_to_cpu_fan_display(device)
            if not ok:
                try:
                    device.close()
                except OSError:
                    pass
                print("Tentando reabrir o dispositivo...")
                while True:
                    try:
                        device = open_device(VENDOR_ID, PRODUCT_ID)
                        print("Dispositivo reaberto com sucesso.")
                        break
                    except RuntimeError as exc:
                        print(str(exc))
                    time.sleep(reconnect_delay)
            time.sleep(interval)
    except KeyboardInterrupt:
        device.close()
        print("Encerrando monitoramento.")


if __name__ == "__main__":
    main()