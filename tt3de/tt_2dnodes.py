
from types import TracebackType
from typing import Any, List, Optional
import glm
from typing_extensions import Self

from tt3de.glm.pyglmtexture import GLMCamera


class TT2DNode():
    def __init__(self, name: str = None,
                 transform: Optional[glm.mat3] = None):
        super().__init__()
        self.name = name if name is not None else "random"
        self.elements:List[TT2DNode]=  []
        self.local_transform = transform if transform is not None else glm.mat3(1.0)

    def cache_output(self,segmap):
        for e in self.elements:
            e.cache_output(segmap)
    def render_point(self,some_info)->int:
        
        (elem,pixinfo) = some_info
        return elem.render_point(pixinfo)
        
    def draw(self,camera:GLMCamera,transform=None,*args):
        if transform is not None:
            localchange = transform*self.local_transform
        else:
            localchange = self.local_transform
        for elem in self.elements:
            for pixcoord,pixinfo in elem.draw(camera,localchange):
                yield pixcoord,(elem,pixinfo)



class TT2DMesh(TT2DNode):

    def __init__(self):
        
        self.elements=[]
        self.uvmap = []

    def cache_output(self,segmap):
        self.texture.cache_output(segmap)
        self.glm_elements=[p3d_triplet_to_matrix(elment)
            for elment in self.elements]
        
        self.glm_uvmap =[p2d_uv_tomatrix(uv) for uv in self.uvmap]


    def render_point(self,some_info)->int:

        vertid,mode,weights = some_info
        

        match mode:
            case 1:
                uvmat = self.glm_uvmap[vertid]
                #uvcoord = glm.saturate(uvmat*weights)
                uvcoord = (uvmat*weights)
                return self.texture.render_point(uvcoord,None)
            case 2:
                return vertid+1
        return 5
    

    def draw(self,camera:GLMCamera,transform=None,*args):

        screen_width, screen_height = camera.screen_width,camera.screen_height
        scc = min(screen_width,screen_height)
        screenscaling = glm.scale(glm.vec2(scc*camera.character_factor,scc))

        final_transform = screenscaling*transform if transform is not None else screenscaling
        for faceidx,trimat in enumerate(self.glm_elements):
            transformed = final_transform*trimat
            tri_inv = glm.inverse(transformed)

            for pxi,pyi in glmtriangle_render(transformed,tri_inv,screen_width,screen_height):
                weights = tri_inv*glm.vec3(pxi,pyi,1)

                if (weights>VEC3_ZERO) == VEC3_YES:
                    yield (pxi,pyi,0),(faceidx,1,weights)

            #vertidx = 0
            #for pxi,pyi in glm_triangle_vertex_pixels(transformed, screen_width,screen_height):
            #    yield (pxi,pyi,-1),(vertidx,2,(1.0,0.0,0.0))
            #    vertidx+=1



