use nalgebra_glm::{Vec2, Vec3, Vec4};

/// Host-provided 2D texture sampling for TTSL ``TT_TEXTURE`` / ``tt_texture``.
pub trait TtslTextureEnv {
    fn sample_tt_texture(&self, idx: i32, uv: Vec2) -> Vec4;
}

/// Host-provided light table for TTSL ``tt_light*`` accessors.
///
/// Positions and directions are **view space** (after [`crate::lightbuffer::LightBuffer::update_view_space`]).
pub trait TtslLightEnv {
    fn light_count(&self) -> i32;
    fn light_type(&self, index: i32) -> i32;
    fn light_color(&self, index: i32) -> Vec3;
    fn light_direction(&self, index: i32) -> Vec3;
    fn light_position(&self, index: i32) -> Vec3;
    fn light_attenuation(&self, index: i32) -> Vec3;
}

pub mod ir;
pub mod jit;

#[derive(Clone)]
pub struct Registers {
    pub bool_: [bool; 256],
    pub i32_: [i32; 256],
    pub f32_: [f32; 256],
    pub v2: [Vec2; 256],
    pub v3: [Vec3; 256],
    pub v4: [Vec4; 256],
}

impl Registers {
    pub fn new() -> Self {
        Registers {
            bool_: [false; 256],
            i32_: [0; 256],
            f32_: [0.0; 256],
            v2: [Vec2::zeros(); 256],
            v3: [Vec3::zeros(); 256],
            v4: [Vec4::zeros(); 256],
        }
    }
}
