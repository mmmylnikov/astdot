import contextlib
import dis
import io
import re
import sys
from collections.abc import Callable
from typing import Literal

import graphviz
import streamlit as st
from code_editor import code_editor
from streamlit.delta_generator import DeltaGenerator

import astdot
from templates import templates as code_templates


def is_stlite():
    return sys.platform == 'emscripten'


def remove_material_icons(text: str) -> str:
    pattern = r':material/[a-zA-Z0-9_]+:'
    return re.sub(pattern, '', text)


PLATFORM: Literal['STLITE', 'STREAMLIT'] = (
    'STLITE' if is_stlite() else 'STREAMLIT'
)

APP_TITLE = 'Python AST Viewer'
APP_ICON_EMOJI = '🌳'
APP_ICON_PNG_SMALL = 'static/images/icon/logo_small.png'
APP_ICON_PNG_LARGE = 'static/images/icon/logo_large.png'
STATE = st.session_state

ICONS = {
    'download': ':material/download:',
    'svg': ':material/blur_on:',
    'png': ':material/image:',
    'ui': ':material/format_paint:',
    'ast': ':material/account_tree:',
    'code': ':material/edit_note:',
    'output': ':material/terminal:',
    'bytecode': ':material/memory:',
    'vars': ':material/input:',
    'tune': ':material/tune:',
    'dot': ':material/schema:',
}

if 'code_template_name' not in STATE:
    STATE['code_template_name'] = code_templates[0].name
if 'code_editor_template' not in STATE:
    STATE['code_editor_template'] = code_templates[0].code.strip()


def display_settings_block(
    label: str,
    container: DeltaGenerator,
    body_generator: Callable,
    expanded: bool = True,
    icon: str | None = None,
):
    if PLATFORM == 'STREAMLIT':
        with container.expander(
            label=label,
            expanded=expanded,
            icon=icon,
            width='stretch',
        ):
            body_generator()
    else:
        with container.expander(
            label=remove_material_icons(label),
            expanded=expanded,
            icon=icon,
        ):
            body_generator()


def prepare_ui_settings():
    st.checkbox(
        label='show headers',
        value=STATE.get('ui_show_headers', True),
        key='ui_show_headers',
    )
    if 'ui_theme_current' not in STATE:
        STATE['ui_theme_current'] = 'light'
    st.radio(
        'change theme',
        options=['light', 'dark'],
        key='ui_theme',
        index=0,
    )
    st.warning(
        'When you change the theme, settings from other '
        'sections will be reset to their default values.'
    )

    if STATE['ui_theme'] == 'dark':
        st._config.set_option('theme.base', 'dark')  # noqa: SLF001
        st._config.set_option('theme.backgroundColor', 'black')  # noqa: SLF001
    else:
        st._config.set_option('theme.base', 'light')  # noqa: SLF001
        st._config.set_option('theme.backgroundColor', 'white')  # noqa: SLF001

    if STATE['ui_theme_current'] != STATE['ui_theme']:
        STATE['ui_theme_current'] = STATE['ui_theme']
        if PLATFORM == 'STREAMLIT':
            st.rerun()


def prepare_code_editor_settings():
    col1, col2 = st.columns(2)
    col1.selectbox(
        label='response mode',
        options=['default', 'debounce'],
        index=0,
        help=(
            'In "default" mode, rendering requires manual action; '
            'in "debounce" mode, AST rendering happens automatically '
            'while typing.'
        ),
        key='code_editor_response_mode',
    )
    theme_index = 0 if STATE['ui_theme'] == 'light' else 1
    col2.selectbox(
        'theme',
        options=['light', 'dark'],
        index=theme_index,
        key='code_editor_theme',
    )
    col1, col2 = st.columns(2)
    col1.selectbox(
        label='cursor style',
        options=['ace', 'slim', 'smooth', 'wide'],
        index=3,
        key='code_editor_cursorStyle',
    )
    col2.number_input(
        label='font size',
        value=STATE.get('code_editor_fontSize', 14),
        min_value=8,
        max_value=32,
        key='code_editor_fontSize',
    )

    col1, col2 = st.columns(2)
    col1.selectbox(
        label='shortcuts',
        options=['vscode', 'vim', 'emacs', 'sublime'],
        index=0,
        key='code_editor_shortcuts',
    )

    st.checkbox(
        label='wrap',
        value=STATE.get('code_editor_wrap', True),
        key='code_editor_wrap',
    )
    st.checkbox(
        label='show line numbers',
        value=STATE.get('code_editor_showLineNumbers', True),
        key='code_editor_showLineNumbers',
    )


