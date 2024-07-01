import gi, time, logging, math, numpy, cairo
from threading import Thread, Lock
from datetime import datetime

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

logging.basicConfig(level=logging.DEBUG)


class DisplayWidget(Gtk.ScrolledWindow):
    def __init__(self):
        super(DisplayWidget, self).__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        self._view = Gtk.TextView()
        self._view.set_editable(False)
        self.add(self._view)

        self._buff = self._view.get_buffer()

    @staticmethod
    def _get_start_line_info():
        return r'<span foreground="blue">[{time}]</span>' \
            .format(time=datetime.now().strftime("%H:%M:%S"))

    @staticmethod
    def _get_end_line_info(full_msg):
        return r'<span foreground="red">[{msg_size}]</span>' \
            .format(msg_size=len(full_msg.encode('utf-8')))

    def out_start_line(self, msg, *args, **kwargs):
        self.out_part_line(DisplayWidget._get_start_line_info() + msg)

    def out_part_line(self, msg, *args, **kwargs):
        self._buff.insert_markup(self._buff.get_end_iter(), msg, -1)
        self._view.scroll_to_mark(self._buff.get_insert(), 0.0, True, 0.0, 1.0)

    def out_end_line(self, msg, full_msg, *args, **kwargs):
        end_line_info = self._get_end_line_info(full_msg)
        self.out_part_line(msg + end_line_info + '\n')

    def out_full_line(self, msg):
        start_line_info = DisplayWidget._get_start_line_info()
        end_line_info = DisplayWidget._get_end_line_info(msg)
        self.out_part_line(start_line_info + msg + end_line_info + '\n')

    def clear(self):
        self._buff.set_text("")


class ConnectionWidget(Gtk.Grid):
    device = None

    def __init__(self, device):
        super(ConnectionWidget, self).__init__()
        self.on_connected = None
        self.on_disconnected = None
        self.on_error = None

        self._device = device
        self._is_connected = False
        self._available_ports = []

        self._bt_connect = Gtk.Button()
        self._bt_connect.connect("clicked", self._do_connect)
        self._bt_connect.set_sensitive(False)
        self._bt_connect.set_size_request(100, 0)

        self._port = Gtk.ComboBoxText()
        self._port.connect("changed", self._on_setting_changed)
        self._port.set_entry_text_column(False)
        self._port.set_size_request(150, 0)

        self._baudrate = Gtk.ComboBoxText()
        self._baudrate.connect("changed", self._on_setting_changed)
        self._baudrate.set_entry_text_column(False)
        self._baudrate.set_size_request(100, 0)

        for i in [110, 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600,  115200]:
            self._baudrate.append_text(str(i))
        self._baudrate.set_active(5)  # 9600

        self._entry_msg = Gtk.Entry()
        self._bt_send = Gtk.Button(label="Send")
        self._bt_send.connect("clicked", self._on_click_send)
        self._chbox_send_endline = Gtk.CheckButton(label="End line")

        self._lb_status = Gtk.Label()
        self._lb_status.set_margin_top(5)
        self._lb_status.set_margin_bottom(5)

        padding = 2
        box1 = Gtk.Box()
        box1.pack_start(self._bt_connect, True, True, padding)
        box1.pack_start(Gtk.Label(label="Device: "), False, False, padding)
        box1.pack_start(self._port, True, True, padding)
        box1.pack_start(Gtk.Label(label="Baud-rate: "), False, False, padding)
        box1.pack_start(self._baudrate, True, True, padding)
        box1.pack_start(self._entry_msg, True, True, padding)
        box1.pack_start(self._bt_send, True, True, padding)
        box1.pack_start(self._chbox_send_endline, True, True, padding)

        box2 = Gtk.Box()
        box2.pack_start(self._lb_status, False, False, 5)
        self.attach(box1, 0, 0, 1, 1)
        self.attach(box2, 0, 1, 1, 1)
        self._update_widgets()
        self._update_ports()

    class ReadStream(object):
        def __init__(self, stream, on_read_error_signal):
            self._stream = stream
            self._on_read_error = on_read_error_signal

        def readline(self):
            if self._stream is None:
                return ''
            try:
                return self._stream.readline()
            except Exception as err:
                self._stream = None
                if self._on_read_error is not None:
                    self._on_read_error(err)

    def _signal_error(self, err):
        if self.on_error is not None:
            self.on_error(err)

    def _do_connect(self, widget):
        if not self._is_connected:
            try:
                self._device.close()
                self._device.open(self._port.get_active_text(), self._baudrate.get_active_text())
            except Exception as err:
                self._signal_error(err)
        else:
            self._device.close()

        self._is_connected = self._device.is_open()
        if self._is_connected:
            if self.on_connected is not None:
                self.on_connected(self.ReadStream(self._device.get_stream(), self._on_read_error))
        else:
            if self.on_disconnected is not None:
                self.on_disconnected()
        self._update_widgets()
        self._update_ports()

    def _on_click_send(self, widget):
        try:
            msg = self._entry_msg.get_text()
            if self._chbox_send_endline.get_active():
                msg += '\n'
            self._device.write(msg)
        except Exception as err:
            self._signal_error(err)

    def _on_read_error(self, err):
        self._is_connected = False
        self._update_widgets()
        self._signal_error(err)

    def _on_setting_changed(self, widget):
        self._bt_connect.set_sensitive(
            self._port.get_active_text() is not None
            and self._baudrate.get_active_text() is not None)

    def _update_widgets(self):
        self._entry_msg.set_sensitive(self._is_connected)
        self._bt_send.set_sensitive(self._is_connected)
        self._chbox_send_endline.set_sensitive(self._is_connected)
        self._port.set_sensitive(not self._is_connected)
        self._baudrate.set_sensitive(not self._is_connected)

        if not self._is_connected:
            status = r'<span foreground="red"> Not connected. </span>'
            bt_label = "Connect"
        else:
            status = r'<span foreground="green"> Connected: {port} : {baudrate} </span>' \
                .format(port=self._port.get_active_text(), baudrate=self._baudrate.get_active_text())
            bt_label = "Disconnect"

        self._lb_status.set_markup(status)
        self._bt_connect.set_label(bt_label)

    def _update_ports(self):
        if not self._is_connected:
            Thread(target=self._get_ports, daemon=True).start()

    def _get_ports(self):
        while True:
            if self._is_connected:
                break
            GObject.idle_add(self._append_ports, self._device.get_ports(), property=GObject.PRIORITY_DEFAULT)
            time.sleep(0.5)

    def _append_ports(self, ports):
        for port in set(ports).difference(set(self._available_ports)):
            self._available_ports.append(port)
            self._port.append_text(port)
        if len(self._available_ports) == 1:
            self._port.set_active(0)


