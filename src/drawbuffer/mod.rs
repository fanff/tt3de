use nalgebra_glm::Vec2;
use pyo3::{
    intern,
    prelude::*,
    types::{PyList, PyTuple},
};
pub mod drawbuffer;
use drawbuffer::*;
use pyo3::types::PyDict;
pub mod glyphset;
use glyphset::*;
pub mod segment_cache;
use crate::utils::convert_glm_vec2;
use segment_cache::*;

#[pyclass]
pub struct DrawingBufferPy {
    pub db: DrawBuffer<2, f32>,
    max_row: usize,
    max_col: usize,
    layer_count: usize,

    segment_class: Py<PyAny>,
    style_class: Py<PyAny>,
    color_class: Py<PyAny>,
    color_triplet_class: Py<PyAny>,

    seg_cache: SegmentCache,

    pub default_segment: Py<PyAny>,
}

#[pymethods]
impl DrawingBufferPy {
    #[new]
    fn new(py: Python, max_row: usize, max_col: usize) -> Self {
        let rich_style_module = py.import_bound("rich.style").unwrap();
        let rich_color_module = py.import_bound("rich.color").unwrap();
        let rich_text_module = py.import_bound("rich.text").unwrap();
        let rich_color_triplet_module = py.import_bound("rich.color_triplet").unwrap();

        let segment_class = rich_text_module.getattr("Segment").unwrap();
        let style_class = rich_style_module.getattr("Style").unwrap();
        let color_class = rich_color_module.getattr("Color").unwrap();
        let color_triplet_class = rich_color_triplet_module.getattr("ColorTriplet").unwrap();

        let mut segment_cache = SegmentCache::new_iso(4);
        let aseg0 = create_textual_segment(
            py,
            [0, 0, 0, 0, 0, 0, 0],
            &color_triplet_class,
            &color_class,
            &segment_class,
            &style_class,
        );
        let default_segment = create_textual_segment(
            py,
            [0, 0, 0, 0, 0, 0, 1],
            &color_triplet_class,
            &color_class,
            &segment_class,
            &style_class,
        );
        segment_cache.insert_with_hash(0, aseg0);
        DrawingBufferPy {
            db: DrawBuffer::new(max_row, max_col, 10.0),
            max_row,
            max_col,
            layer_count: 2,
            segment_class: segment_class.into(),
            style_class: style_class.into(),
            color_class: color_class.into(),
            color_triplet_class: color_triplet_class.into(),
            seg_cache: segment_cache,
            default_segment,
        }
    }
    pub fn layer_count(&self) -> usize {
        self.layer_count
    }

    pub fn get_row_count(&self) -> usize {
        self.db.row_count
    }
    pub fn get_col_count(&self) -> usize {
        self.db.col_count
    }
    //set the number of bit for every channel of the front color.
    pub fn set_bit_size_front(&mut self, r: u8, g: u8, b: u8) {
        self.seg_cache.set_bit_size_front(r, g, b)
    }
    // set the number of bit for every channel of the back color.
    pub fn set_bit_size_back(&mut self, r: u8, g: u8, b: u8) {
        self.seg_cache.set_bit_size_back(r, g, b)
    }

    fn hard_clear(&mut self, init_value: f32) {
        self.db.clear_depth(init_value);
        self.db.clear_pixinfo();
    }

    fn get_min_max_depth(&self, py: Python, layer: usize) -> Py<PyTuple> {
        let mima = self.db.get_min_max_depth(layer);
        mima.into_py(py)
    }

    fn set_depth_content(
        &mut self,
        py: Python,
        row: usize,
        col: usize,
        depth: f32,
        uv_py: Py<PyAny>,
        uv_1_py: Py<PyAny>,
        node_id: usize,
        geom_id: usize,
        material_id: usize,
        primitive_id: usize,
    ) {
        let uv: Vec2 = convert_glm_vec2(py, uv_py);
        let uv_1: Vec2 = convert_glm_vec2(py, uv_1_py);

        self.db.set_depth_content(
            row,
            col,
            depth,
            uv,
            uv_1,
            node_id,
            geom_id,
            material_id,
            primitive_id,
        )
    }

