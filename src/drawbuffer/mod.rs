use nalgebra_glm::Vec3;
use pyo3::{
    intern,
    prelude::*,
    types::{PyList, PyTuple},
};
pub mod drawbuffer;
use drawbuffer::*;
use pyo3::types::PyDict;
use std::{borrow::BorrowMut, collections::HashMap};
pub mod glyphset;
use glyphset::*;

use crate::utils::convert_glm_vec3;

#[pyclass]
pub struct Small16Drawing {
    db: DrawBuffer<2, f32>,
}

#[pymethods]
impl Small16Drawing {
    #[new]
    fn new() -> Self {
        Small16Drawing {
            db: DrawBuffer::new(
                16,
                16,
                DEPTH_BUFFER_CELL_INIT_F32_2L,
                create_pixinfo_init_f32(),
            ),
        }
    }
    fn apply_material(&mut self) {
        self.db.apply_material()
    }
    fn hard_clear(&mut self, init_value: f32) {
        (self.db.borrow_mut()).clear_depth(init_value)
    }

    fn get_at(&self, r: usize, c: usize, l: usize) -> f32 {
        self.db.get_depth(r, c, l)
    }
}

pub struct SegmentCache {
    data: HashMap<u64, Py<PyAny>>,
    bit_size_front: [u8; 3],
    bit_size_back: [u8; 3],
}

impl SegmentCache {
    pub fn new(bit_size_front: [u8; 3], bit_size_back: [u8; 3]) -> Self {
        SegmentCache {
            data: HashMap::new(),
            bit_size_front,
            bit_size_back,
        }
    }
    pub fn set_bit_size_front(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_front = [r, g, b];
        self.data = HashMap::new()
    }

    pub fn set_bit_size_back(&mut self, r: u8, g: u8, b: u8) {
        self.bit_size_back = [r, g, b];
        self.data = HashMap::new()
    }

    fn get_reduced(&self, f: Color, b: Color, glyph: u8) -> [u8; 7] {
        // lets reduce the accuraccy of the color by reducing the bit count.
        let hfr = f.r >> (8 - self.bit_size_front[0]);
        let hfg = f.g >> (8 - self.bit_size_front[1]);
        let hfb = f.b >> (8 - self.bit_size_front[2]);

        let hbr = b.r >> (8 - self.bit_size_back[0]);
        let hbg = b.g >> (8 - self.bit_size_back[1]);
        let hbb = b.b >> (8 - self.bit_size_back[2]);

        // now assemblate a hash value based on this.
        [hfr, hfg, hfb, hbr, hbg, hbb, glyph]
    }

    pub fn insert_with_hash(&mut self, hash_value: u64, value: Py<PyAny>) {
        self.data.insert(hash_value, value);
    }

    pub fn get_with_hash(&self, hash_value: u64) -> Option<&Py<PyAny>> {
        self.data.get(&hash_value)
    }

    pub fn hash_tuple_to_int(&self, hash_tuple: [u8; 7]) -> u64 {
        let mut hash: u64 = 0;

        for i in 0..3 {
            // Retain only the highest bits as specified by bit_reductions[i]
            let reduced_num = hash_tuple[i] >> (8 - self.bit_size_front[i]);
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_front[i]) | reduced_num as u64;
        }

        for i in 0..3 {
            // Retain only the highest bits as specified by bit_reductions[i]
            let reduced_num = hash_tuple[i] >> (8 - self.bit_size_back[i]);
            // Shift the hash left by the number of bits retained and add the reduced number
            hash = (hash << self.bit_size_back[i]) | reduced_num as u64;
        }

        // Add  without any bit reduction
        hash = (hash << 8) | hash_tuple[6] as u64;

        hash
    }

    pub fn estimate_max_combinations(&self) -> u64 {
        let front_combinations = (1 << self.bit_size_front[0]) as u64
            * (1 << self.bit_size_front[1]) as u64
            * (1 << self.bit_size_front[2]) as u64;
        let back_combinations = (1 << self.bit_size_back[0]) as u64
            * (1 << self.bit_size_back[1]) as u64
            * (1 << self.bit_size_back[2]) as u64;

        front_combinations * back_combinations * 256 // 256 possible glyph values (u8)
    }
}

