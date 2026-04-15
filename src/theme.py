import gradio as gr
from gradio.themes.utils import colors, fonts, sizes


# --- KI.M brand palettes ---
# Brand colors:
# Cyan:   #00E5FF
# Gray:   #DDDFDE
# White:  #FFFFFF
# Navy:   #0F1742
# Black:  #000000

kim_cyan = colors.Color(
    name="kim_cyan",
    c50="#ECFDFF",
    c100="#D4FAFF",
    c200="#A8F4FF",
    c300="#77EEFF",
    c400="#42E8FF",
    c500="#00E5FF",  # brand cyan
    c600="#00C7DE",
    c700="#00A8BC",
    c800="#008A99",
    c900="#006D79",
    c950="#004A53",
)

kim_navy = colors.Color(
    name="kim_navy",
    c50="#EEF1FA",
    c100="#DCE3F4",
    c200="#BAC7E8",
    c300="#96A9DA",
    c400="#748CCB",
    c500="#5571BC",
    c600="#405A99",
    c700="#2F4475",
    c800="#1F2E5A",
    c900="#0F1742",  # brand navy
    c950="#080D28",
)

# Neutral palette tuned for stronger contrast in light mode
kim_neutral = colors.Color(
    name="kim_neutral",
    c50="#FFFFFF",
    c100="#F7F9FC",  # panel bg / cards
    c200="#EEF2F6",  # app bg (darker than before)
    c300="#E1E7EE",  # borders light
    c400="#CBD5E1",  # borders stronger
    c500="#A8B4C3",
    c600="#7A8799",
    c700="#556275",
    c800="#2E3A52",
    c900="#111A3D",  # strong text
    c950="#0A1028",
)


def kim_theme():
    """
    KI.M / Kompass theme with improved contrast for:
    - chat area visibility
    - chat input bar visibility
    - clearer panel boundaries
    - slightly darker app background
    """
    theme = gr.themes.Soft(
        primary_hue=kim_cyan,
        secondary_hue=kim_navy,
        neutral_hue=kim_neutral,
        spacing_size=sizes.spacing_md,
        radius_size=sizes.radius_lg,
        text_size=sizes.text_md,
        font=[
            fonts.GoogleFont("Montserrat"),
            "ui-sans-serif",
            "system-ui",
            "Arial",
            "sans-serif",
        ],
        font_mono=[
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "Consolas",
            "monospace",
        ],
    ).set(
        # =========================================================
        # Light mode (main target) - higher contrast than before
        # =========================================================
        body_background_fill="*neutral_200",  # darker app canvas
        background_fill_primary="*neutral_100",  # main panel surfaces
        background_fill_secondary="*neutral_200",  # surrounding areas
        block_background_fill="*neutral_50",  # cards / blocks
        border_color_primary="*neutral_400",  # stronger borders
        block_border_width="1px",
        # Text / headings
        body_text_color="*neutral_900",
        body_text_color_subdued="*neutral_800",  # improved readability
        block_title_text_color="*secondary_900",
        block_label_text_color="*neutral_900",
        block_title_text_weight="700",
        # Inputs (important for chat bar visibility)
        input_background_fill="*neutral_50",
        input_border_color="*neutral_400",
        input_border_color_hover="*neutral_500",
        input_border_color_focus="*primary_600",
        input_shadow="0 1px 2px rgba(15, 23, 66, 0.05)",
        # Primary buttons (cyan with dark/navy text)
        button_primary_background_fill="*primary_500",
        button_primary_background_fill_hover="*primary_600",
        button_primary_border_color="*primary_600",
        button_primary_text_color="*secondary_950",
        button_primary_text_color_hover="*secondary_950",
        # Secondary buttons / UI controls
        button_secondary_background_fill="*neutral_50",
        button_secondary_background_fill_hover="*neutral_100",
        button_secondary_border_color="*neutral_400",
        button_secondary_border_color_hover="*primary_500",
        button_secondary_text_color="*secondary_900",
        button_secondary_text_color_hover="*secondary_900",
        # Links / accents
        link_text_color="*secondary_800",
        link_text_color_hover="*primary_700",
        slider_color="*primary_500",
        loader_color="*primary_500",
        # Checkbox / radio / selection accents
        checkbox_background_color="*neutral_50",
        checkbox_background_color_selected="*primary_500",
        checkbox_border_color="*neutral_500",
        checkbox_border_color_focus="*primary_600",
        # Tables / card-like internals
        table_border_color="*neutral_400",
        table_even_background_fill="*neutral_50",
        table_odd_background_fill="*neutral_100",
        # =========================================================
        # Dark mode fallback (branded + clearer separation)
        # =========================================================
        body_background_fill_dark="*secondary_950",
        background_fill_primary_dark="#0F1733",
        background_fill_secondary_dark="#121C3D",
        block_background_fill_dark="#121C3D",
        border_color_primary_dark="rgba(255,255,255,0.14)",
        block_border_width_dark="1px",
        body_text_color_dark="#F5F8FD",
        body_text_color_subdued_dark="rgba(245,248,253,0.78)",
        block_title_text_color_dark="#FFFFFF",
        block_label_text_color_dark="rgba(255,255,255,0.92)",
        input_background_fill_dark="rgba(255,255,255,0.05)",
        input_border_color_dark="rgba(255,255,255,0.18)",
        input_border_color_hover_dark="rgba(255,255,255,0.26)",
        input_border_color_focus_dark="*primary_500",
        button_primary_background_fill_dark="*primary_500",
        button_primary_background_fill_hover_dark="*primary_400",
        button_primary_border_color_dark="*primary_600",
        button_primary_text_color_dark="*secondary_950",
        button_secondary_background_fill_dark="rgba(255,255,255,0.04)",
        button_secondary_background_fill_hover_dark="rgba(255,255,255,0.08)",
        button_secondary_border_color_dark="rgba(255,255,255,0.22)",
        button_secondary_border_color_hover_dark="*primary_500",
        button_secondary_text_color_dark="#FFFFFF",
        link_text_color_dark="*primary_300",
        link_text_color_hover_dark="*primary_200",
        slider_color_dark="*primary_400",
        loader_color_dark="*primary_400",
        checkbox_background_color_dark="rgba(255,255,255,0.03)",
        checkbox_background_color_selected_dark="*primary_500",
        checkbox_border_color_dark="rgba(255,255,255,0.22)",
        checkbox_border_color_focus_dark="*primary_400",
        table_border_color_dark="rgba(255,255,255,0.12)",
        table_even_background_fill_dark="rgba(255,255,255,0.03)",
        table_odd_background_fill_dark="rgba(255,255,255,0.05)",
    )

    return theme
