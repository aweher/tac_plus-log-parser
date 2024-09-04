import sys
from datetime import datetime, timedelta

# Intentar importar los módulos, manejar excepciones si no están instalados
try:
    import json
except ImportError:
    print("Error: El módulo 'json' no está instalado. Puedes instalarlo usando: pip3 install json")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: El módulo 'yaml' no está instalado. Puedes instalarlo usando: pip3 install pyyaml")
    sys.exit(1)

# Diccionario de zonas horarias y sus diferencias en horas con UTC
timezone_offsets = {
    '-3': -3,  # Ejemplo: Argentina Time (UTC-3)
    '0': 0,    # UTC
    'ART': -3  # Argentina Time (UTC-3)
}

# Función para calcular la hora local basada en la fecha UTC y la zona horaria
def get_local_time(date_utc_str, timezone):
    try:
        # Permitir fechas con uno o dos dígitos en el día (ej. "Mar 20" o "Mar  2")
        date_utc = datetime.strptime(date_utc_str.strip(), '%b %d %H:%M:%S')
        offset = timezone_offsets.get(timezone, 0)
        date_local = date_utc + timedelta(hours=offset)
        return date_local.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        if '--debug' in sys.argv:
            print(f"Debug: Error al procesar la fecha: {date_utc_str} - {e}")
        return f"Error parsing date: {e}"

# Función para procesar la línea del log
def process_log_line(line):
    # Dividir la línea considerando múltiples espacios y tabulaciones
    parts = [part for part in line.split() if part]  # Eliminar partes vacías

    # Verificar que la línea tenga al menos 6 partes (fecha, hora, IP, etc.)
    if len(parts) < 6:
        if '--debug' in sys.argv:
            print(f"Debug: Línea ignorada por tener menos de 6 partes: {line.strip()}")
        return None

    # Extraer solo la fecha y hora para validarlas
    date_part = f"{parts[0]} {parts[1]}"  # Parte con la fecha
    time_part = parts[2]  # Parte con la hora

    # Combinar la fecha y hora en una sola cadena
    try:
        date_utc = f"{date_part} {time_part}"
        # Validar solo la parte de la fecha y hora
        if '--debug' in sys.argv:
            print(f"Debug: Validando fecha y hora {date_utc}")
        datetime.strptime(date_utc, '%b %d %H:%M:%S')
    except ValueError:
        if '--debug' in sys.argv:
            print(f"Debug: Línea ignorada por formato de fecha incorrecto: {line.strip()}")
        return None

    # Extraer otros campos
    device_ip = parts[3].strip()
    hostname = parts[4].strip()
    tty = parts[5].strip()
    source_ip = parts[6].strip()
    status = parts[7].strip()

    # Inicializar variables adicionales
    task_id = timezone = service = start_time = privilege_level = command = None

    # Procesar los campos adicionales si existen
    additional_parts = parts[8:]
    for part in additional_parts:
        if part.startswith("task_id="):
            task_id = part.split('=')[1]
        elif part.startswith("timezone="):
            timezone = part.split('=')[1]  # Manejar la zona horaria
        elif part.startswith("service="):
            service = part.split('=')[1]
        elif part.startswith("start_time="):
            start_time = part.split('=')[1]
        elif part.startswith("priv-lvl="):
            privilege_level = part.split('=')[1]
        elif part.startswith("cmd="):
            command = part.split('=', 1)[1]  # El comando puede contener "="

    # Calcular la fecha local usando la fecha UTC y la zona horaria
    date_local_str = get_local_time(date_utc, timezone)

    # Crear el diccionario con los valores
    log_dict = {
        'date_utc': date_utc,
        'time': time_part,
        'device_ip': device_ip,
        'hostname': hostname,
        'tty': tty,
        'source_ip': source_ip,
        'status': status,
        'task_id': task_id,
        'timezone': timezone,
        'service': service,
        'start_time': start_time,
        'privilege_level': privilege_level,
        'command': command,
        'date_local': date_local_str
    }

    if '--debug' in sys.argv:
        print(f"Debug: Línea procesada correctamente: {log_dict}")
    return log_dict

# Función para obtener el contenido de los logs
def get_log_lines():
    if not sys.stdin.isatty():  # Detecta si la entrada es desde stdin (ej. `cat archivo | script.py`)
        return sys.stdin.buffer.read().decode('utf-8', errors='ignore').splitlines()
    else:
        # Si no es stdin, usa el argumento o solicita el archivo manualmente
        if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
            log_file_path = sys.argv[1]
        else:
            log_file_path = input("Introduce el nombre del archivo de log: ")
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.readlines()
        except FileNotFoundError:
            print(f"Error: El archivo '{log_file_path}' no existe o no se puede leer.")
            sys.exit(1)

# Obtener las líneas del log desde archivo o stdin
log_lines = get_log_lines()
if '--debug' in sys.argv:
    print(f"Debug: {len(log_lines)} líneas leídas desde el archivo o stdin.")

# Procesar las líneas y almacenarlas en una lista
parsed_logs = [process_log_line(line) for line in log_lines if process_log_line(line)]

# Verificar si se solicita la salida en formato JSON o YAML
if "--json" in sys.argv:
    print(json.dumps(parsed_logs, indent=4))
elif "--yaml" in sys.argv:
    print(yaml.dump(parsed_logs, default_flow_style=False))
else:
    # Imprimir salida estándar legible si no se especifica json ni yaml
    for log_dict in parsed_logs:
        print(log_dict)
