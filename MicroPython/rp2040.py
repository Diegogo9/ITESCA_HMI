from machine import Pin, ADC # type: ignore
import sys
import json
import uselect # type: ignore

# Constantes
NUM_OUTPUTS = 4
NUM_INPUTS = 4

# Pines de salida digital
DIGITAL_OUTPUTS = {'DO0': Pin(25, Pin.OUT),
                   'DO1': Pin(2, Pin.OUT),
                   'DO2': Pin(3, Pin.OUT),
                   'DO3': Pin(4, Pin.OUT)}

# Pines de entrada digital con pull-up
DIGITAL_INPUTS = {'DI0': Pin(24, Pin.IN, Pin.PULL_UP),
                  'DI1': Pin(21, Pin.IN, Pin.PULL_UP),
                  'DI2': Pin(22, Pin.IN, Pin.PULL_UP),
                  'DI3': Pin(26, Pin.IN, Pin.PULL_UP)}

# Pines de entrada analógica
ANALOG_INPUTS = {"A0": ADC(Pin(28)),
                 "A1": ADC(Pin(29))}

# Inicializar salidas a 0
for pin in DIGITAL_OUTPUTS.values():
    pin.value(0)

def read_digital_inputs():
    """Lee los estados de las entradas digitales y las devuelve en un diccionario"""
    return {name: int(not pin.value()) for name, pin in DIGITAL_INPUTS.items()}

def read_analog_inputs():
    """Lee los valores de las entradas analógicas y las devuelve en un diccionario"""
    return {name: adc.read_u16() >> 4 for name, adc in ANALOG_INPUTS.items()}  # Convertir a 12 bits

def get_inputs():
    """Devuelve estados digitales y analógicos en JSON"""
    data = read_digital_inputs()
    data.update(read_analog_inputs())
    return json.dumps(data)

def set_outputs(data):
    """Establece el estado de salidas digitales"""
    if len(data) != NUM_OUTPUTS or not set(data).issubset({'0', '1'}):
        return "400"
    for i, val in enumerate(data):
        DIGITAL_OUTPUTS[f'DO{i}'].value(int(val))
    return "200"

def handle_command(command):
    """Procesa un comando recibido"""
    command = command.strip()
    if not command:
        return None  # Comando vacío

    if command == "GET":
        return get_inputs()

    if command.startswith("POST "):
        return set_outputs(command[5:].strip())

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
    print("RP2040 Ready - Waiting for commands...")
    while True:
        cmd = read_command()
        if cmd is not None:
            response = handle_command(cmd)
            if response is not None:
                print(response)

if __name__ == '__main__':
    main()