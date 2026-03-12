import os
import glob
import platform
import shutil
import json
import time
import threading
from system_utils import run_command

class HardwareManager:
    def __init__(self):
        self.controller = self._get_controller()

    def _get_controller(self):
        # NVIDIA (Linux/Windows): nvidia-smi costuma existir em ambos.
        if shutil.which("nvidia-smi"):
            print("Placa de vídeo NVIDIA detectada (via nvidia-smi).")
            if platform.system().lower() == "windows":
                return WindowsNvidiaController()
            return NvidiaController()

        # AMD via sysfs (somente Linux)
        if platform.system().lower() == "windows":
            names = _get_windows_video_controller_names()
            if names:
                print(f"Controladores de vídeo detectados (Windows): {', '.join(names)}")
            else:
                print("Não foi possível detectar o nome da GPU no Windows.")

            # Ainda não há backend de controle para AMD no Windows, mas retornamos um controller
            # "limitado" para permitir que a GUI abra.
            if any(("AMD" in n.upper()) or ("RADEON" in n.upper()) for n in (names or [])):
                print("GPU AMD detectada no Windows (modo limitado).")
            amd_controller = WindowsAmdMonitorController.try_create()
            if amd_controller:
                print("Monitoramento AMD no Windows habilitado via LibreHardwareMonitor.")
                return amd_controller
            return WindowsUnsupportedController(
                reason="AMD no Windows: controle não suportado. Para monitoramento, rode o LibreHardwareMonitor com WMI/CIM habilitado."
            )

        for card_path in sorted(glob.glob('/sys/class/drm/card*')):
            try:
                with open(os.path.join(card_path, 'device/vendor'), 'r') as f:
                    if f.read().strip() == '0x1002':
                        hwmon_paths = glob.glob(os.path.join(card_path, 'device/hwmon/hwmon*'))
                        if hwmon_paths:
                            card_name = os.path.basename(card_path)
                            hwmon_path = hwmon_paths[0]
                            print(f"Placa de vídeo AMD detectada em '{card_name}' com hwmon '{os.path.basename(hwmon_path)}'.")
                            return AmdController(card_path, hwmon_path)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Erro ao verificar {card_path}: {e}")

        else:
            print("Nenhuma placa de vídeo compatível detectada.")
            return None

def _get_windows_video_controller_names():
    if platform.system().lower() != "windows":
        return None
    cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join \\"`n\\""'
    out = run_command(cmd)
    if not out:
        return None
    names = [line.strip() for line in out.splitlines() if line.strip()]
    return names or None

def _query_hwmonitor_sensors(namespaces):
    """
    Tenta consultar sensores via CIM/WMI, retornando (namespace, sensors_list) ou (None, None).
    Requer que LibreHardwareMonitor (ou OpenHardwareMonitor) esteja rodando e expondo o namespace.
    """
    for ns in namespaces:
        # Select-Object reduz payload; ConvertTo-Json facilita parse.
        ps = (
            "powershell -NoProfile -Command "
            "\"$s = Get-CimInstance -Namespace '{ns}' -ClassName Sensor -ErrorAction Stop | "
            "Select-Object Name, SensorType, Value; "
            "$s | ConvertTo-Json -Compress\""
        ).format(ns=ns.replace("'", "''"))
        out = run_command(ps)
        if not out:
            continue
        try:
            data = json.loads(out)
            if isinstance(data, dict):
                sensors = [data]
            elif isinstance(data, list):
                sensors = data
            else:
                sensors = None
            if sensors:
                return ns, sensors
        except Exception:
            continue
    return None, None

def _pick_sensor_value(sensors, sensor_type, name_contains_any):
    sensor_type_upper = str(sensor_type).upper()
    needles = [n.upper() for n in name_contains_any]
    for s in sensors:
        st = str(s.get("SensorType", "")).upper()
        if st != sensor_type_upper:
            continue
        name = str(s.get("Name", "")).upper()
        if any(n in name for n in needles):
            try:
                val = s.get("Value", None)
                return float(val) if val is not None else None
            except (TypeError, ValueError):
                return None
    return None

