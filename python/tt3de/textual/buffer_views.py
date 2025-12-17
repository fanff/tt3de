# -*- coding: utf-8 -*-
import time
from collections.abc import Callable
from typing import List, Tuple
from textual.containers import Horizontal
from textual.widgets import (
    Static,
    DataTable,
    Input,
    Label,
    TabbedContent,
    TabPane,
    Rule,
)
from textual.app import ComposeResult
from textual.visual import VisualType

from tt3de.render_context_rust import RustRenderContext
from tt3de.tt3de import GeometryBufferPy, PrimitiveBufferPy, VertexBufferPy


def tuple_to_str(tup):
    return " ".join([f"{v:.2f}" for v in tup])


def vertex_dict_to_str(vdict):
    if vdict is None:
        return "None"
    return f"Po {tuple_to_str(vdict['pos'])}\nNo {tuple_to_str(vdict['normal'])}\nUV {tuple_to_str(vdict['uv'])}"


class FilteredDataView(Static):
    DEFAULT_CSS = """
    .configrow {
        height: 3;
        width: auto;
    }
    .labelinput {
        height: 3;
        content-align: center middle;
        width: auto;
    }
    .input_field {
        width: auto;
    }
    """

    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        column_names: list[str] = [],
        index_filters: list[str] = [],
        iterator_filtered,
        to_row,
        row_height: int,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

        self.column_names = column_names

        self.index_filters = index_filters
        self.index_filters_wdg = []
        self._iterator_filtered: Callable = iterator_filtered
        self._to_row: Callable = to_row
        self.row_height = row_height
        self.index_filters_wdg: List[Tuple[str, Input]] = []

    def compose(self):
        self.table = DataTable()
        self.table.add_columns(*self.column_names)
        self.index_start_wdgt = Input(
            placeholder="Vertex Index",
            id="vbv_index_input_2d",
            type="integer",
            value="0",
            classes="input_field",
        )
        self.count_wdgt = Input(
            placeholder="Vertex Index",
            id="vbv_count_vertex_2d",
            type="integer",
            value="10",
            classes="input_field",
        )

        self.index_filters_wdg = [
            Input(
                placeholder=f"Filter {filter_name}",
                id=f"filter_{filter_name}",
                type="integer",
                value="",
                classes="input_field",
            )
            for filter_name in self.index_filters
        ]

        with Horizontal(classes="configrow"):
            yield Label("Start Index:", classes="labelinput")
            yield self.index_start_wdgt
            yield Rule(orientation="vertical")
            yield Label("Count:", classes="labelinput")
            yield self.count_wdgt

            for filter_name, filter_wdgt in zip(
                self.index_filters, self.index_filters_wdg
            ):
                yield Rule(orientation="vertical")
                yield Label(f"Filter {filter_name}:", classes="labelinput")
                yield filter_wdgt

        yield self.table

    def refresh_content(self):
        start_value = (
            int(self.index_start_wdgt.value)
            if len(self.index_start_wdgt.value) > 0
            else 0
        )
        count_2d_value = (
            int(self.count_wdgt.value) if len(self.count_wdgt.value) > 0 else 10
        )

        self.table.clear()

        aquired_count = 0

        filter_params = [start_value]
        for filter_wdgt in self.index_filters_wdg:
            filter_value = filter_wdgt.value
            if len(filter_value) == 0:
                filter_params.append(None)
            else:
                filter_params.append(int(filter_value))

        buffer_iter = self._iterator_filtered(*filter_params)
        while aquired_count < count_2d_value:
            try:
                idx, content = next(buffer_iter)

                cells = self._to_row(content)
                self.table.add_row(*cells, height=self.row_height, label=str(idx))
                aquired_count += 1

            except StopIteration:
                break


class PrimitiveViewPanel(FilteredDataView):
    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        primitive_buffer: PrimitiveBufferPy,
    ) -> None:
        column_names = ("Type", "NID", "GID", "MID", "pa", "pb", "pc")
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            column_names=column_names,
            index_filters=["node_id", "geometry_id", "material_id"],
            iterator_filtered=self.rr,
            to_row=self.primitive_to_row,
            row_height=3,
        )
        self.primitive_buffer: PrimitiveBufferPy = primitive_buffer

    def rr(
        self,
        start_index: int,
        node_id: int = None,
        geometry_id: int = None,
        material_id: int = None,
    ):
        for idx in range(start_index, self.primitive_buffer.primitive_count()):
            prim = self.primitive_buffer.get_primitive(idx)
            if node_id is not None and prim.get("node_id", -1) != node_id:
                continue
            if geometry_id is not None and prim.get("geometry_id", -1) != geometry_id:
                continue
            if material_id is not None and prim.get("material_id", -1) != material_id:
                continue
            yield idx, prim

    def primitive_to_row(self, prim_dict):
        return [
            str(prim_dict.get("_type", "")),
            prim_dict.get("node_id", -1),
            prim_dict.get("geometry_id", -1),
            prim_dict.get("material_id", -1),
            vertex_dict_to_str(prim_dict.get("pa", None)),
            vertex_dict_to_str(prim_dict.get("pb", None)),
            vertex_dict_to_str(prim_dict.get("pc", None)),
        ]


