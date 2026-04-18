#!/usr/bin/env python3
"""
Configurador de punto de acceso WiFi para Raspberry Pi.
Soporta dos métodos:
  - NetworkManager (nmcli)
  - Manual (hostapd + dnsmasq)
"""

from pathlib import Path
import subprocess
import shutil
import sys
import time
import os
import signal
import argparse
import tempfile


class RaspberryAccessPointNMConfigurator:
    """Configura un AP usando NetworkManager (nmcli)."""
    def __init__(
        self,
        ssid="TurtleRally-AP",
        password="123456789",
        wlan_interface="wlan0",
        ap_ip="192.168.4.1/24",
        gateway="192.168.4.1",
        dhcp_range_note="192.168.4.2-192.168.4.20",
        channel=6,
        country_code="ES",
        connection_name="TurtleRally-AP",
    ):
        self.ssid = ssid
        self.password = password
        self.wlan_interface = wlan_interface
        self.ap_ip = ap_ip
        self.gateway = gateway
        self.dhcp_range_note = dhcp_range_note
        self.channel = str(channel)
        self.country_code = country_code
        self.connection_name = connection_name

    def run(self, cmd, check=True, capture_output=False):
        return subprocess.run(cmd, check=check, text=True, capture_output=capture_output)

    def ensure_root(self):
        if os.geteuid() != 0:
            print("[ERROR] Este script debe ejecutarse con sudo o como root.")
            sys.exit(1)

    def command_exists(self, command):
        return shutil.which(command) is not None

    def ensure_nmcli(self):
        if not self.command_exists("nmcli"):
            print("[ERROR] nmcli no está disponible. Instala NetworkManager.")
            sys.exit(1)

    def ensure_networkmanager(self):
        result = subprocess.run(["systemctl", "is-active", "NetworkManager"], text=True, capture_output=True)
        if result.stdout.strip() != "active":
            print("[INFO] NetworkManager no está activo. Intentando habilitarlo y arrancarlo...")
            subprocess.run(["systemctl", "enable", "NetworkManager"], check=False)
            subprocess.run(["systemctl", "start", "NetworkManager"], check=False)

        result = subprocess.run(["systemctl", "is-active", "NetworkManager"], text=True, capture_output=True)
        if result.stdout.strip() != "active":
            print("[ERROR] NetworkManager no está activo.")
            sys.exit(1)

        print("[OK] NetworkManager activo")

    def set_regulatory_domain(self):
        if self.command_exists("raspi-config"):
            print(f"[INFO] Intentando fijar regulatory domain a {self.country_code}")
            subprocess.run(["raspi-config", "nonint", "do_wifi_country", self.country_code], check=False)
        else:
            print("[WARN] raspi-config no disponible; verifica manualmente el país WiFi si hay problemas de canal.")

    def connection_exists(self):
        result = self.run(["nmcli", "-t", "-f", "NAME", "connection", "show"], capture_output=True)
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return self.connection_name in names

    def delete_existing_connection(self):
        if self.connection_exists():
            print(f"[INFO] Eliminando conexión previa: {self.connection_name}")
            self.run(["nmcli", "connection", "delete", self.connection_name], check=False)

    def release_ap_ip(self):
        ip = self.gateway

        print(f"[INFO] Liberando IP/sockets previos en {ip} ...")
        self.run(["fuser", "-k", f"{ip}/tcp"], check=False)
        self.run(["fuser", "-k", f"{ip}/udp"], check=False)
        self.run(["fuser", "-k", "67/udp"], check=False)
        self.run(["fuser", "-k", "68/udp"], check=False)

        result = subprocess.run(
            ["ip", "addr", "show", self.wlan_interface],
            text=True,
            capture_output=True
        )

        if ip in result.stdout:
            print(f"[INFO] Eliminando IP residual {self.ap_ip} de {self.wlan_interface}")
            subprocess.run(
                ["ip", "addr", "del", self.ap_ip, "dev", self.wlan_interface],
                check=False,
                text=True,
                capture_output=True
            )

        time.sleep(1)
        print("[OK] Limpieza previa completada")

    def create_hotspot_connection(self):
        print(f"[INFO] Creando hotspot '{self.connection_name}' en {self.wlan_interface}")
        self.run([
            "nmcli", "connection", "add",
            "type", "wifi",
            "ifname", self.wlan_interface,
            "con-name", self.connection_name,
            "autoconnect", "no",
            "ssid", self.ssid,
        ])

        self.run(["nmcli", "connection", "modify", self.connection_name, "802-11-wireless.mode", "ap"])
        self.run(["nmcli", "connection", "modify", self.connection_name, "802-11-wireless.band", "bg"])
        self.run(["nmcli", "connection", "modify", self.connection_name, "802-11-wireless.channel", self.channel])
        self.run(["nmcli", "connection", "modify", self.connection_name, "802-11-wireless.hidden", "no"])

        self.run(["nmcli", "connection", "modify", self.connection_name, "wifi-sec.key-mgmt", "wpa-psk"])
        self.run(["nmcli", "connection", "modify", self.connection_name, "wifi-sec.psk", self.password])
        self.run(["nmcli", "connection", "modify", self.connection_name, "wifi-sec.proto", "rsn"])
        self.run(["nmcli", "connection", "modify", self.connection_name, "wifi-sec.pairwise", "ccmp"])

        # Agrupado: método manual + IP + gateway
        self.run([
            "nmcli", "connection", "modify", self.connection_name,
            "ipv4.method", "manual",
            "ipv4.addresses", self.ap_ip,
            "ipv4.gateway", self.gateway,
            "ipv6.method", "disabled"
        ])

        print("[OK] Hotspot configurado en NetworkManager")

    def bring_connection_up(self):
        print(f"[INFO] Activando conexión '{self.connection_name}'")
        result = subprocess.run(["nmcli", "connection", "up", self.connection_name], text=True, capture_output=True)
        if result.returncode != 0:
            print("[ERROR] No se pudo activar la conexión.")
            print(result.stdout)
            print(result.stderr)
            return False
        print(result.stdout.strip() or "[OK] Conexión activada")
        return True

    def show_status(self):
        print("\n========== RESUMEN AP (NetworkManager) ==========")
        print(f"SSID: {self.ssid}")
        print(f"Conexión: {self.connection_name}")
        print(f"Interfaz: {self.wlan_interface}")
        print(f"IP configurada: {self.ap_ip}")
        print(f"Gateway esperado: {self.gateway}")
        print(f"Rango DHCP esperado: {self.dhcp_range_note}")
        print("=================================================\n")

        subprocess.run(["nmcli", "connection", "show", self.connection_name], check=False)
        print()
        subprocess.run(["nmcli", "device", "status"], check=False)
        print()
        subprocess.run(["ip", "addr", "show", self.wlan_interface], check=False)

    def setup(self, recreate=True):
        self.ensure_root()
        self.ensure_nmcli()
        self.ensure_networkmanager()
        self.set_regulatory_domain()

        self.release_ap_ip()

        if recreate:
            self.delete_existing_connection()
            self.create_hotspot_connection()
            success = self.bring_connection_up()
            if not success:
                print("[ERROR] Fallo al levantar el AP con NetworkManager.")
                return False
            self.show_status()
            return True
        return False

    def teardown(self):
        """Desactiva el AP de NetworkManager."""
        print("[INFO] Desactivando AP de NetworkManager...")
        subprocess.run(["nmcli", "connection", "down", self.connection_name], check=False)
        self.delete_existing_connection()
        print("[OK] AP de NetworkManager eliminado.")