class PlotterWidget(Gtk.Box):

    def __init__(self):
        super(PlotterWidget, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        self._frame = Gtk.Frame()
        # self._frame.set_size_request(700, 0)
        self._frame.set_size_request(700, 700)
        self._frame.vexpand = True
        self._frame.hexpand = True
        self._surface = None

        self._area = Gtk.DrawingArea()
        self._area.connect("draw", self.on_draw)
        self._area.connect("configure-event", self.on_configure)
        self._frame.add(self._area)

        # test buttons
        box = Gtk.HBox()
        btn_reset = Gtk.Button(label="Reset")
        btn_reset.connect("clicked", self.on_click_btn_reset)

        btn_sin_wave = Gtk.Button(label="sin wave")
        btn_sin_wave.connect("clicked", self.on_click_btn_sin_wave)

        box.pack_start(btn_reset, False, True, 2)
        box.pack_start(btn_sin_wave, False, True, 2)

        self.pack_start(box, False, True, 2)
        self.pack_start(self._frame, True, True, 2)

        # max point by x
        self.wave_factory = WaveFactory()
        # count points by x
        self.wave_factory.buffer_size = 200
        self._wave_labels_created = False

########################################################################################################################
    received_floats = []
    def on_read_float(self, values):
        self.received_floats.append(values)
        # count_waves = len(values)
        # for i in range(count_waves - self.wave_factory.get_count_waves()):
        #     self.wave_factory.create_wave()
        # for i in range(count_waves):
        #     self.wave_factory.get_wave(i).put(values[i])

    received_msg = []
    def on_read_last_part(self, msg, full_msg, *args, **kwargs):
        self.received_msg.append(full_msg)
        # self.create_labels(full_msg)

    def on_read_all(self, full_msg, *args, **kwargs):
        self.received_msg.append(full_msg)
        # self.create_labels(full_msg)

    def update_waves(self):
        if not self.received_floats:
            return
        values = self.received_floats.pop(0)
        count_waves = len(values)
        for i in range(count_waves - self.wave_factory.get_count_waves()):
            self.wave_factory.create_wave()
        for i in range(count_waves):
            self.wave_factory.get_wave(i).put(values[i])

    # def create_labels(self, msg):
    def update_labels(self):
        if self._wave_labels_created or not self.received_msg:
            return
        msg = self.received_msg.pop(0)
        split_by = None
        if ',' in msg:
            split_by = ','
        elif ' ' in msg:
            split_by = ' '
        if split_by is not None:
            labels = msg.split(split_by)
            for lb in labels:
                self.wave_factory.create_label(lb)
        self._wave_labels_created = True
########################################################################################################################

    def on_click_btn_reset(self, widget):
        self.test_stop_loop = True
        # time.sleep(5.0)
        self.wave_factory.reset()
        self._wave_labels_created = False

    def on_click_btn_sin_wave(self, widget):
        self.test_stop_loop = False
        Thread(target=self._loop_sinus_wave, daemon=True).start()

    test_device = None
    test_stop_loop = False
    def _loop_sinus_wave(self):
        # labels
        self.test_device.write('sinus1, sinus2(+90dg) \n')
        angle = 0.0
        while True:
            if self.test_stop_loop:
                break
            val1 = round(math.sin(angle), 5)
            val2 = round(5 * math.sin(angle + 90.0), 5)
            # val3 = round(3 * math.sin(angle + 30.0), 5)
            #
            # val4 = round(2 * math.sin(angle), 5)
            # val5 = round(6 * math.sin(angle + 120.0), 5)
            # val6 = round(8 * math.sin(angle + 15.0), 5)

            # send value as print()
            self.test_device.write(str(val1))
            self.test_device.write(',')
            self.test_device.write(str(val2))
            # self.test_device.write(',')
            # self.test_device.write(str(val3))
            # self.test_device.write(',')
            # self.test_device.write(str(val4))
            # self.test_device.write(',')
            # self.test_device.write(str(val5))
            # self.test_device.write(',')
            # self.test_device.write(str(val6))

            # send println()
            self.test_device.write('\n')

            angle += .1
            # signal spped
            time.sleep(0.02)

    def draw_grid(self, ctx):
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(.001)
        ctx.set_dash([.002])
        for i in numpy.arange(0, 1, .04):
            ctx.move_to(i, 1)
            ctx.line_to(i, 0)
            ctx.move_to(0, 1-i)
            ctx.line_to(1, 1-i)

        ctx.stroke()

    def on_draw(self, area, ctx):
        ctx.set_source_rgb(255, 255, 255)
        ctx.paint()
        ctx.scale(self._surface.get_width(), self._surface.get_height())
        self.draw_grid(ctx)
        self.wave_factory.draw(ctx)
        return False

    def on_configure(self, area, event, data=None):
        if self._surface is not None:
            self._surface.finish()
            self.surface = None
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                                   self._area.get_allocated_width(),
                                                   self._area.get_allocated_height())
        return False

    # refresh drawing area
    def start_drawing(self):
        Thread(target=self._start_drawing, daemon=True).start()
        Thread(target=self._full_update, daemon=True).start()

    def _full_update(self):
        while True:
            self.update_labels()
            self.update_waves()
            self.wave_factory.prepare_drawing_data()
            time.sleep(0.01)

    def _start_drawing(self):
        while True:
            GObject.idle_add(self._queue_draw, property=GObject.PRIORITY_DEFAULT)
            time.sleep(0.3)

    def _queue_draw(self):
        self._area.queue_draw()


