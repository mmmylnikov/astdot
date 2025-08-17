import ast
import inspect
import sys
from typing import Literal


DEFAULT_FONT = 'Menlo'
ALLOWED_FONTS = ['Menlo', 'Monaco', 'Helvetica', 'JetBrains Mono']


def make_style(
    fontname: str | None = None,
    fontsize: int = 15,
    fontcolor: str = '#000000',
    penwidth: float = 1.0,
    border_color: str = '#000000',
    fillcolor: str = '#E5FDCD',
    edge_fontsize: int = 12,
    edge_fontcolor: str = '#555555',
    edge_penwidth: float = 1.0,
    edge_arrowsize: float = 0.5,
    edge_color: str = '#000000',
    width_in: int | None = None,
    height_in: int | None = None,
    rankdir: Literal['TB', 'LR'] = 'TB',
    ranksep: int = 0.4,
    nodesep: int = 0.25,
    splines: Literal['true', 'line', 'polyline', 'ortho'] = 'true',
    force_fit: bool = True,
):
    font = fontname if fontname in ALLOWED_FONTS else DEFAULT_FONT
    size_attr = ''
    if width_in and height_in:
        size_attr = f' size="{width_in},{height_in}{"!" if force_fit else ""}"'
    elif width_in:
        size_attr = f' size="{width_in}{"!" if force_fit else ""}"'
    elif height_in:
        size_attr = f' size="100,{height_in}{"!" if force_fit else ""}"'

    return f"""
graph [
    bgcolor="transparent"
    fontname="{font}"
    fontcolor="{fontcolor}"
    fontsize={fontsize}
    fontnames="ps"
    {size_attr}
    rankdir={rankdir}
    ranksep={ranksep}
    nodesep={nodesep}
    splines={splines}
    ratio=compress
]
node [
    fontname="{font}"
    fontcolor="{fontcolor}"
    fontsize={fontsize}
    shape=box
    style="rounded, filled"
    fillcolor="{fillcolor}"
    penwidth={penwidth}
    color="{border_color}"
]
edge [
    fontname="{font}"
    fontcolor="{edge_fontcolor}"
    fontsize={edge_fontsize}
    penwidth={edge_penwidth}
    arrowsize={edge_arrowsize}
    color="{edge_color}"
]
"""


def graph_to_dot(graph, node_labels, edge_labels, style):
    dot = [f'digraph G {{{style}']
    for n in graph:
        label = node_labels[n].replace('"', '\\"')
        dot.append(f'{n} [label="{label}"]')
    dot.extend(
        f'{src} -> {dst} [label="{edge_labels[src, dst]}"]'
        for src in graph
        for dst in graph[src]
    )
    dot.append('}')
    return '\n'.join(dot)


def skip(name, value):
    return name != 'value' and value in ([], None)


def _to_dot_from_ast(root, skip, style):
    def walk_fields(node_id, node):
        args = []
        for name, value in ast.iter_fields(node):
            match value:
                case _ if skip(name, value):
                    pass
                case ast.AST() | list():
                    walk_node(node_id, value, f'.{name}')
                case _:
                    args.append(f'{name}: {value!r}')
        return args

    def walk_node(parent_id, node, edge_label):
        node_id = len(graph)
        graph[node_id] = []
        if parent_id is not None:
            graph[parent_id].append(node_id)
            edge_labels[parent_id, node_id] = edge_label
        match node:
            case ast.AST():
                args = [node.__class__.__name__, *walk_fields(node_id, node)]
                node_labels[node_id] = '\\n'.join(args)
            case list():
                node_labels[node_id] = 'list'
                for i, x in enumerate(node):
                    walk_node(node_id, x, f'[{i}]')

    if style is None:
        style = make_style()

    graph, node_labels, edge_labels = {}, {}, {}
    walk_node(None, root, '')
    return graph_to_dot(graph, node_labels, edge_labels, style)


def source_to_ast(
    source,
    *,
    optimize: Literal[None, -1, 0, 1, 2] = None,
    mode: Literal['exec', 'eval', 'single'] = 'exec',
):
    if optimize is None or sys.version_info < (3, 13):
        return ast.parse(source, mode=mode)
    return ast.parse(source, mode=mode, optimize=optimize)


def ast_to_dot(node, skip=skip, style=None):
    return _to_dot_from_ast(node, skip, style)


def source_to_dot(
    source,
    skip=skip,
    style=None,
    *,
    optimize: Literal[None, -1, 0, 1, 2] = None,
    mode: Literal['exec', 'eval', 'single'] = 'exec',
):
    tree = source_to_ast(source, optimize=optimize, mode=mode)
    return _to_dot_from_ast(tree, skip, style)


def object_to_dot(
    obj,
    skip=skip,
    style=None,
    *,
    optimize: Literal[None, -1, 0, 1, 2] = None,
    mode: Literal['exec', 'eval', 'single'] = 'exec',
):
    return source_to_dot(
        source=inspect.getsource(obj),
        skip=skip,
        style=style,
        optimize=optimize,
        mode=mode,
    )
