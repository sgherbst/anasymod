class CodeGenerator:
    def __init__(self, tab_string: str=None, line_ending='\n'):
        # save settings
        self.tab_string = tab_string if tab_string is not None else '    '
        self.line_ending = line_ending if line_ending is not None else '\n'

        # initialize variables
        self.tab_level = 0
        self.text = ''

    def write(self, line):
        self.text += line

    def writeln(self, line=''):
        self.write(self.tab_level * self.tab_string + line + self.line_ending)

    def reset(self):
        self.text = ''

    def use_templ(self, template):
        self.write(template.render())

    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(self.text)
        self.reset()

    def read_from_file(self, filename):
        with open(filename, 'r') as f:
            self.text += f.read()

    def dump(self):
        return self.text

    def indent(self, quantity=1):
        self.tab_level += (1 * quantity)

    def dedent(self, quantity=1):
        self.tab_level -= (1 * quantity)
        assert self.tab_level >= 0