class WindowsAmdMonitorController:
    """
    Monitoramento AMD no Windows via LibreHardwareMonitor/OpenHardwareMonitor (CIM/WMI).
    Observação: isto só monitora; controle de fan/power/clock não é suportado aqui.
    """
    is_limited = True

    def __init__(self, namespace):
        self.namespace = namespace
        self._lock = threading.Lock()
        self._cache_ts = 0.0
        self._cache_sensors = []

    @staticmethod
    def try_create():
        if platform.system().lower() != "windows":
            return None
        namespaces = ["root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor"]
        ns, sensors = _query_hwmonitor_sensors(namespaces)
        if ns and sensors:
            ctrl = WindowsAmdMonitorController(namespace=ns)
            ctrl._cache_sensors = sensors
            ctrl._cache_ts = time.time()
            return ctrl
        return None

    def _refresh(self):
        now = time.time()
        with self._lock:
            if (now - self._cache_ts) < 1.0 and self._cache_sensors:
                return
            ns, sensors = _query_hwmonitor_sensors([self.namespace])
            if sensors:
                self._cache_sensors = sensors
                self._cache_ts = now

    def set_fan_speed(self, speed_percent):
        print("Controle de ventoinha para AMD no Windows não é suportado (somente monitoramento).")

    def set_power_limit(self, limit_watts):
        print("Limite de energia para AMD no Windows não é suportado (somente monitoramento).")

    def set_core_clock_offset(self, offset_mhz):
        print("Offset de clock para AMD no Windows não é suportado (somente monitoramento).")

    def set_mem_clock_offset(self, offset_mhz):
        print("Offset de memória para AMD no Windows não é suportado (somente monitoramento).")

    def reset_settings(self):
        print("Reset de configurações para AMD no Windows não é suportado (somente monitoramento).")

    def get_power_limit_range(self):
        return None, None

    def get_gpu_usage(self):
        self._refresh()
        # Heurísticas comuns do LHM/OHM: "GPU Core", "GPU", "D3D 3D"
        val = _pick_sensor_value(self._cache_sensors, "Load", ["GPU CORE", "GPU", "D3D 3D"])
        return f"{val:.0f}%" if val is not None else "N/A"

    def get_memory_usage(self):
        self._refresh()
        used = _pick_sensor_value(self._cache_sensors, "Data", ["GPU MEMORY USED", "VRAM USED", "MEMORY USED"])
        total = _pick_sensor_value(self._cache_sensors, "Data", ["GPU MEMORY TOTAL", "VRAM TOTAL", "MEMORY TOTAL"])

        if used is None or total is None or total <= 0:
            # Alguns setups expõem como "SmallData"
            used = used if used is not None else _pick_sensor_value(self._cache_sensors, "SmallData", ["GPU MEMORY USED", "VRAM USED", "MEMORY USED"])
            total = total if total is not None else _pick_sensor_value(self._cache_sensors, "SmallData", ["GPU MEMORY TOTAL", "VRAM TOTAL", "MEMORY TOTAL"])

        if used is None or total is None or total <= 0:
            return "N/A"
        pct = (used / total) * 100.0
        # LHM costuma usar MB; mantemos como MB.
        return f"{pct:.1f}% ({used:.0f}MB / {total:.0f}MB)"

    def get_temperature(self):
        self._refresh()
        val = _pick_sensor_value(self._cache_sensors, "Temperature", ["GPU CORE", "GPU"])
        return val

class WindowsUnsupportedController:
    def __init__(self, reason="Controle não suportado nesta plataforma"):
        self.reason = reason
        self.is_limited = True

    def set_fan_speed(self, speed_percent):
        print(self.reason)

    def set_power_limit(self, limit_watts):
        print(self.reason)

    def set_core_clock_offset(self, offset_mhz):
        print(self.reason)

    def set_mem_clock_offset(self, offset_mhz):
        print(self.reason)

    def reset_settings(self):
        print(self.reason)

    def get_power_limit_range(self):
        return None, None

    def get_gpu_usage(self):
        return "N/A"

    def get_memory_usage(self):
        return "N/A"

    def get_temperature(self):
        return None

