use std::borrow::BorrowMut;

use nalgebra::Dyn;
use nalgebra::VecStorage;
use nalgebra_glm::clamp_vec;
use nalgebra_glm::floor;
use nalgebra_glm::max;
use nalgebra_glm::round;
use nalgebra_glm::vec2;
use nalgebra_glm::Number;
use nalgebra_glm::TVec2;
use nalgebra_glm::Vec2;
use nalgebra_glm::Vec3;
use nalgebra_glm::Vec4;

use super::super::texturebuffer::texture_buffer::TextureBuffer;
use crate::material::apply_material;
use crate::material::MaterialBuffer;
use crate::primitivbuffer::primitivbuffer::PrimitiveBuffer;
use crate::texturebuffer::RGBA;
use crate::vertexbuffer::uv_buffer::UVBuffer;

/// Represents information about a pixel with variable accuracy.
///
/// # Type Parameters
///
/// - `T`: A scalar type that implements the `nalgebra_glm::Scalar` trait. This allows the vectors to have variable precision.
///
/// # Fields
///
/// - `uv`: A 2D vector representing the primary texture coordinates of the pixel.
/// - `uv_1`: A 2D vector representing secondary texture coordinates of the pixel
/// - `material_id`: An identifier for the material, typically used to reference a material in a materials database or array.
/// - `primitive_id`: An identifier for the primitive (e.g., a geometric primitive like a triangle or sphere).
/// - `node_id`: An identifier for the node, possibly in a scene graph or spatial partitioning structure.
/// - `geometry_id`: An identifier for the geometry, which could refer to a specific geometric object or model.
#[derive(Clone, Copy, Debug)]
pub struct PixInfo<InfoAccuracy: nalgebra_glm::Number> {
    pub uv: TVec2<InfoAccuracy>,
    pub uv_1: TVec2<InfoAccuracy>,
    pub normal: Vec3,
    pub material_id: usize,
    pub primitive_id: usize,
    pub node_id: usize,
    pub geometry_id: usize,
}

