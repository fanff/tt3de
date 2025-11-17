class ComboMaterialPy:
    count: int
    idx0: int
    idx1: int
    idx2: int
    idx3: int
    idx4: int

    def __init__(self) -> "ComboMaterialPy": ...
    def from_list(lst: list[int]) -> "ComboMaterialPy": ...

class StaticColorBackPy:
    back_color: tuple[int, int, int, int]
    def __init__(self, color: tuple[int, int, int, int]) -> "StaticColorBackPy": ...

class StaticColorFrontPy:
    front_color: tuple[int, int, int, int]
    def __init__(self, color: tuple[int, int, int, int]) -> "StaticColorFrontPy": ...
