use std::fmt;

use nalgebra_glm::{Vec2, Vec3, Vec4};

/// Represents a vertex in a 3D space.
///
/// This struct holds the essential attributes of a vertex for rendering a triangle:
/// - `pos`: The position of the vertex in 4D space.
/// - `normal`: The normal vector at the vertex, used for lighting calculations.
/// - `uv`: The texture coordinates for mapping textures onto the surface.
/// - `view_pos`: View-space position premultiplied by NDC `w` (same perspective convention as `uv`);
///   raster divides by `pos.w` for per-pixel Cartesian view position.
///
/// This struct is `Clone` and `Copy` for easy duplication and efficient use.
#[derive(Clone, Copy)]
pub struct Vertex {
    pub pos: Vec4,
    pub normal: Vec3,
    pub uv: Vec2,
    pub view_pos: Vec3,
}

impl Vertex {
    /// Creates a new `Vertex` instance.
    ///
    /// # Parameters
    /// - `pos`: The position of the vertex in 4D space.
    /// - `normal`: The normal vector at the vertex.
    /// - `uv`: The texture coordinates for the vertex.
    /// - `view_pos`: View-space `xyz * pos.w` for perspective-correct interpolation (use `Vec3::zeros()` when N/A).
    ///
    /// # Returns
    /// A new `Vertex` with the specified attributes.
    pub fn new(pos: Vec4, normal: Vec3, uv: Vec2, view_pos: Vec3) -> Self {
        Self {
            pos,
            normal,
            uv,
            view_pos,
        }
    }

    pub fn zero() -> Self {
        Self {
            pos: Vec4::zeros(),
            normal: Vec3::zeros(),
            uv: Vec2::zeros(),
            view_pos: Vec3::zeros(),
        }
    }
}
// implementing math operation for Vertex (+, - , scalar mult&division)
impl std::ops::Add for Vertex {
    type Output = Self;

    fn add(self, rhs: Self) -> Self {
        Self {
            pos: self.pos + rhs.pos,
            normal: self.normal + rhs.normal,
            uv: self.uv + rhs.uv,
            view_pos: self.view_pos + rhs.view_pos,
        }
    }
}
impl std::ops::Sub for Vertex {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self {
        Self {
            pos: self.pos - rhs.pos,
            normal: self.normal - rhs.normal,
            uv: self.uv - rhs.uv,
            view_pos: self.view_pos - rhs.view_pos,
        }
    }
}
impl std::ops::Div<f32> for Vertex {
    type Output = Self;

    fn div(self, rhs: f32) -> Self {
        Self {
            pos: self.pos / rhs,
            normal: self.normal / rhs,
            uv: self.uv / rhs,
            view_pos: self.view_pos / rhs,
        }
    }
}
impl std::ops::Mul<f32> for Vertex {
    type Output = Self;

    fn mul(self, rhs: f32) -> Self {
        Self {
            pos: self.pos * rhs,
            normal: self.normal * rhs,
            uv: self.uv * rhs,
            view_pos: self.view_pos * rhs,
        }
    }
}
// implementing math operation for Vertex (+=, -=)
impl std::ops::AddAssign for Vertex {
    fn add_assign(&mut self, rhs: Self) {
        self.pos += rhs.pos;
        self.normal += rhs.normal;
        self.uv += rhs.uv;
        self.view_pos += rhs.view_pos;
    }
}
impl std::ops::SubAssign for Vertex {
    fn sub_assign(&mut self, rhs: Self) {
        self.pos -= rhs.pos;
        self.normal -= rhs.normal;
        self.uv -= rhs.uv;
        self.view_pos -= rhs.view_pos;
    }
}
impl std::fmt::Debug for Vertex {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Vertex")
            .field("pos", &(&self.pos.x, &self.pos.y, &self.pos.z, &self.pos.w))
            .field("normal", &(&self.normal.x, &self.normal.y, &self.normal.z))
            .field("uv", &(&self.uv.x, &self.uv.y))
            .field(
                "view_pos",
                &(&self.view_pos.x, &self.view_pos.y, &self.view_pos.z),
            )
            .finish()
    }
}

#[cfg(test)]
mod test_vertext {

    use nalgebra_glm::{Vec2, Vec3, Vec4};

    #[test]
    pub fn test_vertex_add() {
        //let a = super::Vertex::new(
        //    Vec4::new(1.0, 2.0, 3.0, 4.0),
        //    Vec3::new(1.0, 2.0, 3.0),
        //    Vec2::new(1.0, 2.0),
        //);
        let a = dbg!(super::Vertex::new(
            Vec4::new(1.0, 2.0, 3.0, 4.0),
            Vec3::new(1.0, 2.0, 3.0),
            Vec2::new(1.0, 2.0),
            Vec3::zeros(),
        ));
        let b = super::Vertex::new(
            Vec4::new(1.0, 2.0, 3.0, 4.0),
            Vec3::new(1.0, 2.0, 3.0),
            Vec2::new(1.0, 2.0),
            Vec3::zeros(),
        );

        let c = a + b;

        assert_eq!(c.pos.x, 2.0);
        assert_eq!(c.pos.y, 4.0);
        assert_eq!(c.pos.z, 6.0);
        assert_eq!(c.pos.w, 8.0);

        assert_eq!(c.normal.x, 2.0);
        assert_eq!(c.normal.y, 4.0);
        assert_eq!(c.normal.z, 6.0);

        assert_eq!(c.uv.x, 2.0);
        assert_eq!(c.uv.y, 4.0);
    }
}
