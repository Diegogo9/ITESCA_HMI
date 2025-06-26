from machine import Pin
import sys
import json
import uselect

# Constantes
NUM_OUTPUTS = 4
NUM_INPUTS = 4

# Pines de salida digital
DIGITAL_OUTS = [Pin(pin_num, Pin.OUT) for pin_num in (4, 0, 2, 15)]

# Pines de entrada digital con pull-up
DIGITAL_INS = [Pin(pin_num, Pin.IN, Pin.PULL_UP) for pin_num in (36, 39, 34, 35)]

# Inicializar salidas a 0
for pin in DIGITAL_OUTS:
    pin.value(0)

def get_inputs():
    """Devuelve los estados de entradas digitales en formato JSON"""
    return json.dumps({f'DI{i}': int(not pin.value()) for i, pin in enumerate(DIGITAL_INS)})

def set_outputs(data):
    """Establece el estado de salidas digitales"""
    if len(data) != NUM_OUTPUTS or not set(data).issubset({'0', '1'}):
        return "400"
    for i, val in enumerate(data):
        DIGITAL_OUTS[i].value(int(val))
    return "200"

def handle_command(cmd):
    """Procesa un comando recibido"""
    cmd = cmd.strip()
    if not cmd:
        return None  # Comando vacío

    if cmd == "GET":
        return get_inputs()

    if cmd.startswith("POST "):
        return set_outputs(cmd[5:].strip())
    
    if cmd == "exit":
        exit()

    return "400"

# Configurar lectura no bloqueante
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

def read_command():
    """Lee un comando completo desde stdin hasta newline"""
    if poll.poll(0):
        cmd = sys.stdin.readline()
        return cmd if cmd else None
    return None

def main():
    print("ESP32 Ready - Waiting for commands...")
    while True:
        cmd = read_command()
        if cmd is not None:
            response = handle_command(cmd)
            if response is not None:
                print(response)

if __name__ == '__main__':
    main()