class WaveFactory:

    buffer_size = 0
    _waves = []
    _labels = []
    _color_counter = 0
    _label_counter = 0

    colors = [
        (102, 168, 203),  # dirty blue
        (224, 56, 44),  # scarlet
        (41, 155, 73),  # dark mint
    ]

    def __init__(self):
        tmp_colors = []
        for color in self.colors:
            r, g, b = color
            tmp_colors.append((r / 255 , g / 255, b / 255))
        self.colors = tmp_colors

    def reset(self):
        self._waves = []
        self._labels = []
        self._color_counter = 0
        self._label_counter = 0

    def get_next_color(self):
        color = self.colors[self._color_counter]
        self._color_counter += 1
        if self._color_counter == len(self.colors):
            self._color_counter = 0
        return color

    def get_next_label(self):
        if self._labels and self._label_counter < len(self._labels):
            title = self._labels[self._label_counter]
            self._label_counter += 1
            return title
        return None

    def create_wave(self):
        wave = Wave(self.buffer_size, self.get_next_color(), self.get_next_label())
        self._waves.append(wave)
        return wave

    def create_label(self, title):
        self._labels.append(title)

    def get_wave(self, index):
        return self._waves[index]

    def get_waves(self):
        return self._waves

    def get_count_waves(self):
        return len(self._waves)

    def calculate_drawing_data(self):
        _max_y, _min_y = ([], [])
        for wave in self._waves:
            buff = list(filter(lambda i: i is not None, wave.get_buff()))
            wave.set_buff_with_data(buff)

            if not buff:
                continue

            max_y = max(buff)
            min_y = min(buff)

            if min_y < 0:
                max_y += -min_y

            space = max_y / 10  # top and bottom space percent
            _max_y.append(max_y + space)
            _min_y.append(min_y - (space / 2))

        if _max_y and _min_y:
            return max(_max_y), min(_min_y)
        return 0, 0

    def prepare_drawing_data(self):
        max_y, min_y = self.calculate_drawing_data()
        for wave in self._waves:
            if max_y == 0:
                continue
            wave.prepare_drawing_data(max_y, min_y)

    def draw(self, ctx):
        label_y_offset = 0
        for wave in self._waves:
            wave.draw(ctx)
            wave.draw_label(ctx, label_y_offset)
            label_y_offset += 1


