use nalgebra::geometry;
use nalgebra::ArrayStorage;
use nalgebra::Matrix;
use nalgebra_glm::vec3;
use nalgebra_glm::Scalar;
use nalgebra_glm::TVec3;
use pyo3::prelude::*;
use std::borrow::BorrowMut;

use pyo3::prelude::*;

//pixel info can have variable accuracy ?
#[derive(Clone, Copy)]
struct PixInfo<T: nalgebra_glm::Scalar> {
    w: TVec3<T>,
    w_1: TVec3<T>,

    material_id: usize,
    primive_id: usize,
    node_id: usize,
    geometry_id: usize,
}

impl<T: nalgebra_glm::Scalar> PixInfo<T> {
    fn clear(&mut self) {
        self.material_id = 0;
        self.primive_id = 0;
        self.node_id = 0;
        self.geometry_id = 0;
    }
}

struct PixelBuffer<A: Scalar, const N: usize> {
    pix: [PixInfo<A>; N],
}

// A is the "accuracy of the detph buffer, expect a f32 here"
// could be a u8 for simple rendering engine; with flat 2D and layers
// L is the layer count ; more layer means more potential material stacking effects
#[derive(Clone, Copy)]
struct DepthBufferCell<A: Scalar, const L: usize> {
    pixinfo: [usize; L], // referencing pixel info per index
    depth: [A; L],
}

// alternativelly, an array of tuple
//content: [(usize, A); L],
impl<D: Scalar, const L: usize> DepthBufferCell<D, L> {
    #[inline(always)]
    fn clear(&mut self, value: D) {
        for (d, p) in self.depth.iter_mut().zip(self.pixinfo.iter_mut()) {
            *d = value;
            *p = 0;
        }
    }
}

#[derive(Clone, Copy)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
    a: u8,
}

#[derive(Clone, Copy)]
struct CanvasCell {
    front_color: Color,
    back_color: Color,
    glyph: u32,
}

struct DrawBuffer<const R: usize, const C: usize, const L: usize, A: Scalar> {
    /// seems like this should be done that way ? R rows, C column , L depth layer, A ccurcy
    depthbuffer: [[DepthBufferCell<A, L>; C]; R],
    canvas: [[CanvasCell; C]; R], // column/row,
}

impl<const R: usize, const C: usize, const L: usize, A: Scalar> DrawBuffer<R, C, L, A> {
    #[inline(always)] // should this help ?!
    fn clear(&mut self, value: A) {
        for row in self.depthbuffer.iter_mut() {
            for depth_cell in row.iter_mut() {
                depth_cell.clear(value);
            }
        }
    }

    fn get_depth(&self, r: usize, c: usize, l: usize) -> A {
        let x = self.depthbuffer[r][c];
        let d = x.depth[l];
        d
    }
}

#[pyclass]
pub struct Small8Drawing {
    db: DrawBuffer<8, 8, 2, f32>,
    pixel_buffer: PixelBuffer<f32, 128>,
}

#[pymethods]
impl Small8Drawing {
    #[new]
    fn new() -> Self {
        const R: usize = 8;
        const C: usize = 8;
        const L: usize = 2;

        let initial_depth_cell: DepthBufferCell<f32, L> = DepthBufferCell {
            pixinfo: [0; L],
            depth: [1.0; L],
        };

        let initial_canvas_cell = CanvasCell {
            back_color: Color {
                r: 0,
                g: 0,
                b: 0,
                a: 0,
            },
            front_color: Color {
                r: 0,
                g: 0,
                b: 0,
                a: 0,
            },
            glyph: 0,
        };

        let depthbuffer = [[initial_depth_cell; C]; R];
        let canvas = [[initial_canvas_cell; C]; R];

        let draw_buffer = DrawBuffer {
            depthbuffer,
            canvas,
        };

        let initial_pix_info: PixInfo<f32> = PixInfo {
            w: vec3(0.0, 0.0, 0.0),
            w_1: vec3(0.0, 0.0, 0.0),

            material_id: 0,
            primive_id: 0,
            node_id: 0,
            geometry_id: 0,
        };

        let pixel_buffer = PixelBuffer {
            pix: [initial_pix_info; R * C * L],
        };

        Small8Drawing {
            db: draw_buffer,
            pixel_buffer,
        }
    }

    fn hard_clear(&mut self, init_value: f32) {
        let x = self.db.borrow_mut();
        x.clear(init_value)
    }

    fn get_at(&self, r: usize, c: usize, l: usize) -> f32 {
        let d = self.db.get_depth(r, c, l);
        return d;
    }
}
