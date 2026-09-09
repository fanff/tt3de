use nalgebra_glm::{Vec2, Vec4};
/// Clips a 2D line segment defined by points `pa` and `pb` with texture coordinates `uva` and `uvb`
/// using the Cohen-Sutherland algorithm.
/// The clipping region is the NDC box: x, y ∈ [-1, 1].
///
/// Returns the clipped line segment as a tuple:
/// (clipped_pa, clipped_pb, clipped_uva, clipped_uvb),
/// or `None` if the line is completely outside the clipping region.
pub fn clip_line2d(
    pa: &Vec4,
    pb: &Vec4,
    uva: &Vec2,
    uvb: &Vec2,
) -> Option<(Vec4, Vec4, Vec2, Vec2)> {
    // Clipping bounds (NDC)
    const X_MIN: f32 = -1.0;
    const X_MAX: f32 = 1.0;
    const Y_MIN: f32 = -1.0;
    const Y_MAX: f32 = 1.0;

    // Region codes
    const INSIDE: u8 = 0;
    const LEFT: u8 = 1 << 0;
    const RIGHT: u8 = 1 << 1;
    const BOTTOM: u8 = 1 << 2;
    const TOP: u8 = 1 << 3;

    fn compute_out_code(x: f32, y: f32) -> u8 {
        let mut code = INSIDE;

        if x < X_MIN {
            code |= LEFT;
        } else if x > X_MAX {
            code |= RIGHT;
        }

        if y < Y_MIN {
            code |= BOTTOM;
        } else if y > Y_MAX {
            code |= TOP;
        }

        code
    }

    // Positions
    let mut x0 = pa.x;
    let mut y0 = pa.y;
    let mut z0 = pa.z;
    let mut w0 = pa.w;

    let mut x1 = pb.x;
    let mut y1 = pb.y;
    let mut z1 = pb.z;
    let mut w1 = pb.w;

    // UVs
    let mut u0 = uva.x;
    let mut v0 = uva.y;
    let mut u1 = uvb.x;
    let mut v1 = uvb.y;

    let mut out0 = compute_out_code(x0, y0);
    let mut out1 = compute_out_code(x1, y1);

    loop {
        // Trivial accept: both inside
        if (out0 | out1) == 0 {
            let p0 = Vec4::new(x0, y0, z0, w0);
            let p1 = Vec4::new(x1, y1, z1, w1);
            let uv0 = Vec2::new(u0, v0);
            let uv1 = Vec2::new(u1, v1);
            return Some((p0, p1, uv0, uv1));
        }

        // Trivial reject: segment is completely outside
        if (out0 & out1) != 0 {
            return None;
        }

        // At least one endpoint is outside; pick it
        let outcode_out = if out0 != 0 { out0 } else { out1 };

        // Direction
        let dx = x1 - x0;
        let dy = y1 - y0;
        let dz = z1 - z0;
        let dw = w1 - w0;
        let du = u1 - u0;
        let dv = v1 - v0;

        // Intersection point
        let (x, y, z, w, u, v);

        if (outcode_out & TOP) != 0 {
            // y = Y_MAX
            let t = (Y_MAX - y0) / dy;
            x = x0 + t * dx;
            y = Y_MAX;
            z = z0 + t * dz;
            w = w0 + t * dw;
            u = u0 + t * du;
            v = v0 + t * dv;
        } else if (outcode_out & BOTTOM) != 0 {
            // y = Y_MIN
            let t = (Y_MIN - y0) / dy;
            x = x0 + t * dx;
            y = Y_MIN;
            z = z0 + t * dz;
            w = w0 + t * dw;
            u = u0 + t * du;
            v = v0 + t * dv;
        } else if (outcode_out & RIGHT) != 0 {
            // x = X_MAX
            let t = (X_MAX - x0) / dx;
            x = X_MAX;
            y = y0 + t * dy;
            z = z0 + t * dz;
            w = w0 + t * dw;
            u = u0 + t * du;
            v = v0 + t * dv;
        } else {
            // LEFT: x = X_MIN
            let t = (X_MIN - x0) / dx;
            x = X_MIN;
            y = y0 + t * dy;
            z = z0 + t * dz;
            w = w0 + t * dw;
            u = u0 + t * du;
            v = v0 + t * dv;
        }

        // Replace the outside endpoint with the intersection and recompute its outcode
        if outcode_out == out0 {
            x0 = x;
            y0 = y;
            z0 = z;
            w0 = w;
            u0 = u;
            v0 = v;
            out0 = compute_out_code(x0, y0);
        } else {
            x1 = x;
            y1 = y;
            z1 = z;
            w1 = w;
            u1 = u;
            v1 = v;
            out1 = compute_out_code(x1, y1);
        }
    }
}
