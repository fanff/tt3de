use std::marker::PhantomData;
use std::sync::atomic::{AtomicPtr, Ordering};

use nalgebra_glm::{normalize, Mat4, Vec3, Vec4};

use crate::ttsl::TtslLightEnv;

/// Compile-time slot array size. Python `capacity` is a runtime cap ≤ this.
pub const MAX_LIGHTS: usize = 32;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(i32)]
pub enum LightType {
    Empty = 0,
    Ambient = 1,
    Directional = 2,
    Point = 3,
}

impl LightType {
    pub fn from_i32(value: i32) -> Self {
        match value {
            1 => Self::Ambient,
            2 => Self::Directional,
            3 => Self::Point,
            _ => Self::Empty,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct LightSlot {
    pub light_type: LightType,
    pub color: Vec3,
    pub world_direction: Vec3,
    pub world_position: Vec3,
    pub attenuation: Vec3,
    pub view_direction: Vec3,
    pub view_position: Vec3,
}

impl LightSlot {
    pub fn empty() -> Self {
        Self {
            light_type: LightType::Empty,
            color: Vec3::zeros(),
            world_direction: Vec3::zeros(),
            world_position: Vec3::zeros(),
            attenuation: Vec3::zeros(),
            view_direction: Vec3::zeros(),
            view_position: Vec3::zeros(),
        }
    }
}

impl Default for LightSlot {
    fn default() -> Self {
        Self::empty()
    }
}

#[derive(Clone, Debug)]
pub struct LightBuffer {
    slots: [LightSlot; MAX_LIGHTS],
    /// Highest occupied index + 1 (dense prefix for `tt_lightCount` loops).
    count: usize,
    /// Runtime validation cap (≤ [`MAX_LIGHTS`]).
    user_capacity: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LightError {
    CapacityTooLarge { requested: usize, max: usize },
    IndexOutOfRange { index: usize, capacity: usize },
}

impl std::fmt::Display for LightError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::CapacityTooLarge { requested, max } => {
                write!(f, "light capacity {requested} exceeds MAX_LIGHTS ({max})")
            }
            Self::IndexOutOfRange { index, capacity } => {
                write!(f, "light index {index} is out of range for capacity {capacity}")
            }
        }
    }
}

impl std::error::Error for LightError {}

impl LightBuffer {
    pub fn new() -> Self {
        Self::with_capacity(16).expect("default capacity is within MAX_LIGHTS")
    }

    pub fn with_capacity(user_capacity: usize) -> Result<Self, LightError> {
        if user_capacity > MAX_LIGHTS {
            return Err(LightError::CapacityTooLarge {
                requested: user_capacity,
                max: MAX_LIGHTS,
            });
        }
        Ok(Self {
            slots: [LightSlot::empty(); MAX_LIGHTS],
            count: 0,
            user_capacity,
        })
    }

    pub fn user_capacity(&self) -> usize {
        self.user_capacity
    }

    pub fn count(&self) -> usize {
        self.count
    }

    fn check_index(&self, index: usize) -> Result<(), LightError> {
        if index >= self.user_capacity {
            return Err(LightError::IndexOutOfRange {
                index,
                capacity: self.user_capacity,
            });
        }
        Ok(())
    }

    fn note_occupied(&mut self, index: usize) {
        if index + 1 > self.count {
            self.count = index + 1;
        }
    }

    fn shrink_trailing_empty(&mut self) {
        while self.count > 0 && self.slots[self.count - 1].light_type == LightType::Empty {
            self.count -= 1;
        }
    }

    pub fn set_ambient(&mut self, index: usize, color: Vec3) -> Result<(), LightError> {
        self.check_index(index)?;
        let mut slot = LightSlot::empty();
        slot.light_type = LightType::Ambient;
        slot.color = color;
        self.slots[index] = slot;
        self.note_occupied(index);
        Ok(())
    }

