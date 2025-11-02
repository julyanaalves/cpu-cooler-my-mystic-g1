# Mancer Mystic G1 no Linux

Script em Python que lê a temperatura da CPU (via `psutil`) e envia o valor para o display USB do water cooler Mancer Mystic G1. A fabricante só entrega software para Windows; este projeto substitui essa funcionalidade no Linux e ainda reconecta automaticamente caso o dispositivo USB seja reenumerado (ex.: após suspensão).

![](images/cpu-cooler.jpeg)
![](images/water-cooler-husky-glacier-argb.webp)

---

## Pré-requisitos

- Python 3.11+ (testado em 3.13)
- Dependências Python: `hidapi`, `psutil`
- Acesso ao dispositivo USB `aa88:8666` (Mystic G1)

Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv .venv
source .venv/bin/activate
pip install hidapi psutil
```

## Configurando permissão (udev)

Para rodar sem `sudo`, instale a regra udev que libera tanto o nó `hidraw` quanto o nó USB bruto usado pelo `hidapi`:

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="aa88", ATTRS{idProduct}=="8666", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="aa88", ATTR{idProduct}=="8666", MODE="0666", TAG+="uaccess"
```

1. Copie `udev/99-mystic-g1-cpu-cooler.rules` para `/etc/udev/rules.d/`:

	```bash
	sudo cp udev/99-mystic-g1-cpu-cooler.rules /etc/udev/rules.d/
	sudo udevadm control --reload
	```

2. Reaplique a regra ao dispositivo sem precisar desconectar:

	```bash
	lsusb | grep -i aa88            # identifique bus/device, ex: 001/002
	sudo udevadm trigger --name=/dev/bus/usb/001/002 --action=add
	```

3. Confirme permissões 0666 em `/dev/hidrawX` e `/dev/bus/usb/BBB/DDD`. Se necessário, faça rebind:

	```bash
	echo '1-7:1.0' | sudo tee /sys/bus/usb/drivers/usbhid/unbind
	echo '1-7:1.0' | sudo tee /sys/bus/usb/drivers/usbhid/bind
	```

## Execução manual

Com a venv ativa e permissões aplicadas:

```bash
python cpu_cooler.py
```

O script imprime `Conectado ao dispositivo 8666` e segue atualizando o display a cada segundo. Interrompa com `Ctrl+C`.
Se a escrita falhar (dispositivo desconectado, suspensão, etc.), ele fecha o handle e tenta reabrir a cada 2 segundos até voltar a funcionar.

## Rodando como serviço systemd

Um unit file de usuário está pronto em `cpu-cooler.service`.

```bash
mkdir -p ~/.config/systemd/user
cp cpu-cooler.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cpu-cooler.service
```

Após atualizar o código, recarregue com `systemctl --user daemon-reload` e `systemctl --user restart cpu-cooler.service` para usar a versão nova.

Para que o serviço suba antes do login gráfico, habilite linger:

```bash
sudo loginctl enable-linger $USER
```

Verifique logs/status:

```bash
systemctl --user status cpu-cooler.service
journalctl --user -u cpu-cooler.service -f
```

## Solução de problemas

- **`OSError: open failed`**: verifique permissões dos nós `hidraw` e `/dev/bus/usb/BBB/DDD`; confirme se o VID/PID continua `aa88:8666` (alterações de porta podem mudar `BBB/DDD`).
- **`psutil não retornou sensores`**: instale pacotes de sensores (`lm-sensors`) e carregue módulos (ex.: `k10temp` para AMD). Use `psutil.sensors_temperatures()` para listar opções.
- **Pylance reclamando de imports**: selecione a venv em `Python: Select Interpreter` ou use `python.analysis.extraPaths` conforme `.vscode/settings.json`.

---

Projeto adaptado por Julyana Alves a partir das ideias de https://github.com/martiniano/.
