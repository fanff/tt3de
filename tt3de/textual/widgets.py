
from dataclasses import dataclass
from typing import Any, Coroutine
from textual import events
from textual.app import App, ComposeResult, RenderResult
from textual.containers import Container
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Label,
    Markdown,
    Sparkline,
    Static,
    Input
)
from rich.color import Color
from rich.style import Style
from rich.text import Segment
from textual import events
from textual.app import App, ComposeResult, RenderResult
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Static,
)

from textual.message import Message
from textual.layouts import horizontal

from tt3de.glm.pyglmtexture import GLMMesh3D
from tt3de.richtexture import (
    DistGradBGShade,
    ImageTexture,
    RenderContext,
    StaticTexture,
)
from tt3de.textual_widget import TT3DView
from tt3de.tt3de import FPSCamera, Line3D, Mesh3D, Node3D, Point3D, PointElem, Quaternion, Triangle3D


class FloatSelector(Widget, can_focus=False):
    DEFAULT_CSS="""

    FloatSelector{
        layout: horizontal;
        
        height:auto;
    }
    FloatSelector > Button {
        border: none;
        width: 3;
        min-width:2;

        height: 3;
        min-height:2;

    }
    FloatSelector > Input{
        align-horizontal: center;
        width: 1fr;
    }

    FloatSelector > .minus-1{
        align-horizontal: left;
        
        
    }
    FloatSelector > .plus-1{
        align-horizontal: right;
    }

    """
    minvalue:float = reactive(1)
    maxvalue:float = reactive(10)
    
    current_value: float = reactive(1.0)
    current_buffer: float = reactive(1.0)

    inclusive_left:bool = reactive(True)
    inclusive_right:bool = reactive(True)
    
    accuracy = .1
    
    round_figures:int = reactive(3)
    mouse_factor:float = .5

    button_factor:float = 5.0

    is_mouse_clicking = False

    @dataclass
    class Changed(Message):
        """Posted when the value changes.

        Can be handled using `on_float_selector_changed` in a subclass of `FloatSelector` or in a parent
        widget in the DOM.
        """

        input: 'FloatSelector'
        """The `FloatSelector` widget that was changed."""

        value: float
        """The value that the input was changed to."""

        value_str:str

        
    def __init__(self,
                 minvalue=1.0,
                 maxvalue=100.0,
                 initial_value = None,

                 id=None
                 ):
        super().__init__(id=id)
        self.minvalue=minvalue
        self.maxvalue=maxvalue
        self.current_value = initial_value if initial_value is not None else (self.maxvalue+self.minvalue)/2
        self.current_buffer = initial_value if initial_value is not None else (self.maxvalue+self.minvalue)/2
        
    def compose(self):
        
        yield Button("-",classes="minus-1")
        yield Input(f"{round(self.current_value,self.round_figures)}")
        yield Button("+",classes="plus-1")

    def on_button_pressed(self,event:Button.Pressed):
        match str(event.button.label):
            case "-":
                self.current_buffer-=self.button_factor
            case "+":
                self.current_buffer+=self.button_factor


    async def _on_mouse_down(self, event: events.MouseDown) -> Coroutine[Any, Any, None]:
        self.is_mouse_clicking = True
        #myinp = self.query_one(Input)
        #myinp.value = "lol"
        return super()._on_mouse_down(event)
    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        self.is_mouse_clicking = False
        return await super()._on_mouse_up(event)

    async def on_event(self, event: events.Event):
        if self.is_mouse_clicking:
            if isinstance(event,events.Leave):
                pass  # TODO : Find why I can't catch this dude ?! 
                self.is_mouse_clicking = False
            if isinstance(event,(events.DescendantBlur,events.DescendantFocus)):
                self.is_mouse_clicking = False

        if isinstance(event,events.Leave):
            1/0 # traying to capture randomly 

        await super().on_event(event)
                
    def on_mouse_move(self,event:events.MouseMove):
        if self.is_mouse_clicking:
            diff = event.delta_x
            self.current_buffer = self.current_value+(self.mouse_factor*diff)



    def watch_current_buffer(self,buffered_value):
        self._set_current_value(buffered_value)


    def watch_current_value(self,value):
        myinp = None
        try:
            myinp = self.query_one(Input)
            myinp.value=f"{round(value,self.round_figures)}"
        except NoMatches:
            pass

    def _set_current_value(self,value):
        min_bound_c = value>= self.minvalue if self.inclusive_left else  value> self.minvalue
        max_bound_c = value<= self.maxvalue if self.inclusive_right else  value< self.maxvalue
        if min_bound_c:
            if max_bound_c:
                self.current_value = value
            else:
                self.current_value = self.maxvalue if self.inclusive_right else self.maxvalue-self.accuracy
        else:
            self.current_value = self.minvalue if self.inclusive_left else self.minvalue+self.accuracy

        self.post_message(self.Changed(self, self.current_value, f"{round(self.current_value,self.round_figures)}"))


class GlmMeshInfo(Widget):
    meshindex:int = reactive(-1)



    def compose(self):
        pass