class NvidiaController:
    def set_fan_speed(self, speed_percent):
        run_command("nvidia-settings -a '[gpu:0]/GPUFanControlState=1'")
        run_command(f"nvidia-settings -a '[fan:0]/GPUTargetFanSpeed={speed_percent}'")

    def set_power_limit(self, limit_watts):
        run_command(f"sudo nvidia-smi -pl {limit_watts}")

    def set_core_clock_offset(self, offset_mhz):
        run_command(f"nvidia-settings -a '[gpu:0]/GPUGraphicsClockOffset[3]={offset_mhz}'")

    def set_mem_clock_offset(self, offset_mhz):
        run_command(f"nvidia-settings -a '[gpu:0]/GPUMemoryTransferRateOffset[3]={offset_mhz}'")

    def reset_settings(self):
        print("Restaurando configurações padrão da NVIDIA.")
        self.set_core_clock_offset(0)
        self.set_mem_clock_offset(0)
        
        run_command("nvidia-settings -a '[gpu:0]/GPUFanControlState=0'")
        
        try:
            default_power_limit = run_command("nvidia-smi --query-gpu=power.default_limit --format=csv,noheader,nounits").split('.')[0]
            self.set_power_limit(int(default_power_limit))
        except (ValueError, TypeError, AttributeError):
            print("Não foi possível resetar o limite de energia para o padrão.")

    def get_power_limit_range(self):
        try:
            min_limit = run_command("nvidia-smi --query-gpu=power.min_limit --format=csv,noheader,nounits").split('.')[0]
            max_limit = run_command("nvidia-smi --query-gpu=power.max_limit --format=csv,noheader,nounits").split('.')[0]
            if min_limit and max_limit:
                return int(min_limit), int(max_limit)
        except (ValueError, TypeError, AttributeError):
            return None, None
        return None, None

    def get_gpu_usage(self):
        usage = run_command("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits")
        return f"{usage}%" if usage else "N/A"

    def get_memory_usage(self):
        try:
            total_mem_str = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits")
            used_mem_str = run_command("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
            if total_mem_str and used_mem_str:
                total_mem = int(total_mem_str)
                used_mem = int(used_mem_str)
                return f"{(used_mem / total_mem) * 100:.1f}% ({used_mem}MB / {total_mem}MB)"
        except (ValueError, TypeError):
            return "N/A"
        return "N/A"

    def get_temperature(self):
        temp = run_command("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits")
        return int(temp) if temp and temp.isdigit() else None

class WindowsNvidiaController:
    """
    Implementação mínima para Windows:
    - Monitoramento via nvidia-smi (uso, memória, temperatura, limites)
    - Ajustes avançados (fan/clock) via nvidia-settings não existem no Windows por padrão
    """
    def set_fan_speed(self, speed_percent):
        print("Controle de ventoinha via nvidia-settings não é suportado no Windows.")

    def set_power_limit(self, limit_watts):
        # Em muitas GPUs/drivers, -pl existe no Windows; se falhar, run_command retorna None.
        run_command(f"nvidia-smi -pl {limit_watts}")

    def set_core_clock_offset(self, offset_mhz):
        print("Offset de clock via nvidia-settings não é suportado no Windows.")

    def set_mem_clock_offset(self, offset_mhz):
        print("Offset de clock via nvidia-settings não é suportado no Windows.")

    def reset_settings(self):
        print("Reset automático não é suportado no Windows (depende de ferramentas do driver).")

    def get_power_limit_range(self):
        try:
            min_limit = run_command("nvidia-smi --query-gpu=power.min_limit --format=csv,noheader,nounits")
            max_limit = run_command("nvidia-smi --query-gpu=power.max_limit --format=csv,noheader,nounits")
            if min_limit and max_limit:
                return int(min_limit.split('.')[0]), int(max_limit.split('.')[0])
        except (ValueError, TypeError, AttributeError):
            return None, None
        return None, None

    def get_gpu_usage(self):
        usage = run_command("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits")
        return f"{usage}%" if usage else "N/A"

    def get_memory_usage(self):
        try:
            total_mem_str = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits")
            used_mem_str = run_command("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
            if total_mem_str and used_mem_str:
                total_mem = int(total_mem_str)
                used_mem = int(used_mem_str)
                return f"{(used_mem / total_mem) * 100:.1f}% ({used_mem}MB / {total_mem}MB)"
        except (ValueError, TypeError):
            return "N/A"
        return "N/A"

    def get_temperature(self):
        temp = run_command("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits")
        return int(temp) if temp and temp.isdigit() else None

class AmdController:
    def __init__(self, card_path, hwmon_path):
        self.card_path = card_path
        self.hwmon_path = hwmon_path
        self.device_path = os.path.join(card_path, "device/")

    def set_fan_speed(self, speed_percent):
        pwm_value = int((speed_percent / 100) * 255)
        
        run_command(f"echo 1 | sudo tee {self.hwmon_path}/pwm1_enable")
        run_command(f"echo {pwm_value} | sudo tee {self.hwmon_path}/pwm1")

    def set_core_clock_offset(self, offset_mhz):
        print("Controle de clock para AMD ainda não implementado.")

    def set_mem_clock_offset(self, offset_mhz):
        print("Controle de clock de memória para AMD ainda não implementado.")

    def reset_settings(self):
        print("Restaurando configurações padrão da AMD.")
        run_command(f"echo 2 | sudo tee {self.hwmon_path}/pwm1_enable")

        _min_limit, max_limit = self.get_power_limit_range()
        if max_limit:
            self.set_power_limit(max_limit)

    def get_power_limit_range(self):
        try:
            with open(f"{self.hwmon_path}/power1_cap_max") as f:
                max_limit = int(f.read().strip()) / 1_000_000
            min_limit = 10
            return min_limit, int(max_limit)
        except (FileNotFoundError, ValueError):
            return None, None

    def set_power_limit(self, limit_watts):
        limit_microwatts = int(limit_watts * 1_000_000)
        run_command(f"echo {limit_microwatts} | sudo tee {self.hwmon_path}/power1_cap")

    def get_gpu_usage(self):
        try:
            with open(f"{self.device_path}gpu_busy_percent") as f:
                usage = f.read().strip()
                return f"{usage}%"
        except FileNotFoundError:
            return "N/A"

    def get_memory_usage(self):
        try:
            with open(f"{self.device_path}mem_info_vram_used") as f:
                used_mem = int(f.read().strip()) / (1024**2)
            with open(f"{self.device_path}mem_info_vram_total") as f:
                total_mem = int(f.read().strip()) / (1024**2)
            return f"{(used_mem / total_mem) * 100:.1f}% ({used_mem:.0f}MB / {total_mem:.0f}MB)"
        except (FileNotFoundError, ValueError, ZeroDivisionError):
            return "N/A"

    def get_temperature(self):
        try:
            with open(f"{self.hwmon_path}/temp1_input") as f:
                return int(f.read().strip()) / 1000
        except (FileNotFoundError, ValueError):
            return None
