from jinja2 import Environment

class JinjaTempl:
    def __init__(self, trim_blocks=False, lstrip_blocks=False):
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks

    def render(self):
        t = Environment(trim_blocks=self.trim_blocks, lstrip_blocks=self.lstrip_blocks).from_string(self.TEMPLATE_TEXT)
        #t = Template(self.TEMPLATE_TEXT)

        return t.render(subst=self)+'\n'

    TEMPLATE_TEXT = ''