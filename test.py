from src import astdot


def test():
    output = r"""
digraph G {
0 [label="Module" shape=box style="rounded, filled"]
1 [label="list" shape=box style="rounded, filled"]
2 [label="Expr" shape=box style="rounded, filled"]
3 [label="BinOp" shape=box style="rounded, filled"]
4 [label="Constant\nvalue: 2" shape=box style="rounded, filled"]
5 [label="Add" shape=box style="rounded, filled"]
6 [label="Constant\nvalue: 2" shape=box style="rounded, filled"]
0 -> 1 [label=".body"]
1 -> 2 [label="[0]"]
2 -> 3 [label=".value"]
3 -> 4 [label=".left"]
3 -> 5 [label=".op"]
3 -> 6 [label=".right"]
}
    """
    assert astdot.source_to_dot('2 + 2', style='').strip() == output.strip()
