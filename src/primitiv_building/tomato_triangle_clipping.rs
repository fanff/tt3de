use nalgebra_glm::{lerp, Vec2, Vec3, Vec4};

use super::SmallTriangleBuffer;

fn interpolate_clip_varyings(
    p1: &Vec4,
    p2: &Vec4,
    uv1: &Vec2,
    uv2: &Vec2,
    vp1: &Vec3,
    vp2: &Vec3,
    t: f32,
) -> (Vec4, Vec2, Vec3) {
    (lerp(p1, p2, t), lerp(uv1, uv2, t), lerp(vp1, vp2, t))
}

fn clip1<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    (vpa, vpb, vpc): (&Vec3, &Vec3, &Vec3),
    output_buffer: &mut SmallTriangleBuffer<OUTPUT_SIZE>,
) {
    let alpha_a = (-pa.z) / (pb.z - pa.z);
    let alpha_b = -pa.z / (pc.z - pa.z);

    let (v0a, uv0a, vp0a) = interpolate_clip_varyings(pa, pb, uva, uvb, vpa, vpb, alpha_a);
    let (v0b, uv0b, vp0b) = interpolate_clip_varyings(pa, pc, uva, uvc, vpa, vpc, alpha_b);

    output_buffer.push_vec4(v0a, *pb, *pc, (&uv0a, uvb, uvc), (&vp0a, vpb, vpc));
    output_buffer.push_vec4(v0b, v0a, *pc, (&uv0b, &uv0a, uvc), (&vp0b, &vp0a, vpc));
}

fn clip2<const OUTPUT_SIZE: usize>(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    (vpa, vpb, vpc): (&Vec3, &Vec3, &Vec3),
    output_buffer: &mut SmallTriangleBuffer<OUTPUT_SIZE>,
) {
    let alpha_a = (-pa.z) / (pc.z - pa.z);
    let alpha_b = (-pb.z) / (pc.z - pb.z);

    let (vac, uv0a, vp0a) = interpolate_clip_varyings(pa, pc, uva, uvc, vpa, vpc, alpha_a);
    let (vbc, uv0b, vp0b) = interpolate_clip_varyings(pb, pc, uvb, uvc, vpb, vpc, alpha_b);
    output_buffer.push_vec4(vac, vbc, *pc, (&uv0a, &uv0b, uvc), (&vp0a, &vp0b, vpc));
}

pub fn tomato_clip_triangle_to_clip_space(
    pa: &Vec4,
    pb: &Vec4,
    pc: &Vec4,
    (uva, uvb, uvc): (&Vec2, &Vec2, &Vec2),
    (eye_a, eye_b, eye_c): (&Vec3, &Vec3, &Vec3),
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
            clip2(pa, pb, pc, (uva, uvb, uvc), (eye_a, eye_b, eye_c), output_buffer); //
        } else if pc.z < 0.0 {
            clip2(pa, pc, pb, (uva, uvc, uvb), (eye_a, eye_c, eye_b), output_buffer); //
        } else {
            clip1(pa, pb, pc, (uva, uvb, uvc), (eye_a, eye_b, eye_c), output_buffer) //
        }
    } else if pb.z < 0.0 {
        if pc.z < 0.0 {
            clip2(pb, pc, pa, (uvb, uvc, uva), (eye_b, eye_c, eye_a), output_buffer) //
        } else {
            clip1(pb, pa, pc, (uvb, uva, uvc), (eye_b, eye_a, eye_c), output_buffer) //
        }
    } else if pc.z < 0.0 {
        clip1(pc, pa, pb, (uvc, uva, uvb), (eye_c, eye_a, eye_b), output_buffer) //
    } else {
        output_buffer.push_vec4(*pa, *pb, *pc, (uva, uvb, uvc), (eye_a, eye_b, eye_c));
    }
}
