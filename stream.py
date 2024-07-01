# import gi
from threading import Thread
from abc import ABC
from time import sleep

# gi.require_version("Gtk", "3.0")
from gi.repository import GObject


class StreamMessage:

    def __init__(self, msg=''):
        self._msg = list(msg)
        self._send_part = True
        self._msg = []

        self.close_stream_after_read = False
        self.by_one_byte = False

    def set_msg(self, msg):
        self._msg += list(msg)

    def readline(self):
        if len(self._msg):
            if self.by_one_byte:
                if self._send_part:
                    self._send_part = False
                    return self._msg.pop(0).encode()
                else:
                    self._send_part = True
                    return ''.encode()
            else:
                return self._msg.pop(0).encode()

        if self.close_stream_after_read:
            # close stream
            return None
        # wait next message
        # sleep(0.001)
        return ''.encode()


class StreamSignal(ABC):

    _signals = {}
    _is_gobject = False

    def call_signal(self, signal, *args, **kwargs):
        for sig in self._signals[signal]:
            if self._is_gobject:
                kwargs['property'] = GObject.PRIORITY_DEFAULT
                GObject.idle_add(sig, *args, **kwargs)
            else:
                sig(*args, **kwargs)

    def connect(self, sig, handler, is_gobject = False):
        self._is_gobject = is_gobject
        self._signals[sig].append(handler)


class StreamParser(StreamSignal):
    _signals = {
        'read_all': [],
        'read_first_part': [],
        'read_part': [],
        'read_last_part': [],
        'read_float': [],
    }

    def __init__(self):
        self._ready_for_read = True
        self._full_msg = ''

    def parse(self, msg):
        _msg = msg.replace('\r', '')
        if not _msg:
            return

        is_end_of_msg = _msg.endswith('\n')
        _msg = msg.replace('\n', '')

        # receive full message at one time
        if self._ready_for_read and is_end_of_msg:
            float_value = self._convert_to_float(_msg)
            if float_value is not None:
                self.call_signal('read_float', float_value)
            self.call_signal('read_all', _msg)
            self._full_msg = ''
            return

        self._full_msg += _msg

        # receive last part of message
        if is_end_of_msg:
            if not self._ready_for_read:
                self._ready_for_read = True

                float_value = self._convert_to_float(self._full_msg)
                if float_value is not None:
                    self.call_signal('read_float', float_value)
                self.call_signal('read_last_part', _msg, self._full_msg)

                self._full_msg = ''

        # receive first part of message
        elif self._ready_for_read:
            self._ready_for_read = False
            self.call_signal('read_first_part', _msg, self._full_msg)

        # receiving part of message
        else:
            self.call_signal('read_part', _msg, self._full_msg)

    @staticmethod
    def _convert_to_float(msg):
        try:
            float_values = []
            split_by = None
            if ',' in msg:
                split_by = ','
            elif ' ' in msg:
                split_by = ' '

            if split_by is not None:
                for val in msg.split(split_by):
                    float_values.append(float(val))
            else:
                float_values.append(float(msg))

            return float_values
        except:
            return None

class StreamReader(StreamSignal):
    _signals = {
        'read_message': [],
        'read_error': [],
    }

    def __init__(self):
        self._stop = False

    def start(self, stream, daemon=True):
        self._stop = False
        if daemon:
            Thread(target=self._read_stream, args=(stream, ), daemon=True).start()
        else:
            self._read_stream(stream)

    def stop(self):
        self._stop = True

    def _read_stream(self, stream):
        while True:
            if self._stop:
                break
            msg_str = ''

            for line in iter(stream.readline, b''):
                if line is None:
                    self._stop = True
                    break
                try:
                    msg_str += line.decode('utf-8')
                except Exception as err:
                    self.call_signal('read_error', str(err))
                    break
            if msg_str:
                self.call_signal('read_message', msg_str)