    fn get_pix_info_element(&self, py: Python, idx: usize) -> Py<PyDict> {
        let pix_info_element = self.db.pixbuffer[idx];
        let dict = PyDict::new_bound(py);

        let wslice = pix_info_element.uv.as_slice();
        let w_1_slice = pix_info_element.uv_1.as_slice();
        dict.set_item("uv", wslice).unwrap();
        dict.set_item("uv_1", w_1_slice).unwrap();

        dict.set_item("material_id", pix_info_element.material_id)
            .unwrap();
        dict.set_item("primitive_id", pix_info_element.primitive_id)
            .unwrap();
        dict.set_item("node_id", pix_info_element.node_id).unwrap();
        dict.set_item("geometry_id", pix_info_element.geometry_id)
            .unwrap();
        dict.into()
    }

    fn get_depth_buffer_cell(
        &self,
        py: Python,
        row: usize,
        col: usize,
        layer: usize,
    ) -> Py<PyDict> {
        let cell = self.db.get_depth_buffer_cell(row, col);
        let dict = PyDict::new_bound(py);

        let pix_info_element = self.db.pixbuffer[cell.pixinfo[layer]];

        // Assuming DepthBufferCell has some fields `field1` and `field2`
        dict.set_item("depth", cell.depth[layer]).unwrap();
        dict.set_item("pix_info", cell.pixinfo[layer]).unwrap();

        dict.set_item("uv", pix_info_element.uv.as_slice()).unwrap();
        dict.set_item("uv_1", pix_info_element.uv_1.as_slice())
            .unwrap();

        dict.set_item("material_id", pix_info_element.material_id)
            .unwrap();
        dict.set_item("primitive_id", pix_info_element.primitive_id)
            .unwrap();
        dict.set_item("node_id", pix_info_element.node_id).unwrap();
        dict.set_item("geometry_id", pix_info_element.geometry_id)
            .unwrap();
        dict.into()
    }

    fn set_canvas_cell(
        &mut self,
        row: usize,
        col: usize,
        front_color_tuple: [u8; 4],
        back_color_tuple: [u8; 4],
        glyph: u8,
    ) {
        let frontc = Color {
            r: front_color_tuple[0],
            g: front_color_tuple[1],
            b: front_color_tuple[2],
            a: front_color_tuple[3],
        };
        let backc = Color {
            r: back_color_tuple[0],
            g: back_color_tuple[1],
            b: back_color_tuple[2],
            a: back_color_tuple[3],
        };

        self.db.set_canvas_content(row, col, frontc, backc, glyph)
    }

    fn get_canvas_cell(&self, py: Python, r: usize, c: usize) -> Py<PyDict> {
        let cell = self.db.get_canvas_cell(r, c);
        let dict = PyDict::new_bound(py); // this will be super slow
        dict.set_item("f_r", cell.front_color.r).unwrap();
        dict.set_item("f_g", cell.front_color.g).unwrap();
        dict.set_item("f_b", cell.front_color.b).unwrap();

        dict.set_item("b_r", cell.back_color.r).unwrap();
        dict.set_item("b_g", cell.back_color.g).unwrap();
        dict.set_item("b_b", cell.back_color.b).unwrap();

        dict.set_item("glyph", cell.glyph).unwrap();

        dict.into()
    }

