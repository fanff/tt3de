use pyo3::{intern, prelude::*, types::PyList};
pub mod drawbuffer;
use drawbuffer::*;
use pyo3::types::PyDict;
use std::{borrow::BorrowMut, collections::HashMap};

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
    data: HashMap<(u8, u8, u8, u8, u8, u8, u8), Py<PyAny>>,
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
        self.bit_size_front = [r, g, b];
        self.data = HashMap::new()
    }

    fn get_hash(&self, f: Color, b: Color, glyph: u8) -> (u8, u8, u8, u8, u8, u8, u8) {
        // lets reduce the accuraccy of the color by reducing the bit count.
        let hfr = f.r >> (8 - self.bit_size_front[0]);
        let hfg = f.g >> (8 - self.bit_size_front[1]);
        let hfb = f.b >> (8 - self.bit_size_front[2]);

        let hbr = b.r >> (8 - self.bit_size_back[0]);
        let hbg = b.g >> (8 - self.bit_size_back[1]);
        let hbb = b.b >> (8 - self.bit_size_back[2]);

        // now assemblate a hash value based on this.
        (hfr, hfg, hfb, hbr, hbg, hbb, glyph)
    }
    pub fn insert(&mut self, f: Color, b: Color, glyph: u8, value: Py<PyAny>) {
        let hash = self.get_hash(f, b, glyph);
        self.data.insert(hash, value);
    }

    pub fn insert_with_hash(&mut self, hash: (u8, u8, u8, u8, u8, u8, u8), value: Py<PyAny>) {
        self.data.insert(hash, value);
    }

    pub fn get_with_hash(&self, hash: (u8, u8, u8, u8, u8, u8, u8)) -> Option<&Py<PyAny>> {
        self.data.get(&hash)
    }

    pub fn get(&self, f: Color, b: Color, glyph: u8) -> Option<&Py<PyAny>> {
        let hash = self.get_hash(f, b, glyph);
        self.data.get(&hash)
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
    db: DrawBuffer<2, f32>,
    max_row: usize,
    max_col: usize,

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

        AbigDrawing {
            db: DrawBuffer::new(
                max_row,
                max_col,
                DEPTH_BUFFER_CELL_INIT_F32_2L,
                create_pixinfo_init_f32(),
            ),
            max_row: max_row,
            max_col: max_col,
            segment_class: segment_class.into(),
            style_class: style_class.into(),
            color_class: color_class.into(),
            color_triplet_class: color_triplet_class.into(),
            seg_cache: SegmentCache::new([3, 3, 3], [3, 3, 3]),
        }
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

    fn get_at(&self, r: usize, c: usize, l: usize) -> f32 {
        self.db.get_depth(r, c, l)
    }

    fn get_depth_buffer_cell(&self, py: Python, r: usize, c: usize, l: usize) -> Py<PyDict> {
        let cell = self.db.get_depth_buffer_cell(r, c);
        let dict = PyDict::new_bound(py);

        let sdsd = self.db.pixbuffer[cell.pixinfo[l]];

        // Assuming DepthBufferCell has some fields `field1` and `field2`
        dict.set_item("depth", cell.depth[l]).unwrap();
        //sdsd.w: TVec3<T>,
        //sdsd.w_1: TVec3<T>,

        dict.set_item("material_id", sdsd.material_id).unwrap();
        dict.set_item("primitive_id", sdsd.primitive_id).unwrap();
        dict.set_item("node_id", sdsd.node_id).unwrap();
        dict.set_item("geometry_id", sdsd.geometry_id).unwrap();
        dict.into()
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

                        let the_hashval = self.seg_cache.get_hash(
                            cell.front_color,
                            cell.back_color,
                            cell.glyph as u8,
                        );

                        match self.seg_cache.get_with_hash(the_hashval) {
                            Some(value) => {
                                append_method.call1((&value.clone_ref(py),)).unwrap();
                            }
                            None => {
                                let f_triplet = self
                                    .color_triplet_class
                                    .call1(
                                        py,
                                        (
                                            cell.front_color.r,
                                            cell.front_color.g,
                                            cell.front_color.b,
                                        ),
                                    )
                                    .unwrap();
                                let b_triplet = self
                                    .color_triplet_class
                                    .call1(
                                        py,
                                        (cell.back_color.r, cell.back_color.g, cell.back_color.b),
                                    )
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

                                let anewseg = self
                                    .segment_class
                                    .call1(
                                        py,
                                        (
                                            "?",
                                            &self
                                                .style_class
                                                .call_bound(py, (), Some(&dict))
                                                .unwrap(),
                                        ),
                                    )
                                    .unwrap();
                                self.seg_cache
                                    .insert_with_hash(the_hashval, anewseg.clone_ref(py));

                                append_method.call1((anewseg.clone_ref(py),)).unwrap();
                            }
                        }
                    } else {
                        // we are outbound ; we need to feed some extra segments
                        // requested line count
                        let seg = self.seg_cache.get_with_hash((0, 0, 0, 0, 0, 0, 0)).unwrap();
                        append_method.call1((seg.clone_ref(py),)).unwrap();
                    }
                }
                append_row_method.call1((&arow_list,)).unwrap();
            } else {
                // we are outbound ; we need to feed some extra lines
                // requested line count
                let seg = self.seg_cache.get_with_hash((0, 0, 0, 0, 0, 0, 0)).unwrap();

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

fn get_color_cache_index(r: u8, g: u8, b: u8) -> usize {
    ((r / 4) as usize) * 64 * 64 + ((g / 4) as usize) * 64 + ((b / 4) as usize)
}

// Function to retrieve the color triplet from the buffer
fn get_color_triplet(color_buffer: &Vec<Py<PyAny>>, r: u8, g: u8, b: u8) -> &Py<PyAny> {
    let index = get_color_cache_index(r, g, b);
    &color_buffer[index]
}