#[pyclass]
pub struct AbigDrawing {
    pub db: DrawBuffer<2, f32>,
    max_row: usize,
    max_col: usize,
    layer_count: usize,

    segment_class: Py<PyAny>,
    style_class: Py<PyAny>,
    color_class: Py<PyAny>,
    color_triplet_class: Py<PyAny>,

    seg_cache: SegmentCache,
}

#[pymethods]
impl AbigDrawing {
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
        let mut segment_cache = SegmentCache::new([3, 3, 3], [3, 3, 3]);
        let aseg0 = create_textual_segment(
            py,
            [0, 0, 0, 0, 0, 0, 0],
            &color_triplet_class,
            &color_class,
            &segment_class,
            &style_class,
        );

        segment_cache.insert_with_hash(0, aseg0);
        AbigDrawing {
            db: DrawBuffer::new(
                max_row,
                max_col,
                DEPTH_BUFFER_CELL_INIT_F32_2L,
                create_pixinfo_init_f32(),
            ),
            max_row: max_row,
            max_col: max_col,
            layer_count: 2,
            segment_class: segment_class.into(),
            style_class: style_class.into(),
            color_class: color_class.into(),
            color_triplet_class: color_triplet_class.into(),
            seg_cache: segment_cache,
        }
    }
    pub fn layer_count(&self) -> usize {
        return self.layer_count;
    }
    //set the number of bit for every channel of the front color.
    pub fn set_bit_size_front(&mut self, r: u8, g: u8, b: u8) {
        self.seg_cache.set_bit_size_front(r, g, b)
    }
    // set the number of bit for every channel of the back color.
    pub fn set_bit_size_back(&mut self, r: u8, g: u8, b: u8) {
        self.seg_cache.set_bit_size_back(r, g, b)
    }

    fn apply_material(&mut self) {
        self.db.apply_material()
    }
    fn hard_clear(&mut self, init_value: f32) {
        (self.db.borrow_mut()).clear_depth(init_value)
    }

    fn get_depth_buff_content(&self, r: usize, c: usize, layer: usize) -> f32 {
        self.db.get_depth(r, c, layer)
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
        weight: Py<PyAny>,
        weight_2: Py<PyAny>,
        node_id: usize,
        geom_id: usize,
        material_id: usize,
        primitive_id: usize,
    ) {
        let w: Vec3 = convert_glm_vec3(py, weight);
        let w_alt: Vec3 = convert_glm_vec3(py, weight_2);

        self.db.set_depth_content(
            row,
            col,
            depth,
            w,
            w_alt,
            node_id,
            geom_id,
            material_id,
            primitive_id,
        )
    }

    fn get_pix_info_element(&self, py: Python, idx: usize) -> Py<PyDict> {
        let pix_info_element = self.db.pixbuffer[idx];
        let dict = PyDict::new_bound(py);

        let wslice = pix_info_element.w.as_slice();
        let w_1_slice = pix_info_element.w_1.as_slice();
        dict.set_item("w", wslice).unwrap();
        dict.set_item("w_1", w_1_slice).unwrap();

        dict.set_item("material_id", pix_info_element.material_id)
            .unwrap();
        dict.set_item("primitive_id", pix_info_element.primitive_id)
            .unwrap();
        dict.set_item("node_id", pix_info_element.node_id).unwrap();
        dict.set_item("geometry_id", pix_info_element.geometry_id)
            .unwrap();
        dict.into()
    }

    fn get_depth_buffer_cell(&self, py: Python, r: usize, c: usize, layer: usize) -> Py<PyDict> {
        let cell = self.db.get_depth_buffer_cell(r, c);
        let dict = PyDict::new_bound(py);

        let pix_info_element = self.db.pixbuffer[cell.pixinfo[layer]];

        // Assuming DepthBufferCell has some fields `field1` and `field2`
        dict.set_item("depth", cell.depth[layer]).unwrap();
        dict.set_item("pix_info", cell.pixinfo[layer]).unwrap();

        let wslice = pix_info_element.w.as_slice();
        let w_1_slice = pix_info_element.w_1.as_slice();
        dict.set_item("w", wslice).unwrap();
        dict.set_item("w_1", w_1_slice).unwrap();

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
        r: usize,
        c: usize,
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

        self.db.set_canvas_content(r, c, frontc, backc, glyph)
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

        let all_rows_list = PyList::empty_bound(py);
        let append_row_method = all_rows_list.getattr(intern!(py, "append")).unwrap();
        for row_idx in min_y..max_y {
            let arow_list = PyList::empty_bound(py);
            let append_method = arow_list.getattr(intern!(py, "append")).unwrap();
            if row_idx < self.max_row {
                for col_idx in min_x..max_x {
                    if col_idx < self.max_col {
                        let idx = row_idx * self.max_col + col_idx;
                        let cell = canvas[idx];

                        let reduced_hash = self.seg_cache.get_reduced(
                            cell.front_color,
                            cell.back_color,
                            cell.glyph as u8,
                        );
                        let hash_value = self.seg_cache.hash_tuple_to_int(reduced_hash);

                        match self.seg_cache.get_with_hash(hash_value) {
                            Some(value) => {
                                append_method.call1((&value.clone_ref(py),)).unwrap();
                            }
                            None => {
                                let f_triplet = self
                                    .color_triplet_class
                                    .call1(py, (reduced_hash[0], reduced_hash[1], reduced_hash[2]))
                                    .unwrap();
                                let b_triplet = self
                                    .color_triplet_class
                                    .call1(py, (reduced_hash[3], reduced_hash[4], reduced_hash[5]))
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

                                let theglyph = GLYPH_STATIC_STR[reduced_hash[6] as usize];

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
                                self.seg_cache
                                    .insert_with_hash(hash_value, anewseg.clone_ref(py));

                                append_method.call1((anewseg.clone_ref(py),)).unwrap();
                            }
                        }
                    } else {
                        // we are outbound ; we need to feed some extra segments
                        let seg = self.seg_cache.get_with_hash(0).unwrap();
                        append_method.call1((seg.clone_ref(py),)).unwrap();
                    }
                }
                append_row_method.call1((&arow_list,)).unwrap();
            } else {
                // we are outbound ; we need to feed extra line with the good number of columns
                // requested line count
                let seg = self.seg_cache.get_with_hash(0).unwrap();

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
fn create_textual_segment(
    py: Python,
    reduced_hash: [u8; 7],
    color_triplet_class: &Bound<PyAny>,
    color_class: &Bound<PyAny>,
    segment_class: &Bound<PyAny>,
    style_class: &Bound<PyAny>,
) -> Py<PyAny> {
    let dict = PyDict::new_bound(py);
    let f_triplet = color_triplet_class
        .call1((reduced_hash[0], reduced_hash[1], reduced_hash[2]))
        .unwrap();
    let b_triplet = color_triplet_class
        .call1((reduced_hash[3], reduced_hash[4], reduced_hash[5]))
        .unwrap();
    dict.set_item(
        intern!(py, "color"),
        color_class
            .call_method1(intern!(py, "from_triplet"), (f_triplet,))
            .unwrap(),
    )
    .unwrap();

    dict.set_item(
        intern!(py, "bgcolor"),
        color_class
            .call_method1(intern!(py, "from_triplet"), (b_triplet,))
            .unwrap(),
    )
    .unwrap();
    let theglyph = GLYPH_STATIC_STR[reduced_hash[6] as usize];
    let anewseg = segment_class
        .call1((theglyph, &style_class.call((), Some(&dict)).unwrap()))
        .unwrap();
    anewseg.into()
}