    // bound the output to a list of list of segment.
    // this is the way textual UI expect the output to be provided
    // a pixel size reduction is applied inside this function using the cache.
    // see set_bit_size_front , set_bit_size_back methods
    fn to_textual_2(
        &mut self,
        py: Python,
        min_x: usize,
        max_x: usize,
        min_y: usize,
        max_y: usize,
    ) -> Py<PyList> {
        let canvas = &self.db.canvas;
        let dict = PyDict::new_bound(py);

        // create a list of rows
        let all_rows_list = PyList::empty_bound(py);
        let append_row_method = all_rows_list.getattr(intern!(py, "append")).unwrap();
        for row_idx in min_y..max_y {
            // create a list of stuff for this current row.
            let arow_list = PyList::empty_bound(py);
            let append_method = arow_list.getattr(intern!(py, "append")).unwrap();
            if row_idx < self.max_row {
                // the row_idx is inside the screen;
                // we can iterate on the columns
                for col_idx in min_x..max_x {
                    if col_idx < self.max_col {
                        // the col_idx is withing the screen

                        // calculate a linear index
                        let idx = row_idx * self.max_col + col_idx;
                        // get the cell
                        let cell = &canvas[idx];

                        // calculate the reduced pixel values
                        let reduced_hash = self.seg_cache.get_reduced(
                            &cell.front_color,
                            &cell.back_color,
                            cell.glyph,
                        );
                        // calculate the hash
                        let hash_value = self.seg_cache.reduced_tuple_to_int(reduced_hash);

                        // find in the cache the Segment
                        match self.seg_cache.get_with_hash(hash_value) {
                            Some(value) => {
                                // we have a segment; so let insert in the current row
                                append_method.call1((&value.clone_ref(py),)).unwrap();
                            }
                            None => {
                                let (front_col, back_col, glyph) =
                                    self.seg_cache.reduced_to_triplet(reduced_hash);
                                // we don't have a segment, we should create it.
                                let f_triplet = self
                                    .color_triplet_class
                                    .call1(py, (front_col[0], front_col[1], front_col[2]))
                                    .unwrap();
                                let b_triplet = self
                                    .color_triplet_class
                                    .call1(py, (back_col[0], back_col[1], back_col[2]))
                                    .unwrap();
                                dict.set_item(
                                    intern!(py, "color"),
                                    self.color_class
                                        .call_method1(py, intern!(py, "from_triplet"), (f_triplet,))
                                        .unwrap(),
                                )
                                .unwrap();

                                dict.set_item(
                                    intern!(py, "bgcolor"),
                                    self.color_class
                                        .call_method1(py, intern!(py, "from_triplet"), (b_triplet,))
                                        .unwrap(),
                                )
                                .unwrap();

                                let theglyph = GLYPH_STATIC_STR[glyph as usize];

                                let anewseg = self
                                    .segment_class
                                    .call1(
                                        py,
                                        (
                                            theglyph,
                                            &self
                                                .style_class
                                                .call_bound(py, (), Some(&dict))
                                                .unwrap(),
                                        ),
                                    )
                                    .unwrap();

                                // store segment in the cache.
                                self.seg_cache
                                    .insert_with_hash(hash_value, anewseg.clone_ref(py));
                                // add the segment to the current line
                                append_method.call1((anewseg.clone_ref(py),)).unwrap();
                            }
                        }
                    } else {
                        // we are outbound ; we need to feed some extra segments
                        let seg = &self.default_segment;
                        append_method.call1((seg.clone_ref(py),)).unwrap();
                    }
                }
                append_row_method.call1((&arow_list,)).unwrap();
            } else {
                // we are outbound ; we need to feed extra line with the good number of columns
                // requested line count
                //let seg = self.seg_cache.get_with_hash(0).unwrap();
                let seg = &self.default_segment;
                for _col_idx in min_x..max_x {
                    append_method.call1((seg.clone_ref(py),)).unwrap();
                }
                append_row_method.call1((&arow_list,)).unwrap();
            }
        }
        all_rows_list.into()
    }

    // this version is slow; it is instanciating everything from scratch.
    // see version to_textual_2 for the "fast" version.
    fn to_textual(
        &self,
        py: Python,
        min_x: usize,
        max_x: usize,
        min_y: usize,
        max_y: usize,
    ) -> Py<PyList> {
        let canvas = &self.db.canvas;

        let mut rows = Vec::new();

        for row_idx in min_y..max_y {
            let mut row = Vec::new();
            for col_idx in min_x..max_x {
                let idx = row_idx * self.max_col + col_idx;
                let cell = canvas[idx];

                let front_triplet = self
                    .color_triplet_class
                    .call1(
                        py,
                        (cell.front_color.r, cell.front_color.g, cell.front_color.b),
                    )
                    .unwrap();
                let back_triplet = self
                    .color_triplet_class
                    .call1(
                        py,
                        (cell.back_color.r, cell.back_color.g, cell.back_color.b),
                    )
                    .unwrap();

                let front_color = self
                    .color_class
                    .call_method1(py, "from_triplet", (front_triplet,))
                    .unwrap();

                let back_color = self
                    .color_class
                    .call_method1(py, "from_triplet", (back_triplet,))
                    .unwrap();

                let dict = PyDict::new_bound(py);
                dict.set_item("color", front_color).unwrap();
                dict.set_item("bgcolor", back_color).unwrap();

                // trying to call Style(color=front_color,bgcolor=back_color)
                let style = self.style_class.call_bound(py, (), Some(&dict)).unwrap();

                let segment = self.segment_class.call1(py, ("?", style)).unwrap();

                row.push(segment);
            }
            rows.push(PyList::new_bound(py, row));
        }

        PyList::new_bound(py, rows).into()
    }
}

/// Finds the glyph index for the given character.
///
/// # Arguments
///
/// * `input` - A single character for which the glyph index is to be found.
///
/// # Returns
///
/// The glyph index as an `i8`.
#[pyfunction(text_signature = "(input)")]
pub fn find_glyph_indices_py(input: char) -> i8 {
    find_glyph_index(input)
}