class Wave:
    def __init__(self, size, color, label):
        self._size = size
        self._buff = [None] * size
        self._buff_with_data = []
        self._index = 0
        self._color = color
        if label is not None:
            self._label = label.strip()
        else:
            self._label = None

    def put(self, value):
        self._buff[self._index] = value
        if self._index == self._size - 1:
            for _i in range(0, self._size - 1):
                self._buff[_i] = self._buff[_i+1]
            self._buff[self._index] = None
        else:
            self._index += 1

    def get_buff(self):
        return self._buff

    def set_buff_with_data(self, buff):
        self._buff_with_data = buff

    def get_color(self):
        return self._color

    coordinates = []
    y_peaks_positive_coordinates = []  # координаты положительных вершины синусоиды
    y_peaks_negative_coordinates = []  # координаты отрицательных вершины синусоиды

    def prepare_drawing_data(self, max_y, min_y):
        if not self._buff_with_data:
            return
        # вершина синусоиды
        i = 0
        y_peaks_positive = []
        y_peaks_negative = []
        cnt = len(self._buff_with_data)
        for y in self._buff_with_data:
            if i - 1 > 0 and i + 1 < cnt:
                left = self._buff_with_data[i - 1]
                right = self._buff_with_data[i + 1]
                if y > left and y > right:
                    y_peaks_positive.append(y)
                if y < left and y < right:
                    y_peaks_negative.append(y)
            i += 1

        x = 1
        self.coordinates = []
        self.y_peaks_positive_coordinates = []  # координаты положительных вершины синусоиды
        self.y_peaks_negative_coordinates = []  # координаты отрицательных вершины синусоиды
        for y in self._buff_with_data:
            coordinate = (x / self._size), ((y - min_y) / max_y)
            if y in y_peaks_positive:
                self.y_peaks_positive_coordinates.append(coordinate)
            if y in y_peaks_negative:
                self.y_peaks_negative_coordinates.append(coordinate)
            self.coordinates.append(coordinate)
            x += 1

    def draw(self, ctx):
        if not self.coordinates:
            return

        ctx.set_source_rgb(*self._color)
        ctx.set_line_width(.002)
        ctx.set_dash([])

        x, y = self.coordinates[0]
        ctx.move_to(x, 1-y)

        for x, y in self.coordinates:
            ctx.line_to(x, 1-y)
        ctx.stroke()

        # вывод кружков на положительной вершине синусоиды
        for x, y in self.y_peaks_positive_coordinates:
            ctx.arc(x, 1-y, 0.005,  0, 2*math.pi)
            ctx.fill()
            ctx.stroke()

        # вывод кружков на отрицательной вершине синусоиды
        for x, y in self.y_peaks_negative_coordinates:
            ctx.arc(x, 1 - y, 0.005, 0, 2 * math.pi)
            ctx.fill()
            ctx.stroke()

    def draw_label(self, ctx, y_offset):
        if self._label is None:
            return
        y_offset_rec = 0.01
        y_offset_text = 0.03
        for i in range(y_offset):
            y_offset_rec += 0.03
            y_offset_text += 0.03

        ctx.rectangle(0.01, y_offset_rec, 0.02, 0.02)
        ctx.set_source_rgb(*self._color)
        ctx.fill()
        ctx.stroke()

        ctx.set_source_rgb(0,0,0)
        ctx.set_font_size(0.025)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(0.04, y_offset_text)
        ctx.show_text(self._label)

        ctx.stroke()
