use nalgebra_glm::{Vec2, Vec3};
use pyo3::{
    exceptions::PyValueError,
    intern,
    prelude::*,
    types::{PyList, PyTuple},
};
use rayon::ThreadPool;
use std::sync::Arc;
pub mod drawbuffer;
use drawbuffer::*;
use pyo3::types::PyDict;
pub mod glyphset;
use glyphset::*;
pub mod segment_cache;
use crate::utils::{convert_glm_vec2, convert_glm_vec3};
use segment_cache::*;

#[pyclass]
pub struct DrawingBufferPy {
    pub db: DrawBuffer<2, f32>,
    max_row: usize,
    max_col: usize,
    layer_count: usize,

    /// When `Some(n)`, parallel material shading uses `n` Rayon threads; `None` means serial-only.
    #[pyo3(get)]
    pub material_parallel_threads: Option<usize>,
    pub(crate) material_pool: Option<Arc<ThreadPool>>,

    segment_class: Py<PyAny>,
    style_class: Py<PyAny>,
    color_class: Py<PyAny>,
    color_triplet_class: Py<PyAny>,

    seg_cache: SegmentCache,

    pub default_segment: Py<PyAny>,
}

fn build_material_thread_pool(num_threads: usize) -> Arc<ThreadPool> {
    Arc::new(
        rayon::ThreadPoolBuilder::new()
            .num_threads(num_threads)
            .build()
            .expect("Failed to build material thread pool"),
    )
}

/// Interprets optional kwarg from Python: omitted → 8 threads; explicit `None` → serial;
/// `0` → serial; `n >= 1` → pool with `n` threads.
fn material_parallelism_from_py(spec: Option<Option<usize>>) -> (Option<usize>, Option<Arc<ThreadPool>>) {
    match spec {
        None => {
            let n = 8;
            (Some(n), Some(build_material_thread_pool(n)))
        }
        Some(None) => (None, None),
        Some(Some(0)) => (None, None),
        Some(Some(n)) => (Some(n), Some(build_material_thread_pool(n))),
    }
}

#[pymethods]
impl DrawingBufferPy {
    #[new]
    #[pyo3(signature = (max_row, max_col, flip_x=false, flip_y=true, material_parallel_threads=-1))]
    fn new(
        py: Python<'_>,
        max_row: usize,
        max_col: usize,
        flip_x: bool,
        flip_y: bool,
        material_parallel_threads: i64,
    ) -> PyResult<Self> {
        let spec = match material_parallel_threads {
            -1 => None,
            0 => Some(None),
            n if n > 0 => Some(Some(n as usize)),
            _ => {
                return Err(PyValueError::new_err(
                    "material_parallel_threads must be -1 (default 8 threads), 0 (serial), or a positive count",
                ));
            }
        };
        let rich_style_module = py.import("rich.style").unwrap();
        let rich_color_module = py.import("rich.color").unwrap();
        let rich_text_module = py.import("rich.text").unwrap();
        let rich_color_triplet_module = py.import("rich.color_triplet").unwrap();

        let segment_class = rich_text_module.getattr("Segment").unwrap();
        let style_class = rich_style_module.getattr("Style").unwrap();
        let color_class = rich_color_module.getattr("Color").unwrap();
        let color_triplet_class = rich_color_triplet_module.getattr("ColorTriplet").unwrap();

        let segment_cache = SegmentCache::new_iso(4);
        let default_segment = create_textual_segment(
            py,
            [0, 0, 0, 0, 0, 0, 1],
            &color_triplet_class,
            &color_class,
            &segment_class,
            &style_class,
        );
        let (material_parallel_threads, material_pool) = material_parallelism_from_py(spec);
        Ok(DrawingBufferPy {
            db: DrawBuffer::new(max_row, max_col, 10.0, flip_x, flip_y),
            max_row,
            max_col,
            layer_count: 2,
            material_parallel_threads,
            material_pool,
            segment_class: segment_class.into(),
            style_class: style_class.into(),
            color_class: color_class.into(),
            color_triplet_class: color_triplet_class.into(),
            seg_cache: segment_cache,
            default_segment,
        })
    }

    pub fn get_cache_size(&self) -> usize {
        self.seg_cache.get_cache_size()
    }
    pub fn layer_count(&self) -> usize {
        self.layer_count
    }
    pub fn get_flip_x(&self) -> bool {
        self.db.flip_x
    }
    pub fn set_flip_x(&mut self, v: bool) {
        self.db.set_flip_x(v);
    }
    pub fn get_flip_y(&self) -> bool {
        self.db.flip_y
    }

    pub fn set_flip_y(&mut self, v: bool) {
        self.db.set_flip_y(v);
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
        let tt = PyTuple::new(py, [mima.0, mima.1]).unwrap();
        tt.into()
    }

