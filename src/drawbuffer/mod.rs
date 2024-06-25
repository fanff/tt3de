use pyo3::prelude::*;
pub mod drawbuffer;
use drawbuffer::*;
use pyo3::types::PyDict;
use std::borrow::BorrowMut;

#[pyclass]
pub struct Small8Drawing {
    db: DrawBuffer<2, f32>,
}

#[pymethods]
impl Small8Drawing {
    #[new]
    fn new() -> Self {
        Small8Drawing {
            db: DrawBuffer::new(
                8,
                8,
                DEPTH_BUFFER_CELL_INIT_F32_2L,
                create_pixinfo_init_f32(),
            ),
        }
    }

    fn hard_clear(&mut self, init_value: f32) {
        self.db.borrow_mut().clear_depth(init_value)
    }

    fn get_at(&self, r: usize, c: usize, l: usize) -> f32 {
        self.db.get_depth(r, c, l)
    }
}

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

    fn hard_clear(&mut self, init_value: f32) {
        (self.db.borrow_mut()).clear_depth(init_value)
    }

    fn get_at(&self, r: usize, c: usize, l: usize) -> f32 {
        self.db.get_depth(r, c, l)
    }
}

#[pyclass]
pub struct AbigDrawing {
    db: DrawBuffer<2, f32>,
    max_row: usize,
    max_col: usize,
}

#[pymethods]
impl AbigDrawing {
    #[new]
    fn new(max_row: usize, max_col: usize) -> Self {
        // assume max < Max size ?
        AbigDrawing {
            db: DrawBuffer::new(
                max_row,
                max_col,
                DEPTH_BUFFER_CELL_INIT_F32_2L,
                create_pixinfo_init_f32(),
            ),
            max_row: max_row,
            max_col: max_col,
        }
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
}

#[pyclass]
pub struct AbigDrawingWithDirtyregion {
    db: Box<[DrawBuffer<2, f32>]>, // we will allocate enough of those to fill the screen.
    dirty_map: Box<[bool]>, // this will store wich one are "dirty"; like;.. we actually draw something on it.
    max_row: usize,
    max_col: usize,
}

#[pymethods]
impl AbigDrawingWithDirtyregion {
    fn hard_clear(&mut self, init_value: f32) {
        for e in self.db.iter_mut() {
            e.clear_depth(init_value)
        }
    }
}