class RaspberryAccessPointManual:
    def __init__(
        self,
        ssid="TurtleRally-AP",
        password="123456789",
        wlan_interface="wlan0",
        ap_ip="192.168.4.1/24",
        dhcp_range="192.168.4.2,192.168.4.20,255.255.255.0,24h",
        channel=6,
    ):
        self.ssid = ssid
        self.password = password
        self.wlan_interface = wlan_interface
        self.ap_ip = ap_ip
        self.dhcp_range = dhcp_range
        self.channel = channel

        self.hostapd_conf = None
        self.pid_file = "/tmp/turtlerally_ap.pid"

    def ensure_root(self):
        if os.geteuid() != 0:
            print("[ERROR] Debes ejecutar con sudo.")
            sys.exit(1)

    def command_exists(self, cmd):
        return shutil.which(cmd) is not None

    def install_dependencies(self):
        missing = []
        for pkg in ["hostapd", "dnsmasq"]:
            if not self.command_exists(pkg):
                missing.append(pkg)
        if missing:
            print(f"[INFO] Instalando: {' '.join(missing)}")
            subprocess.run(["apt", "update"], check=False)
            subprocess.run(["apt", "install", "-y"] + missing, check=True)

    def stop_conflicting_services(self):
        services = ["NetworkManager", "wpa_supplicant", "dhcpcd"]
        for svc in services:
            subprocess.run(["systemctl", "stop", svc], check=False)

    def create_hostapd_conf(self):
        content = f"""interface={self.wlan_interface}
driver=nl80211
ssid={self.ssid}
hw_mode=g
channel={self.channel}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ieee80211n=0
"""
        fd, path = tempfile.mkstemp(suffix=".conf", prefix="hostapd_", text=True)
        with os.fdopen(fd, 'w', newline='\n', encoding='ascii') as f:
            f.write(content)
        self.hostapd_conf = path
        print(f"[INFO] Configuración hostapd: {path}")

    def configure_interface(self):
        subprocess.run(["ip", "link", "set", self.wlan_interface, "down"], check=False)
        subprocess.run(["ip", "addr", "flush", "dev", self.wlan_interface], check=False)
        subprocess.run(["ip", "addr", "add", self.ap_ip, "dev", self.wlan_interface], check=True)
        subprocess.run(["ip", "link", "set", self.wlan_interface, "up"], check=True)

    def start(self):
        self.ensure_root()
        self.install_dependencies()
        self.stop_conflicting_services()

        # Limpiar procesos previos
        subprocess.run(["pkill", "hostapd"], check=False)
        subprocess.run(["pkill", "dnsmasq"], check=False)
        time.sleep(1)

        self.create_hostapd_conf()
        self.configure_interface()

        # Iniciar hostapd en background
        subprocess.run(["hostapd", "-B", self.hostapd_conf], check=True)
        print("[OK] hostapd iniciado")

        # Iniciar dnsmasq en background
        subprocess.run([
            "dnsmasq",
            f"--interface={self.wlan_interface}",
            f"--dhcp-range={self.dhcp_range}",
            "--except-interface=lo",
            "--bind-interfaces",
            "--no-daemon"  # pero lo lanzamos en segundo plano con &
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        # Alternativa: usar --daemon si se prefiere, pero dejamos que el script termine
        print("[OK] dnsmasq iniciado")

        # Guardar PID de dnsmasq para detener después
        pid = subprocess.run(["pgrep", "-f", "dnsmasq.*{}".format(self.wlan_interface)], capture_output=True, text=True).stdout.strip()
        with open(self.pid_file, "w") as f:
            f.write(pid)

        self.show_status()
        print("\n[INFO] AP en funcionamiento. Para detenerlo: sudo python3 {} --stop".format(sys.argv[0]))

    def stop(self):
        self.ensure_root()
        print("[INFO] Deteniendo AP...")
        subprocess.run(["pkill", "hostapd"], check=False)
        subprocess.run(["pkill", "dnsmasq"], check=False)
        subprocess.run(["ip", "addr", "flush", "dev", self.wlan_interface], check=False)
        subprocess.run(["ip", "link", "set", self.wlan_interface, "down"], check=False)

        # Eliminar archivo PID
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

        # Eliminar config temporal (buscar y borrar /tmp/hostapd_*.conf)
        for f in os.listdir("/tmp"):
            if f.startswith("hostapd_") and f.endswith(".conf"):
                os.remove(os.path.join("/tmp", f))

        print("[OK] AP detenido.")

    def show_status(self):
        print("\n========== AP ACTIVO ==========")
        print(f"SSID: {self.ssid}")
        print(f"Contraseña: {self.password}")
        print(f"IP del AP: {self.ap_ip.split('/')[0]}")
        print("================================")


def main():
    parser = argparse.ArgumentParser(description="Controla el punto de acceso WiFi.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Inicia el AP en segundo plano")
    group.add_argument("--stop", action="store_true", help="Detiene el AP")

    parser.add_argument("--ssid", default="TurtleRally-AP", help="SSID de la red")
    parser.add_argument("--password", default="123456789", help="Contraseña")
    parser.add_argument("--interface", default="wlan0", help="Interfaz WiFi")
    parser.add_argument("--channel", type=int, default=6, help="Canal")
    args = parser.parse_args()

    ap = RaspberryAccessPointManual(
        ssid=args.ssid,
        password=args.password,
        wlan_interface=args.interface,
        channel=args.channel
    )

    if args.start:
        ap.start()
    elif args.stop:
        ap.stop()


if __name__ == "__main__":
    main()