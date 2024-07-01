import gi
import widgets, stream, rs232port
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class RS232Monitor(Gtk.Window):

    def __init__(self):
        super().__init__(title="RS232 Monitor")
        self.connect("destroy", Gtk.main_quit)
        self.set_default_size(1000, 600)

        msg = stream.StreamMessage()
        msg.by_one_byte = True
        self.device = rs232port.RS232PortMock(msg)

        self.reader = stream.StreamReader()
        self.parser = stream.StreamParser()

        self.display = widgets.DisplayWidget()
        self.plotter = widgets.PlotterWidget()
        self.connection = widgets.ConnectionWidget(self.device)

        # reader (parser to reader)
        self.reader.connect('read_message', self.parser.parse)
        self.reader.connect('read_error', self.parser.parse)

        self.parser.connect('read_float', self.plotter.on_read_float)
        self.parser.connect('read_last_part', self.plotter.on_read_last_part)
        self.parser.connect('read_all', self.plotter.on_read_all)

        # for test
        self.plotter.test_device = self.device

        # connection
        self.connection.on_connected = self.reader.start
        self.connection.on_disconnected = self.reader.stop
        self.connection.on_error = self.on_connection_error

        box = Gtk.Box()
        box.pack_start(self.display, True, True, 5)
        grid = Gtk.Grid()
        grid.attach(self.connection, 0, 0, 2, 1)
        grid.attach(box, 0, 1, 1, 1)
        grid.attach(self.plotter, 1, 1, 1, 1)
        self.add(grid)
        self.show_all()
        self.plotter.start_drawing()

    def on_connection_error(self, err):
        # show error message on display
        msg = stream.StreamMessage()
        msg.close_stream_after_read = True
        msg.set_msg(str(err) + '\n')
        self.reader.start(msg)


if __name__ == '__main__':
    RS232Monitor()
    Gtk.main()