    #[pyo3(signature = (row, col, normal_py, depth, uv_py, uv_1_py, node_id, geom_id, material_id, primitive_id, front_facing=true, line_coord=0.0, point_coord=None))]
    fn set_depth_content(
        &mut self,
        py: Python,
        row: usize,
        col: usize,
        normal_py: Py<PyAny>,
        depth: f32,
        uv_py: Py<PyAny>,
        uv_1_py: Py<PyAny>,
        node_id: usize,
        geom_id: usize,
        material_id: usize,
        primitive_id: usize,
        front_facing: bool,
        line_coord: f32,
        point_coord: Option<Py<PyAny>>,
    ) {
        let uv: Vec2 = convert_glm_vec2(py, uv_py);
        let uv_1: Vec2 = convert_glm_vec2(py, uv_1_py);

        let normal: Vec3 = convert_glm_vec3(py, normal_py);
        let point_coord_v = point_coord
            .map(|p| convert_glm_vec2(py, p))
            .unwrap_or_else(Vec2::zeros);

        self.db.set_depth_content(
            row,
            col,
            depth,
            normal,
            uv,
            uv_1,
            node_id,
            geom_id,
            material_id,
            primitive_id,
            front_facing,
            line_coord,
            point_coord_v,
        )
    }

    fn get_pix_info_element(&self, py: Python, idx: usize) -> Py<PyDict> {
        let pix_info_element = self.db.pixbuffer[idx];
        let dict = PyDict::new(py);

        let wslice = pix_info_element.uv.as_slice();
        let w_1_slice = pix_info_element.uv_1.as_slice();
        dict.set_item("uv", wslice).unwrap();
        dict.set_item("uv_1", w_1_slice).unwrap();
        dict.set_item("frag_pos", pix_info_element.frag_pos.as_slice())
            .unwrap();
        dict.set_item("normal", pix_info_element.normal.as_slice())
            .unwrap();

        dict.set_item("material_id", pix_info_element.material_id)
            .unwrap();
        dict.set_item("primitive_id", pix_info_element.primitive_id)
            .unwrap();
        dict.set_item("node_id", pix_info_element.node_id).unwrap();
        dict.set_item("geometry_id", pix_info_element.geometry_id)
            .unwrap();
        dict.set_item("front_facing", pix_info_element.front_facing)
            .unwrap();
        dict.set_item("line_coord", pix_info_element.line_coord)
            .unwrap();
        dict.set_item("point_coord", pix_info_element.point_coord.as_slice())
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
        let dict = PyDict::new(py);

        let pix_info_element = self.db.pixbuffer[cell.pixinfo[layer]];

        // Assuming DepthBufferCell has some fields `field1` and `field2`
        dict.set_item("depth", cell.depth[layer]).unwrap();
        dict.set_item("pix_info", cell.pixinfo[layer]).unwrap();

        dict.set_item("uv", pix_info_element.uv.as_slice()).unwrap();
        dict.set_item("uv_1", pix_info_element.uv_1.as_slice())
            .unwrap();

        dict.set_item("frag_pos", pix_info_element.frag_pos.as_slice())
            .unwrap();

        dict.set_item("material_id", pix_info_element.material_id)
            .unwrap();
        dict.set_item("primitive_id", pix_info_element.primitive_id)
            .unwrap();
        dict.set_item("node_id", pix_info_element.node_id).unwrap();
        dict.set_item("geometry_id", pix_info_element.geometry_id)
            .unwrap();
        dict.set_item("front_facing", pix_info_element.front_facing)
            .unwrap();
        dict.set_item("line_coord", pix_info_element.line_coord)
            .unwrap();
        dict.set_item("point_coord", pix_info_element.point_coord.as_slice())
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
        let dict = PyDict::new(py); // this will be super slow
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
        let dict = PyDict::new(py);

        let ncols = max_x.saturating_sub(min_x);
        let nrows = max_y.saturating_sub(min_y);
        let mut outer_rows: Vec<Py<PyAny>> = Vec::with_capacity(nrows);

        for row_idx in min_y..max_y {
            let mut row_segments: Vec<Py<PyAny>> = Vec::with_capacity(ncols);

            if row_idx < self.max_row {
                for col_idx in min_x..max_x {
                    if col_idx < self.max_col {
                        let idx = row_idx * self.max_col + col_idx;
                        let cell = &canvas[idx];

                        let reduced_hash = self.seg_cache.get_reduced(
                            &cell.front_color,
                            &cell.back_color,
                            cell.glyph,
                        );
                        let hash_value = self.seg_cache.reduced_tuple_to_int(reduced_hash);

                        match self.seg_cache.get_with_hash(hash_value) {
                            Some(value) => {
                                row_segments.push(value.clone_ref(py));
                            }
                            None => {
                                let (front_col, back_col, glyph) =
                                    self.seg_cache.reduced_to_triplet(reduced_hash);
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
                                            &self.style_class.call(py, (), Some(&dict)).unwrap(),
                                        ),
                                    )
                                    .unwrap();

                                self.seg_cache
                                    .insert_with_hash(hash_value, anewseg.clone_ref(py));
                                row_segments.push(anewseg.clone_ref(py));
                            }
                        }
                    } else {
                        row_segments.push(self.default_segment.clone_ref(py));
                    }
                }
            } else {
                row_segments.extend(
                    std::iter::repeat_with(|| self.default_segment.clone_ref(py)).take(ncols),
                );
            }

            let row_list = PyList::new(py, row_segments).unwrap();
            outer_rows.push(row_list.into_any().unbind());
        }

        PyList::new(py, outer_rows).unwrap().into()
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

#[pyfunction(text_signature = "(input)")]
pub fn get_glyph_set() -> String {
    GLYPH_STATIC_STR.join("")
}
