import serial


class RS232Port:
    def __init__(self):
        self._device = serial.Serial()
        self.configure()

    def open(self, port, baudrate):
        self._device.port = port
        self._device.baudrate = baudrate
        self._device.open()
        self._device.flushInput()

    def is_open(self):
        return self._device.is_open

    def write(self, cmd):
        self._device.write(bytes(cmd, "utf-8"))

    def get_stream(self):
        return self._device

    def close(self):
        self._device.close()

    @staticmethod
    def get_ports():
        import serial.tools.list_ports
        ports = []
        for port, desc, hwid in serial.tools.list_ports.comports():
            ports.append(port)
        return ports

    def configure(self):
        self._device.bytesize = serial.EIGHTBITS
        self._device.parity = serial.PARITY_NONE
        self._device.stopbits = serial.STOPBITS_ONE
        self._device.timeout = 0  # 0 Non-Block reading
        self._device.xonxoff = False  # Disable Software Flow Control
        self._device.rtscts = False  # Disable (RTS/CTS) flow Control
        self._device.dsrdtr = False  # Disable (DSR/DTR) flow Control
        self._device.writeTimeout = 2


class RS232PortMock:
    def __init__(self, stream):
        self._stream = stream
        self._is_open = False

    def open(self, port, baudrate):
        self._is_open = True

    def is_open(self):
        return self._is_open

    def write(self, msg):
        self._stream.set_msg(msg)

    def get_stream(self):
        return self._stream

    def close(self):
        self._is_open = False

    @staticmethod
    def get_ports():
        return ["/dev/ttyASM0", "/dev/ttyASM1", "/dev/ttyASM2"]

    def configure(self):
        pass
