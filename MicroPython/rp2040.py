from machine import Pin, ADC
import sys
import json
import uselect

# Constantes
NUM_OUTPUTS = 4
NUM_INPUTS = 4

# Pines de salida digital
DIGITAL_OUTS = [Pin(pin_num, Pin.OUT) for pin_num in (25, 2, 3, 4)]

# Pines de entrada digital con pull-up
DIGITAL_INPUTS = [Pin(pin_num, Pin.IN, Pin.PULL_UP) for pin_num in (24, 21, 22, 26)]

# Pines de entrada analógica
ANALOG_INPUTS = {
    "A0": ADC(Pin(28)),  # GP28 (ADC2)
    "A1": ADC(Pin(29))   # GP29 (ADC3, depende del modelo, usar GP27 para ADC1 si es necesario)
}

# Inicializar salidas a 0
for pin in DIGITAL_OUTS:
    pin.value(0)

def get_inputs():
    """Devuelve estados digitales y analógicos en JSON"""
    data = {f'DI{i}': int(not pin.value()) for i, pin in enumerate(DIGITAL_INPUTS)}
    for name, adc in ANALOG_INPUTS.items():
        data[name] = adc.read_u16() >> 4  # Convertir de 16 bits (0-65535) a 12 bits (0-4095)
    return json.dumps(data)

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