impl<T: nalgebra_glm::Number> Default for PixInfo<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: nalgebra_glm::Number> PixInfo<T> {
    pub fn new() -> Self {
        PixInfo {
            uv: TVec2::zeros(),
            uv_1: TVec2::zeros(),
            normal: Vec3::new(0.0, 0.0, 1.0),
            material_id: 0,
            primitive_id: 0,
            node_id: 0,
            geometry_id: 0,
        }
    }
    fn clear(&mut self) {
        self.material_id = 0;
        self.primitive_id = 0;
        self.node_id = 0;
        self.geometry_id = 0;
    }
    pub fn set_uv(&mut self, uv: TVec2<T>) {
        self.uv = uv;
    }
    pub fn set_uv_1(&mut self, uv: TVec2<T>) {
        self.uv_1 = uv;
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

impl Color {
    pub fn new(r: u8, g: u8, b: u8, a: u8) -> Self {
        Color { r, g, b, a }
    }

    pub fn new_opaque_from_vec3(color_vec: &Vec3) -> Self {
        let w = max(&floor(&(color_vec * 256.0)), 0.0);
        Color::new(w.x as u8, w.y as u8, w.z as u8, 255)
    }

    pub fn new_opaque_from_vec2(color_vec: &Vec2) -> Self {
        let w = max(&floor(&(color_vec * 256.0)), 0.0);
        Color::new(w.x as u8, w.y as u8, 0, 255)
    }

    pub fn copy_from(&mut self, rgba: &RGBA) {
        self.r = rgba.r;
        self.g = rgba.g;
        self.b = rgba.b;
        self.a = rgba.a;
    }
}

#[cfg(test)]
mod test_drawbuffer_color {
    use super::*;
    #[test]
    pub fn test_new_color() {
        let color = Color::new(255, 0, 0, 255);
        assert_eq!(color.r, 255);
        assert_eq!(color.g, 0);
        assert_eq!(color.b, 0);
        assert_eq!(color.a, 255);
    }
    #[test]
    pub fn test_new_opaque_from_vec3() {
        let color = Color::new_opaque_from_vec3(&Vec3::new(1.0, 0.0, 0.0));
        assert_eq!(color.r, 255);
        assert_eq!(color.g, 0);
        assert_eq!(color.b, 0);
        assert_eq!(color.a, 255);
    }
    #[test]
    pub fn test_copy_from() {
        let mut color: Color = Color::new(0, 0, 0, 0);
        color.copy_from(&RGBA::new(255, 0, 0, 255));
        assert_eq!(color.r, 255);
        assert_eq!(color.g, 0);
        assert_eq!(color.b, 0);
        assert_eq!(color.a, 255);
    }
}

#[derive(Clone, Copy)]
pub struct CanvasCell {
    pub front_color: Color,
    pub back_color: Color,
    pub glyph: u8,
}

impl CanvasCell {
    pub fn new(front_color: Color, back_color: Color, glyph: u8) -> Self {
        Self {
            front_color,
            back_color,
            glyph,
        }
    }
    pub fn default() -> Self {
        Self {
            front_color: Color::new(0, 0, 0, 0),
            back_color: Color::new(0, 0, 0, 0),
            glyph: 0,
        }
    }
    pub fn set_front(&mut self, color: Color) {
        self.front_color = color;
    }
    pub fn set_back(&mut self, color: Color) {
        self.back_color = color;
    }
    pub fn set_glyph(&mut self, glyph: u8) {
        self.glyph = glyph;
    }
}

#[derive(Clone, Copy)]
pub struct DepthBufferCell<A: Number, const L: usize> {
    pub pixinfo: [usize; L], // referencing pixel info per index
    pub depth: [A; L],
}
impl<DepthAccuracy: Number, const DEPTHLAYERCOUNT: usize> Default
    for DepthBufferCell<DepthAccuracy, DEPTHLAYERCOUNT>
{
    fn default() -> Self {
        Self::new()
    }
}

impl<DepthAccuracy: Number, const DEPTHLAYERCOUNT: usize>
    DepthBufferCell<DepthAccuracy, DEPTHLAYERCOUNT>
{
    pub fn new() -> Self {
        DepthBufferCell {
            pixinfo: [0; DEPTHLAYERCOUNT],
            depth: [DepthAccuracy::zero(); DEPTHLAYERCOUNT],
        }
    }

    pub fn get_depth(&self, layer: usize) -> DepthAccuracy {
        self.depth[layer]
    }

    fn new_set(value: DepthAccuracy) -> Self {
        DepthBufferCell {
            pixinfo: [0; DEPTHLAYERCOUNT],
            depth: [value; DEPTHLAYERCOUNT],
        }
    }
    fn clear(&mut self, value: DepthAccuracy, idx: usize) {
        for (layeridx, (d, p)) in self
            .depth
            .iter_mut()
            .zip(self.pixinfo.iter_mut())
            .enumerate()
        {
            *d = value;
            *p = idx + layeridx;
        }
    }

    fn set_init_pix_ref(&mut self, idx: usize) {
        for layer in 0..DEPTHLAYERCOUNT {
            let lol = &mut (self.pixinfo[layer]);
            *(lol) = idx + layer
        }
    }
}

pub const CANVAS_CELL_INIT: CanvasCell = CanvasCell {
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
/// Stores the depth buffer, canvas, and pixel information for a drawing buffer.
/// Template parameters are used to specify the number of depth layers and the accuracy of the depth buffer.
pub struct DrawBuffer<const DEPTH_LAYER_COUNT: usize, DepthBufferAccuracy: Number> {
    pub depthbuffer: Box<[DepthBufferCell<DepthBufferAccuracy, DEPTH_LAYER_COUNT>]>,
    pub canvas: Box<[CanvasCell]>,
    pub pixbuffer: Box<[PixInfo<f32>]>,
    pub row_count: usize,
    pub col_count: usize,
    pub half_size: Vec2,
    pub flip_x: bool,
    pub flip_y: bool,
    scale: Vec2,
}
fn flip_to_vec(flip_x: bool, flip_y: bool) -> Vec2 {
    let x = if flip_x { -1.0 } else { 1.0 };
    let y = if flip_y { -1.0 } else { 1.0 };
    vec2(x, y)
}

// here theL ( layer) are like.. bounded; A is accuracy of the depth buffer (f32 usually)
impl<const L: usize, DEPTHACC: Number> DrawBuffer<L, DEPTHACC> {
    pub fn new(
        row_count: usize,
        col_count: usize,
        default_depth: DEPTHACC,
        flip_x: bool,
        flip_y: bool,
    ) -> Self {
        // this store the depth for every cell, for every "layer" + and index
        let mut depthbuffer =
            vec![DepthBufferCell::new_set(default_depth); row_count * col_count].into_boxed_slice();

        // this store specific propertiees in RxCxL. The index inside the depth buffer is actually pointing into this
        // array.
        // reason is that we will often do "compare and move/swap"; by using the index I guess the swap is just "swaping u8, instead of swapping the whole struc";

        let inipix: PixInfo<f32> = PixInfo::new();
        let pixbuffer = vec![inipix; row_count * col_count * L].into_boxed_slice();

        // we init the depth buffer with the pixel info.
        // each cell has L layers of depth,
        // and the info of the layers are within "pixbuffer"
        // the pix
        for row in 0..row_count {
            for col in 0..col_count {
                let idx = row * col_count + col;

                depthbuffer[idx].set_init_pix_ref(idx * L);
            }
        }

        // this stores the actually pixel "color pair + glyph"
        let canvas = vec![CANVAS_CELL_INIT; row_count * col_count].into_boxed_slice();

        DrawBuffer {
            depthbuffer,
            canvas,
            pixbuffer,
            col_count,
            row_count,
            half_size: Vec2::new(col_count as f32 / 2.0, row_count as f32 / 2.0),
            flip_x: flip_x,
            flip_y: flip_y,
            scale: flip_to_vec(flip_x, flip_y),
        }
    }
    pub fn set_flip_x(&mut self, v: bool) {
        self.flip_x = v;
        self.scale = flip_to_vec(self.flip_x, self.flip_y);
    }
    pub fn set_flip_y(&mut self, v: bool) {
        self.flip_y = v;
        self.scale = flip_to_vec(self.flip_x, self.flip_y);
    }
    pub fn clear_depth(&mut self, value: DEPTHACC) {
        for (idx, depth_cell) in self.depthbuffer.iter_mut().enumerate() {
            depth_cell.clear(value, idx * L);
        }
    }
    pub fn clear_pixinfo(&mut self) {
        for pixinfo in self.pixbuffer.iter_mut() {
            pixinfo.clear();
        }
    }

    /// Converts a normalized device coordinate (NDC) to a screen coordinate. (col, row)
    /// This does NOT apply clamping to the screen boundaries.
    pub fn ndc_to_screen_floating(&self, v: &Vec2) -> Vec2 {
        let mut sumoftwovec: Vec2 = v.component_mul(&self.scale) + vec2(1.0, 1.0);
        // vectorial summ and multiplication; component wise
        sumoftwovec.component_mul_assign(&self.half_size);
        sumoftwovec
    }
    /// Converts a normalized device coordinate (NDC) to a screen coordinate. (col, row)
    /// This does apply clamping to the screen boundaries.
    pub fn ndc_to_screen_floating_with_clamp(&self, v: &Vec2) -> Vec2 {
        let as_screen = self.ndc_to_screen_floating(v);

        clamp_vec(
            &round(&as_screen),
            &Vec2::zeros(),
            &vec2(self.col_count as f32 - 1.0, self.row_count as f32 - 1.0),
        )
    }

    pub fn get_depth(&self, r: usize, c: usize, l: usize) -> DEPTHACC {
        let x = self.depthbuffer[r * self.col_count + c];

        x.depth[l]
    }

    pub fn get_depth_buffer_cell(&self, row: usize, col: usize) -> DepthBufferCell<DEPTHACC, L> {
        self.depthbuffer[row * self.col_count + col]
    }

    pub fn get_pix_buffer_content_at_row_col(
        &self,
        row: usize,
        col: usize,
        layer_idx: usize,
    ) -> &PixInfo<f32> {
        let depth_buffer_cell = self.depthbuffer[row * self.col_count + col];

        (&self.pixbuffer[depth_buffer_cell.pixinfo[layer_idx]]) as _
    }
    pub fn get_canvas_cell(&self, row: usize, col: usize) -> CanvasCell {
        self.canvas[row * self.col_count + col]
    }

    pub fn get_min_max_depth(&self, layer: usize) -> (DEPTHACC, DEPTHACC) {
        let mut min_value: DEPTHACC = DEPTHACC::max_value();
        let mut max_value: DEPTHACC = DEPTHACC::min_value();

        for depth_cell in self.depthbuffer.iter() {
            let content = depth_cell.depth[layer];

            if content < min_value {
                min_value = content;
            }
            if content > max_value {
                max_value = content;
            }
        }

        (min_value, max_value)
    }

    pub fn set_canvas_content(
        &mut self,
        r: usize,
        c: usize,
        front_color: Color,
        back_color: Color,
        glyph: u8,
    ) {
        let idx = r * self.col_count + c;
        let stuff = &mut self.canvas[idx];
        stuff.front_color = front_color;
        stuff.back_color = back_color;
        stuff.glyph = glyph;
    }

    /// The set_depth_content function is responsible for setting a new depth value into a
    /// layered depth buffer while ensuring that the existing values are correctly shifted to
    /// maintain the order.
    /// This function updates both the depth buffer and the associated pixel information.
    pub fn set_depth_content(
        &mut self,
        row: usize,
        col: usize,
        depth: DEPTHACC,
        normal: Vec3,
        uv: Vec2,
        uv_1: Vec2,
        node_id: usize,
        geom_id: usize,
        material_id: usize,
        primitive_id: usize,
    ) {
        let the_point = row * self.col_count + col;
        let mut the_layer = 0; // starting at layer 0

        let the_cell = &mut self.depthbuffer[the_point];
        while the_layer < L {
            let _pix_info_at_layer = self.pixbuffer[the_cell.pixinfo[the_layer]];

            let depth_at_layer = the_cell.depth[the_layer];

            if depth < depth_at_layer {
                // we are closer to this level of depth. So we can locate the new
                // value here.
                // the existing value need to be pushed "down the layers";
                // Like, if we currently set layer 1;
                // then the new value of the layer 2 is the previous layer1 ; the new of 3 is 2 etc.. :
                // like a shifting operation of +1 index.
                // the last element will be "droped" ; so we keep the pixel idx of the last layer before doing anything
                if the_layer <= L {
                    let last_pix_index = the_cell.pixinfo[L - 1];
                    for moving_layer_idx in (the_layer + 1..L).rev() {
                        the_cell.pixinfo[moving_layer_idx] = the_cell.pixinfo[moving_layer_idx - 1];
                        the_cell.depth[moving_layer_idx] = the_cell.depth[moving_layer_idx - 1];
                    }

                    // now I grab the pix idx for me :)
                    the_cell.pixinfo[the_layer] = last_pix_index;

                    // and now I can set the content at the right location
                    let pix_info_dest = &mut (self.pixbuffer[last_pix_index]);
                    the_cell.depth[the_layer] = depth; // Set the depth
                    pix_info_dest.normal = normal;
                    pix_info_dest.primitive_id = primitive_id;
                    pix_info_dest.geometry_id = geom_id;
                    pix_info_dest.node_id = node_id;
                    pix_info_dest.material_id = material_id;

                    // Store the vectors
                    pix_info_dest.uv = uv;
                    pix_info_dest.uv_1 = uv_1;

                    return;
                } else {
                    // we are at the last layer. There is no way to push down anything; we just will replace.
                    the_cell.depth[the_layer] = depth; // Set the depth
                    let pix_info_dest = (self.pixbuffer[the_cell.pixinfo[the_layer]]).borrow_mut();
                    pix_info_dest.normal = normal;
                    pix_info_dest.primitive_id = primitive_id;
                    pix_info_dest.geometry_id = geom_id;
                    pix_info_dest.node_id = node_id;
                    pix_info_dest.material_id = material_id;

                    // Store the vectors
                    pix_info_dest.uv = uv;
                    pix_info_dest.uv_1 = uv_1;

                    return;
                }
            } else {
                the_layer += 1;
            }
        }
    }
}

// will apply the material for every pixel.
pub fn apply_material_on<const TEXTURESIZE: usize, const DEPTHLAYER: usize>(
    draw_buffer: &mut DrawBuffer<DEPTHLAYER, f32>,
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<TEXTURESIZE>,
    uv_buffer: &UVBuffer<f32>,
    primitive_buffer: &PrimitiveBuffer,
) {
    for (depth_cell, canvascell) in draw_buffer
        .depthbuffer
        .iter()
        .zip(draw_buffer.canvas.iter_mut())
    {
        for depth_layer in (0..DEPTHLAYER).rev() {
            let pixinfo = draw_buffer.pixbuffer[depth_cell.pixinfo[depth_layer]];

            apply_material(
                pixinfo,
                material_buffer,
                texture_buffer,
                uv_buffer,
                primitive_buffer,
                depth_cell,
                depth_layer,
                canvascell,
            );
        }
    }
}

use once_cell::sync::Lazy;
use rayon::prelude::*;

// Create a global thread pool that is initialized only once.
static GLOBAL_THREAD_POOL: Lazy<rayon::ThreadPool> = Lazy::new(|| {
    // Set your desired fixed number of threads.
    rayon::ThreadPoolBuilder::new()
        .num_threads(8) // For example, use 4 threads.
        .build()
        .expect("Failed to build thread pool")
});

/// This function applies the material to every pixel in parallel.
pub fn apply_material_on_parallel<const TEXTURESIZE: usize, const DEPTHLAYER: usize>(
    draw_buffer: &mut DrawBuffer<DEPTHLAYER, f32>,
    material_buffer: &MaterialBuffer,
    texture_buffer: &TextureBuffer<TEXTURESIZE>,
    uv_buffer: &UVBuffer<f32>,
    primitive_buffer: &PrimitiveBuffer,
) {
    // Use the global thread pool to run our work.
    GLOBAL_THREAD_POOL.install(|| {
        // `par_iter` and `par_iter_mut` split the work among threads.
        draw_buffer
            .depthbuffer
            .par_iter()
            .zip(draw_buffer.canvas.par_iter_mut())
            .for_each(|(depth_cell, canvas_cell)| {
                for depth_layer in (0..DEPTHLAYER).rev() {
                    // Access the pixel info; note that `pixbuffer` is assumed read-only.
                    let pixinfo = draw_buffer.pixbuffer[depth_cell.pixinfo[depth_layer]];

                    // Call the material application function.
                    apply_material(
                        pixinfo,
                        material_buffer,
                        texture_buffer,
                        uv_buffer,
                        primitive_buffer,
                        depth_cell,
                        depth_layer,
                        canvas_cell,
                    );
                }
            });
    });
}
