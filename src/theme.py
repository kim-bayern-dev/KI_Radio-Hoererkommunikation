import gradio as gr
from gradio.themes.utils import fonts
from gradio.themes.utils import colors

navy = colors.Color(
    name="navy",
    c50="#f6f7fb",
    c100="#e7e9f0",
    c200="#d9dbe6",
    c300="#b2b5cc",
    c400="#8e8fa3",
    c500="#686a8a",
    c600="#525473",
    c700="#3c3e5c",
    c800="#262945",
    c900="#0f1742",
    c950="#0b102e",
)

cyan = colors.Color(
    name="brand-cyan",
    c50="#f0feff",
    c100="#e0faff",
    c200="#b9f5ff",
    c300="#7ff0ff",
    c400="#3de9ff",
    c500="#00e5ff",
    c600="#00d4eb",
    c700="#00b6c9",
    c800="#0090a0",
    c900="#00636d",
    c950="#004c55",
)

grey = colors.Color(
    name="brand-grey",
    c50="#fafafa",
    c100="#f3f4f4",
    c200="#eeefef",
    c300="#e4e5e5",
    c400="#d9dadb",
    c500="#cfd0d1",
    c600="#b9babb",
    c700="#9fa0a2",
    c800="#7d7f81",
    c900="#5b5d60",
    c950="#3e3f42",
)


theme = gr.themes.Monochrome(
    font=[fonts.GoogleFont("Montserrat"), "ui-sans-serif"],
    radius_size=gr.themes.sizes.radius_sm,
    primary_hue=navy,
    secondary_hue=cyan,
    neutral_hue=navy,
).set(
    body_background_fill="#0f1742",
    # background_fill_secondary="#e0faff",
    # input_background_fill="#e0faff",
)


extra_css = f"""
"""
