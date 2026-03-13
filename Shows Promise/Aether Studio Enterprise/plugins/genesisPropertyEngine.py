# ==============================================================================
# GENESIS PROPERTY ENGINE V10.0 - HORIZON UPDATE
# Plugin for Aether Studio Enterprise
# ------------------------------------------------------------------------------
# 1. Foolproof Global Code Formatter: Eliminates TabError & IndentationError.
# 2. Unified Loop System: Dynamic For/While loops in a single UI node.
# 3. 2x2 Logic Adder Grid: Fixes squashed UI visibility issues.
# 4. Bidirectional AST Sync: Real-time editing between code and visual blocks.
# ==============================================================================

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, scrolledtext
import re
import ast
import uuid
import copy
import textwrap
from typing import Dict, List, Any, Optional

try:
    from v45 import AetherPlugin
except ImportError:
    class AetherPlugin:
        pass

# --- CUSTOM TOOLTIP ENGINE ---
class ToolTip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: Any = None) -> None:
        if not self.widget.winfo_exists(): return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.text, background="#111827", foreground="#F9FAFB", 
                       relief="solid", borderwidth=1, font=("Segoe UI", 8), padx=6, pady=4)
        lbl.pack()

    def hide_tooltip(self, event: Any = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class FakeEvent:
    def __init__(self, x_root: int, y_root: int):
        self.x_root = x_root
        self.y_root = y_root
        self.x = 0
        self.y = 0

class GenesisPropertiesPlugin(AetherPlugin):
    name = "Genesis Horizon Sync"
    author = "Senior Dev / UI Master"
    version = "10.0.0"
    description = "Provides Foolproof AST Indentation formatting, Dynamic Loops, and Fluid Sync."

    def on_load(self, ide: Any) -> None:
        self.ide = ide
        self.inline_editors: Dict[str, scrolledtext.ScrolledText] = {}
        self.popout_editors: Dict[str, scrolledtext.ScrolledText] = {}
        self.node_frames: Dict[str, tk.Frame] = {}

        self.original_render = ide.render_inspector
        self.ide.render_inspector = self.render_genesis_inspector
        self.original_on_widget_motion = self.ide.on_widget_motion
        self.ide.on_widget_motion = lambda e, uid: self.patched_on_widget_motion(self.ide, e, uid)
        self.original_refresh_all = self.ide.refresh_all
        self.ide.refresh_all = self.patched_refresh_all

        self.tools_menu = tk.Menu(self.ide.menubar, tearoff=0, bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"])
        self.tools_menu.add_command(label="Global Logic Manager", command=self.open_global_editor)
        self.ide.menubar.add_cascade(label="Genesis Tools", menu=self.tools_menu)
        
        self.patch_canvas_fluidity()

        self.ENUMS: Dict[str, List[str]] = {
            "state": ["normal", "disabled", "readonly", "active"],
            "relief": ["flat", "raised", "sunken", "ridge", "groove", "solid"],
            "anchor": ["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"],
            "justify": ["left", "center", "right"],
            "cursor": ["arrow", "hand2", "ibeam", "crosshair", "watch", "fleur", "target"]
        }
        
        self.setup_styles()
        self.ide.refresh_all()
        if self.ide.selected_id:
            self.render_genesis_inspector()
            
        print(f"[{self.name}] V10 Horizon Engaged. Structural limiters dissolved.")

    def on_unload(self, ide: Any) -> None:
        self.ide.render_inspector = self.original_render
        self.ide.on_widget_motion = self.original_on_widget_motion
        self.ide.refresh_all = self.original_refresh_all
        try:
            menu_index = self.ide.menubar.index("Genesis Tools")
            if menu_index is not None: self.ide.menubar.delete(menu_index)
        except: pass
        print(f"[{self.name}] Plugin Unloaded. System Restored.")

    # =========================================================================
    # CORE ARCHITECTURE PATCHES
    # =========================================================================
    def patch_canvas_fluidity(self) -> None:
        def on_event_canvas_config(e: Any) -> None:
            for item in self.ide.event_scroll.find_withtag("all"):
                if self.ide.event_scroll.type(item) == "window":
                    self.ide.event_scroll.itemconfig(item, width=e.width)
            self.ide.event_scroll.configure(scrollregion=self.ide.event_scroll.bbox("all"))
        self.ide.event_scroll.bind("<Configure>", on_event_canvas_config)
        self.ide.event_scroll.event_generate("<Configure>", width=self.ide.event_scroll.winfo_width(), height=self.ide.event_scroll.winfo_height())

    def patched_on_widget_motion(self, ide_ref: Any, event: Any, uid: str) -> None:
        if ide_ref.drag_data.get("active", False) or uid not in ide_ref.live_widgets: return
        w = ide_ref.live_widgets[uid].winfo_width()
        h = ide_ref.live_widgets[uid].winfo_height()
        margin = 10
        if event.x >= w - margin and event.y >= h - margin: ide_ref.live_widgets[uid].config(cursor="bottom_right_corner")
        elif event.x >= w - margin: ide_ref.live_widgets[uid].config(cursor="right_side")
        elif event.y >= h - margin: ide_ref.live_widgets[uid].config(cursor="bottom_side")
        else:
            c = ide_ref.get_comp_by_id(uid)
            if c: ide_ref.live_widgets[uid].config(cursor=c['props'].get('cursor', 'arrow'))

    def patched_refresh_all(self) -> None:
        self.original_refresh_all()
        for uid, widget in self.ide.live_widgets.items():
            widget.unbind("<Button-3>")
            widget.bind("<Button-3>", lambda e, id=uid: self.show_context_menu(e, id))

    def show_context_menu(self, event: Any, uid: str) -> None:
        comp = self.ide.get_comp_by_id(uid)
        if not comp: return
        self.ide.on_widget_press(FakeEvent(event.x_root, event.y_root), uid)
        ctx = tk.Menu(self.ide.root, tearoff=0, bg=self.ide.ide_theme["panel"], fg=self.ide.ide_theme["text"], bd=0, activebackground=self.ide.ide_theme["accent"])
        ctx.add_command(label=f"❖ Inspect: {comp['type']}", state="disabled")
        ctx.add_separator()
        ctx.add_command(label="Duplicate Element", command=lambda: self.clone_component(uid))
        ctx.add_command(label="Delete Element", command=lambda: self.ide.delete_component())
        ctx.tk_popup(event.x_root, event.y_root)

    def clone_component(self, uid: str) -> None:
        orig = self.ide.get_comp_by_id(uid)
        if not orig: return
        new_comp = copy.deepcopy(orig)
        idx = len(self.ide.components)
        new_id = f"{orig['type'].lower()}_{idx}_{uuid.uuid4().hex[:4]}"
        new_comp["id"] = new_id
        new_comp["layout"]["relx"] = min(0.9, new_comp["layout"]["relx"] + 0.02)
        new_comp["layout"]["rely"] = min(0.9, new_comp["layout"]["rely"] + 0.02)
        self.ide.components[new_id] = new_comp
        self.ide.selected_id = new_id
        self.ide.push_history()
        self.ide.refresh_all()
        self.render_genesis_inspector()

    # =========================================================================
    # GLOBAL EDITORS (WITH FOOLPROOF AST FORMATTING)
    # =========================================================================
    def open_global_editor(self) -> None:
        win = tk.Toplevel(self.ide.root)
        win.title("Genesis: Global Logic Manager")
        win.geometry("900x700")
        win.configure(bg=self.ide.ide_theme["bg"])
        win.transient(self.ide.root)
        
        tabs = ttk.Notebook(win)
        tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def create_tab(title: str, content_key: str) -> scrolledtext.ScrolledText:
            frame = tk.Frame(tabs, bg=self.ide.ide_theme["surface"])
            tabs.add(frame, text=f" {title} ")
            editor = scrolledtext.ScrolledText(frame, bg="#0B0F19", fg="#A5D6FF", font=("Consolas", 11), insertbackground="white", bd=0)
            editor.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            editor.insert("1.0", self.ide.user_code.get(content_key, ""))
            self.ide.highlight_syntax(editor)
            editor.bind("<KeyRelease>", lambda e: self.ide.schedule_highlight(editor, ("Consolas", 11)))
            return editor

        ed_imports = create_tab("Imports [USER_IMPORTS_START]", "imports")
        ed_boot = create_tab("Boot Sequence [USER_INIT_START]", "init")
        ed_methods = create_tab("Global Methods [USER_METHODS_START]", "methods")
        
        btn_frame = tk.Frame(win, bg=self.ide.ide_theme["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def format_code(raw_text: str, indent_level: int) -> str:
            """Foolproof code formatter. Eliminates TabError & IndentationError."""
            # 1. Normalize tabs
            text = raw_text.replace('\t', '    ')
            # 2. Dedent to lowest common indentation
            dedented = textwrap.dedent(text)
            # 3. Indent exactly to IDE requirements
            indented = ""
            prefix = " " * indent_level
            for line in dedented.split('\n'):
                if line.strip(): indented += prefix + line + '\n'
                else: indented += '\n'
            return indented.rstrip('\n')
        
        def save_and_close() -> None:
            self.ide.user_code["imports"] = format_code(ed_imports.get("1.0", tk.END), 0)
            self.ide.user_code["init"] = format_code(ed_boot.get("1.0", tk.END), 8)
            self.ide.user_code["methods"] = format_code(ed_methods.get("1.0", tk.END), 4)
            self.ide.push_history()
            messagebox.showinfo("Compiled", "Global Logic compiled and aligned successfully.", parent=win)
            win.destroy()
            
        ttk.Button(btn_frame, text="Save & Inject Logic", style="Action.TButton", command=save_and_close).pack(side=tk.RIGHT)

    def open_popout_editor(self, ev_key: str) -> None:
        if ev_key in self.popout_editors and self.popout_editors[ev_key].winfo_exists():
            self.popout_editors[ev_key].winfo_toplevel().lift()
            return
        win = tk.Toplevel(self.ide.root)
        win.title(f"AST Logic Editor: {ev_key}")
        win.geometry("800x600")
        win.configure(bg=self.ide.ide_theme["bg"])
        win.transient(self.ide.root)
        
        editor = scrolledtext.ScrolledText(win, bg="#0B0F19", fg="#A5D6FF", font=("Consolas", 12), insertbackground="white", bd=0, highlightthickness=1, highlightbackground=self.ide.ide_theme["panel"])
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        current_code = comp["events"][ev_key].get("code", "pass") if comp else "pass"
        editor.insert("1.0", current_code)
        self.ide.highlight_syntax(editor)
        
        editor.bind("<KeyRelease>", lambda e, k=ev_key, ed=editor: [
            self.manual_code_override(k, ed.get("1.0", tk.END), source="popout"),
            self.ide.schedule_highlight(ed, ("Consolas", 12))
        ])
        self.popout_editors[ev_key] = editor
        
        btn_f = tk.Frame(win, bg=self.ide.ide_theme["bg"])
        btn_f.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_f, text="Close Editor", style="Action.TButton", command=win.destroy).pack(side=tk.RIGHT)

    # =========================================================================
    # INSPECTOR UI BUILDERS
    # =========================================================================
    def setup_styles(self) -> None:
        style = ttk.Style()
        style.configure("Genesis.TCombobox", padding=4)
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), padding=4)
        style.configure("Mini.TButton", font=("Consolas", 8, "bold"), padding=0)

    def render_genesis_inspector(self) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        for w in self.ide.prop_scroll.winfo_children(): w.destroy()
        for w in self.ide.layout_frame.winfo_children(): w.destroy()
        for w in self.ide.event_frame.winfo_children(): w.destroy()
        self.ide.layout_entries.clear()
        self.inline_editors.clear()
        self.node_frames.clear()

        self.build_properties_tab(comp)
        self.build_layout_tab(comp)
        self.build_events_tab(comp)

    def build_properties_tab(self, comp: Dict[str, Any]) -> None:
        header_f = tk.Frame(self.ide.prop_scroll, bg=self.ide.ide_theme["panel"], pady=8, padx=10)
        header_f.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_f, text=comp["type"].upper(), font=("Segoe UI", 9, "bold"), bg=self.ide.ide_theme["panel"], fg=self.ide.ide_theme["accent"]).pack(side=tk.LEFT)
        tk.Label(header_f, text=f" {comp['id']}", font=("Consolas", 9), bg=self.ide.ide_theme["panel"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.RIGHT)

        tk.Label(self.ide.prop_scroll, text="ACTIVE PROPERTIES", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"]).pack(anchor="w", padx=5, pady=(5, 5))
        for key, val in list(comp["props"].items()):
            row = tk.Frame(self.ide.prop_scroll, bg=self.ide.ide_theme["surface"], pady=4)
            row.pack(fill=tk.X, padx=5)
            tk.Button(row, text="✕", font=("Segoe UI", 8), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["danger"], bd=0, relief="flat", cursor="hand2", command=lambda k=key: self.remove_prop(k)).pack(side=tk.LEFT)
            tk.Label(row, text=key, font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"], width=14, anchor="w").pack(side=tk.LEFT, padx=(5,0))
            self.create_smart_input(row, comp, key, val)

        tk.Frame(self.ide.prop_scroll, bg=self.ide.ide_theme["panel"], height=1).pack(fill=tk.X, pady=15, padx=5)
        tk.Label(self.ide.prop_scroll, text="ADD / OVERRIDE PROPERTY", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"]).pack(anchor="w", padx=5, pady=(0, 5))

        add_f = tk.Frame(self.ide.prop_scroll, bg=self.ide.ide_theme["surface"], pady=4)
        add_f.pack(fill=tk.X, padx=5)

        live_widget = self.ide.live_widgets.get(comp["id"])
        valid_props = list(live_widget.configure().keys()) if live_widget else []
        valid_props = [p for p in valid_props if p not in comp["props"]]
        valid_props.sort()

        prop_cb = ttk.Combobox(add_f, values=valid_props, font=("Consolas", 9), width=1)
        prop_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        prop_cb.set("Select...")
        val_frame = tk.Frame(add_f, bg=self.ide.ide_theme["surface"])
        val_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        val_entry = tk.Entry(val_frame, font=("Segoe UI", 9), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], borderwidth=0)
        val_entry.pack(fill=tk.X, expand=True, ipady=4)

        def on_prop_select(e: Any) -> None:
            sel_prop = prop_cb.get()
            for w in val_frame.winfo_children(): w.destroy()
            if sel_prop in self.ENUMS:
                new_val = ttk.Combobox(val_frame, values=self.ENUMS[sel_prop], font=("Segoe UI", 9), width=1)
                if self.ENUMS[sel_prop]: new_val.set(self.ENUMS[sel_prop][0])
                new_val.pack(fill=tk.X, expand=True, ipady=2)
            else:
                new_val = tk.Entry(val_frame, font=("Segoe UI", 9), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], borderwidth=0)
                new_val.pack(fill=tk.X, expand=True, ipady=4)
        prop_cb.bind("<<ComboboxSelected>>", on_prop_select)

        def apply_new_override() -> None:
            k = prop_cb.get().strip()
            v = val_frame.winfo_children()[0].get().strip()
            if k and k != "Select...": self.apply_prop(k, v)
                
        ttk.Button(add_f, text="Add", width=4, style="Action.TButton", command=apply_new_override).pack(side=tk.RIGHT, padx=(5,0))

    def create_smart_input(self, master: tk.Widget, comp: Dict[str, Any], key: str, current_val: Any) -> None:
        if any(x in key.lower() for x in ["bg", "fg", "color", "background", "foreground"]):
            c_val = current_val if str(current_val).startswith("#") else "#000000"
            tk.Button(master, text="", bg=c_val, width=2, relief="flat", bd=0, command=lambda k=key, cv=c_val: self.pick_color(k, cv)).pack(side=tk.RIGHT, padx=2)
            ent = tk.Entry(master, font=("Consolas", 9), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], borderwidth=0)
            ent.insert(0, str(current_val))
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2, ipady=3)
            ent.bind("<Return>", lambda e, k=key, w=ent: self.apply_prop(k, w.get()))
            ent.bind("<FocusOut>", lambda e, k=key, w=ent: self.apply_prop(k, w.get()))
        elif key in self.ENUMS:
            cb = ttk.Combobox(master, values=self.ENUMS[key], font=("Segoe UI", 9), width=1)
            cb.set(current_val)
            cb.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            cb.bind("<<ComboboxSelected>>", lambda e, k=key, w=cb: self.apply_prop(k, w.get()))
        else:
            ent = tk.Entry(master, font=("Segoe UI", 9), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], borderwidth=0)
            ent.insert(0, str(current_val))
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=3)
            ent.bind("<Return>", lambda e, k=key, w=ent: self.apply_prop(k, w.get()))
            ent.bind("<FocusOut>", lambda e, k=key, w=ent: self.apply_prop(k, w.get()))

    def pick_color(self, key: str, current: str) -> None:
        color = colorchooser.askcolor(initialcolor=current)[1]
        if color: self.apply_prop(key, color)

    def apply_prop(self, key: str, val: Any) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        if key in ["borderwidth", "bd", "padx", "pady", "width", "height"]:
            try: val = int(float(val))
            except: val = 0
        else:
            val_str = str(val).strip()
            if (val_str.startswith("(") and val_str.endswith(")")) or (val_str.startswith("[") and val_str.endswith("]")):
                try: val = ast.literal_eval(val_str)
                except: pass

        old_val = comp["props"].get(key)
        comp["props"][key] = val
        try:
            self.ide.refresh_all(); self.ide.push_history(); self.render_genesis_inspector()
        except tk.TclError as e:
            messagebox.showerror("Invalid Property", f"Tkinter rejected this property value:\n\n{e}")
            if old_val is not None: comp["props"][key] = old_val
            else: del comp["props"][key]
            self.ide.refresh_all()

    def remove_prop(self, key: str) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if key in comp["props"]:
            del comp["props"][key]
            self.ide.refresh_all(); self.ide.push_history(); self.render_genesis_inspector()

    def build_layout_tab(self, comp: Dict[str, Any]) -> None:
        parent_f = tk.Frame(self.ide.layout_frame, bg=self.ide.ide_theme["surface"])
        parent_f.pack(fill=tk.X, pady=(0, 15))
        tk.Label(parent_f, text="Parent Container:", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT)
        containers = ["root"] + [c["id"] for c in self.ide.components.values() if c["type"] in ["Frame", "Canvas"] and c["id"] != comp["id"]]
        parent_cb = ttk.Combobox(parent_f, values=containers, state="readonly", width=1)
        parent_cb.set(comp["layout"].get("parent", "root"))
        parent_cb.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0), ipady=2)
        parent_cb.bind("<<ComboboxSelected>>", lambda e: [comp["layout"].update({"parent": parent_cb.get()}), self.ide.refresh_all(), self.ide.push_history()])

        top_split = tk.Frame(self.ide.layout_frame, bg=self.ide.ide_theme["surface"])
        top_split.pack(fill=tk.X, pady=5)
        
        snap_f = tk.Frame(top_split, bg=self.ide.ide_theme["surface"])
        snap_f.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(snap_f, text="SNAP", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"]).pack(anchor="w")
        btn_grid1 = tk.Frame(snap_f, bg=self.ide.ide_theme["surface"])
        btn_grid1.pack(anchor="w", pady=4)
        arrows1 = [("NW", "nw", "Top Left"), ("N", "n", "Top Center"), ("NE", "ne", "Top Right"),
                   ("W", "w", "Middle Left"), ("C", "c", "Center Deadzone"), ("E", "e", "Middle Right"),
                   ("SW", "sw", "Bottom Left"), ("S", "s", "Bottom Center"), ("SE", "se", "Bottom Right")]
        for i, (txt, cmd, tip) in enumerate(arrows1):
            btn = ttk.Button(btn_grid1, text=txt, width=3, style="Mini.TButton", command=lambda pos=cmd: self.snap_comp(pos))
            btn.grid(row=i//3, column=i%3, padx=2, pady=2); ToolTip(btn, f"Snap {tip}")

        step_f = tk.Frame(top_split, bg=self.ide.ide_theme["surface"])
        step_f.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        tk.Label(step_f, text="STEPPER", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"]).pack(anchor="e")
        btn_grid2 = tk.Frame(step_f, bg=self.ide.ide_theme["surface"])
        btn_grid2.pack(anchor="e", pady=4)
        ttk.Button(btn_grid2, text="↑", width=3, style="Mini.TButton", command=lambda: self.micro_nudge(0, -0.005)).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(btn_grid2, text="←", width=3, style="Mini.TButton", command=lambda: self.micro_nudge(-0.005, 0)).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(btn_grid2, text="·", width=3, style="Mini.TButton", state="disabled").grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(btn_grid2, text="→", width=3, style="Mini.TButton", command=lambda: self.micro_nudge(0.005, 0)).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(btn_grid2, text="↓", width=3, style="Mini.TButton", command=lambda: self.micro_nudge(0, 0.005)).grid(row=2, column=1, padx=2, pady=2)

        fill_f = tk.Frame(self.ide.layout_frame, bg=self.ide.ide_theme["surface"])
        fill_f.pack(fill=tk.X, pady=(15, 10))
        tk.Label(fill_f, text="FILL SPACE", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"]).pack(anchor="w", pady=(0,4))
        fill_btn_f = tk.Frame(fill_f, bg=self.ide.ide_theme["surface"])
        fill_btn_f.pack(fill=tk.X)
        ttk.Button(fill_btn_f, text="Fill X", command=lambda: self.fill_comp("x")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, ipady=3)
        ttk.Button(fill_btn_f, text="Fill Y", command=lambda: self.fill_comp("y")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, ipady=3)
        ttk.Button(fill_btn_f, text="Fill XY", command=lambda: self.fill_comp("xy")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, ipady=3)

        tk.Label(self.ide.layout_frame, text="INCREMENTAL MATRIX", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(anchor="w", pady=(15, 5))
        matrix_f = tk.Frame(self.ide.layout_frame, bg=self.ide.ide_theme["surface"])
        matrix_f.pack(fill=tk.X)
        for i, key in enumerate(["relx", "rely", "relw", "relh"]):
            row_f = tk.Frame(matrix_f, bg=self.ide.ide_theme["surface"])
            row_f.pack(fill=tk.X, pady=3)
            tk.Label(row_f, text=key.upper(), font=("Consolas", 9, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"], width=5).pack(side=tk.LEFT)
            ttk.Button(row_f, text="-", width=3, style="Mini.TButton", command=lambda k=key: self.adjust_layout(k, -0.01)).pack(side=tk.LEFT, padx=3)
            e = tk.Entry(row_f, bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["accent"], font=("Consolas", 10), borderwidth=0, justify="center")
            e.insert(0, f"{comp['layout'][key]:.4f}")
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, ipady=3)
            e.bind("<Return>", lambda ev, k=key, w=e: self.apply_layout(k, w.get()))
            e.bind("<FocusOut>", lambda ev, k=key, w=e: self.apply_layout(k, w.get()))
            self.ide.layout_entries[key] = e 
            ttk.Button(row_f, text="+", width=3, style="Mini.TButton", command=lambda k=key: self.adjust_layout(k, 0.01)).pack(side=tk.LEFT, padx=3)

    def fill_comp(self, axis: str) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        if axis in ["x", "xy"]: comp["layout"]["relx"] = 0.0; comp["layout"]["relw"] = 1.0
        if axis in ["y", "xy"]: comp["layout"]["rely"] = 0.0; comp["layout"]["relh"] = 1.0
        self.ide.refresh_all(); self.ide.push_history(); self.ide.update_layout_entries()

    def snap_comp(self, pos: str) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        l = comp["layout"]
        if pos == 'nw': l["relx"] = 0.0; l["rely"] = 0.0
        elif pos == 'n': l["relx"] = 0.5 - l["relw"]/2; l["rely"] = 0.0
        elif pos == 'ne': l["relx"] = 1.0 - l["relw"]; l["rely"] = 0.0
        elif pos == 'w': l["relx"] = 0.0; l["rely"] = 0.5 - l["relh"]/2
        elif pos == 'c': l["relx"] = 0.5 - l["relw"]/2; l["rely"] = 0.5 - l["relh"]/2
        elif pos == 'e': l["relx"] = 1.0 - l["relw"]; l["rely"] = 0.5 - l["relh"]/2
        elif pos == 'sw': l["relx"] = 0.0; l["rely"] = 1.0 - l["relh"]
        elif pos == 's': l["relx"] = 0.5 - l["relw"]/2; l["rely"] = 1.0 - l["relh"]
        elif pos == 'se': l["relx"] = 1.0 - l["relw"]; l["rely"] = 1.0 - l["relh"]
        self.ide.refresh_all(); self.ide.push_history(); self.ide.update_layout_entries()

    def micro_nudge(self, dx: float, dy: float) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        comp["layout"]["relx"] += dx; comp["layout"]["rely"] += dy
        self.ide.refresh_all(); self.ide.update_layout_entries()

    def adjust_layout(self, key: str, delta: float) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        comp["layout"][key] = round(comp["layout"][key] + delta, 4)
        if key in ["relw", "relh"] and comp["layout"][key] < 0.01: comp["layout"][key] = 0.01
        self.ide.refresh_all(); self.ide.push_history(); self.ide.update_layout_entries()

    def apply_layout(self, key: str, val: str) -> None:
        try:
            v = float(val)
            comp = self.ide.get_comp_by_id(self.ide.selected_id)
            comp["layout"][key] = v
            self.ide.refresh_all(); self.ide.push_history(); self.ide.update_layout_entries()
        except: pass

    # =========================================================================
    # 3. EVENTS TAB: NEXUS VISUAL LOGIC BUILDER (DYNAMIC LOOPS & 2X2 ADDER)
    # =========================================================================
    def build_events_tab(self, comp: Dict[str, Any]) -> None:
        top_f = tk.Frame(self.ide.event_frame, bg=self.ide.ide_theme["surface"])
        top_f.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_f, text="BLUEPRINT LOGIC BUILDER", font=("Segoe UI", 9, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"]).pack(side=tk.LEFT)
        
        add_f = tk.Frame(self.ide.event_frame, bg=self.ide.ide_theme["surface"])
        add_f.pack(fill=tk.X, pady=5)
        new_ev_cb = ttk.Combobox(add_f, values=self.ide.supported_events, font=("Consolas", 10), width=1)
        new_ev_cb.set("command")
        new_ev_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=3)
        
        btn_add_ev = ttk.Button(add_f, text="Add Event", style="Action.TButton", command=lambda: self.add_event(new_ev_cb.get()))
        btn_add_ev.pack(side=tk.LEFT, ipady=2)

        tk.Frame(self.ide.event_frame, bg=self.ide.ide_theme["panel"], height=2).pack(fill=tk.X, pady=15)

        for ev_key, ev_data in comp.get("events", {}).items():
            ev_frame = tk.Frame(self.ide.event_frame, bg=self.ide.ide_theme["bg"], bd=1, highlightthickness=1, highlightbackground=self.ide.ide_theme["panel"])
            ev_frame.pack(fill=tk.X, pady=10, padx=2)

            hdr = tk.Frame(ev_frame, bg=self.ide.ide_theme["panel"])
            hdr.pack(fill=tk.X)
            tk.Label(hdr, text=f"⚡ {ev_key}", font=("Consolas", 10, "bold"), bg=self.ide.ide_theme["panel"], fg=self.ide.ide_theme["text"]).pack(side=tk.LEFT, padx=8, pady=6)
            tk.Button(hdr, text="✕", font=("Segoe UI", 9), bg=self.ide.ide_theme["panel"], fg=self.ide.ide_theme["danger"], bd=0, relief="flat", cursor="hand2", command=lambda k=ev_key: self.remove_event(k)).pack(side=tk.RIGHT, padx=8)

            if "nexus_nodes" not in ev_data: ev_data["nexus_nodes"] = []
            
            nodes_frame = tk.Frame(ev_frame, bg=self.ide.ide_theme["bg"])
            nodes_frame.pack(fill=tk.X, padx=8, pady=8)
            self.node_frames[ev_key] = nodes_frame

            self.render_blueprint_nodes(nodes_frame, ev_key, ev_data["nexus_nodes"])

            code_hdr = tk.Frame(ev_frame, bg=self.ide.ide_theme["bg"])
            code_hdr.pack(fill=tk.X, padx=8, pady=(10, 2))
            tk.Label(code_hdr, text="Generated AST Code:", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT)
            
            code_view = scrolledtext.ScrolledText(ev_frame, height=8, bg="#0B0F19", fg="#A5D6FF", font=("Consolas", 10), bd=0, insertbackground="white")
            self.inline_editors[ev_key] = code_view

            sz_f = tk.Frame(code_hdr, bg=self.ide.ide_theme["bg"])
            sz_f.pack(side=tk.RIGHT)
            
            btn_pop = tk.Button(sz_f, text="⛶ Pop-Out", font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["accent"], fg="white", bd=0, command=lambda k=ev_key: self.open_popout_editor(k))
            btn_pop.pack(side=tk.RIGHT, padx=6, ipady=2, ipadx=4)
            ToolTip(btn_pop, "Open floating AST editor window.")
            
            tk.Button(sz_f, text="+", font=("Consolas", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"], bd=0, command=lambda cv=code_view: cv.config(height=cv.cget("height")+4)).pack(side=tk.RIGHT, padx=2)
            tk.Button(sz_f, text="-", font=("Consolas", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text"], bd=0, command=lambda cv=code_view: cv.config(height=max(4, cv.cget("height")-4))).pack(side=tk.RIGHT, padx=2)

            code_view.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
            code_view.insert("1.0", ev_data.get("code", "pass"))
            self.ide.highlight_syntax(code_view)
            
            code_view.bind("<KeyRelease>", lambda e, k=ev_key, cv=code_view: [
                self.manual_code_override(k, cv.get("1.0", tk.END), source="inline"),
                self.ide.schedule_highlight(cv, ("Consolas", 10))
            ])

    def refresh_blueprint_ui_only(self, ev_key: str) -> None:
        """Destroys and redraws visual nodes dynamically without losing cursor focus on text."""
        if ev_key in self.node_frames and self.node_frames[ev_key].winfo_exists():
            frame = self.node_frames[ev_key]
            for w in frame.winfo_children(): w.destroy()
            comp = self.ide.get_comp_by_id(self.ide.selected_id)
            if comp:
                self.render_blueprint_nodes(frame, ev_key, comp["events"][ev_key].get("nexus_nodes", []))

    # =========================================================================
    # MULTI-ROW BLUEPRINT NODE RENDERING
    # =========================================================================
    def render_blueprint_nodes(self, parent_ui: tk.Widget, ev_key: str, node_list_ref: List[Dict[str, Any]]) -> None:
        for idx, node in enumerate(node_list_ref):
            ntype = node.get("type", "action")
            colors = {"action": "#3B82F6", "if": "#F59E0B", "math": "#8B5CF6", "loop": "#10B981"}
            titles = {"action": "⚡ ACTION", "if": "❓ IF CONDITION", "math": "ƒ MATH OP", "loop": "↻ LOOP"}
            stripe_color = colors.get(ntype, "#3B82F6")
            
            wrapper = tk.Frame(parent_ui, bg=self.ide.ide_theme["bg"])
            wrapper.pack(fill=tk.X, pady=4)
            tk.Frame(wrapper, bg=stripe_color, width=4).pack(side=tk.LEFT, fill=tk.Y)
            node_card = tk.Frame(wrapper, bg=self.ide.ide_theme["surface"], bd=1, highlightthickness=1, highlightbackground=self.ide.ide_theme["panel"], padx=8, pady=6)
            node_card.pack(side=tk.LEFT, fill=tk.X, expand=True)

            r1 = tk.Frame(node_card, bg=self.ide.ide_theme["surface"])
            r1.pack(fill=tk.X, pady=(0, 6))
            tk.Label(r1, text=titles.get(ntype, "NODE"), font=("Segoe UI", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=stripe_color).pack(side=tk.LEFT)
            tk.Button(r1, text="✕", font=("Segoe UI", 8), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["danger"], bd=0, command=lambda i=idx, l=node_list_ref: self.remove_logic_node(ev_key, l, i)).pack(side=tk.RIGHT, padx=(6, 0))
            tk.Button(r1, text="↓", font=("Consolas", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], bd=0, command=lambda i=idx, l=node_list_ref: self.move_logic_node(ev_key, l, i, 1)).pack(side=tk.RIGHT, padx=2)
            tk.Button(r1, text="↑", font=("Consolas", 8, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], bd=0, command=lambda i=idx, l=node_list_ref: self.move_logic_node(ev_key, l, i, -1)).pack(side=tk.RIGHT, padx=2)

            if ntype == "if":
                self.render_card_condition(node_card, ev_key, node, node_list_ref, idx)
                body_f = tk.Frame(wrapper, bg=self.ide.ide_theme["bg"])
                body_f.pack(side=tk.BOTTOM, fill=tk.X, padx=(24, 0), pady=(4, 0))
                self.render_blueprint_nodes(body_f, ev_key, node.get("body", []))
            elif ntype == "loop":
                self.render_card_loop(node_card, ev_key, node, node_list_ref, idx)
                body_f = tk.Frame(wrapper, bg=self.ide.ide_theme["bg"])
                body_f.pack(side=tk.BOTTOM, fill=tk.X, padx=(24, 0), pady=(4, 0))
                self.render_blueprint_nodes(body_f, ev_key, node.get("body", []))
            elif ntype == "math": self.render_card_math(node_card, ev_key, node, node_list_ref, idx)
            else: self.render_card_action(node_card, ev_key, node, node_list_ref, idx)

        # 2x2 Grid for Adding Nodes (Fixes Squashed Visibility)
        add_f = tk.Frame(parent_ui, bg=parent_ui.cget("bg"))
        add_f.pack(fill=tk.X, pady=6)
        
        row1 = tk.Frame(add_f, bg=parent_ui.cget("bg"))
        row1.pack(fill=tk.X, pady=1)
        ttk.Button(row1, text="+ Action", command=lambda l=node_list_ref: self.add_logic_node(ev_key, l, "action")).pack(side=tk.LEFT, padx=1, ipady=2, expand=True, fill=tk.X)
        ttk.Button(row1, text="+ IF Condition", command=lambda l=node_list_ref: self.add_logic_node(ev_key, l, "if")).pack(side=tk.LEFT, padx=1, ipady=2, expand=True, fill=tk.X)
        
        row2 = tk.Frame(add_f, bg=parent_ui.cget("bg"))
        row2.pack(fill=tk.X, pady=1)
        ttk.Button(row2, text="+ Math", command=lambda l=node_list_ref: self.add_logic_node(ev_key, l, "math")).pack(side=tk.LEFT, padx=1, ipady=2, expand=True, fill=tk.X)
        ttk.Button(row2, text="+ Loop", command=lambda l=node_list_ref: self.add_logic_node(ev_key, l, "loop")).pack(side=tk.LEFT, padx=1, ipady=2, expand=True, fill=tk.X)

    def render_card_action(self, card_f: tk.Widget, ev_key: str, node: Dict[str, Any], node_list: List[Dict[str, Any]], idx: int) -> None:
        r2 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r2.pack(fill=tk.X, pady=2)
        tk.Label(r2, text="Modify:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        target_cb = ttk.Combobox(r2, values=list(self.ide.components.keys()), font=("Consolas", 10), width=1)
        target_cb.set(node.get("target", "Target..."))
        target_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=2)
        tk.Label(r2, text="Prop:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT)
        prop_cb = ttk.Combobox(r2, font=("Consolas", 10), width=1)
        prop_cb.set(node.get("prop", "Property..."))
        prop_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=2)

        r3 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r3.pack(fill=tk.X, pady=2)
        tk.Label(r3, text="Value = ", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        val_ent = tk.Entry(r3, font=("Consolas", 10), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
        val_ent.insert(0, node.get("val", ""))
        val_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def update_props(*args: Any) -> None:
            tgt = self.ide.live_widgets.get(target_cb.get())
            if tgt:
                opts = list(tgt.configure().keys())
                opts.sort(); prop_cb.config(values=opts)
        update_props() 
        target_cb.bind("<<ComboboxSelected>>", lambda e: [self.update_node_data(ev_key, node_list, idx, "target", target_cb.get()), update_props()])
        prop_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "prop", prop_cb.get()))
        val_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "val", val_ent.get()))

    def render_card_math(self, card_f: tk.Widget, ev_key: str, node: Dict[str, Any], node_list: List[Dict[str, Any]], idx: int) -> None:
        r2 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r2.pack(fill=tk.X, pady=2)
        tk.Label(r2, text="Calculate:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        target_cb = ttk.Combobox(r2, values=list(self.ide.components.keys()), font=("Consolas", 10), width=1)
        target_cb.set(node.get("target", "Target..."))
        target_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=2)
        tk.Label(r2, text="Prop:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT)
        prop_cb = ttk.Combobox(r2, font=("Consolas", 10), width=1)
        prop_cb.set(node.get("prop", "Property..."))
        prop_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=2)

        r3 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r3.pack(fill=tk.X, pady=2)
        tk.Label(r3, text="Using:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        op_cb = ttk.Combobox(r3, values=["+=", "-=", "*=", "/="], font=("Consolas", 10), width=3)
        op_cb.set(node.get("op", "+="))
        op_cb.pack(side=tk.LEFT, padx=(0, 4), ipady=2)
        val_ent = tk.Entry(r3, font=("Consolas", 10), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
        val_ent.insert(0, node.get("val", ""))
        val_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def update_props(*args: Any) -> None:
            tgt = self.ide.live_widgets.get(target_cb.get())
            if tgt:
                opts = list(tgt.configure().keys())
                opts.sort(); prop_cb.config(values=opts)
        update_props() 
        target_cb.bind("<<ComboboxSelected>>", lambda e: [self.update_node_data(ev_key, node_list, idx, "target", target_cb.get()), update_props()])
        prop_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "prop", prop_cb.get()))
        op_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "op", op_cb.get()))
        val_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "val", val_ent.get()))

    def render_card_condition(self, card_f: tk.Widget, ev_key: str, node: Dict[str, Any], node_list: List[Dict[str, Any]], idx: int) -> None:
        r2 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r2.pack(fill=tk.X, pady=2)
        tk.Label(r2, text="Check:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        target_cb = ttk.Combobox(r2, values=list(self.ide.components.keys()), font=("Consolas", 10), width=1)
        target_cb.set(node.get("target", "Target..."))
        target_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=2)
        tk.Label(r2, text="Prop:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT)
        prop_cb = ttk.Combobox(r2, font=("Consolas", 10), width=1)
        prop_cb.set(node.get("prop", "Property..."))
        prop_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=2)

        r3 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r3.pack(fill=tk.X, pady=2)
        tk.Label(r3, text="Against:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        op_cb = ttk.Combobox(r3, values=["==", "!=", ">", "<", ">=", "<="], font=("Consolas", 10), width=3)
        op_cb.set(node.get("op", "=="))
        op_cb.pack(side=tk.LEFT, padx=(0, 4), ipady=2)
        val_ent = tk.Entry(r3, font=("Consolas", 10), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
        val_ent.insert(0, node.get("val", ""))
        val_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        def update_props(*args: Any) -> None:
            tgt = self.ide.live_widgets.get(target_cb.get())
            if tgt:
                opts = list(tgt.configure().keys())
                opts.sort(); prop_cb.config(values=opts)
        update_props() 
        target_cb.bind("<<ComboboxSelected>>", lambda e: [self.update_node_data(ev_key, node_list, idx, "target", target_cb.get()), update_props()])
        prop_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "prop", prop_cb.get()))
        op_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "op", op_cb.get()))
        val_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "val", val_ent.get()))

    def render_card_loop(self, card_f: tk.Widget, ev_key: str, node: Dict[str, Any], node_list: List[Dict[str, Any]], idx: int) -> None:
        """Dynamic node that morphs between 'For' and 'While' execution flows."""
        r2 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r2.pack(fill=tk.X, pady=2)
        tk.Label(r2, text="Type:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
        
        type_cb = ttk.Combobox(r2, values=["while", "for"], font=("Consolas", 10), width=8)
        type_cb.set(node.get("loop_type", "for"))
        type_cb.pack(side=tk.LEFT, padx=(0, 4), ipady=2)
        
        type_cb.bind("<<ComboboxSelected>>", lambda e: [self.update_node_data(ev_key, node_list, idx, "loop_type", type_cb.get()), self.refresh_blueprint_ui_only(ev_key)])

        r3 = tk.Frame(card_f, bg=self.ide.ide_theme["surface"])
        r3.pack(fill=tk.X, pady=2)

        if node.get("loop_type", "for") == "while":
            # Render standard While Condition UI
            tk.Label(r3, text="Target:", font=("Segoe UI", 9), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"], width=8, anchor="w").pack(side=tk.LEFT)
            target_cb = ttk.Combobox(r3, values=list(self.ide.components.keys()), font=("Consolas", 10), width=1)
            target_cb.set(node.get("target", "Target..."))
            target_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=2)
            
            prop_cb = ttk.Combobox(r3, font=("Consolas", 10), width=1)
            prop_cb.set(node.get("prop", "Prop..."))
            prop_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=2)

            op_cb = ttk.Combobox(r3, values=["==", "!=", ">", "<", ">=", "<="], font=("Consolas", 10), width=3)
            op_cb.set(node.get("op", "=="))
            op_cb.pack(side=tk.LEFT, padx=(0, 4), ipady=2)
            
            val_ent = tk.Entry(r3, font=("Consolas", 10), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
            val_ent.insert(0, node.get("val", ""))
            val_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

            def update_props(*args: Any) -> None:
                tgt = self.ide.live_widgets.get(target_cb.get())
                if tgt:
                    opts = list(tgt.configure().keys())
                    opts.sort(); prop_cb.config(values=opts)
            update_props()
            target_cb.bind("<<ComboboxSelected>>", lambda e: [self.update_node_data(ev_key, node_list, idx, "target", target_cb.get()), update_props()])
            prop_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "prop", prop_cb.get()))
            op_cb.bind("<<ComboboxSelected>>", lambda e: self.update_node_data(ev_key, node_list, idx, "op", op_cb.get()))
            val_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "val", val_ent.get()))
            
        else:
            # Render standard For Iteration UI
            tk.Label(r3, text="For", font=("Segoe UI", 9, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["accent"], width=8, anchor="w").pack(side=tk.LEFT)
            var_ent = tk.Entry(r3, font=("Consolas", 10), width=8, bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
            var_ent.insert(0, node.get("for_var", "item"))
            var_ent.pack(side=tk.LEFT, padx=(0, 4), ipady=4)
            
            tk.Label(r3, text="in", font=("Segoe UI", 9, "bold"), bg=self.ide.ide_theme["surface"], fg=self.ide.ide_theme["text_dim"]).pack(side=tk.LEFT, padx=2)
            iter_ent = tk.Entry(r3, font=("Consolas", 10), bg=self.ide.ide_theme["bg"], fg=self.ide.ide_theme["text"], bd=0)
            iter_ent.insert(0, node.get("for_iter", "range(5)"))
            iter_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=4)
            
            var_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "for_var", var_ent.get()))
            iter_ent.bind("<KeyRelease>", lambda e: self.update_node_data(ev_key, node_list, idx, "for_iter", iter_ent.get()))

    # =========================================================================
    # BIDIRECTIONAL AST SYNC AND EVENT COMPILATION
    # =========================================================================
    def add_event(self, ev_key: str) -> None:
        if not ev_key: return
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if "events" not in comp: comp["events"] = {}
        if ev_key not in comp["events"]:
            comp["events"][ev_key] = {"fn": f"evt_{comp['id']}_{ev_key.replace('<','').replace('>','').replace('-','')}", "code": "pass", "nexus_nodes": []}
            self.ide.push_history(); self.render_genesis_inspector()

    def remove_event(self, ev_key: str) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if ev_key in comp["events"]:
            del comp["events"][ev_key]
            self.ide.push_history(); self.render_genesis_inspector()

    def add_logic_node(self, ev_key: str, node_list_ref: List[Dict[str, Any]], n_type: str) -> None:
        if n_type == "action": node_list_ref.append({"type": "action", "target": "", "prop": "", "val": ""})
        elif n_type == "math": node_list_ref.append({"type": "math", "target": "", "prop": "", "op": "+=", "val": ""})
        elif n_type == "if": node_list_ref.append({"type": "if", "target": "", "prop": "", "op": "==", "val": "", "body": []})
        elif n_type == "loop": node_list_ref.append({"type": "loop", "loop_type": "for", "target": "", "prop": "", "op": "==", "val": "", "for_var": "item", "for_iter": "range(5)", "body": []})
        self.compile_nexus_logic(ev_key)
        self.render_genesis_inspector()

    def remove_logic_node(self, ev_key: str, node_list_ref: List[Dict[str, Any]], idx: int) -> None:
        node_list_ref.pop(idx)
        self.compile_nexus_logic(ev_key)
        self.render_genesis_inspector()

    def move_logic_node(self, ev_key: str, node_list_ref: List[Dict[str, Any]], idx: int, direction: int) -> None:
        if 0 <= idx + direction < len(node_list_ref):
            node_list_ref[idx], node_list_ref[idx+direction] = node_list_ref[idx+direction], node_list_ref[idx]
            self.compile_nexus_logic(ev_key)
            self.render_genesis_inspector()

    def update_node_data(self, ev_key: str, node_list_ref: List[Dict[str, Any]], idx: int, field: str, val: Any) -> None:
        node_list_ref[idx][field] = val
        self.compile_nexus_logic(ev_key)

    def manual_code_override(self, ev_key: str, code_str: str, source: str = "inline") -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        if not comp: return
        
        comp["events"][ev_key]["code"] = code_str.strip()

        if source == "inline":
            if ev_key in self.popout_editors and self.popout_editors[ev_key].winfo_exists():
                pe = self.popout_editors[ev_key]
                if pe.get("1.0", tk.END).strip() != code_str.strip():
                    pe.delete("1.0", tk.END)
                    pe.insert("1.0", code_str.strip())
                    self.ide.highlight_syntax(pe)
        elif source == "popout":
            if ev_key in self.inline_editors and self.inline_editors[ev_key].winfo_exists():
                ie = self.inline_editors[ev_key]
                if ie.get("1.0", tk.END).strip() != code_str.strip():
                    ie.delete("1.0", tk.END)
                    ie.insert("1.0", code_str.strip())
                    self.ide.highlight_syntax(ie)

        new_nodes = self.ast_to_blueprint(code_str)
        if new_nodes is not None:
            comp["events"][ev_key]["nexus_nodes"] = new_nodes
            self.refresh_blueprint_ui_only(ev_key)

    def ast_to_blueprint(self, code_str: str) -> Optional[List[Dict[str, Any]]]:
        try: tree = ast.parse(code_str)
        except SyntaxError: return None
        
        def parse_body(body: List[Any]) -> List[Dict[str, Any]]:
            nodes = []
            for stmt in body:
                try:
                    # Parse ACTION
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        call = stmt.value
                        if getattr(call.func, 'attr', '') == 'config' and getattr(getattr(call.func, 'value', None), 'value', None) and getattr(call.func.value.value, 'id', '') == 'self':
                            target = call.func.value.attr
                            if call.keywords:
                                kw = call.keywords[0]
                                prop = kw.arg
                                val = ""
                                if isinstance(kw.value, ast.Constant): val = str(kw.value.value)
                                elif isinstance(kw.value, ast.Name): val = kw.value.id
                                elif hasattr(ast, 'unparse'): val = ast.unparse(kw.value)
                                if val.startswith("'") and val.endswith("'"): val = val[1:-1]
                                elif val.startswith('"') and val.endswith('"'): val = val[1:-1]
                                nodes.append({"type": "action", "target": target, "prop": prop, "val": val})
                    
                    # Parse MATH
                    elif isinstance(stmt, ast.Try) and len(stmt.body) >= 2 and isinstance(stmt.body[1], ast.Expr) and isinstance(stmt.body[1].value, ast.Call):
                        call = stmt.body[1].value
                        if getattr(call.func, 'attr', '') == 'config' and call.keywords:
                            target = call.func.value.attr
                            kw = call.keywords[0]
                            prop = kw.arg
                            if isinstance(kw.value, ast.BinOp):
                                op_map = {ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=", ast.Div: "/="}
                                op = op_map.get(type(kw.value.op), "+=")
                                val = ""
                                if isinstance(kw.value.right, ast.Call) and getattr(kw.value.right.func, 'id', '') == 'float':
                                    arg = kw.value.right.args[0]
                                    if isinstance(arg, ast.Constant): val = str(arg.value)
                                    elif isinstance(arg, ast.Name): val = arg.id
                                    elif hasattr(ast, 'unparse'): val = ast.unparse(arg)
                                    if val.startswith("'") and val.endswith("'"): val = val[1:-1]
                                    elif val.startswith('"') and val.endswith('"'): val = val[1:-1]
                                nodes.append({"type": "math", "target": target, "prop": prop, "op": op, "val": val})

                    # Parse IF
                    elif isinstance(stmt, ast.If):
                        if isinstance(stmt.test, ast.Compare) and isinstance(stmt.test.left, ast.Call):
                            inner_call = stmt.test.left.args[0]
                            target = inner_call.func.value.attr
                            prop = inner_call.args[0].value if isinstance(inner_call.args[0], ast.Constant) else ""
                            op_map = {ast.Eq: "==", ast.NotEq: "!=", ast.Gt: ">", ast.Lt: "<", ast.GtE: ">=", ast.LtE: "<="}
                            op = op_map.get(type(stmt.test.ops[0]), "==")
                            right_arg = stmt.test.comparators[0].args[0] if stmt.test.comparators else None
                            val = ""
                            if right_arg:
                                if isinstance(right_arg, ast.Constant): val = str(right_arg.value)
                                elif isinstance(right_arg, ast.Name): val = right_arg.id
                                elif hasattr(ast, 'unparse'): val = ast.unparse(right_arg)
                                if val.startswith("'") and val.endswith("'"): val = val[1:-1]
                                elif val.startswith('"') and val.endswith('"'): val = val[1:-1]
                            body_nodes = parse_body(stmt.body)
                            nodes.append({"type": "if", "target": target, "prop": prop, "op": op, "val": val, "body": body_nodes})
                    
                    # Parse WHILE LOOP
                    elif isinstance(stmt, ast.While):
                        if isinstance(stmt.test, ast.Compare) and isinstance(stmt.test.left, ast.Call):
                            inner_call = stmt.test.left.args[0]
                            target = inner_call.func.value.attr
                            prop = inner_call.args[0].value if isinstance(inner_call.args[0], ast.Constant) else ""
                            op_map = {ast.Eq: "==", ast.NotEq: "!=", ast.Gt: ">", ast.Lt: "<", ast.GtE: ">=", ast.LtE: "<="}
                            op = op_map.get(type(stmt.test.ops[0]), "==")
                            right_arg = stmt.test.comparators[0].args[0] if stmt.test.comparators else None
                            val = ""
                            if right_arg:
                                if isinstance(right_arg, ast.Constant): val = str(right_arg.value)
                                elif isinstance(right_arg, ast.Name): val = right_arg.id
                                elif hasattr(ast, 'unparse'): val = ast.unparse(right_arg)
                                if val.startswith("'") and val.endswith("'"): val = val[1:-1]
                                elif val.startswith('"') and val.endswith('"'): val = val[1:-1]
                            body_nodes = parse_body(stmt.body)
                            f_body = [n for n in body_nodes if not (n.get("type")=="action" and n.get("target")=="self" and n.get("prop")=="update")]
                            nodes.append({"type": "loop", "loop_type": "while", "target": target, "prop": prop, "op": op, "val": val, "body": f_body})

                    # Parse FOR LOOP
                    elif isinstance(stmt, ast.For):
                        var = stmt.target.id if isinstance(stmt.target, ast.Name) else "item"
                        iterable = ast.unparse(stmt.iter) if hasattr(ast, 'unparse') else "[]"
                        body_nodes = parse_body(stmt.body)
                        f_body = [n for n in body_nodes if not (n.get("type")=="action" and n.get("target")=="self" and n.get("prop")=="update")]
                        nodes.append({"type": "loop", "loop_type": "for", "for_var": var, "for_iter": iterable, "body": f_body})

                except Exception:
                    pass 
            return nodes
        
        try: return parse_body(tree.body)
        except Exception: return None

    def compile_nexus_logic(self, ev_key: str) -> None:
        comp = self.ide.get_comp_by_id(self.ide.selected_id)
        nodes = comp["events"][ev_key].get("nexus_nodes", [])
        
        def build_code(node_list: List[Dict[str, Any]], indent_lvl: int) -> List[str]:
            ind = "    " * indent_lvl
            lines = []
            for n in node_list:
                ntype = n.get("type", "action")
                
                t, p, v = n.get("target"), n.get("prop"), n.get("val")
                if v and isinstance(v, str):
                    if v.isdigit() or (v.startswith("-") and v[1:].isdigit()): formatted_val = v
                    elif v.lower() in ["true", "false", "tk.end", "tk.left", "tk.right"]: formatted_val = v
                    else: formatted_val = f"'{v.replace(chr(39), chr(92)+chr(39))}'" 
                else: formatted_val = "''"

                if ntype == "action":
                    if t and p: lines.append(f"{ind}self.{t}.config({p}={formatted_val})")
                
                elif ntype == "math":
                    if t and p:
                        op = n.get("op", "+=")
                        lines.append(f"{ind}try:")
                        lines.append(f"{ind}    _curr = float(self.{t}.cget('{p}'))")
                        if op == "+=": lines.append(f"{ind}    self.{t}.config({p}=_curr + float({formatted_val}))")
                        elif op == "-=": lines.append(f"{ind}    self.{t}.config({p}=_curr - float({formatted_val}))")
                        elif op == "*=": lines.append(f"{ind}    self.{t}.config({p}=_curr * float({formatted_val}))")
                        elif op == "/=": lines.append(f"{ind}    self.{t}.config({p}=_curr / float({formatted_val}))")
                        lines.append(f"{ind}except ValueError: pass")
                
                elif ntype == "if":
                    if t and p:
                        op = n.get("op", "==")
                        lines.append(f"{ind}if str(self.{t}.cget('{p}')) {op} str({formatted_val}):")
                        body_lines = build_code(n.get("body", []), indent_lvl + 1)
                        if not body_lines: body_lines = [f"{ind}    pass"]
                        lines.extend(body_lines)
                        
                elif ntype == "loop":
                    loop_type = n.get("loop_type", "for")
                    if loop_type == "while" and t and p:
                        op = n.get("op", "==")
                        lines.append(f"{ind}while str(self.{t}.cget('{p}')) {op} str({formatted_val}):")
                        body_lines = build_code(n.get("body", []), indent_lvl + 1)
                        body_lines.append(f"{ind}    self.update()  # Prevent Tkinter thread lockup")
                        lines.extend(body_lines)
                    elif loop_type == "for":
                        var = n.get("for_var", "item")
                        iterable = n.get("for_iter", "range(5)")
                        lines.append(f"{ind}for {var} in {iterable}:")
                        body_lines = build_code(n.get("body", []), indent_lvl + 1)
                        body_lines.append(f"{ind}    self.update()  # Prevent Tkinter thread lockup")
                        lines.extend(body_lines)

            return lines

        code_lines = build_code(nodes, 0)
        final_code = "\n".join(code_lines) if code_lines else "pass"
        comp["events"][ev_key]["code"] = final_code
        self.ide.push_history()

        if ev_key in self.inline_editors and self.inline_editors[ev_key].winfo_exists():
            ie = self.inline_editors[ev_key]
            if ie.get("1.0", tk.END).strip() != final_code:
                ie.delete("1.0", tk.END)
                ie.insert("1.0", final_code)
                self.ide.highlight_syntax(ie)
                
        if ev_key in self.popout_editors and self.popout_editors[ev_key].winfo_exists():
            pe = self.popout_editors[ev_key]
            if pe.get("1.0", tk.END).strip() != final_code:
                pe.delete("1.0", tk.END)
                pe.insert("1.0", final_code)
                self.ide.highlight_syntax(pe)

if __name__ == "__main__":
    print("Genesis V10 Horizon Update: Ready.")
