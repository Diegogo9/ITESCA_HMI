from tkinter import * # type: ignore
from tkinter import ttk

try:
    from modules.ESPSerial import serialObject, get_portlist 
except:
    from ESPSerial import serialObject, get_portlist

# MARK: CONSTANTES
NUM_INPUTS = 4
DIGITAL_OUTS = 4

BUTTONSINPUTSON_X_PLACE = 100
BUTTONSINPUTSOFF_X_PLACE = 250
LEDINPUTS_X_POSITION = 600
LABELINPUTS_X_PLACE = 30
GLOBAL_FONT = ("Arial", 10)

class HMIApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Human Machine Interface")
        self.geometry("650x450")
        self.resizable(False, False)
        self.configure(bg="#edb51a")
        self.iconphoto(True, PhotoImage(file='logo.png'))

        # Variables de estado
        self.estado_inputs  = ["0"] * NUM_INPUTS
        self.conectado      = False
        self.serial_conn    = None

        # Elementos UI
        self.buttons_on         = []
        self.buttons_off        = []
        self.botones_control    = []
        self.leds_canvas        = []
        self.leds_rects         = []

        # Componentes
        self._crear_entradas()
        self._crear_botones_globales()
        self._crear_toolbox()

        # Inicialización
        self._set_estado_controles(False)
        self._actualizar_puertos()
        self._ciclo_actualizacion_leds()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_aplicacion)

        self.paneles_analogicos = {}
        self._crear_paneles_analogicos({
            "A0": (400, 50),
            "A1": (400, 100),
            # Aquí podrías añadir más paneles si quieres
        })

    # MARK: botones y LEDs
    def _crear_entradas(self):
        for i in range(NUM_INPUTS):
            y = 50 + i * 50
            Label(self, text=f"Input {i}", font=GLOBAL_FONT, bg="#edb51a", padx=5).place(x=LABELINPUTS_X_PLACE, y=y)

            btn_on = Button(self,
                            text="ON",
                            font=GLOBAL_FONT,
                            padx=40, 
                            command=lambda i=i: self._alternar_input(i, "on"))
            btn_on.place(x=BUTTONSINPUTSON_X_PLACE, y=y)
            self.buttons_on.append(btn_on)
            self.botones_control.append(btn_on)

            btn_off = Button(self, text="OFF",
                             font=GLOBAL_FONT, 
                             padx=40, 
                             command=lambda i=i: self._alternar_input(i, "off"),
                             state=DISABLED)
            btn_off.place(x=BUTTONSINPUTSOFF_X_PLACE, y=y)
            self.buttons_off.append(btn_off)
            self.botones_control.append(btn_off)

            canvas = Canvas(self, 
                            width=20,
                            height=20, 
                            bg="#edb51a", 
                            highlightthickness=0)
            canvas.place(x=LEDINPUTS_X_POSITION, y=y + 5)
            rect = canvas.create_rectangle(0, 0, 20, 20, fill="gray", outline="black")
            self.leds_canvas.append(canvas)
            self.leds_rects.append(rect)

    def _crear_botones_globales(self):
        btn_all_on = Button(self, 
                           text="All On",
                            command=self._input_all_on,
                            font=GLOBAL_FONT,
                            padx=30)
        btn_all_on.place(x=BUTTONSINPUTSON_X_PLACE, y=250)
        self.botones_control.append(btn_all_on)

        btn_all_off = Button(self, 
                             text="All Off", 
                             command=self._input_all_off,
                             font=GLOBAL_FONT,
                             padx=35)
        btn_all_off.place(x=BUTTONSINPUTSOFF_X_PLACE, y=250)
        self.botones_control.append(btn_all_off)

    # MARK: TOOL BOX
    def _crear_toolbox(self):
        frame = Frame(self, bg="#d9d9d9", height=60)

        frame.pack(side=BOTTOM, fill=X)

        Label(frame,  text="Puerto:",  bg="#d9d9d9").pack(side=LEFT, padx=10)

        self.combo_puertos = ttk.Combobox(frame, state="readonly", width=30)
        self.combo_puertos.pack(side=LEFT, padx=10)

        self.btn_actualizar = Button(frame, text="Actualizar", command=self._actualizar_puertos)
        self.btn_actualizar.pack(side=LEFT, padx=5)

        self.btn_desconectar = Button(frame, text="Desconectar", command=self._desconectar, state=DISABLED)
        self.btn_desconectar.pack(side=RIGHT, padx=5)

        self.btn_conectar = Button(frame, text="Conectar", command=self._conectar)
        self.btn_conectar.pack(side=RIGHT, padx=5)

    def _actualizar_puertos(self):
        puertos = get_portlist()
        valores = [f"{k} - {v}" for k, v in puertos.items()]
        self.combo_puertos["values"] = valores
        if valores:
            self.combo_puertos.current(0)

    def _set_estado_toolbox(self, habilitado: bool):
        estado = "readonly" if habilitado else "disabled"
        self.combo_puertos["state"] = estado
        self.btn_actualizar["state"] = NORMAL if habilitado else DISABLED

    #MARK: CAMBIOS DE ESTADO
    def _set_estado_controles(self, estado:bool):
        """
        Cambia el estado general de la entrada

        :param estado: True para activar controles, False para desactivar.
        """
        for b in self.botones_control:
            b["state"] = NORMAL if estado else DISABLED

    def _alternar_input(self, index: int, state: str):
        """
        Cambia el estado de la entrada

        :param index: Indice de la entrada a cambiar.
        :param state: Estado nuevo a modificar.
        """
        self.estado_inputs[index] = "1" if state == "on" else "0"
        self.buttons_on[index]["state"] = DISABLED if state == "on" else NORMAL
        self.buttons_off[index]["state"] = NORMAL if state == "on" else DISABLED
        self._enviar_estado()

    def _input_all_on(self):
        self.estado_inputs[:] = ["1"] * NUM_INPUTS
        for i in range(NUM_INPUTS):
            self.buttons_on[i]["state"] = DISABLED
            self.buttons_off[i]["state"] = NORMAL
        self._enviar_estado()

    def _input_all_off(self):
        self.estado_inputs[:] = ["0"] * NUM_INPUTS
        for i in range(NUM_INPUTS):
            self.buttons_on[i]["state"] = NORMAL
            self.buttons_off[i]["state"] = DISABLED
        self._enviar_estado()

    def _crear_paneles_analogicos(self, paneles_info: dict):
        """
        Crea múltiples paneles analógicos de forma homogénea.

        :param paneles_info: Diccionario con clave = nombre panel, valor = (x, y)
        """
        for nombre, (x, y) in paneles_info.items():
            panel = Label(self,
                          text=f"{nombre}: 0",
                          bg="#800080",   # morado
                          fg="white",     # texto blanco
                          font=GLOBAL_FONT,
                          width=12,
                          height=1,
                          anchor="center")
            panel.place(x=x, y=y)
            self.paneles_analogicos[nombre] = panel

    #MARK: CONEXION
    def _conectar(self):
        seleccion = self.combo_puertos.get().split(" - ")[0]
        self.serial_conn = serialObject(seleccion, 115200)
        if self.serial_conn.connect():
            self.btn_conectar["state"] = DISABLED
            self.btn_desconectar["state"] = NORMAL
            self.conectado = True
            self._set_estado_controles(True)
            self._set_estado_toolbox(False)
            self._input_all_off()

    # MARK: DESCONEXION
    def _desconectar(self):
        if self.serial_conn:
            self.serial_conn.close_port()
        self.conectado = False
        self.serial_conn = None
        self._set_estado_controles(False)
        self.btn_conectar["state"] = NORMAL
        self.btn_desconectar["state"] = DISABLED
        self._set_estado_toolbox(True)

    #MARK: MANEJO DE LEDs
    def _enviar_estado(self):
        if self.conectado and self.serial_conn:
            estado = "".join(self.estado_inputs)
            self.serial_conn.send_data(estado)

    def _actualizar_salidas(self):
        if self.conectado and self.serial_conn:
            data = self.serial_conn.recibe_data()
            if isinstance(data, dict):
                # Actualizar LEDs digitales
                for i in range(NUM_INPUTS):
                    val = data.get(f"DI{i}", 0)
                    color = "green" if val else "gray"
                    self.leds_canvas[i].itemconfig(self.leds_rects[i], fill=color)

                # Actualizar paneles analógicos si existen
                for nombre in ["A0", "A1"]:
                    if nombre in data and nombre in self.paneles_analogicos:
                        self.paneles_analogicos[nombre].config(text=f"{nombre}: {data[nombre]}")

    def _ciclo_actualizacion_leds(self):
        self._actualizar_salidas()
        self.after(50, self._ciclo_actualizacion_leds)

    def _cerrar_aplicacion(self):
        try:
            self._desconectar()
            self.destroy()
        except:
            self.destroy()
            exit()

if __name__ == "__main__":
    print('Codigo escrito por: Diego Ramos - 20130235.')
