import json
import time
import serial
from serial.tools import list_ports  # Importación correcta

DIGITAL_OUTS = 4

# MARK: Obtener puertos
def get_portlist(print_data: bool = False) -> dict:
    """ 
    Regresa la lista de los puertos seriales conectados.

    :param print_data: Si se especifica, la imprimira en consola. 
    
    """
    port_list = {
        f"{port.device}": f"{port.description}"for port in list_ports.comports()}

    if print_data:
        for port, description in port_list.items():
            print(f"{port} - {description}")
    return port_list

# MARK: Creacion del Objeto
class serialObject:
    """ Clase general que posse toda la informacion y metodos de trabajo. """

    def __init__(self, com_port: str, baudrate: int, timeout= 1.0, retries= 3) -> None:
        """
        Inicializa el objtero tipo serialObject.

        :param com_port: Puerto serial al cual se conectara la computadora.
        :param baudrate: Baudios especificos del controlador.
        """
        self.com_port       = com_port
        self.baudrate       = baudrate
        self.serial_port    = None
        self.timeout        = timeout
        self.retries        = retries

        """ Diccionarios reservado de control """
        self._DigitalInputsDict = {f"DI{i}": False for i in range(DIGITAL_OUTS)}
        self._AnalogInputsDict = {"A0": 0, "A1": 0}

        # self._AnalogInputsDict = {"AI0": None, "AI1": None, "AI2": None, "AI3": None}

    # MARK: conectar con µC
    def connect(self) -> bool:
        """
            Inicializa la conexion con el puerto seleccionado.
        """
        for attempt in range(self.retries):
            try:
                self.serial_port = serial.Serial(self.com_port, self.baudrate, timeout=self.timeout, write_timeout=self.timeout)
                    
                if self.serial_port.is_open:
                    self.send_data("0000")
                    return True
                else:
                    self.serial_port.close()
                        
            except serial.SerialException as e:
                print(f"Intento {attempt+1} fallido: {str(e)}")
                time.sleep(1)

        return False
    
    # MARK: Enviar datos.
    def send_data(self, user_data: str) -> bool:
        """
        Envia datos digitales al puerto del objeto.
        
        :param user_data: Datos ingresados por el usuario
        """
        if not (self.serial_port and self.serial_port.is_open):
            return False

        if not (user_data.isdigit() and len(user_data) == DIGITAL_OUTS and set(user_data) <= {"0", "1"}):
            return False

        self.serial_port.reset_input_buffer()
        self.serial_port.write((f'POST {user_data}\n').encode())
        # self.serial_port.flush()


        if self.serial_port.readline().decode().strip() != '200':
            return False
        
        return True
    
    # MARK: Recibir datos.
    def recibe_data(self) -> dict | str:
        """ 
        Recepción de datos del puerto. 

        :return dict: Diccionario con entradas digitales y analógicas.
        :return str: Mensaje de error si aplica.
        """
        if not (self.serial_port and self.serial_port.is_open):
            return ""

        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.write(b'GET\n')
            self.serial_port.flush()

            start_time = time.time()
            while (time.time() - start_time) < 1.0:
                if self.serial_port.in_waiting:
                    raw_info = self.serial_port.readline().decode().strip()
                    try:
                        parsed_data = json.loads(raw_info)
                        for key, value in parsed_data.items():
                            if key.startswith("DI"):
                                self._DigitalInputsDict[key] = value
                            elif key.startswith("A"):
                                self._AnalogInputsDict[key] = value

                        # Combinar y devolver todo el estado
                        return {**self._DigitalInputsDict, **self._AnalogInputsDict}
                    
                    except json.JSONDecodeError:
                        return f"Error: La respuesta no es JSON válido: {repr(raw_info)}"

            return "Error: Timeout - No se recibió respuesta válida"

        except serial.SerialException as e:
            return f"Error de comunicación serial: {str(e)}"

        except Exception as e:
            return f"Error inesperado: {str(e)}"

    
    # MARK: Cerrar puerto.
    def close_port(self) -> None:
        """ Cierra de forma controlada el puerto Serie """
        if self.serial_port and self.serial_port.is_open:
            try:
                self.send_data('0000')  # Intentar apagar salidas antes de cerrar
            except Exception as e:
                print(f"Advertencia: error al enviar datos antes de cerrar puerto: {e}")
            try:
                self.serial_port.close()
            except Exception as e:
                print(f"Advertencia: error al cerrar el puerto: {e}")


    # MARK: Destructor Objeto
    def __del__(self):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except Exception:
            pass  # Ignorar errores en el destructor


if __name__ == '__main__':
    print('Codigo escrito por: Diego Ramos - 20130235.')