from jinja2 import Template

class JinjaTempl:
    def render(self):
        t = Template(self.TEMPLATE_TEXT)
        return t.render(subst=self)

    TEMPLATE_TEXT = ''