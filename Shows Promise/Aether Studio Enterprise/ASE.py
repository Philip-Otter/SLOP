# ==============================================================================
# AETHER STUDIO ENTERPRISE V37 - REACTIVE GUI ARCHITECT
# Upgrades: 9-Way Anchors, Ref Injector, RegEx Code Shielding, Generator Fixes
# ==============================================================================
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, colorchooser
import json
import os
import re
import copy
import datetime
import uuid

# --- ENHANCED WIDGET MAPPER ---
WIDGET_MAP = {
    "Frame": {"icon": "🔲", "class": tk.Frame, "module": "tk", "props": {"bg": "app_surface", "bd": 1, "relief": "solid", "cursor": "arrow"}},
    "Label": {"icon": "🏷️", "class": tk.Label, "module": "tk", "props": {"text": "Label", "bg": "app_surface", "fg": "app_text", "font": ("Segoe UI", 10, "normal"), "bd": 0, "relief": "flat"}},
    "Button": {"icon": "🔘", "class": tk.Button, "module": "tk", "props": {"text": "Button", "bg": "app_accent", "fg": "app_accent_fg", "font": ("Segoe UI", 10, "bold"), "bd": 0, "relief": "flat", "cursor": "hand2"}},
    "Entry": {"icon": "⌨️", "class": tk.Entry, "module": "tk", "props": {"bg": "app_input", "fg": "app_text", "font": ("Segoe UI", 10, "normal"), "bd": 1, "relief": "solid", "insertbackground": "app_text"}},
    "Text": {"icon": "📄", "class": tk.Text, "module": "tk", "props": {"bg": "app_input", "fg": "app_text", "font": ("Consolas", 10, "normal"), "bd": 1, "relief": "solid", "insertbackground": "app_text", "text": ""}},
    "Checkbutton": {"icon": "☑️", "class": tk.Checkbutton, "module": "tk", "props": {"text": "Checkbox", "bg": "app_surface", "fg": "app_text", "activebackground": "app_surface", "activeforeground": "app_accent"}},
    "Canvas": {"icon": "🎨", "class": tk.Canvas, "module": "tk", "props": {"bg": "app_surface", "bd": 1, "relief": "sunken", "highlightthickness": 0}},
    "Scale": {"icon": "🎚️", "class": tk.Scale, "module": "tk", "props": {"orient": "horizontal", "bg": "app_surface", "fg": "app_accent", "bd": 0, "highlightthickness": 0}},
    "Progressbar": {"icon": "🔋", "class": ttk.Progressbar, "module": "ttk", "props": {"orient": "horizontal", "mode": "determinate", "value": 50}},
    "Combobox": {"icon": "🔽", "class": ttk.Combobox, "module": "ttk", "props": {"values": "Option 1, Option 2, Option 3", "state": "readonly", "font": ("Segoe UI", 10, "normal")}},
    "Image": {"icon": "🖼️", "class": tk.Label, "module": "tk", "props": {"image_path": "", "text": "[ No Image Selected ]", "bg": "app_surface", "fg": "app_text"}},
    "Console": {"icon": "🖥️", "class": scrolledtext.ScrolledText, "module": "scrolledtext", "props": {"bg": "#000000", "fg": "#00ff00", "font": ("Consolas", 9, "normal"), "state": "normal", "text": "System Ready..."}}
}

THEMES = {
    "Studio Light": {"bg": "#f3f3f3", "sidebar": "#ffffff", "surface": "#ffffff", "panel": "#f8f9fa", "text": "#242424", "text_dim": "#6e6e6e", "accent": "#005fb8", "accent_hover": "#004a94", "danger": "#c42b1c", "grid": "#e0e0e0"},
    "Studio Dark": {"bg": "#1e1e1e", "sidebar": "#252526", "surface": "#2d2d30", "panel": "#3e3e42", "text": "#f1f1f1", "text_dim": "#a0a0a0", "accent": "#007acc", "accent_hover": "#0098ff", "danger": "#f14c4c", "grid": "#404040"},
    "High Contrast": {"bg": "#000000", "sidebar": "#000000", "surface": "#000000", "panel": "#1a1a1a", "text": "#ffffff", "text_dim": "#ffff00", "accent": "#00ff00", "accent_hover": "#00cc00", "danger": "#ff0000", "grid": "#ffffff"}
}

class HoverTooltip:
    def __init__(self, widget, text):
        self.widget = widget; self.text = text; self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        if not self.widget.winfo_exists(): return
        x, y = self.widget.winfo_rootx() + 25, self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip, text=self.text, background="#ffffe0", foreground="#000000", relief="solid", borderwidth=1, font=("Segoe UI", 8), padx=4, pady=2).pack()

    def leave(self, event=None):
        if self.tooltip: self.tooltip.destroy(); self.tooltip = None

class ToolbarButton(tk.Button):
    def __init__(self, master, hover_text="", **kw):
        self.default_bg = kw.pop('bg', '#f3f3f3')
        self.hover_bg = kw.pop('hover_bg', '#e0e0e0')
        super().__init__(master, bg=self.default_bg, activebackground=self.hover_bg, **kw)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        if hover_text: HoverTooltip(self, hover_text)

    def on_enter(self, e): self['bg'] = self.hover_bg
    def on_leave(self, e): self['bg'] = self.default_bg

class AetherEnterpriseIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Aether Studio Enterprise V37")
        self.root.geometry("1600x900")
        
        self.current_theme_name = "Studio Light"
        self.ide_theme = THEMES[self.current_theme_name]
        self.app_theme = {"app_bg": "#f0f2f5", "app_surface": "#ffffff", "app_input": "#ffffff", "app_text": "#212529", "app_accent": "#0d6efd", "app_accent_fg": "#ffffff"}

        self.metadata = {"name": "EnterpriseApp", "author": "Developer", "width": 1000, "height": 700, "grid_size": 0.05, "show_grid": True}
        self.components = []
        self.live_widgets = {}
        self.image_cache = {} 
        self.selected_id = None
        self.drag_data = {"x": 0, "y": 0, "active": False}
        self.current_project_file = None
        self.custom_templates = self.load_custom_templates()
        
        self.user_code = {"imports": "import os\nfrom tkinter import filedialog", "init": "        # Custom startup logic here", "methods": "    def custom_helper(self):\n        pass"}
        self.history = []
        self.history_index = -1

        self.setup_ide_styles()
        self.setup_menu()
        self.setup_ui()
        self.push_history() 

    def load_custom_templates(self):
        try:
            if os.path.exists("aether_templates.json"):
                with open("aether_templates.json", "r") as f: return json.load(f)
        except Exception: pass
        return {}

    def save_custom_templates(self):
        with open("aether_templates.json", "w") as f: json.dump(self.custom_templates, f, indent=4)

    def highlight_syntax(self, target_widget, base_font=("Consolas", 10)):
        if not isinstance(target_widget, (tk.Text, scrolledtext.ScrolledText)): return
        code = target_widget.get("1.0", tk.END)
        target_widget.tag_configure("kw", foreground="#569cd6", font=(base_font[0], base_font[1], "bold"))
        target_widget.tag_configure("str", foreground="#ce9178")
        target_widget.tag_configure("cmt", foreground="#6a9955")
        for t in ["kw", "str", "cmt"]: target_widget.tag_remove(t, "1.0", tk.END)
        for m in re.finditer(r'#.*', code): target_widget.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'(["\'])(?:(?=(\\?))\2.)*?\1', code): target_widget.tag_add("str", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        keywords = r'\b(def|class|self|import|from|return|pass|if|else|elif|try|except|print|for|while|in|and|or|not)\b'
        for m in re.finditer(keywords, code): target_widget.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def schedule_highlight(self, widget, font):
        if hasattr(widget, "_hlt_timer"): self.root.after_cancel(widget._hlt_timer)
        widget._hlt_timer = self.root.after(250, lambda: self.highlight_syntax(widget, font))

    def push_history(self):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(copy.deepcopy(self.components))
        self.history_index += 1
        if len(self.history) > 30: 
            self.history.pop(0)
            self.history_index -= 1
        self.update_chronos_ui()

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.components = copy.deepcopy(self.history[self.history_index])
            self.refresh_all(); self.update_chronos_ui(); self.render_inspector()

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.components = copy.deepcopy(self.history[self.history_index])
            self.refresh_all(); self.update_chronos_ui(); self.render_inspector()

    def update_chronos_ui(self):
        if hasattr(self, 'btn_undo'):
            c_on, c_off = self.ide_theme["text"], self.ide_theme["text_dim"]
            self.btn_undo.config(fg=c_on if self.history_index > 0 else c_off)
            self.btn_redo.config(fg=c_on if self.history_index < len(self.history)-1 else c_off)

    def change_ide_theme(self, theme_name):
        self.current_theme_name = theme_name
        self.ide_theme = THEMES[theme_name]
        self.root.configure(bg=self.ide_theme["bg"])
        self.setup_ide_styles()
        self.setup_ui()
        self.refresh_all()
        self.draw_grid()

    def setup_ide_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TPanedwindow", background=self.ide_theme["bg"])
        style.configure("Treeview", background=self.ide_theme["surface"], foreground=self.ide_theme["text"], fieldbackground=self.ide_theme["surface"], borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.ide_theme["panel"], foreground=self.ide_theme["accent"], font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", self.ide_theme["accent"])], foreground=[("selected", "#ffffff")])
        style.configure("TNotebook", background=self.ide_theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.ide_theme["panel"], foreground=self.ide_theme["text"], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", self.ide_theme["surface"])], foreground=[("selected", self.ide_theme["accent"])])
        style.configure("Horizontal.TProgressbar", troughcolor=self.ide_theme["panel"], background=self.ide_theme["accent"], bordercolor=self.ide_theme["bg"])

    def setup_menu(self):
        if hasattr(self, "menubar"): self.menubar.destroy()
        self.menubar = tk.Menu(self.root, bg=self.ide_theme["bg"], fg=self.ide_theme["text"], activebackground=self.ide_theme["accent"], relief="flat")
        file_menu = tk.Menu(self.menubar, tearoff=0, bg=self.ide_theme["surface"], fg=self.ide_theme["text"])
        file_menu.add_command(label="Open Workspace (.aether)", command=self.load_project)
        file_menu.add_command(label="Save Workspace (.aether)", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Build Architecture & Docs", command=self.export_build)
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)
        view_menu = tk.Menu(self.menubar, tearoff=0, bg=self.ide_theme["surface"], fg=self.ide_theme["text"])
        view_menu.add_command(label="Toggle Viewport Grid", command=lambda: self.toggle_meta("show_grid"))
        view_menu.add_separator()
        view_menu.add_command(label="Open Call Graph Explorer", command=self.show_logic_visualizer)
        self.menubar.add_cascade(label="View", menu=view_menu)
        theme_menu = tk.Menu(self.menubar, tearoff=0, bg=self.ide_theme["surface"], fg=self.ide_theme["text"])
        for t in THEMES.keys(): theme_menu.add_command(label=t, command=lambda name=t: self.change_ide_theme(name))
        self.menubar.add_cascade(label="Preferences", menu=theme_menu)
        self.root.config(menu=self.menubar)

    def toggle_meta(self, key):
        self.metadata[key] = not self.metadata.get(key, True)
        if key == "show_grid": self.draw_grid()

    # --- ADVANCED MACROS & TEMPLATES ---
    def load_prefab_into_matrix(self, template_name):
        if template_name not in self.custom_templates: return
        template = self.custom_templates[template_name]
        id_map = {}
        for c in template: id_map[c["id"]] = f"{c['type'].lower()}_{uuid.uuid4().hex[:6]}"
        for c in template:
            new_c = copy.deepcopy(c)
            new_c["id"] = id_map[c["id"]]
            if new_c["layout"]["parent"] in id_map: new_c["layout"]["parent"] = id_map[c["layout"]["parent"]]
            else: new_c["layout"]["parent"] = "root"
            self.components.append(new_c)
        self.push_history()
        self.refresh_all()
        messagebox.showinfo("Success", f"Deployed Template: {template_name}")

    def create_custom_template(self):
        comp = self.get_comp_by_id(self.selected_id)
        if not comp or comp["type"] not in ["Frame", "Canvas"]:
            messagebox.showwarning("Selection Error", "You must select a Container (Frame/Canvas) to save as a template.")
            return
        def get_all_children(pid):
            kids = [c for c in self.components if c["layout"].get("parent") == pid]
            all_kids = list(kids)
            for k in kids: all_kids.extend(get_all_children(k["id"]))
            return all_kids
        tree_to_save = [copy.deepcopy(comp)] + copy.deepcopy(get_all_children(comp["id"]))
        tree_to_save[0]["layout"]["parent"] = "root"
        from tkinter import simpledialog
        t_name = simpledialog.askstring("Save Template", "Enter a name for this custom Template:")
        if t_name:
            self.custom_templates[t_name] = tree_to_save
            self.save_custom_templates()
            self.render_toolbox()
            messagebox.showinfo("Saved", f"Template '{t_name}' added to your Toolbox!")

    def macro_sysinfo(self):
        panel = self.add_component("Frame", override_layout={"relx": 0.1, "rely": 0.1, "relw": 0.35, "relh": 0.4})
        self.add_component("Label", {"text": "System Dashboard", "font": ("Segoe UI", 12, "bold")}, override_layout={"relx": 0.05, "rely": 0.05, "relw": 0.9, "relh": 0.15}, set_parent=panel)
        self.add_component("Label", {"text": "CPU Load", "anchor": "w"}, override_layout={"relx": 0.05, "rely": 0.3, "relw": 0.3, "relh": 0.1}, set_parent=panel)
        self.add_component("Progressbar", {"value": 35}, override_layout={"relx": 0.4, "rely": 0.3, "relw": 0.55, "relh": 0.1}, set_parent=panel)
        self.add_component("Button", {"text": "Refresh Metrics"}, override_layout={"relx": 0.05, "rely": 0.75, "relw": 0.9, "relh": 0.15}, set_parent=panel)

    def macro_file_upload(self):
        panel = self.add_component("Frame", {"bd":0}, override_layout={"relx": 0.2, "rely": 0.2, "relw": 0.5, "relh": 0.1})
        self.add_component("Label", {"text": "File:", "anchor": "w"}, override_layout={"relx": 0.0, "rely": 0.1, "relw": 0.15, "relh": 0.8}, set_parent=panel)
        entry_id = self.add_component("Entry", {"text": ""}, override_layout={"relx": 0.15, "rely": 0.1, "relw": 0.6, "relh": 0.8}, set_parent=panel)
        btn_id = self.add_component("Button", {"text": "Browse..."}, override_layout={"relx": 0.78, "rely": 0.1, "relw": 0.22, "relh": 0.8}, set_parent=panel)
        code = f"path = filedialog.askopenfilename()\nif path:\n    self.{entry_id}.delete(0, tk.END)\n    self.{entry_id}.insert(0, path)"
        self.get_comp_by_id(btn_id)["events"]["command"] = {"fn": f"browse_{btn_id}", "code": code}

    def macro_audio_deck(self):
        panel = self.add_component("Frame", {"bg": "#222222", "bd":2, "relief": "ridge"}, override_layout={"relx": 0.3, "rely": 0.3, "relw": 0.4, "relh": 0.2})
        self.add_component("Label", {"text": "MEDIA DECK", "bg": "#222222", "fg": "#00ff00", "font": ("Consolas", 10, "bold")}, override_layout={"relx": 0.0, "rely": 0.0, "relw": 1.0, "relh": 0.3}, set_parent=panel)
        play_btn = self.add_component("Button", {"text": "▶ Play", "bg": "#00aa00"}, override_layout={"relx": 0.1, "rely": 0.4, "relw": 0.25, "relh": 0.4}, set_parent=panel)
        self.add_component("Button", {"text": "⏹ Stop", "bg": "#aa0000"}, override_layout={"relx": 0.4, "rely": 0.4, "relw": 0.25, "relh": 0.4}, set_parent=panel)
        self.add_component("Scale", {"bg": "#222222", "fg": "#00ff00"}, override_layout={"relx": 0.7, "rely": 0.4, "relw": 0.25, "relh": 0.4}, set_parent=panel)
        code = "import platform, os\nif platform.system() == 'Windows':\n    import winsound\n    winsound.MessageBeep()\nelse:\n    os.system('echo -e \"\\a\"')"
        self.get_comp_by_id(play_btn)["events"]["command"] = {"fn": "play_audio", "code": code}

    # --- CALLGRAPH ---
    def show_logic_visualizer(self):
        win = tk.Toplevel(self.root)
        win.title("Call Graph & Logic Explorer")
        win.geometry("1150x750")
        win.configure(bg=self.ide_theme["bg"])
        
        pane = tk.PanedWindow(win, orient=tk.HORIZONTAL, bg=self.ide_theme["panel"], sashwidth=4)
        pane.pack(fill=tk.BOTH, expand=True)

        graph_frame = tk.Frame(pane, bg=self.ide_theme["bg"])
        pane.add(graph_frame, width=600)
        tk.Label(graph_frame, text="INTERACTIVE GRAPH (CLICK TO EDIT)", bg=self.ide_theme["bg"], fg=self.ide_theme["text"], font=("Segoe UI", 10, "bold")).pack(pady=5)
        canvas = tk.Canvas(graph_frame, bg=self.ide_theme["surface"], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        info_frame = tk.Frame(pane, bg=self.ide_theme["surface"])
        pane.add(info_frame, width=550)
        tk.Label(info_frame, text="LOGIC INSPECTOR", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        # Ref Injector inside Graph Editor
        insert_f = tk.Frame(info_frame, bg=self.ide_theme["surface"])
        insert_f.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(insert_f, text="Inject Element ID:", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"]).pack(side=tk.LEFT)
        ref_cb_g = ttk.Combobox(insert_f, values=[f"self.{c['id']}" for c in self.components], state="readonly", width=25)
        ref_cb_g.pack(side=tk.LEFT, padx=5)
        
        self.graph_info = scrolledtext.ScrolledText(info_frame, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10), insertbackground="white")
        self.graph_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.graph_info.bind("<KeyRelease>", lambda e: self.schedule_highlight(self.graph_info, ("Consolas", 10)))
        
        def inject_ref_graph(*args):
            if ref_cb_g.get():
                self.graph_info.insert(tk.INSERT, ref_cb_g.get())
                ref_cb_g.set('')
        ref_cb_g.bind("<<ComboboxSelected>>", inject_ref_graph)

        self.current_graph_edit_context = None

        def commit_graph_code():
            if not self.current_graph_edit_context: return
            new_code = self.graph_info.get("1.0", tk.END).strip()
            ctx = self.current_graph_edit_context
            if ctx["type"] == "inline_event":
                comp = self.get_comp_by_id(ctx["comp_id"])
                comp["events"][ctx["event"]]["code"] = new_code
                self.push_history()
                messagebox.showinfo("Success", "Event Logic Updated.")
            elif ctx["type"] == "global_method":
                old_code = ctx["old_code"]
                self.user_code["methods"] = self.user_code["methods"].replace(old_code, new_code)
                messagebox.showinfo("Success", "Global Method Updated.")

        ToolbarButton(info_frame, text="[ SAVE LOGIC ]", bg=self.ide_theme["accent"], hover_bg=self.ide_theme["accent_hover"], fg="white", font=("Segoe UI", 9, "bold"), command=commit_graph_code).pack(fill=tk.X, padx=5, pady=5)

        shared_vars = {} 
        funcs = re.split(r'^\s*def\s+', self.user_code["methods"], flags=re.MULTILINE)[1:]
        func_bodies = {}
        for f in funcs:
            lines = f.split('\n')
            fn_name = lines[0].split('(')[0].strip()
            body = '\n'.join(lines[1:])
            func_bodies[fn_name] = f"def {lines[0]}\n{body}"
            for v in set(re.findall(r'self\.([a-zA-Z0-9_]+)', body)):
                if v not in shared_vars: shared_vars[v] = []
                shared_vars[v].append(fn_name)

        nodes_data = {}
        y_offset = 40
        for c in self.components:
            ui_id = canvas.create_rectangle(20, y_offset, 180, y_offset+50, fill=self.ide_theme["panel"], outline=self.ide_theme["text_dim"], width=1, tags=("node", c['id']))
            canvas.create_text(100, y_offset+25, text=f"{c['id']}", fill=self.ide_theme["text"], font=("Segoe UI", 9, "bold"), tags=("node", c['id']))
            nodes_data[ui_id] = {"type": "ui", "id": c['id'], "events": c.get("events", {})}
            
            if c.get("events", {}):
                x_off = 300
                for event_trigger, action_data in c["events"].items():
                    action = action_data.get("fn", "")
                    if not action: continue
                    act_id = canvas.create_rectangle(x_off, y_offset, x_off+180, y_offset+50, fill=self.ide_theme["bg"], outline=self.ide_theme["accent"], width=2, tags=("node", action))
                    canvas.create_text(x_off+90, y_offset+25, text=f"{event_trigger} -> {action}", fill=self.ide_theme["text"], font=("Segoe UI", 8), tags=("node", action))
                    canvas.create_line(180, y_offset+25, x_off, y_offset+25, arrow=tk.LAST, fill=self.ide_theme["text_dim"], width=1)
                    
                    is_global = action in func_bodies
                    nodes_data[act_id] = {
                        "type": "action", "name": action, 
                        "code": func_bodies.get(action, action_data.get("code", "pass")),
                        "edit_ctx": {"type": "global_method", "old_code": func_bodies.get(action, "")} if is_global else {"type": "inline_event", "comp_id": c['id'], "event": event_trigger}
                    }
                    for var_name, funcs_touching in shared_vars.items():
                        if action in funcs_touching:
                            var_id = canvas.create_oval(x_off+220, y_offset, x_off+320, y_offset+50, fill=self.ide_theme["surface"], outline=self.ide_theme["danger"], width=2, tags=("node", var_name))
                            canvas.create_text(x_off+270, y_offset+25, text=f"self.{var_name}", fill=self.ide_theme["danger"], font=("Segoe UI", 8), tags=("node", var_name))
                            canvas.create_line(x_off+180, y_offset+25, x_off+220, y_offset+25, fill=self.ide_theme["danger"], dash=(2,2), width=1)
                            nodes_data[var_id] = {"type": "var", "name": var_name, "shared_by": funcs_touching}
                    x_off += 200
            y_offset += 70

        def on_canvas_click(event):
            item = canvas.find_withtag("current")
            if not item: return
            tags = canvas.gettags(item[0])
            if "node" in tags:
                node_tag = tags[1]
                self.graph_info.delete(1.0, tk.END)
                self.current_graph_edit_context = None
                for nid, data in nodes_data.items():
                    if data.get("id") == node_tag or data.get("name") == node_tag:
                        if data["type"] == "action":
                            self.graph_info.insert(tk.END, data["code"])
                            self.current_graph_edit_context = data["edit_ctx"]
                            self.highlight_syntax(self.graph_info, ("Consolas", 10))
                        elif data["type"] == "ui":
                            self.graph_info.insert(tk.END, f"# UI COMPONENT: {data['id']}\n# Select a connected action node to edit.")
                        break
        canvas.bind("<Button-1>", on_canvas_click)

    # --- CORE UI ENGINE ---
    def setup_ui(self):
        if hasattr(self, "hud"): self.hud.destroy()
        if hasattr(self, "master_pane"): self.master_pane.destroy()

        self.hud = tk.Frame(self.root, bg=self.ide_theme["sidebar"], height=45, bd=0)
        self.hud.pack(fill=tk.X, side=tk.TOP)
        self.hud.pack_propagate(False)
        
        tk.Label(self.hud, text="AETHER STUDIO V37", font=("Segoe UI", 11, "bold"), fg=self.ide_theme["text"], bg=self.ide_theme["sidebar"]).pack(side=tk.LEFT, padx=15)
        self.btn_undo = ToolbarButton(self.hud, text="⮌ Undo", font=("Segoe UI", 9), bg=self.ide_theme["sidebar"], fg=self.ide_theme["text"], hover_bg=self.ide_theme["panel"], command=self.undo)
        self.btn_undo.pack(side=tk.LEFT, padx=2)
        self.btn_redo = ToolbarButton(self.hud, text="⮎ Redo", font=("Segoe UI", 9), bg=self.ide_theme["sidebar"], fg=self.ide_theme["text"], hover_bg=self.ide_theme["panel"], command=self.redo)
        self.btn_redo.pack(side=tk.LEFT, padx=2)
        self.update_chronos_ui()

        ToolbarButton(self.hud, text="Build Executable ▶", bg=self.ide_theme["accent"], hover_bg=self.ide_theme["accent_hover"], fg="white", font=("Segoe UI", 9, "bold"), command=self.export_build).pack(side=tk.RIGHT, padx=15, pady=8)

        self.master_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.ide_theme["bg"], sashwidth=4)
        self.master_pane.pack(fill=tk.BOTH, expand=True)
        self.build_left_pane()
        self.build_center_pane()
        self.build_right_pane()

    def build_left_pane(self):
        self.left_pane = tk.Frame(self.master_pane, bg=self.ide_theme["surface"])
        self.master_pane.add(self.left_pane, width=280)
        left_split = tk.PanedWindow(self.left_pane, orient=tk.VERTICAL, bg=self.ide_theme["bg"], sashwidth=4)
        left_split.pack(fill=tk.BOTH, expand=True)

        self.toolbox = tk.Frame(left_split, bg=self.ide_theme["surface"])
        left_split.add(self.toolbox, height=500)
        tk.Label(self.toolbox, text=" TOOLBOX", bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill=tk.X)
        
        self.tool_scroll = tk.Canvas(self.toolbox, bg=self.ide_theme["surface"], highlightthickness=0)
        self.tool_content = tk.Frame(self.tool_scroll, bg=self.ide_theme["surface"])
        self.tool_scroll.create_window((0, 0), window=self.tool_content, anchor="nw", width=260)
        self.tool_scroll.pack(side="left", fill="both", expand=True)
        self.tool_content.bind("<Configure>", lambda e: self.tool_scroll.configure(scrollregion=self.tool_scroll.bbox("all")))
        self.render_toolbox()

        self.hierarchy = tk.Frame(left_split, bg=self.ide_theme["surface"])
        left_split.add(self.hierarchy, height=300)
        tk.Label(self.hierarchy, text=" DOCUMENT OUTLINE", bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill=tk.X)
        
        self.tree = ttk.Treeview(self.hierarchy, columns=("Type", "Vis"), show="tree headings")
        self.tree.heading("#0", text="ID"); self.tree.column("#0", width=120)
        self.tree.heading("Type", text="Class"); self.tree.column("Type", width=70)
        self.tree.heading("Vis", text="Vis"); self.tree.column("Vis", width=40)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        ToolbarButton(self.hierarchy, text="Delete Selected", bg=self.ide_theme["danger"], hover_bg="#e81123", fg="white", font=("Segoe UI", 9, "bold"), command=self.delete_component).pack(fill=tk.X)

    def render_toolbox(self):
        for w in self.tool_content.winfo_children(): w.destroy()
        
        tk.Label(self.tool_content, text=" STANDARD ELEMENTS", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 8, "bold"), anchor="w").pack(fill=tk.X, pady=(5, 5), padx=5)
        for c, data in WIDGET_MAP.items():
            ToolbarButton(self.tool_content, text=f"{data['icon']} {c}", command=lambda x=c: self.add_component(x), bg=self.ide_theme["surface"], hover_bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 10), relief="flat", anchor="w", padx=20).pack(fill=tk.X, pady=1)

        tk.Label(self.tool_content, text=" MACROS", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 8, "bold"), anchor="w").pack(fill=tk.X, pady=(15, 5), padx=5)
        ToolbarButton(self.tool_content, text="[+] System Dashboard", command=self.macro_sysinfo, bg=self.ide_theme["surface"], hover_bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9), relief="flat", anchor="w", padx=20).pack(fill=tk.X, pady=1)
        ToolbarButton(self.tool_content, text="[+] File Upload Picker", command=self.macro_file_upload, bg=self.ide_theme["surface"], hover_bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9), relief="flat", anchor="w", padx=20).pack(fill=tk.X, pady=1)
        ToolbarButton(self.tool_content, text="[+] Audio Control Deck", command=self.macro_audio_deck, bg=self.ide_theme["surface"], hover_bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9), relief="flat", anchor="w", padx=20).pack(fill=tk.X, pady=1)
        
        if self.custom_templates:
            tk.Label(self.tool_content, text=" CUSTOM PREFABS", bg=self.ide_theme["surface"], fg=self.ide_theme["accent"], font=("Segoe UI", 8, "bold"), anchor="w").pack(fill=tk.X, pady=(15, 5), padx=5)
            for t_name in self.custom_templates.keys():
                ToolbarButton(self.tool_content, text=f"📦 {t_name}", command=lambda n=t_name: self.load_prefab_into_matrix(n), bg=self.ide_theme["surface"], hover_bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9), relief="flat", anchor="w", padx=20).pack(fill=tk.X, pady=1)

    def build_center_pane(self):
        self.center_pane = tk.Frame(self.master_pane, bg=self.ide_theme["bg"])
        self.master_pane.add(self.center_pane, width=900)
        self.tab_header = tk.Frame(self.center_pane, bg=self.ide_theme["panel"], height=35)
        self.tab_header.pack(fill=tk.X)
        self.tab_header.pack_propagate(False)
        self.btn_design = tk.Button(self.tab_header, text="Canvas View", bg=self.ide_theme["surface"], fg=self.ide_theme["accent"], relief="flat", font=("Segoe UI", 9, "bold"), command=lambda: self.switch_center_tab(0))
        self.btn_design.pack(side=tk.LEFT, padx=2, fill=tk.Y)
        self.btn_code = tk.Button(self.tab_header, text="Source Logic", bg=self.ide_theme["panel"], fg=self.ide_theme["text_dim"], relief="flat", font=("Segoe UI", 9), command=lambda: self.switch_center_tab(1))
        self.btn_code.pack(side=tk.LEFT, padx=2, fill=tk.Y)
        
        self.center_content = tk.Frame(self.center_pane, bg=self.ide_theme["bg"])
        self.center_content.pack(fill=tk.BOTH, expand=True)

        self.view_designer = tk.Frame(self.center_content, bg=self.ide_theme["bg"])
        self.res_label = tk.Label(self.view_designer, text="", bg=self.ide_theme["bg"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 9))
        self.res_label.pack(pady=5)
        self.viewport_frame = tk.Frame(self.view_designer, bg=self.app_theme["app_bg"], bd=0, highlightthickness=1, highlightbackground=self.ide_theme["text_dim"])
        self.viewport_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.workspace = tk.Canvas(self.viewport_frame, bg=self.app_theme["app_bg"], highlightthickness=0)
        self.workspace.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.view_designer.pack(fill=tk.BOTH, expand=True)

        self.view_code = tk.Frame(self.center_content, bg="#1e1e1e")
        self.code_editor = scrolledtext.ScrolledText(self.view_code, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 11), insertbackground="white", bd=0)
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.code_editor.bind("<KeyRelease>", lambda e: self.schedule_highlight(self.code_editor, ("Consolas", 11)))
        self.root.after(100, self.update_viewport_scale)

    # --- REGEX CODE SHIELDING ---
    def extract_block(self, content, start_marker, end_marker, default_val):
        pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
        match = re.search(pattern, content, re.DOTALL)
        if match: return match.group(1).strip("\n")
        return default_val # Safe fallback if marker was deleted

    def switch_center_tab(self, index):
        if index == 0:
            content = self.code_editor.get(1.0, tk.END)
            self.user_code["imports"] = self.extract_block(content, "# [USER_IMPORTS_START]", "# [USER_IMPORTS_END]", self.user_code["imports"])
            self.user_code["init"] = self.extract_block(content, "# [USER_INIT_START]", "# [USER_INIT_END]", self.user_code["init"])
            self.user_code["methods"] = self.extract_block(content, "# [USER_METHODS_START]", "# [USER_METHODS_END]", self.user_code["methods"])
            
            self.view_code.pack_forget()
            self.view_designer.pack(fill=tk.BOTH, expand=True)
            self.btn_design.config(bg=self.ide_theme["surface"], fg=self.ide_theme["accent"], font=("Segoe UI", 9, "bold"))
            self.btn_code.config(bg=self.ide_theme["panel"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 9))
        else:
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(tk.END, self.generate_code_string())
            self.highlight_syntax(self.code_editor, ("Consolas", 11))
            self.view_designer.pack_forget()
            self.view_code.pack(fill=tk.BOTH, expand=True)
            self.btn_code.config(bg=self.ide_theme["surface"], fg=self.ide_theme["accent"], font=("Segoe UI", 9, "bold"))
            self.btn_design.config(bg=self.ide_theme["panel"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 9))

    def build_right_pane(self):
        self.right_pane = tk.Frame(self.master_pane, bg=self.ide_theme["surface"])
        self.master_pane.add(self.right_pane, width=380)
        self.right_tabs = ttk.Notebook(self.right_pane)
        self.right_tabs.pack(fill=tk.BOTH, expand=True)

        self.tab_props = tk.Frame(self.right_tabs, bg=self.ide_theme["surface"])
        self.tab_layout = tk.Frame(self.right_tabs, bg=self.ide_theme["surface"])
        self.tab_events = tk.Frame(self.right_tabs, bg=self.ide_theme["surface"])
        self.tab_app_theme = tk.Frame(self.right_tabs, bg=self.ide_theme["surface"])
        
        self.right_tabs.add(self.tab_props, text=" Properties ")
        self.right_tabs.add(self.tab_layout, text=" Layout ")
        self.right_tabs.add(self.tab_events, text=" Events ")
        self.right_tabs.add(self.tab_app_theme, text=" Config ")

        self.prop_scroll = scrolledtext.ScrolledText(self.tab_props, bg=self.ide_theme["surface"], bd=0, highlightthickness=0, fg=self.ide_theme["text"])
        self.prop_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.layout_frame = tk.Frame(self.tab_layout, bg=self.ide_theme["surface"])
        self.layout_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.layout_entries = {}
        
        self.event_scroll = tk.Canvas(self.tab_events, bg=self.ide_theme["surface"], highlightthickness=0)
        self.event_scroll.pack(side="left", fill="both", expand=True)
        self.event_frame = tk.Frame(self.event_scroll, bg=self.ide_theme["surface"])
        self.event_scroll.create_window((0, 0), window=self.event_frame, anchor="nw", width=360)
        self.event_frame.bind("<Configure>", lambda e: self.event_scroll.configure(scrollregion=self.event_scroll.bbox("all")))
        self.setup_app_theme_tab()

    def update_viewport_scale(self):
        max_w, max_h = 850, 650
        proj_w, proj_h = self.metadata["width"], self.metadata["height"]
        ratio = min(max_w / proj_w, max_h / proj_h)
        scaled_w, scaled_h = int(proj_w * ratio), int(proj_h * ratio)
        self.viewport_frame.config(width=scaled_w, height=scaled_h)
        self.res_label.config(text=f"Resolution: {proj_w}x{proj_h} (Scaled View)")
        self.workspace.configure(bg=self.app_theme["app_bg"])
        self.draw_grid()

    def draw_grid(self):
        self.workspace.delete("grid")
        if not self.metadata.get("show_grid", True): return
        w, h = self.viewport_frame.winfo_width(), self.viewport_frame.winfo_height()
        grid_size = self.metadata["grid_size"]
        if grid_size < 0.02: return 
        x = 0.0
        while x <= w:
            self.workspace.create_line(int(x), 0, int(x), h, fill=self.ide_theme["grid"], tags="grid")
            x += w * grid_size
        y = 0.0
        while y <= h:
            self.workspace.create_line(0, int(y), w, int(y), fill=self.ide_theme["grid"], tags="grid")
            y += h * grid_size

    def get_comp_by_id(self, uid):
        return next((c for c in self.components if c["id"] == uid), None)

    def add_component(self, c_type, override_props=None, override_layout=None, set_parent="root"):
        idx = len(self.components)
        uid = f"{c_type.lower()}_{idx}"
        relw = 0.3 if c_type in ["Entry", "Button", "Scale", "Combobox"] else (0.8 if c_type in ["Frame", "Canvas", "Console", "Image"] else 0.2)
        relh = 0.06 if c_type not in ["Frame", "Text", "Canvas", "Console", "Image"] else 0.4
        
        conf = WIDGET_MAP[c_type]
        props = {}
        for k, v in conf["props"].items():
            if k == "text" and c_type not in ["Text", "Console", "Image"]: props[k] = f"{c_type}_{idx}"
            elif isinstance(v, str) and v in self.app_theme: props[k] = self.app_theme[v]
            else: props[k] = v
            
        if override_props: props.update(override_props)
        layout = {"relx": 0.1, "rely": 0.1, "relw": relw, "relh": relh, "parent": set_parent}
        if override_layout: layout.update(override_layout)
        
        default_layout = copy.deepcopy(layout)
        self.components.append({
            "type": c_type, "id": uid, "props": props, "layout": layout, "default_layout": default_layout, 
            "events": {}, "init_hidden": False, "data_bind": ""
        })
        
        self.push_history(); self.refresh_all()
        self.selected_id = uid
        self.tree.selection_set(uid)
        return uid

    def delete_component(self):
        if not self.selected_id: return
        to_delete = [self.selected_id]
        for c in self.components:
            if c["layout"].get("parent") == self.selected_id: to_delete.append(c["id"])
        self.components = [c for c in self.components if c["id"] not in to_delete]
        self.selected_id = None
        self.push_history(); self.refresh_all()
        for w in self.prop_scroll.winfo_children(): w.destroy()
        for w in self.layout_frame.winfo_children(): w.destroy()
        for w in self.event_frame.winfo_children(): w.destroy()

    def refresh_all(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for w in self.live_widgets.values(): w.destroy()
        self.live_widgets.clear()
        
        added = set(["root"])
        def insert_node(c):
            icon = WIDGET_MAP[c["type"]]["icon"]
            pid = c["layout"].get("parent", "root")
            if pid == "root": pid = "" 
            vis = "[H]" if c.get("init_hidden", False) else "👁"
            self.tree.insert(pid, "end", iid=c["id"], text=f"{icon} {c['id']}", values=(c['type'], vis))
            self.tree.item(c["id"], open=True)
            added.add(c["id"])

        for _ in range(3): 
            for c in [x for x in self.components if x["id"] not in added]:
                if c["layout"].get("parent", "root") in added: insert_node(c)
        
        def get_depth(c_id, depth=0):
            c = self.get_comp_by_id(c_id)
            if not c or c["layout"].get("parent", "root") == "root": return depth
            return get_depth(c["layout"]["parent"], depth + 1)
        sorted_comps = sorted(self.components, key=lambda x: get_depth(x["id"]))

        for c in sorted_comps:
            try:
                cls = WIDGET_MAP[c['type']]["class"]
                safe_props = {}
                text_content, img_path = None, None
                for k, v in c['props'].items():
                    if k == 'command': continue
                    if c['type'] in ['Text', 'Console'] and k == 'text': text_content = v; continue
                    if c['type'] == 'Combobox' and k == 'values':
                        safe_props[k] = tuple([x.strip() for x in str(v).split(',') if x.strip()]); continue
                    if c['type'] == 'Image' and k == 'image_path':
                        img_path = str(v); continue
                    safe_props[k] = v

                parent_id = c['layout'].get("parent", "root")
                parent_widget = self.live_widgets.get(parent_id, self.workspace) if parent_id != "root" else self.workspace
                
                obj = cls(parent_widget, **safe_props)
                
                if c['type'] in ['Text', 'Console'] and text_content is not None:
                    obj.insert("1.0", text_content)
                if c['type'] == 'Image' and img_path and os.path.exists(img_path):
                    try:
                        img = tk.PhotoImage(file=img_path)
                        self.image_cache[c['id']] = img 
                        obj.config(image=img, text="") 
                    except: pass 

                l = c['layout']
                obj.place(relx=l['relx'], rely=l['rely'], relwidth=l['relw'], relheight=l['relh'])
                
                obj.bind("<Button-1>", lambda e, uid=c['id']: self.on_widget_press(e, uid))
                obj.bind("<B1-Motion>", lambda e, uid=c['id']: self.on_widget_drag(e, uid))
                obj.bind("<ButtonRelease-1>", lambda e, uid=c['id']: self.on_widget_release(e, uid))
                self.live_widgets[c['id']] = obj
            except Exception as e:
                print(f"Render Error on {c['id']}: {e}")

    def on_widget_press(self, event, uid):
        self.selected_id = uid
        self.tree.selection_set(uid)
        self.on_tree_select(None)
        self.drag_data.update({"x": event.x_root, "y": event.y_root, "active": True})

    def on_widget_drag(self, event, uid):
        if not self.drag_data["active"]: return
        comp = self.get_comp_by_id(uid)
        dx, dy = event.x_root - self.drag_data["x"], event.y_root - self.drag_data["y"]
        parent_id = comp["layout"].get("parent", "root")
        parent_widget = self.live_widgets.get(parent_id) if parent_id != "root" else self.viewport_frame
        pw, ph = parent_widget.winfo_width(), parent_widget.winfo_height()
        new_rx = comp["layout"]["relx"] + (dx / pw if pw else 0)
        new_ry = comp["layout"]["rely"] + (dy / ph if ph else 0)
        comp["layout"].update({"relx": new_rx, "rely": new_ry})
        self.live_widgets[uid].place(relx=new_rx, rely=new_ry)
        self.drag_data.update({"x": event.x_root, "y": event.y_root})
        self.update_layout_entries()

    def on_widget_release(self, event, uid):
        self.drag_data["active"] = False
        comp = self.get_comp_by_id(uid)
        grid = self.metadata["grid_size"]
        if grid > 0.01 and self.metadata.get("show_grid", True):
            l = comp["layout"]
            l["relx"], l["rely"] = round(l["relx"] / grid) * grid, round(l["rely"] / grid) * grid
            self.live_widgets[uid].place(relx=l["relx"], rely=l["rely"])
        self.update_layout_entries()
        self.push_history() 

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.selected_id = sel[0]
        self.render_inspector()

    def render_inspector(self):
        comp = self.get_comp_by_id(self.selected_id)
        if not comp: return
        
        for w in self.prop_scroll.winfo_children(): w.destroy()
        tk.Label(self.prop_scroll, text=f"Widget ID: {comp['id']}", bg=self.ide_theme["surface"], fg=self.ide_theme["accent"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(self.prop_scroll, text="Architecture States", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 5))
        
        vf = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
        vf.pack(fill=tk.X, pady=2)
        tk.Label(vf, text="Init Hidden", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        v_cb = ttk.Combobox(vf, values=["False", "True"], state="readonly", width=8)
        v_cb.set("True" if comp.get("init_hidden", False) else "False")
        v_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        def toggle_vis(*a):
            comp["init_hidden"] = (v_cb.get() == "True")
            self.refresh_all(); self.push_history()
        v_cb.bind("<<ComboboxSelected>>", toggle_vis)

        if comp["type"] in ["Entry", "Label", "Checkbutton", "Scale", "Combobox"]:
            df = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
            df.pack(fill=tk.X, pady=2)
            tk.Label(df, text="Data Bind Key", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=12, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            db_e = ttk.Entry(df, font=("Segoe UI", 9))
            db_e.insert(0, str(comp.get("data_bind", "")))
            db_e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            def update_bind(ev):
                comp["data_bind"] = db_e.get().strip()
                self.push_history()
            db_e.bind("<FocusOut>", update_bind); db_e.bind("<Return>", update_bind)

        tk.Label(self.prop_scroll, text="Core Properties", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        for key, val in comp["props"].items():
            if key in ["relief", "cursor", "bd", "font"]: continue 
            f = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=key, bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            if key in ["bg", "fg", "insertbackground", "activebackground", "activeforeground"] or "color" in key.lower():
                c_val = val if str(val).startswith("#") else self.app_theme.get(val, "#ffffff")
                btn = tk.Button(f, text="■", fg=c_val, font=("Arial", 10), bg=self.ide_theme["panel"], relief="flat", command=lambda k=key, cv=c_val: self.pick_prop_color(k, cv))
                btn.pack(side=tk.RIGHT, padx=(2, 0))
            e = ttk.Entry(f, font=("Segoe UI", 9))
            e.insert(0, str(val))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            e.bind("<FocusOut>", lambda ev, k=key, ent=e: self.live_prop_update(k, ent.get(), push_only=True))
            e.bind("<Return>", lambda ev, k=key, ent=e: self.live_prop_update(k, ent.get(), push_only=True))

        if "font" in comp["props"]:
            tk.Label(self.prop_scroll, text="Typography", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
            f_val = comp["props"]["font"]
            fam = f_val[0] if len(f_val) > 0 else "Segoe UI"
            sz = f_val[1] if len(f_val) > 1 else 10
            wt = f_val[2] if len(f_val) > 2 else "normal"
            ff = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
            ff.pack(fill=tk.X, pady=2)
            ttk.Combobox(ff, values=["Segoe UI", "Arial", "Consolas", "Courier New", "Verdana"], width=12).pack(side=tk.LEFT, padx=1)
            ff.winfo_children()[0].set(fam)
            ttk.Combobox(ff, values=[8, 9, 10, 11, 12, 14, 16, 20, 24], width=4).pack(side=tk.LEFT, padx=1)
            ff.winfo_children()[1].set(sz)
            ttk.Combobox(ff, values=["normal", "bold", "italic"], width=8).pack(side=tk.LEFT, padx=1)
            ff.winfo_children()[2].set(wt)
            def update_font(*args):
                new_f = (ff.winfo_children()[0].get(), int(ff.winfo_children()[1].get()), ff.winfo_children()[2].get())
                self.live_prop_update("font", new_f, push_only=True)
            for child in ff.winfo_children(): 
                child.bind("<<ComboboxSelected>>", update_font)
                child.bind("<FocusOut>", update_font)

        tk.Label(self.prop_scroll, text="Shape & Borders", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        rf = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
        rf.pack(fill=tk.X, pady=2)
        tk.Label(rf, text="Relief", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        relief_cb = ttk.Combobox(rf, values=["flat", "raised", "sunken", "solid", "ridge", "groove"], state="readonly")
        relief_cb.set(comp["props"].get("relief", "flat"))
        relief_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        relief_cb.bind("<<ComboboxSelected>>", lambda ev: self.live_prop_update("relief", relief_cb.get(), push_only=True))

        bf = tk.Frame(self.prop_scroll, bg=self.ide_theme["surface"])
        bf.pack(fill=tk.X, pady=2)
        tk.Label(bf, text="Border (bd)", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        bd_e = ttk.Entry(bf, font=("Segoe UI", 9))
        bd_e.insert(0, str(comp["props"].get("bd", 0)))
        bd_e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        bd_e.bind("<FocusOut>", lambda ev, ent=bd_e: self.live_prop_update("bd", ent.get(), push_only=True))

        for w in self.layout_frame.winfo_children(): w.destroy()
        self.layout_entries.clear()
        
        tk.Label(self.layout_frame, text="Parent Container:", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 9)).pack(anchor="w")
        containers = ["root"] + [c["id"] for c in self.components if c["type"] in ["Frame", "Canvas"] and c["id"] != comp["id"]]
        parent_cb = ttk.Combobox(self.layout_frame, values=containers, state="readonly")
        parent_cb.set(comp["layout"].get("parent", "root"))
        parent_cb.pack(fill=tk.X, pady=(0, 15))
        parent_cb.bind("<<ComboboxSelected>>", lambda ev: self.update_parent(parent_cb.get()))

        tk.Label(self.layout_frame, text="Relative Vectors", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        grid_f = tk.Frame(self.layout_frame, bg=self.ide_theme["surface"])
        grid_f.pack(fill=tk.X)
        for i, key in enumerate(["relx", "rely", "relw", "relh"]):
            lbl = tk.Label(grid_f, text=key.upper(), bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 8))
            lbl.grid(row=i//2, column=(i%2)*2, sticky="w", padx=2, pady=2)
            e = ttk.Entry(grid_f, width=8, font=("Segoe UI", 9))
            e.insert(0, str(round(comp["layout"][key], 3)))
            e.grid(row=i//2, column=(i%2)*2+1, sticky="ew", padx=2, pady=2)
            e.bind("<FocusOut>", lambda ev, k=key, ent=e: self.live_layout_update(k, ent.get()))
            e.bind("<Return>", lambda ev, k=key, ent=e: self.live_layout_update(k, ent.get()))
            self.layout_entries[key] = e

        # --- 9-Way Snap Layout Presets ---
        tk.Label(self.layout_frame, text="Anchor & Stretch Commands", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        snap_f = tk.Frame(self.layout_frame, bg=self.ide_theme["surface"])
        snap_f.pack(fill=tk.X)
        
        ttk.Button(snap_f, text="↖", width=3, command=lambda: self.apply_preset('tl')).grid(row=0, column=0, padx=1, pady=1)
        ttk.Button(snap_f, text="↑", width=3, command=lambda: self.apply_preset('tc')).grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(snap_f, text="↗", width=3, command=lambda: self.apply_preset('tr')).grid(row=0, column=2, padx=1, pady=1)
        ttk.Button(snap_f, text="←", width=3, command=lambda: self.apply_preset('ml')).grid(row=1, column=0, padx=1, pady=1)
        ttk.Button(snap_f, text="•", width=3, command=lambda: self.apply_preset('cc')).grid(row=1, column=1, padx=1, pady=1)
        ttk.Button(snap_f, text="→", width=3, command=lambda: self.apply_preset('mr')).grid(row=1, column=2, padx=1, pady=1)
        ttk.Button(snap_f, text="↙", width=3, command=lambda: self.apply_preset('bl')).grid(row=2, column=0, padx=1, pady=1)
        ttk.Button(snap_f, text="↓", width=3, command=lambda: self.apply_preset('bc')).grid(row=2, column=1, padx=1, pady=1)
        ttk.Button(snap_f, text="↘", width=3, command=lambda: self.apply_preset('br')).grid(row=2, column=2, padx=1, pady=1)
        
        ttk.Button(snap_f, text="Fill X", command=lambda: self.apply_preset('fx')).grid(row=0, column=3, sticky="ew", padx=5)
        ttk.Button(snap_f, text="Fill Y", command=lambda: self.apply_preset('fy')).grid(row=1, column=3, sticky="ew", padx=5)
        ttk.Button(snap_f, text="Fill XY", command=lambda: self.apply_preset('fxy')).grid(row=2, column=3, sticky="ew", padx=5)

        ttk.Button(self.layout_frame, text="Restore Default Spacing", command=self.restore_default_layout).pack(fill=tk.X, pady=10)
        if comp["type"] in ["Frame", "Canvas"]:
            ToolbarButton(self.layout_frame, text="[ Save as Custom Template ]", bg=self.ide_theme["accent"], fg="white", font=("Segoe UI", 9, "bold"), command=self.create_custom_template).pack(fill=tk.X, pady=5)

        for w in self.event_frame.winfo_children(): w.destroy()
        tk.Label(self.event_frame, text="Inline Event Code", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        add_f = tk.Frame(self.event_frame, bg=self.ide_theme["surface"])
        add_f.pack(fill=tk.X, pady=5)
        ev_cb = ttk.Combobox(add_f, values=["command", "<Button-1>", "<Enter>", "<Leave>", "<KeyRelease>"], width=12)
        ev_cb.set("command")
        ev_cb.pack(side=tk.LEFT, padx=2)
        ttk.Button(add_f, text="Add Hook", command=lambda: self.add_event_bind(ev_cb.get(), f"exec_{comp['id']}")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Frame(self.event_frame, bg=self.ide_theme["panel"], height=1).pack(fill=tk.X, pady=5)
        
        for ev, data in list(comp.get("events", {}).items()):
            ef = tk.Frame(self.event_frame, bg=self.ide_theme["surface"], bd=1, relief="solid")
            ef.pack(fill=tk.X, pady=4, padx=2)
            header = tk.Frame(ef, bg=self.ide_theme["panel"])
            header.pack(fill=tk.X)
            tk.Label(header, text=ev, bg=self.ide_theme["panel"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(header, text="Remove", bg=self.ide_theme["danger"], fg="white", bd=0, font=("Segoe UI", 8), cursor="hand2", command=lambda k=ev: self.remove_event_bind(k)).pack(side=tk.RIGHT, padx=5, pady=2)
            
            # --- NEW: Inline Ref Injector ---
            tools_f = tk.Frame(ef, bg=self.ide_theme["surface"])
            tools_f.pack(fill=tk.X, padx=2, pady=2)
            tk.Label(tools_f, text="Inject ID:", bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], font=("Segoe UI", 8)).pack(side=tk.LEFT)
            ref_cb = ttk.Combobox(tools_f, values=[f"self.{x['id']}" for x in self.components], state="readonly", width=18)
            ref_cb.pack(side=tk.LEFT, padx=2)
            
            code_area = tk.Text(ef, height=4, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9), insertbackground="white", bd=0)
            code_area.pack(fill=tk.X, padx=2, pady=2)
            code_area.insert("1.0", data.get("code", "pass"))
            self.highlight_syntax(code_area, ("Consolas", 9))
            
            def inject_ref_inline(e, rcb=ref_cb, ca=code_area, ev_key=ev):
                if rcb.get():
                    ca.insert(tk.INSERT, rcb.get())
                    rcb.set('')
                    self.live_event_code_update(ev_key, ca.get("1.0", tk.END).strip())
                    self.schedule_highlight(ca, ("Consolas", 9))
            ref_cb.bind("<<ComboboxSelected>>", inject_ref_inline)

            def on_code_change(e, ev_key=ev, ca=code_area):
                self.live_event_code_update(ev_key, ca.get("1.0", tk.END).strip())
                self.schedule_highlight(ca, ("Consolas", 9))
            code_area.bind("<KeyRelease>", on_code_change)

    def pick_prop_color(self, key, current_val):
        color = colorchooser.askcolor(initialcolor=current_val)[1]
        if color: 
            self.live_prop_update(key, color, push_only=False)
            self.render_inspector() 

    def live_prop_update(self, key, val, push_only=False):
        comp = self.get_comp_by_id(self.selected_id)
        if key == "bd":
            try: val = int(val)
            except: val = 0
        comp["props"][key] = val
        self.refresh_all() 
        if push_only: self.push_history()

    def live_layout_update(self, key, val):
        try:
            self.get_comp_by_id(self.selected_id)["layout"][key] = float(val)
            self.refresh_all(); self.push_history()
        except ValueError: pass

    def update_layout_entries(self):
        if not self.selected_id or not self.layout_entries: return
        comp = self.get_comp_by_id(self.selected_id)
        for key, entry in self.layout_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(round(comp["layout"][key], 3)))

    def update_parent(self, new_parent):
        self.get_comp_by_id(self.selected_id)["layout"]["parent"] = new_parent
        self.refresh_all(); self.push_history()

    def apply_preset(self, action):
        comp = self.get_comp_by_id(self.selected_id)
        l = comp["layout"]
        # Anchor snaps
        if action == 'tl': l["relx"] = 0.0; l["rely"] = 0.0
        if action == 'tc': l["relx"] = 0.5 - (l["relw"] / 2); l["rely"] = 0.0
        if action == 'tr': l["relx"] = 1.0 - l["relw"]; l["rely"] = 0.0
        if action == 'ml': l["relx"] = 0.0; l["rely"] = 0.5 - (l["relh"] / 2)
        if action == 'cc': l["relx"] = 0.5 - (l["relw"] / 2); l["rely"] = 0.5 - (l["relh"] / 2)
        if action == 'mr': l["relx"] = 1.0 - l["relw"]; l["rely"] = 0.5 - (l["relh"] / 2)
        if action == 'bl': l["relx"] = 0.0; l["rely"] = 1.0 - l["relh"]
        if action == 'bc': l["relx"] = 0.5 - (l["relw"] / 2); l["rely"] = 1.0 - l["relh"]
        if action == 'br': l["relx"] = 1.0 - l["relw"]; l["rely"] = 1.0 - l["relh"]
        # Stretches
        if action == 'fx': l["relx"] = 0.0; l["relw"] = 1.0
        if action == 'fy': l["rely"] = 0.0; l["relh"] = 1.0
        if action == 'fxy': l["relx"] = 0.0; l["rely"] = 0.0; l["relw"] = 1.0; l["relh"] = 1.0
        # Legacy mappings
        if action == 'cx': l["relx"] = 0.5 - (l["relw"] / 2)
        if action == 'cy': l["rely"] = 0.5 - (l["relh"] / 2)
        
        self.refresh_all(); self.update_layout_entries(); self.push_history()

    def restore_default_layout(self):
        comp = self.get_comp_by_id(self.selected_id)
        if "default_layout" in comp:
            comp["layout"] = copy.deepcopy(comp["default_layout"])
            self.refresh_all(); self.update_layout_entries(); self.push_history()

    def add_event_bind(self, ev, fn_name):
        if not ev or not fn_name: return
        comp = self.get_comp_by_id(self.selected_id)
        if "events" not in comp: comp["events"] = {}
        comp["events"][ev] = {"fn": fn_name, "code": "pass"}
        self.push_history(); self.render_inspector()

    def remove_event_bind(self, ev):
        comp = self.get_comp_by_id(self.selected_id)
        if ev in comp.get("events", {}):
            del comp["events"][ev]
            self.push_history(); self.render_inspector()
            
    def live_event_code_update(self, ev_key, code_str):
        comp = self.get_comp_by_id(self.selected_id)
        if ev_key in comp.get("events", {}): comp["events"][ev_key]["code"] = code_str

    def setup_app_theme_tab(self):
        for w in self.tab_app_theme.winfo_children(): w.destroy()
        
        tk.Label(self.tab_app_theme, text="Project Metadata", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 5), padx=10)
        for key in ["name", "author"]:
            f = tk.Frame(self.tab_app_theme, bg=self.ide_theme["surface"])
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=key.title(), bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            e = ttk.Entry(f, font=("Segoe UI", 9))
            e.insert(0, str(self.metadata.get(key, "")))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            e.bind("<FocusOut>", lambda ev, k=key, ent=e: self.update_metadata(k, ent.get()))

        tk.Label(self.tab_app_theme, text="System Resolution", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5), padx=10)
        for key in ["width", "height", "grid_size"]:
            f = tk.Frame(self.tab_app_theme, bg=self.ide_theme["surface"])
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=key.title(), bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=10, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            e = ttk.Entry(f, font=("Segoe UI", 9))
            e.insert(0, str(self.metadata[key]))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            e.bind("<FocusOut>", lambda ev, k=key, ent=e: self.update_metadata(k, ent.get()))

        tk.Label(self.tab_app_theme, text="Application Theme Palette", bg=self.ide_theme["surface"], fg=self.ide_theme["text"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5), padx=10)
        for key, val in self.app_theme.items():
            f = tk.Frame(self.tab_app_theme, bg=self.ide_theme["surface"])
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=key.replace("app_", "").title(), bg=self.ide_theme["surface"], fg=self.ide_theme["text_dim"], width=12, anchor="w", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            btn = tk.Button(f, text="■", fg=val, font=("Arial", 12), bg=self.ide_theme["panel"], relief="flat", command=lambda k=key, cv=val: self.pick_app_color(k, cv))
            btn.pack(side=tk.RIGHT, padx=(5, 0))
            e = ttk.Entry(f, font=("Segoe UI", 9))
            e.insert(0, str(val))
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            e.bind("<FocusOut>", lambda ev, k=key, ent=e: self.update_app_theme(k, ent.get()))

    def pick_app_color(self, key, current):
        color = colorchooser.askcolor(initialcolor=current)[1]
        if color: self.update_app_theme(key, color)

    def update_app_theme(self, key, val):
        self.app_theme[key] = val
        self.setup_app_theme_tab()
        for c in self.components:
            conf = WIDGET_MAP[c["type"]]
            for p_k, p_v in conf["props"].items():
                if p_v == key: c["props"][p_k] = val
        self.workspace.configure(bg=self.app_theme["app_bg"])
        self.refresh_all(); self.push_history()

    def update_metadata(self, key, val):
        if key in ["name", "author"]:
            self.metadata[key] = val
            return
        try:
            self.metadata[key] = float(val) if '.' in str(val) else int(val)
            if key in ["width", "height"]: self.update_viewport_scale()
            if key == "grid_size": self.draw_grid()
        except ValueError: pass

    def save_project(self):
        if not self.current_project_file:
            self.current_project_file = filedialog.asksaveasfilename(defaultextension=".aether", filetypes=[("Aether Workspace", "*.aether")])
            if not self.current_project_file: return
        payload = {"version": "37.0", "metadata": self.metadata, "app_theme": self.app_theme, "components": self.components, "user_code": self.user_code}
        with open(self.current_project_file, 'w') as f: json.dump(payload, f, indent=4)
        messagebox.showinfo("Saved", f"Workspace saved to {os.path.basename(self.current_project_file)}")

    def load_project(self):
        fn = filedialog.askopenfilename(filetypes=[("Aether Workspace", "*.aether")])
        if fn: 
            try:
                with open(fn, 'r') as f: data = json.load(f)
                self.metadata = data.get("metadata", self.metadata)
                self.app_theme = data.get("app_theme", self.app_theme)
                
                comps = data.get("components", [])
                for c in comps:
                    for ev, val in list(c.get("events", {}).items()):
                        if isinstance(val, str): c["events"][ev] = {"fn": val, "code": "pass"}
                self.components = comps
                
                self.user_code = data.get("user_code", self.user_code)
                self.current_project_file = fn
                self.update_viewport_scale()
                self.setup_app_theme_tab()
                self.selected_id = None
                
                self.history = []
                self.history_index = -1
                self.push_history()
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to open workspace:\n{e}")

    def export_docs(self, sanitized_name):
        doc = f"# {self.metadata.get('name', 'Application')} // Enterprise Architecture Blueprint\n\n"
        doc += f"**Architect:** {self.metadata.get('author', 'Developer')}\n"
        doc += f"**Compiled:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        doc += "## 🗂️ Component Hierarchy\n```text\n"
        def print_tree(parent_id="root", indent=""):
            children = [c for c in self.components if c["layout"].get("parent", "root") == parent_id]
            for i, c in enumerate(children):
                branch = "└── " if i == len(children) - 1 else "├── "
                hidden = "[HIDDEN]" if c.get("init_hidden") else ""
                bound = f"(State: {c.get('data_bind')})" if c.get("data_bind") else ""
                doc_chunk = f"{indent}{branch}{c['id']} ({c['type']}) {hidden} {bound}\n"
                nonlocal doc; doc += doc_chunk
                print_tree(c["id"], indent + ("    " if i == len(children) - 1 else "│   "))
        doc += "root [Application Window]\n"
        print_tree()
        doc += "```\n\n## ⚡ Event Map\n"
        for c in self.components:
            for ev, data in c.get("events", {}).items():
                doc += f"- `{c['id']}` listens for `{ev}` -> Executes `self.{data['fn']}()`\n"
        with open(f"{sanitized_name}_Docs.md", "w", encoding="utf-8") as f: f.write(doc)

    def generate_code_string(self):
        sanitized_name = re.sub(r'\W|^(?=\d)', '_', self.metadata.get("name", "App"))
        body, stubs = [], []
        handled_events = set()
        state_vars = set()
        
        for c in self.components:
            if c.get("data_bind"): state_vars.add(c["data_bind"])

        def get_depth(c_id, depth=0):
            c = self.get_comp_by_id(c_id)
            if not c or c["layout"].get("parent", "root") == "root": return depth
            return get_depth(c["layout"]["parent"], depth + 1)
        sorted_comps = sorted(self.components, key=lambda x: get_depth(x["id"]))

        for c in sorted_comps:
            mod = WIDGET_MAP[c["type"]]["module"]
            # SQUASHED BUG: Resolve true class name dynamically
            actual_class_name = WIDGET_MAP[c["type"]]["class"].__name__
            
            l = c['layout']
            p_str_parts = []
            
            text_val, img_path, cb_vals = None, None, None
            for k, v in c['props'].items():
                if k == 'command': continue
                if c['type'] in ['Text', 'Console'] and k == 'text': text_val = v; continue
                if c['type'] == 'Combobox' and k == 'values': cb_vals = tuple([x.strip() for x in str(v).split(',') if x.strip()]); continue
                if c['type'] == 'Image' and k == 'image_path': img_path = str(v); continue
                if type(v) == str: p_str_parts.append(f"{k}='{v}'")
                else: p_str_parts.append(f"{k}={v}")

            if c.get("data_bind"):
                if c["type"] in ["Entry", "Label"]: p_str_parts.append(f"textvariable=self.state['{c['data_bind']}']")
                elif c["type"] in ["Checkbutton"]: p_str_parts.append(f"variable=self.state['{c['data_bind']}']")
                elif c["type"] in ["Scale"]: p_str_parts.append(f"variable=self.state['{c['data_bind']}']")
                elif c["type"] == "Combobox": p_str_parts.append(f"textvariable=self.state['{c['data_bind']}']")
            
            if cb_vals: p_str_parts.append(f"values={cb_vals}")

            events = c.get("events", {})
            if "command" in events and c["type"] in ["Button", "Checkbutton", "Scale"]:
                fn_name = events["command"]["fn"]
                raw_code = events["command"].get("code", "pass").strip() or "pass"
                indented_code = '\n'.join([f"        {line}" for line in raw_code.split('\n')])
                p_str_parts.append(f"command=self.{fn_name}")
                if fn_name not in handled_events:
                    stubs.append(f"    def {fn_name}(self, *args):\n{indented_code}")
                    handled_events.add(fn_name)
            
            p_str = ", ".join(p_str_parts)
            parent_ref = f"self.{l['parent']}" if l.get("parent") and l["parent"] != "root" else "self.main_container"
            
            # Write with True class name
            body.append(f"        self.{c['id']} = {mod}.{actual_class_name}({parent_ref}, {p_str})")
            
            if not c.get("init_hidden", False):
                body.append(f"        self.{c['id']}.place(relx={l['relx']:.3f}, rely={l['rely']:.3f}, relwidth={l['relw']:.3f}, relheight={l['relh']:.3f})")
            else:
                body.append(f"        # self.{c['id']}.place(...) omitted due to init_hidden state")

            if c['type'] in ['Text', 'Console'] and text_val is not None:
                safe_text = str(text_val).replace('\n', '\\n').replace("'", "\\'")
                body.append(f"        self.{c['id']}.insert('1.0', '{safe_text}')")
            
            if c['type'] == 'Image' and img_path:
                body.append(f"        try:\n            self.img_{c['id']} = tk.PhotoImage(file='{img_path}')\n            self.{c['id']}.config(image=self.img_{c['id']}, text='')\n        except: pass")
            
            for ev, ev_data in events.items():
                if ev == "command": continue
                fn_name = ev_data["fn"]
                raw_code = ev_data.get("code", "pass").strip() or "pass"
                indented_code = '\n'.join([f"        {line}" for line in raw_code.split('\n')])
                body.append(f"        self.{c['id']}.bind('{ev}', self.{fn_name})")
                if fn_name not in handled_events:
                    stubs.append(f"    def {fn_name}(self, event):\n{indented_code}")
                    handled_events.add(fn_name)
            body.append("") 

        state_init_lines = []
        for var in state_vars:
            state_init_lines.append(f"        self.state['{var}'] = tk.StringVar(value='')")

        final_code = f"""# ==========================================================
# AETHER STUDIO ENTERPRISE V37 - REACTIVE UI
# Application: {self.metadata.get('name', 'App')}
# Author: {self.metadata.get('author', 'Developer')}
# ==========================================================
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

# [USER_IMPORTS_START]
{self.user_code['imports']}
# [USER_IMPORTS_END]

class {sanitized_name}App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("{self.metadata.get('name', 'App')}")
        self.geometry("{self.metadata['width']}x{self.metadata['height']}")
        self.configure(bg="{self.app_theme['app_bg']}")
        
        self.main_container = tk.Frame(self, bg="{self.app_theme['app_bg']}")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.state = {{}}
        self.init_reactive_state()
        
        self.setup_ui()
        self.boot_sequence()

    def init_reactive_state(self):
{chr(10).join(state_init_lines) if state_init_lines else "        pass"}

    def setup_ui(self):
{chr(10).join(body)}

    def boot_sequence(self):
# [USER_INIT_START]
{self.user_code['init']}
# [USER_INIT_END]
        pass

    # --- BEHAVIOR / EVENT LOGIC ---
{chr(10).join(stubs)}

# [USER_METHODS_START]
{self.user_code['methods']}
# [USER_METHODS_END]

if __name__ == "__main__":
    app = {sanitized_name}App()
    app.mainloop()
"""
        return final_code

    def export_build(self):
        if self.btn_code.cget("bg") == self.ide_theme["panel"]: self.switch_center_tab(0) 
        final_code = self.generate_code_string()
        sanitized_name = re.sub(r'\W|^(?=\d)', '_', self.metadata.get("name", "App")) or "CompiledApp"
        fn = f"{sanitized_name}.py"
        with open(fn, "w", encoding="utf-8") as f: f.write(final_code)
        self.export_docs(sanitized_name)
        messagebox.showinfo("Compilation Complete", f"Application built successfully!\n\nSource Code: {fn}\nDocumentation: {sanitized_name}_Docs.md")

if __name__ == "__main__":
    root = tk.Tk()
    app = AetherEnterpriseIDE(root)
    root.mainloop()
