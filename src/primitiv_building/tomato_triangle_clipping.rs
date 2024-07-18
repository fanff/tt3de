use nalgebra_glm::{lerp, Vec2, Vec4};

use super::TriangleBuffer;
fn clip1<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<OUTPUT_SIZE>,
) {
    let alphaA = (-pa.z) / (pb.z - pa.z);
    let alphaB = -pa.z / (pc.z - pa.z);

    let v0a = lerp(pa, pb, alphaA);
    let v0b = lerp(pa, pc, alphaB);

    let uv0a = lerp(uva, uvb, alphaA);
    let uv0b = lerp(uva, uvc, alphaB);

    output_buffer.push_vec4(v0a, *pb, *pc, (&uv0a, uvb, uvc));
    output_buffer.push_vec4(v0b, v0a, *pc, (&uv0b, &uv0a, uvc));
}

fn clip2<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<OUTPUT_SIZE>,
) {
    let alphaA = (-pa.z) / (pc.z - pa.z);
    let alphaB = (-pb.z) / (pc.z - pb.z);

    let vac = lerp(pa, pc, alphaA);
    let vbc = lerp(pb, pc, alphaB);

    let uv0a = lerp(uva, uvc, alphaA);
    let uv0b = lerp(uvb, uvc, alphaB);

    output_buffer.push_vec4(vac, vbc, *pc, (&uv0a, &uv0b, uvc));
}

pub fn tomato_clip_triangle_to_clip_space(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    output_buffer: &mut TriangleBuffer<12>,
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
