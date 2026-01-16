import jinja2


def render_jinja_template(template: str, **kwargs) -> str:
    return jinja2.Template(template).render(**kwargs)
