import os.path
from ConfigParser import ConfigParser, NoSectionError, NoOptionError


class Config(object):
    """
    Read and write Tatlin configuration.
    """
    def __init__(self, fname):
        self.defaults = {
            # makerbot thing-o-matic platform size
            'machine.platform_w': 120,
            'machine.platform_d': 100,
            'machine.platform_offset_x': 0,
            'machine.platform_offset_y': 0,
            'ui.window_w': 640,
            'ui.window_h': 480,
            'ui.gcode_2d': False,
        }

        self.fname = fname
        self.config = ConfigParser()
        self.config.read(self.fname)

    def read(self, key, conv=None):
        val = self._read_file(key, conv)
        if val is None:
            val = self.defaults[key]

        return val

    def _read_file(self, key, conv):
        section, option = self._parse_specifier(key)
        try:
            if conv:
                val = conv(self.config.get(section, option))
            else:
                val = self.config.get(section, option)
        except (NoSectionError, NoOptionError, ValueError):
            val = None
        return val

    def write(self, key, val):
        section, option = self._parse_specifier(key)

        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, key, val)

        with open(self.fname, 'wb') as conf_file:
            self.config.write(conf_file)

    def _parse_specifier(self, spec):
        parts = spec.split('.', 1)
        if len(parts) < 2:
            section, option = 'general', parts[0]
        else:
            section, option = parts
        return (section, option)


if __name__ == '__main__':
    c = Config('.tatlin')
    c.write('foo', 'bar')
    c.write('machine.toolhead', 0)
    print c.read('foo')
    print c.read('general.foo')
    print c.read('machine.platform_w')
