import os.path
from ConfigParser import ConfigParser, NoSectionError, NoOptionError


class Config(object):
    """
    Read and write Tatlin configuration.
    """
    def __init__(self):
        self.defaults = {
            'machine.platform_w': 120,
            'machine.platform_h': 100,
        }

        self.fname = os.path.expanduser(os.path.join('~', '.tatlin'))

        self.config = ConfigParser()
        self.config.read(self.fname)

    def read(self, key):
        val = self._read_file(key)
        if val is None:
            val = self.defaults[key]

        return val

    def _read_file(self, key):
        section, option = self._parse_specifier(key)
        try:
            val = self.config.get(section, option)
        except (NoSectionError, NoOptionError):
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
    c = Config()
    c.write('foo', 'bar')
    c.write('machine.toolhead', 0)
    print c.read('foo')
    print c.read('general.foo')
    print c.read('machine.platform_w')
