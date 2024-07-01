import stream

def create_parser():
    parser = stream.StreamParser()
    parser.connect('read_all', stream_parser_read_all)
    parser.connect('read_float', stream_parser_read_float)
    parser.connect('read_first_part', stream_parser_read_first_part)
    parser.connect('read_part', stream_parser_read_part)
    parser.connect('read_last_part', stream_parser_read_last_part)
    return parser

def stream_parser():
    parser = create_parser()

    parser.parse('test message \n')
    parser.parse('123.45 \n')

    parser.parse('a')
    parser.parse('bc')
    parser.parse('defj')
    parser.parse('h\n')

    parser.parse('5')
    parser.parse('43')
    parser.parse('.')
    parser.parse('2')
    parser.parse('1')
    parser.parse('\n')


def stream_parser_read_all(msg, *args, **kwargs):
    print('parser:read_all(msg={})'.format(msg))

def stream_parser_read_float(value, *args, **kwargs):
    print('parser:read_float()->:', value, type(value))

def stream_parser_read_first_part(msg, full_msg, *args, **kwargs):
    print('parser:read_first_part(msg={}, full_msg={})'.format(msg, full_msg))

def stream_parser_read_part(msg, full_msg, *args, **kwargs):
    print('parser:read_part(msg={}, full_msg={})'.format(msg, full_msg))

def stream_parser_read_last_part(msg, full_msg, *args, **kwargs):
    print('parser:read_last_part(msg={}, full_msg={})'.format(msg, full_msg))

def stream_reader():
    reader = stream.StreamReader()
    reader.connect('read_message', stream_reader_read_message)

    parser = create_parser()
    reader.connect('read_message', parser.parse)

    stream_message = stream.StreamMessage()
    stream_message.close_stream_after_read = True

    stream_message.set_msg('this is stream message')
    reader.start(stream_message, daemon=False)

    stream_message.set_msg('890.543')
    reader.start(stream_message, daemon=False)

    stream_message.by_one_byte = True
    stream_message.set_msg('by one byte')
    reader.start(stream_message, daemon=False)


def stream_reader_read_message(msg, *args, **kwargs):
    print('reader:read_message(msg={})'.format(msg))

if __name__ == '__main__':
    stream_parser()
    stream_reader()




