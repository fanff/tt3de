use nalgebra_glm::{Vec2, Vec4};

pub fn clip_rectangle(
    top_left: &Vec4,
    bottom_right: &Vec4,
    (uv_top_left, uv_bottom_right): (&Vec2, &Vec2),
) -> Option<((Vec4, Vec4), (Vec2, Vec2))> {
    let mut tl = top_left.to_owned();
    let mut br = bottom_right.to_owned();
    let mut uv_tl = uv_top_left.to_owned();
    let mut uv_br = uv_bottom_right.to_owned();

    // clip left
    if tl.x < -tl.w {
        if br.x < -br.w {
            return None;
        }
        let alpha = (-(tl.w + tl.x)) / (br.x - tl.x + br.w - tl.w);
        tl.x = -tl.w;
        uv_tl.x += (uv_br.x - uv_tl.x) * alpha;
    }
    // clip right
    if br.x > br.w {
        if tl.x > tl.w {
            return None;
        }
        let alpha = (br.x - br.w) / (br.x - tl.x + br.w - tl.w);
        br.x = br.w;
        uv_br.x -= (uv_br.x - uv_tl.x) * alpha;
    }
    // clip top
    if tl.y < -tl.w {
        if br.y < -br.w {
            return None;
        }
        let alpha = (-(tl.w + tl.y)) / (br.y - tl.y + br.w - tl.w);
        tl.y = -tl.w;
        uv_tl.y += (uv_br.y - uv_tl.y) * alpha;
    }
    // clip bottom
    if br.y > br.w {
        if tl.y > tl.w {
            return None;
        }
        let alpha = (br.y - br.w) / (br.y - tl.y + br.w - tl.w);
        br.y = br.w;
        uv_br.y -= (uv_br.y - uv_tl.y) * alpha;
    }

    Some(((tl, br), (uv_tl, uv_br)))
}