    pub fn set_directional(
        &mut self,
        index: usize,
        color: Vec3,
        direction: Vec3,
    ) -> Result<(), LightError> {
        self.check_index(index)?;
        let world_direction = safe_normalize(direction);
        let mut slot = LightSlot::empty();
        slot.light_type = LightType::Directional;
        slot.color = color;
        slot.world_direction = world_direction;
        slot.view_direction = world_direction;
        self.slots[index] = slot;
        self.note_occupied(index);
        Ok(())
    }

    pub fn set_point(
        &mut self,
        index: usize,
        color: Vec3,
        position: Vec3,
        attenuation: Vec3,
    ) -> Result<(), LightError> {
        self.check_index(index)?;
        let mut slot = LightSlot::empty();
        slot.light_type = LightType::Point;
        slot.color = color;
        slot.world_position = position;
        slot.view_position = position;
        slot.attenuation = attenuation;
        self.slots[index] = slot;
        self.note_occupied(index);
        Ok(())
    }

    pub fn clear(&mut self, index: usize) -> Result<(), LightError> {
        self.check_index(index)?;
        self.slots[index] = LightSlot::empty();
        self.shrink_trailing_empty();
        Ok(())
    }

    pub fn slot(&self, index: usize) -> Option<&LightSlot> {
        self.slots.get(index)
    }

    /// Transform world-space directions (`w=0`) and positions (`w=1`) by `view_matrix`.
    /// Directional directions are re-normalized. Ambient slots are space-independent.
    pub fn update_view_space(&mut self, view_matrix: &Mat4) {
        for slot in self.slots.iter_mut() {
            match slot.light_type {
                LightType::Empty | LightType::Ambient => {}
                LightType::Directional => {
                    slot.view_direction = transform_direction(view_matrix, slot.world_direction);
                }
                LightType::Point => {
                    slot.view_position = transform_point(view_matrix, slot.world_position);
                }
            }
        }
    }

    fn slot_or_empty(&self, index: i32) -> LightSlot {
        if index < 0 {
            return LightSlot::empty();
        }
        self.slots
            .get(index as usize)
            .copied()
            .unwrap_or_else(LightSlot::empty)
    }
}

impl Default for LightBuffer {
    fn default() -> Self {
        Self::new()
    }
}

impl TtslLightEnv for LightBuffer {
    fn light_count(&self) -> i32 {
        self.count as i32
    }

    fn light_type(&self, index: i32) -> i32 {
        self.slot_or_empty(index).light_type as i32
    }

    fn light_color(&self, index: i32) -> Vec3 {
        self.slot_or_empty(index).color
    }

    fn light_direction(&self, index: i32) -> Vec3 {
        self.slot_or_empty(index).view_direction
    }

    fn light_position(&self, index: i32) -> Vec3 {
        self.slot_or_empty(index).view_position
    }

    fn light_attenuation(&self, index: i32) -> Vec3 {
        self.slot_or_empty(index).attenuation
    }
}

fn safe_normalize(v: Vec3) -> Vec3 {
    if v.norm() > 1e-8 {
        normalize(&v)
    } else {
        Vec3::zeros()
    }
}

fn transform_direction(view: &Mat4, dir: Vec3) -> Vec3 {
    let v = view * Vec4::new(dir.x, dir.y, dir.z, 0.0);
    safe_normalize(Vec3::new(v.x, v.y, v.z))
}

fn transform_point(view: &Mat4, pos: Vec3) -> Vec3 {
    let v = view * Vec4::new(pos.x, pos.y, pos.z, 1.0);
    Vec3::new(v.x, v.y, v.z)
}

static FRAME_LIGHTS: AtomicPtr<LightBuffer> = AtomicPtr::new(std::ptr::null_mut());

/// Binds `buf` as the shader-visible light table for the current apply pass.
///
/// Parallel material workers all read the same pointer. The guard must outlive
/// the pass (including Rayon work).
pub fn bind_frame_lights(buf: &LightBuffer) -> FrameLightsGuard<'_> {
    FRAME_LIGHTS.store(buf as *const LightBuffer as *mut LightBuffer, Ordering::Release);
    FrameLightsGuard {
        _marker: PhantomData,
    }
}

