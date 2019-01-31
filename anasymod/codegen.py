class CodeGenerator:
    def __init__(self, line_ending='\n'):
        # save settings
        self.line_ending = line_ending

        # initialize
        self.text = None
        self.reset()

    def print(self, s):
        self.text += s

    def println(self, s):
        self.print(s + self.line_ending)

    def reset(self):
        self.text = ''

    def use_templ(self, template):
        self.print(template.render())

    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(self.text)