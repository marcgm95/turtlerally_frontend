#!/usr/bin/env python3
"""
Punto de Acceso estable para TurtleRally usando create_ap.
Uso:
  sudo python3 turtlerally_ap.py --start   # Inicia AP en segundo plano
  sudo python3 turtlerally_ap.py --stop    # Detiene el AP
"""

import subprocess
import sys
import time
import os
import argparse

class TurtleRallyAP:
    def __init__(self, ssid="TurtleRally-AP", password="123456789",
                 interface="wlan0", channel=6):
        self.ssid = ssid
        self.password = password
        self.interface = interface
        self.channel = channel
        self.process = None

    def require_root(self):
        if os.geteuid() != 0:
            print("[ERROR] Ejecuta con sudo.")
            sys.exit(1)

    def check_create_ap_installed(self):
        """Verifica que create_ap esté instalado."""
        if subprocess.run(["which", "create_ap"], capture_output=True).returncode != 0:
            print("[ERROR] create_ap no está instalado. Instálalo con:")
            print("git clone https://github.com/oblique/create_ap")
            print("cd create_ap && sudo make install")
            sys.exit(1)

    def stop_interfering_services(self):
        """Detiene servicios que pueden bloquear wlan0."""
        services = ["NetworkManager", "wpa_supplicant", "dhcpcd"]
        for svc in services:
            subprocess.run(["systemctl", "stop", svc], check=False)

    def start(self):
        self.require_root()
        self.check_create_ap_installed()
        self.stop_interfering_services()

        # Limpiar procesos previos
        subprocess.run(["pkill", "create_ap"], check=False)
        subprocess.run(["pkill", "hostapd"], check=False)
        subprocess.run(["pkill", "dnsmasq"], check=False)
        time.sleep(1)

        # Comando create_ap con --no-virt para evitar problemas de interfaz virtual
        cmd = [
            "create_ap",
            "--no-virt",
            "-c", str(self.channel),
            self.interface,
            self.ssid,
            self.password
        ]

        print(f"[INFO] Iniciando AP con create_ap: {self.ssid} en canal {self.channel}")
        # Ejecutar en segundo plano y redirigir salida a /dev/null para no bloquear
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Dar tiempo para que el AP se inicie
        time.sleep(5)
        if self.process.poll() is not None:
            print("[ERROR] create_ap finalizó inesperadamente. Revisa los logs del sistema.")
            sys.exit(1)

        # Obtener la IP que create_ap asignó (normalmente 192.168.12.1)
        result = subprocess.run(["ip", "-4", "addr", "show", self.interface], capture_output=True, text=True)
        ip_line = [line for line in result.stdout.splitlines() if "inet " in line]
        if ip_line:
            ip = ip_line[0].strip().split()[1].split('/')[0]
        else:
            ip = "192.168.12.1"  # valor por defecto

        print(f"\n✅ AP '{self.ssid}' activo")
        print(f"   Contraseña: {self.password}")
        print(f"   IP del AP: {ip}")
        print(f"   Canal: {self.channel}")
        print("\nPara detener: sudo python3 turtlerally_ap.py --stop")

    def stop(self):
        self.require_root()
        print("[INFO] Deteniendo AP...")
        subprocess.run(["pkill", "create_ap"], check=False)
        subprocess.run(["pkill", "hostapd"], check=False)
        subprocess.run(["pkill", "dnsmasq"], check=False)
        # Limpiar interfaz
        subprocess.run(["ip", "addr", "flush", "dev", self.interface], check=False)
        subprocess.run(["ip", "link", "set", self.interface, "down"], check=False)
        print("[OK] AP detenido.")

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start", action="store_true", help="Iniciar AP")
    group.add_argument("--stop", action="store_true", help="Detener AP")
    parser.add_argument("--ssid", default="TurtleRally-AP")
    parser.add_argument("--password", default="123456789")
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--channel", type=int, default=6)
    args = parser.parse_args()

    ap = TurtleRallyAP(
        ssid=args.ssid,
        password=args.password,
        interface=args.interface,
        channel=args.channel
    )

    if args.start:
        ap.start()
    elif args.stop:
        ap.stop()

if __name__ == "__main__":
    main()