class GeometryViewPanel(FilteredDataView):
    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        geometry_buffer: GeometryBufferPy,
    ) -> None:
        column_names = ["Type", "NID", "MID", "P_Start"]
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            column_names=column_names,
            index_filters=["node_id", "material_id"],
            iterator_filtered=self.rr,
            to_row=self.primitive_to_row,
            row_height=1,
        )
        self.geometry_buffer: GeometryBufferPy = geometry_buffer

    def rr(self, start_index: int, node_id: int = None, material_id: int = None):
        for idx in range(start_index, self.geometry_buffer.geometry_count()):
            geom_dict = self.geometry_buffer.get_element(idx)
            if (
                node_id is not None
                and geom_dict["geom_ref"].get("node_id", "") != node_id
            ):
                continue

            if (
                material_id is not None
                and geom_dict["geom_ref"].get("material_id", "") != material_id
            ):
                continue
            yield idx, geom_dict

    def primitive_to_row(self, geom_dict):
        return [
            geom_dict.get("_type", ""),
            geom_dict["geom_ref"].get("node_id", ""),
            geom_dict["geom_ref"].get("material_id", ""),
            geom_dict.get("p_start", geom_dict.get("point_start", "")),
        ]


class Vertex2DViewPanel(FilteredDataView):
    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        vertex_buffer: VertexBufferPy,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            column_names=["src", "calc"],
            index_filters=[],
            iterator_filtered=self.iterator_filtered,
            to_row=self.primitive_to_row,
            row_height=1,
        )
        self.vertex_buffer: VertexBufferPy = vertex_buffer

    def iterator_filtered(self, start_index: int):
        for idx in range(start_index, self.vertex_buffer.get_2d_len()):
            yield idx, idx

    def primitive_to_row(self, vertex_idx):
        return [
            tuple_to_str(self.vertex_buffer.get_2d_vertex_tuple(vertex_idx)),
            tuple_to_str(self.vertex_buffer.get_2d_calculated_tuple(vertex_idx)),
        ]


class Vertex3DViewPanel(FilteredDataView):
    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        vertex_buffer: VertexBufferPy,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            column_names=["src", "calc"],
            index_filters=[],
            iterator_filtered=self.iterator_filtered,
            to_row=self.primitive_to_row,
            row_height=1,
        )
        self.vertex_buffer: VertexBufferPy = vertex_buffer

    def iterator_filtered(self, start_index: int):
        for idx in range(start_index, self.vertex_buffer.get_3d_len()):
            yield idx, idx

    def primitive_to_row(self, vertex_idx):
        return [
            tuple_to_str(self.vertex_buffer.get_3d_vertex_tuple(vertex_idx)),
            tuple_to_str(self.vertex_buffer.get_3d_calculated_tuple(vertex_idx)),
        ]


class BufferViewPanel(Static):
    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        rc: RustRenderContext,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.rc: RustRenderContext = rc
        self.refresh_period = 0.5  # seconds
        self._last_refresh_time = time.time()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Vertex", id="tabvertex"):
                self.vbvp = VertexBufferViewPanel(vertex_buffer=self.rc.vertex_buffer)
                yield self.vbvp
            with TabPane("Geometry", id="tabgeometry"):
                self.gvp = GeometryViewPanel(geometry_buffer=self.rc.geometry_buffer)

                yield self.gvp
            with TabPane("Primitive", id="tabprimitive"):
                self.pvp = PrimitiveViewPanel(primitive_buffer=self.rc.primitive_buffer)
                yield self.pvp

    def refresh_content(self):
        current_time = time.time()
        if current_time - self._last_refresh_time < self.refresh_period:
            return  # Skip refresh if not enough time has passed
        self._last_refresh_time = current_time
        # find the activated tab pane
        self.tc = self.query_one(TabbedContent)
        match self.tc.active_pane.id:
            case "tabvertex":
                self.vbvp.refresh_content()
            case "tabgeometry":
                self.gvp.refresh_content()
            case "tabprimitive":
                self.pvp.refresh_content()
            case _:
                pass


class VertexBufferViewPanel(Static):
    DEFAULT_CSS = """


    .configrow {
        height: 3;
        width: auto;
    }
    .labelinput {
        height: 3;
        content-align: center middle;
        width: auto;
    }
    .input_field {
        width: auto;
    }
    """

    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        vertex_buffer: VertexBufferPy,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.vertex_buffer: VertexBufferPy = vertex_buffer

    def compose(self):
        self.table_uv = DataTable()
        COLLUMNS_UV = ("uv",)
        self.table_uv.add_columns(*COLLUMNS_UV)

        with TabbedContent():
            with TabPane("3D", id="tab3d"):
                self.vertex_view_3d = Vertex3DViewPanel(
                    vertex_buffer=self.vertex_buffer
                )
                yield self.vertex_view_3d
            with TabPane("2D", id="tab2d"):
                self.gvp = Vertex2DViewPanel(vertex_buffer=self.vertex_buffer)
                yield self.gvp
            with TabPane("UV", id="tabuv"):
                yield self.table_uv

    def refresh_content(self):
        self.gvp.refresh_content()
