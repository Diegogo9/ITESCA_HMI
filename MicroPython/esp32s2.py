from machine import Pin
import sys
import json
import uselect


NUM_OUTPUTS = 4
NUM_INPUTS = 4

DIGITAL_OUTS = [Pin(pin_num, Pin.OUT) for pin_num in (15, 1, 2, 3)]
DIGITAL_INS = [Pin(pin_num, Pin.IN, Pin.PULL_UP) for pin_num in (0, 38, 39, 40)]

for pin in DIGITAL_OUTS:
    pin.value(0)


# MARK: Manejo de I/O
def send_inputs():
    """Devuelve los estados de entradas digitales en formato JSON"""

    return json.dumps({f'DI{i}': int(not pin.value()) for i, pin in enumerate(DIGITAL_INS)})

def set_outputs(data):
    """Establece el estado de salidas digitales"""

    if len(data) != NUM_OUTPUTS or not set(data).issubset({'0', '1'}):
        return "400"
    for i, val in enumerate(data):
        DIGITAL_OUTS[i].value(int(val))
    return "200"

# MARK: Manejo de comandos
def handle_command(command):
    """Procesa un comando recibido"""
    command = command.strip()
    if not command:
        return None 

    if command == "GET":
        return send_inputs()

    if command.startswith("POST "):
        return set_outputs(command[5:].strip())

    return "400"

# MARK: Evita bloqueo
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

def read_command():
    """Lee un comando completo desde stdin hasta newline"""
    if poll.poll(0):
        command = sys.stdin.readline()
        return command if command else None
    return None


if __name__ == '__main__':
    while True:
        command = read_command()

        if command is not None:
            response = handle_command(command)
            
            if response is not None:
                print(response)
