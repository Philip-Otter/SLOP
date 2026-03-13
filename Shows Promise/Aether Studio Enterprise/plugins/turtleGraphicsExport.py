# ==============================================================================
# AETHER STUDIO PLUGIN: TURTLE GRAPHICS EXPORTER (V44 FIXED)
# Compiles Aether UI to a fully self-contained Python Turtle App (with clicks!)
# ==============================================================================
import tkinter as tk
from tkinter import messagebox
import sys

# Safe IDE Hook
try:
    main_mod = sys.modules.get('__main__')
    AetherPlugin = main_mod.AetherPlugin
except AttributeError:
    class AetherPlugin:
        def on_load(self, ide_instance): pass
        def on_unload(self, ide_instance): pass

class TurtleExporterPlugin(AetherPlugin):
    name = "Turtle Exporter"
    author = "Senior Quantum Dev"
    version = "2.0.0"
    description = "Parses VDOM into absolute bounds and generates an Interactive Turtle app."

    def on_load(self, ide_instance):
        self.ide = ide_instance
        self.ide.export_builders["Turtle Graphics Application"] = self.export_turtle
        print(f"[{self.name}] Registered Turtle Compilation Target.")

    def on_unload(self, ide_instance):
        if "Turtle Graphics Application" in self.ide.export_builders:
            del self.ide.export_builders["Turtle Graphics Application"]

    def _resolve_color(self, color_ref):
        if color_ref in self.ide.app_theme: return self.ide.app_theme[color_ref]
        if str(color_ref).startswith("#"): return color_ref
        # Prevents turtle crash from empty/invalid colors by defaulting to transparent black
        return color_ref if color_ref and color_ref != "None" else "#000000"

    def get_abs_geometry(self, comp_id, comps, root_w, root_h):
        comp = comps[comp_id]
        layout = comp["layout"]
        parent_id = layout.get("parent", "root")

        if parent_id == "root" or parent_id not in comps:
            px, py, pw, ph = 0, 0, root_w, root_h
        else:
            px, py, pw, ph = self.get_abs_geometry(parent_id, comps, root_w, root_h)

        x = px + (layout["relx"] * pw)
        y = py + (layout["rely"] * ph)
        w = layout["relw"] * pw
        h = layout["relh"] * ph

        return x, y, w, h

    def get_depth(self, comp_id, comps):
        comp = comps.get(comp_id)
        if not comp or comp["layout"].get("parent", "root") == "root": return 0
        return 1 + self.get_depth(comp["layout"]["parent"], comps)

    def export_turtle(self):
        app_name = self.ide.metadata.get("name", "Aether_Turtle_App")
        root_w = self.ide.metadata.get("width", 1000)
        root_h = self.ide.metadata.get("height", 700)
        bg_color = self._resolve_color(self.ide.app_theme.get("app_bg", "#1e1e1e"))

        comps = self.ide.components
        sorted_comps = sorted(comps.values(), key=lambda c: self.get_depth(c["id"], comps))

        draw_commands = []
        handled_events = set()
        stubs = []

        for c in sorted_comps:
            if c.get("init_hidden", False): continue 

            x, y, w, h = self.get_abs_geometry(c["id"], comps, root_w, root_h)
            
            turtle_x = x - (root_w / 2)
            turtle_y = (root_h / 2) - y

            bg = self._resolve_color(c["props"].get("bg", ""))
            fg = self._resolve_color(c["props"].get("fg", "#000000"))
            bd = c["props"].get("bd", 1)
            text = c["props"].get("text", "")
            font = c["props"].get("font", ("Arial", 10, "normal"))

            events = c.get("events", {})
            if "command" in events:
                fn_name = events["command"]["fn"]
                raw_code = events["command"].get("code", "pass").strip() or "pass"
                indented_code = '\n'.join([f"        {line}" for line in raw_code.split('\n')])
                
                # FIX: Array mapping pushed into the draw commands cycle directly
                draw_commands.append(f"        self.buttons.append(({turtle_x:.1f}, {turtle_y:.1f}, {w:.1f}, {h:.1f}, '{fn_name}'))")

                if fn_name not in handled_events:
                    stubs.append(f"    def {fn_name}(self):\n{indented_code}")
                    handled_events.add(fn_name)

            draw_commands.append(f"        # Rendering {c['id']} ({c['type']})")
            if c["type"] in ["Frame", "Button", "Entry", "Canvas", "Progressbar"]:
                draw_commands.append(f"        self.draw_rect({turtle_x:.1f}, {turtle_y:.1f}, {w:.1f}, {h:.1f}, '{bg}', '{fg}', {bd})")
            
            if text and c["type"] not in ["Canvas", "Frame", "Scrollbar"]:
                safe_txt = str(text).replace('\n', '\\n').replace("'", "\\'")
                draw_commands.append(f"        self.draw_text({turtle_x:.1f}, {turtle_y:.1f}, {w:.1f}, {h:.1f}, '{safe_txt}', '{fg}', {list(font)})")
            
            draw_commands.append("")

        draw_code_str = "\n".join(draw_commands)
        stubs_str = "\n".join(stubs)

        # Output final compiler string
        final_script = f"""# ==========================================================
# AETHER STUDIO ENTERPRISE V44 - QUANTUM BUILD
# Export Target: Interactive Python Turtle Graphics
# Application: {app_name}
# ==========================================================
import turtle
import time

# [USER_IMPORTS]
{self.ide.user_code['imports']}

class TurtleApp:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.title("{app_name}")
        self.screen.setup(width={root_w}, height={root_h})
        # FIX: Explicit Cartesian Map ensures raycast hitboxes work regardless of OS DPI resizing
        self.screen.setworldcoordinates(-{root_w}/2, -{root_h}/2, {root_w}/2, {root_h}/2)
        self.screen.bgcolor("{bg_color}")
        self.screen.tracer(0) 

        self.t = turtle.Turtle()
        self.t.hideturtle()
        self.t.speed(0)

        self.state = {{}}
        self.buttons = [] 

        self.setup_ui()
        self.screen.onscreenclick(self.handle_click)
        self.boot_sequence()

    def draw_rect(self, x, y, w, h, bg, fg, bd=1):
        self.t.penup()
        self.t.goto(x, y)
        self.t.pendown()
        self.t.setheading(0)
        
        if bg and bg != "None":
            self.t.fillcolor(bg)
            self.t.begin_fill()
            
        try:
            self.t.pensize(int(bd) if bd else 1)
        except:
            self.t.pensize(1)
            
        self.t.pencolor(fg if fg and fg != "None" else bg)
        
        for _ in range(2):
            self.t.forward(w)
            self.t.right(90)
            self.t.forward(h)
            self.t.right(90)
            
        if bg and bg != "None":
            self.t.end_fill()

    def draw_text(self, x, y, w, h, text, fg, font_tuple):
        if not text: return
        self.t.penup()
        font_name = font_tuple[0] if len(font_tuple) > 0 else "Arial"
        font_size = int(font_tuple[1]) if len(font_tuple) > 1 else 10
        font_weight = font_tuple[2] if len(font_tuple) > 2 else "normal"

        self.t.goto(x + w/2, y - h/2 - font_size * 0.7)
        self.t.pencolor(fg)
        self.t.write(str(text), align="center", font=(font_name, font_size, font_weight))

    def setup_ui(self):
        self.t.clear()
        self.buttons.clear() # FIX: Stops infinite array appending loop
{draw_code_str}
        self.screen.update()

    def handle_click(self, x, y):
        for btn in self.buttons:
            bx, by, bw, bh, cmd_name = btn
            if bx <= x <= bx + bw and (by - bh) <= y <= by:
                if hasattr(self, cmd_name):
                    getattr(self, cmd_name)()
                    self.setup_ui() 

    def boot_sequence(self):
        # [USER_INIT]
{self.ide.user_code['init']}
        pass

    # --- COMPILED EVENT HANDLERS ---
{stubs_str}

    # --- GLOBAL USER METHODS ---
{self.ide.user_code['methods']}

if __name__ == "__main__":
    app = TurtleApp()
    app.screen.mainloop()
"""
        self.ide._write_export(final_script)
        messagebox.showinfo("Turtle Export Complete", f"Successfully cross-compiled {len(sorted_comps)} VDOM nodes into raw Turtle geometry arrays and interactive hitboxes.")