def prepare_ast_settings():
    st.caption('Parse options')
    col1, col2 = st.columns(2)
    col1.selectbox(
        label='mode',
        options=['exec', 'eval', 'single'],
        index=0,
        key='code_ast_mode',
    )
    col2.selectbox(
        label='optimize (≥3.13 only)',
        options=[-1, 0, 1, 2],
        index=0,
        key='code_ast_optimize',
        disabled=not sys.version_info >= (3, 13),
    )

    st.caption('Style options')
    st.checkbox(
        label='show dot',
        value=STATE.get('code_ast_show_dot', False),
        key='code_ast_show_dot',
    )
    col1, col2 = st.columns(2)
    col1.selectbox(
        label='font name',
        options=astdot.ALLOWED_FONTS,
        index=0,
        key='code_ast_fontname',
    )
    col2.number_input(
        label='font size',
        value=15,
        min_value=1,
        max_value=32,
        step=1,
        key='code_ast_fontsize',
    )

    col1, col2 = st.columns(2)
    col1.number_input(
        label='edge arrow size',
        value=0.5,
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        key='code_ast_edge_arrowsize',
    )
    col2.number_input(
        label='edge font size',
        value=12,
        min_value=1,
        max_value=32,
        step=1,
        key='code_ast_edge_fontsize',
    )

    col1, col2 = st.columns(2)
    col1.number_input(
        label='pen width',
        value=1.0,
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        key='code_ast_penwidth',
    )
    col2.number_input(
        label='edge pen width',
        value=1.0,
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        key='code_ast_edge_penwidth',
    )

    col1, col2 = st.columns(2)
    col1.number_input(
        label='rank sep',
        value=0.20,
        min_value=0.0,
        max_value=10.0,
        step=0.05,
        key='code_ast_ranksep',
    )
    col2.number_input(
        label='node sep',
        value=0.10,
        min_value=0.0,
        max_value=10.0,
        step=0.05,
        key='code_ast_nodesep',
    )

    col1, col2 = st.columns(2)
    col1.selectbox(
        label='rank dir',
        options=['TB', 'LR'],
        index=0,
        key='code_ast_rankdir',
    )
    col2.selectbox(
        label='splines',
        options=['true', 'line', 'polyline', 'ortho'],
        index=0,
        key='code_ast_splines',
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.color_picker(
        label='fill',
        value='#E5FDCD',
        key='code_ast_fillcolor',
    )
    col2.color_picker(
        label='border',
        value='#000000' if STATE['ui_theme'] == 'light' else '#555555',
        key='code_ast_border_color',
    )
    col3.color_picker(
        label='font',
        value='#000000',
        key='code_ast_fontcolor',
    )
    col4.color_picker(
        label='edge',
        value='#555555',
        key='code_ast_edge_fontcolor',
    )

    st.checkbox(
        label='force fit',
        value=STATE.get('code_ast_force_fit', True),
        key='code_ast_force_fit',
    )

    if st.checkbox(
        label='use size',
        value=STATE.get('code_ast_use_size', False),
        key='code_ast_use_size',
    ):
        col1, col2 = st.columns(2)
        col1.number_input(
            label='width',
            value=5.0,
            min_value=0.5,
            max_value=100.0,
            step=0.5,
            key='code_ast_width_in',
        )
        col2.number_input(
            label='height',
            value=5.0,
            min_value=0.5,
            max_value=100.0,
            step=0.5,
            key='code_ast_height_in',
        )


def prepare_output_settings():
    if st.checkbox(
        label='show output',
        value=STATE.get('code_output_show', False),
        key='code_output_show',
    ):
        st.checkbox(
            label='line numbers',
            value=STATE.get('code_output_line_numbers', True),
            key='code_output_line_numbers',
        )
        st.checkbox(
            label='wrap lines',
            value=STATE.get('code_output_wrap_lines', True),
            key='code_output_wrap_lines',
        )
        st.checkbox(
            label='show user variables',
            value=STATE.get('code_output_show_var', True),
            key='code_output_show_var',
        )


def prepare_bytecode_settings():
    if st.checkbox(
        label='show bytecode',
        value=STATE.get('code_bytecode_show', False),
        key='code_bytecode_show',
    ):
        st.caption('Disassemble options')
        if st.checkbox(
            label='use depth',
            value=STATE.get('code_bytecode_use_depth', False),
            key='code_bytecode_use_depth',
        ):
            st.number_input(
                label='depth',
                value=STATE.get('code_bytecode_depth', 0),
                min_value=0,
                max_value=1000,
                step=1,
                key='code_bytecode_depth',
            )
        st.checkbox(
            label='show caches (≥3.11 only)',
            value=STATE.get('code_bytecode_show_caches', False),
            key='code_bytecode_show_caches',
            disabled=not sys.version_info >= (3, 11),
        )
        st.checkbox(
            label='adaptive (≥3.11 only)',
            value=STATE.get('code_bytecode_adaptive', False),
            key='code_bytecode_adaptive',
            disabled=not sys.version_info >= (3, 11),
        )

        st.checkbox(
            label='show offsets (≥3.13 only)',
            value=STATE.get('code_bytecode_show_offsets', False),
            key='code_bytecode_show_offsets',
            disabled=not sys.version_info >= (3, 13),
        )
        st.caption('Style options')
        theme_index = 0 if STATE['ui_theme'] == 'light' else 1
        st.selectbox(
            'theme',
            options=['light', 'dark'],
            index=theme_index,
            key='code_bytecode_theme',
        )
        st.number_input(
            label='font size',
            value=STATE.get('code_bytecode_fontSize', 12),
            min_value=4,
            max_value=32,
            key='code_bytecode_fontSize',
        )
        st.checkbox(
            label='wrap',
            value=STATE.get('code_bytecode_wrap', False),
            key='code_bytecode_wrap',
        )
        st.checkbox(
            label='show line numbers',
            value=STATE.get('code_bytecode_showLineNumbers', False),
            key='code_bytecode_showLineNumbers',
        )


def load_code_template():
    selected_name = STATE['code_template_name']
    template = next(
        (t for t in code_templates if t.name == selected_name), None
    )
    if template:
        STATE['code_editor_template'] = template.code.strip()


def display_card(
    container: DeltaGenerator,
    body: Callable,
    label: str,
    show: bool = True,
):
    if not show:
        return
    with container:
        if STATE['ui_show_headers']:
            st.subheader(label)
        body()


def display_code_editor():
    options = [template.name for template in code_templates]
    st.selectbox(
        label='Template',
        options=options,
        key='code_template_name',
        on_change=load_code_template,
    )
    code_editor(
        code=STATE['code_editor_template'],
        lang='python',
        key='code_editor',
        shortcuts=STATE['code_editor_shortcuts'],
        allow_reset=True,
        focus=True,
        theme=STATE['code_editor_theme'],
        response_mode=STATE['code_editor_response_mode'],
        options={
            'wrap': STATE['code_editor_wrap'],
            'minLines': 3,
            'fontSize': STATE['code_editor_fontSize'],
            'cursorStyle': STATE['code_editor_cursorStyle'],
            'showLineNumbers': STATE['code_editor_showLineNumbers'],
        },
        buttons=[
            {
                'name': 'Render (CMD+Enter)',
                'feather': 'Monitor',
                'hasText': True,
                'style': {'top': '0.46rem', 'right': '0.4rem'},
                'commands': ['submit'],
            },
            {
                'name': 'Copy',
                'feather': 'Copy',
                'hasText': True,
                'style': {'top': '2.46rem', 'right': '0.4rem'},
                'commands': ['copyAll'],
            },
        ],
    )


def display_ast_viewer():
    if not STATE['code_editor'] or not STATE['code_editor']['text']:
        st.caption('No data available for rendering')
        st.info('Please click Render in the code editor or start typing.')
        return
    style = astdot.make_style(
        fillcolor=STATE['code_ast_fillcolor'],
        penwidth=STATE['code_ast_penwidth'],
        border_color=STATE['code_ast_border_color'],
        fontname=STATE['code_ast_fontname'],
        fontsize=STATE['code_ast_fontsize'],
        fontcolor=STATE['code_ast_fontcolor'],
        edge_fontsize=STATE['code_ast_edge_fontsize'],
        edge_fontcolor=STATE['code_ast_edge_fontcolor'],
        edge_penwidth=STATE['code_ast_edge_penwidth'],
        edge_arrowsize=STATE['code_ast_edge_arrowsize'],
        edge_color=STATE['code_ast_border_color'],
        width_in=STATE['code_ast_width_in']
        if STATE['code_ast_use_size']
        else None,
        height_in=STATE['code_ast_height_in']
        if STATE['code_ast_use_size']
        else None,
        rankdir=STATE['code_ast_rankdir'],
        ranksep=STATE['code_ast_ranksep'],
        nodesep=STATE['code_ast_nodesep'],
        splines=STATE['code_ast_splines'],
        force_fit=STATE['code_ast_force_fit'],
    )
    try:
        dot = astdot.source_to_dot(
            source=STATE['code_editor']['text'],
            skip=astdot.skip,
            mode=STATE['code_ast_mode'],
            optimize=STATE['code_ast_optimize'],
            style=style,
        )
    except SyntaxError as error:
        st.caption('Exception raised.')
        st.warning(f'SyntaxError: {error}')
    else:
        st.graphviz_chart(
            figure_or_dot=dot,
            use_container_width=True,
        )

        if PLATFORM == 'STREAMLIT':
            src = graphviz.Source(dot)
            svg_bytes = src.pipe(format='svg')
            png_bytes = src.pipe(format='png')
            col1, col2, col3 = STATE['download_container'].columns(3)
            col1.download_button(
                label='DOT',
                data=dot,
                file_name='ast.dot',
                mime='text/plain',
                use_container_width=True,
                icon=ICONS['dot'],
            )
            col2.download_button(
                label='SVG',
                data=svg_bytes,
                file_name='ast.svg',
                mime='image/svg+xml',
                use_container_width=True,
                icon=ICONS['svg'],
            )
            col3.download_button(
                label='PNG',
                data=png_bytes,
                file_name='ast.png',
                mime='image/png',
                use_container_width=True,
                icon=ICONS['png'],
            )
        else:
            with STATE['download_container'].container():
                st.info(
                    'Currently, `png` and `svg` downloads are only available '
                    'in the local environment.'
                )
                st.download_button(
                    label='DOT',
                    data=dot,
                    file_name='ast.dot',
                    mime='text/plain',
                    use_container_width=True,
                )

        if STATE['code_ast_show_dot']:
            st.code(
                body=dot,
                language='dot',
            )


def display_code_output():
    if not STATE['code_editor'] or not STATE['code_editor']['text']:
        st.warning('The code is missing or the render failed.')
        return
    code = STATE['code_editor']['text']
    exec_globals = {}
    output = None
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        try:
            exec(code, exec_globals)
        except Exception as e:
            print(f'Error: {e}')
        output = buf.getvalue()
    if PLATFORM == 'STREAMLIT':
        st.code(
            body=output,
            language='sh',
            wrap_lines=STATE['code_output_wrap_lines'],
            line_numbers=STATE['code_output_line_numbers'],
        )
    else:
        st.code(
            body=output,
            language='sh',
            line_numbers=STATE['code_output_line_numbers'],
        )

    if STATE['code_output_show_var']:
        if STATE['ui_show_headers']:
            label_vars = f'{ICONS["vars"]} Variables'
            st.subheader(label_vars)
        variables = {
            k: v
            for k, v in exec_globals.items()
            if not k.startswith('__') and k != '__builtins__'
        }
        if variables:
            st.json(variables)
        else:
            st.write('No user variables.')


def display_code_bytecode():
    if not STATE['code_editor'] or not STATE['code_editor']['text']:
        st.warning('The code is missing or the render failed.')
        return
    code = STATE['code_editor']['text']
    buf = io.StringIO()
    try:
        if sys.version_info >= (3, 13):
            dis.dis(
                x=code,
                file=buf,
                depth=STATE['code_bytecode_depth']
                if STATE['code_bytecode_use_depth']
                else None,
                show_caches=STATE['code_bytecode_show_caches'],
                adaptive=STATE['code_bytecode_adaptive'],
                show_offsets=STATE['code_bytecode_show_offsets'],
            )
        elif sys.version_info >= (3, 11):
            dis.dis(
                x=code,
                file=buf,
                depth=STATE['code_bytecode_depth']
                if STATE['code_bytecode_use_depth']
                else None,
                show_caches=STATE['code_bytecode_show_caches'],
                adaptive=STATE['code_bytecode_adaptive'],
            )
        else:
            dis.dis(
                x=code,
                file=buf,
                depth=STATE['code_bytecode_depth']
                if STATE['code_bytecode_use_depth']
                else None,
            )
    except SyntaxError as error:
        st.warning(f'SyntaxError: {error}')
    else:
        bytecode_str = buf.getvalue()
        code_editor(
            code=bytecode_str,
            lang='sh',
            allow_reset=False,
            focus=False,
            theme=STATE['code_bytecode_theme'],
            response_mode='default',
            options={
                'readOnly': True,
                'showFoldWidgets': False,
                'showGutter': STATE['code_bytecode_showLineNumbers'],
                'showLineNumbers': STATE['code_bytecode_showLineNumbers'],
                'wrap': STATE['code_bytecode_wrap'],
                'fontSize': STATE['code_bytecode_fontSize'],
            },
            buttons=[
                {
                    'name': 'Copy',
                    'feather': 'Copy',
                    'hasText': True,
                    'style': {'top': '0.46rem', 'right': '0.4rem'},
                    'commands': ['copyAll'],
                },
            ],
        )


def prepare_sidebar():
    sidebar = st.sidebar
    sidebar_download_label = f'{ICONS["download"]} Download'
    sidebar_settings_label = f'{ICONS["tune"]} Settings'

    if STATE.get('code_editor'):
        sidebar.header(sidebar_download_label)
        STATE['download_container'] = sidebar.empty()

    sidebar.header(sidebar_settings_label)
    display_settings_block(
        'UI', sidebar, prepare_ui_settings, False, ICONS['ui']
    )
    display_settings_block(
        'Code', sidebar, prepare_code_editor_settings, False, ICONS['code']
    )
    display_settings_block(
        'AST', sidebar, prepare_ast_settings, False, ICONS['ast']
    )
    display_settings_block(
        'Output', sidebar, prepare_output_settings, False, ICONS['output']
    )
    display_settings_block(
        'Bytecode', sidebar, prepare_bytecode_settings, False, ICONS['bytecode']
    )


def prepare_body():
    col1, col2 = st.columns(2)
    display_card(
        container=col1,
        body=display_code_editor,
        label=f'{ICONS["code"]} Code editor',
    )
    display_card(
        container=col2,
        body=display_ast_viewer,
        label=f'{ICONS["ast"]} Abstract Syntax Tree',
    )
    display_card(
        container=col1,
        body=display_code_output,
        label=f'{ICONS["output"]} Output',
        show=STATE['code_output_show'],
    )
    display_card(
        container=col1,
        body=display_code_bytecode,
        label=f'{ICONS["bytecode"]} Bytecode',
        show=STATE['code_bytecode_show'],
    )


def render_page():
    prepare_sidebar()
    prepare_body()


def set_page_config():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON_PNG_SMALL,
        layout='wide',
        initial_sidebar_state='expanded',
    )


def set_logo():
    if PLATFORM == 'STREAMLIT':
        st.logo(
            image=APP_ICON_PNG_LARGE,
            size='large',
            icon_image=APP_ICON_PNG_SMALL,
        )
    else:
        with st.sidebar:
            st.title(APP_TITLE)
            st.info(
                'You are using a serverless solution. For the best experience, '
                'deploy the application in a local environment.'
            )


def display_python_version(container: DeltaGenerator):
    container.caption(f'Run on Python {sys.version}')


def run_app():
    set_page_config()
    set_logo()
    display_python_version(st.sidebar)
    render_page()


if __name__ == '__main__':
    run_app()
