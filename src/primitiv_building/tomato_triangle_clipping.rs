use nalgebra_glm::{lerp, Vec2, Vec4};

use super::SmallTriangleBuffer;

fn interpolate_with_uv(p1: &Vec4, p2: &Vec4, uv1: &Vec2, uv2: &Vec2, t: f32) -> (Vec4, Vec2) {
    //p1 + t * (p2 - p1)
    (lerp(p1, p2, t), lerp(uv1, uv2, t))
}

fn clip1<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut SmallTriangleBuffer<OUTPUT_SIZE>,
) {
    let alpha_a = (-pa.z) / (pb.z - pa.z);
    let alpha_b = -pa.z / (pc.z - pa.z);

    let (v0a, uv0a) = interpolate_with_uv(pa, pb, uva, uvb, alpha_a);
    //let v0a = lerp(pa, pb, alpha_a);
    //let uv0a = lerp(uva, uvb, alpha_a);

    //let v0b = lerp(pa, pc, alpha_b);
    //let uv0b = lerp(uva, uvc, alpha_b);
    let (v0b, uv0b) = interpolate_with_uv(pa, pc, uva, uvc, alpha_b);

    output_buffer.push_vec4(v0a, *pb, *pc, (&uv0a, uvb, uvc));
    output_buffer.push_vec4(v0b, v0a, *pc, (&uv0b, &uv0a, uvc));
}

fn clip2<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut SmallTriangleBuffer<OUTPUT_SIZE>,
) {
    let alpha_a = (-pa.z) / (pc.z - pa.z);
    let alpha_b = (-pb.z) / (pc.z - pb.z);

    //let vac = lerp(pa, pc, alpha_a);
    //let uv0a = lerp(uva, uvc, alpha_a);
    let (vac, uv0a) = interpolate_with_uv(pa, pc, uva, uvc, alpha_a);
    //let vbc = lerp(pb, pc, alpha_b);
    //let uv0b = lerp(uvb, uvc, alpha_b);
    let (vbc, uv0b) = interpolate_with_uv(pb, pc, uvb, uvc, alpha_b);
    output_buffer.push_vec4(vac, vbc, *pc, (&uv0a, &uv0b, uvc));
}

pub fn tomato_clip_triangle_to_clip_space(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut SmallTriangleBuffer<12>,
) {
    if pa.x > pa.w && pb.x > pb.w && pc.x > pc.w {
        return;
    }
    if pa.x < -pa.w && pb.x < -pb.w && pc.x < -pc.w {
        return;
    }
    if pa.y > pa.w && pb.y > pb.w && pc.y > pc.w {
        return;
    }
    if pa.y < -pa.w && pb.y < -pb.w && pc.y < -pc.w {
        return;
    }
    if pa.z > pa.w && pb.z > pb.w && pc.z > pc.w {
        return;
    }
    if pa.z < 0.0 && pb.z < 0.0 && pc.z < 0.0 {
        return;
    }

    // test against the near plane
    if pa.z < 0.0 {
        // a is behind the near plane
        if pb.z < 0.0 {
            clip2(pa, pb, pc, (uva, uvb, uvc), output_buffer); //
        } else if pc.z < 0.0 {
            clip2(pa, pc, pb, (uva, uvc, uvb), output_buffer); //
        } else {
            clip1(pa, pb, pc, (uva, uvb, uvc), output_buffer) //
        }
    } else if pb.z < 0.0 {
        if pc.z < 0.0 {
            clip2(pb, pc, pa, (uvb, uvc, uva), output_buffer) //
        } else {
            clip1(pb, pa, pc, (uvb, uva, uvc), output_buffer) //
        }
    } else if pc.z < 0.0 {
        clip1(pc, pa, pb, (uvc, uva, uvb), output_buffer) //
    } else {
        output_buffer.push_vec4(*pa, *pb, *pc, (uva, uvb, uvc));
    }
}