pub struct FrameLightsGuard<'a> {
    _marker: PhantomData<&'a LightBuffer>,
}

impl Drop for FrameLightsGuard<'_> {
    fn drop(&mut self) {
        FRAME_LIGHTS.store(std::ptr::null_mut(), Ordering::Release);
    }
}

pub fn current_frame_lights() -> Option<&'static LightBuffer> {
    let ptr = FRAME_LIGHTS.load(Ordering::Acquire);
    if ptr.is_null() {
        None
    } else {
        Some(unsafe { &*ptr })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use nalgebra_glm::{rotate_y, vec3, Mat4};

    #[test]
    fn set_and_clear_updates_count() {
        let mut buf = LightBuffer::new();
        buf.set_ambient(0, vec3(0.1, 0.1, 0.1)).unwrap();
        buf.set_point(2, vec3(1.0, 0.0, 0.0), vec3(3.0, 0.0, 0.0), vec3(1.0, 0.0, 0.0))
            .unwrap();
        assert_eq!(buf.count(), 3);
        assert_eq!(buf.light_type(1), LightType::Empty as i32);
        buf.clear(2).unwrap();
        assert_eq!(buf.count(), 1);
        buf.clear(0).unwrap();
        assert_eq!(buf.count(), 0);
    }

    #[test]
    fn capacity_rejects_over_max_and_index() {
        assert!(matches!(
            LightBuffer::with_capacity(MAX_LIGHTS + 1),
            Err(LightError::CapacityTooLarge { .. })
        ));
        let mut buf = LightBuffer::with_capacity(2).unwrap();
        assert!(buf.set_ambient(2, vec3(1.0, 0.0, 0.0)).is_err());
    }

    #[test]
    fn directional_normalizes_on_write() {
        let mut buf = LightBuffer::new();
        buf.set_directional(0, vec3(1.0, 1.0, 1.0), vec3(0.0, 0.0, -2.0))
            .unwrap();
        let dir = buf.slot(0).unwrap().world_direction;
        assert!((dir.z + 1.0).abs() < 1e-5);
        assert!((dir.norm() - 1.0).abs() < 1e-5);
    }

    #[test]
    fn update_view_space_rotates_direction_and_position() {
        let mut buf = LightBuffer::new();
        buf.set_directional(0, vec3(1.0, 1.0, 1.0), vec3(0.0, 0.0, -1.0))
            .unwrap();
        buf.set_point(
            1,
            vec3(1.0, 0.5, 0.2),
            vec3(1.0, 0.0, 0.0),
            vec3(1.0, 0.0, 0.0),
        )
        .unwrap();
        // 90° about Y: +Z → +X in a right-handed rotate_y? nalgebra rotate_y
        // sends (0,0,-1) toward -X or +X depending on convention.
        let view = rotate_y(&Mat4::identity(), std::f32::consts::FRAC_PI_2);
        buf.update_view_space(&view);
        let dir = buf.light_direction(0);
        assert!((dir.norm() - 1.0).abs() < 1e-5);
        // w=0 direction (0,0,-1) * Ry(90°) → (-1, 0, 0) or (1, 0, 0)
        assert!(dir.y.abs() < 1e-5);
        assert!((dir.x.abs() - 1.0).abs() < 1e-4);
        assert!(dir.z.abs() < 1e-4);

        let pos = buf.light_position(1);
        assert!(pos.y.abs() < 1e-5);
        assert!((pos.x.abs() - 1.0).abs() < 1e-4 || (pos.z.abs() - 1.0).abs() < 1e-4);
    }

    #[test]
    fn out_of_range_accessors_are_zero() {
        let buf = LightBuffer::new();
        assert_eq!(buf.light_count(), 0);
        assert_eq!(buf.light_type(99), 0);
        assert_eq!(buf.light_color(-1), Vec3::zeros());
    }
}
