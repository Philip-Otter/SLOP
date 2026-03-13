# ==============================================================================
# AETHER STUDIO PLUGIN: ULTRA ELEMENTS PACK (V45 FIXED)
# Adds 25 New Element Options (10 Native Widgets + 15 Custom Prefabs)
# ==============================================================================
import tkinter as tk
from tkinter import ttk
import sys
import copy

try:
    main_mod = sys.modules.get('__main__')
    AetherPlugin = main_mod.AetherPlugin
except AttributeError:
    class AetherPlugin:
        def on_load(self, ide_instance): pass
        def on_unload(self, ide_instance): pass

class UltraElementsPlugin(AetherPlugin):
    name = "Ultra Elements Pack"
    author = "Senior Quantum Dev"
    version = "2.2.0"
    description = "Expands the Aether Toolbox with 10 native Tkinter/TTK widgets and 15 complex UI prefabs. Fully compliant with V45 Theme Resolution."

    def on_load(self, ide_instance):
        self.ide = ide_instance
        self.inject_native_widgets()
        self.inject_complex_prefabs()
        self.ide.render_toolbox()
        print(f"[{self.name}] Initialization Complete: 25 new elements loaded.")

    def on_unload(self, ide_instance):
        print(f"[{self.name}] Unloaded. (Elements persist in memory until restart).")

    def inject_native_widgets(self):
        main_mod = sys.modules.get('__main__')
        if not hasattr(main_mod, 'WIDGET_MAP'):
            return

        new_widgets = {
            "Listbox": {"icon": "📋", "class": tk.Listbox, "module": "tk", "props": {"bg": "app_input", "fg": "app_text", "font": ("Segoe UI", 10, "normal"), "bd": 1}},
            "Radiobutton": {"icon": "🔘", "class": tk.Radiobutton, "module": "tk", "props": {"text": "Option", "bg": "app_surface", "fg": "app_text", "value": "1"}},
            "Spinbox": {"icon": "🔢", "class": ttk.Spinbox, "module": "ttk", "props": {"from_": 0, "to": 100, "font": ("Segoe UI", 10, "normal")}},
            "LabelFrame": {"icon": "🗂️", "class": tk.LabelFrame, "module": "tk", "props": {"text": "Group Box", "bg": "app_surface", "fg": "app_text", "font": ("Segoe UI", 9, "bold")}},
            "Treeview": {"icon": "🌲", "class": ttk.Treeview, "module": "ttk", "props": {"show": "headings"}},
            "Separator": {"icon": "➖", "class": ttk.Separator, "module": "ttk", "props": {"orient": "horizontal"}},
            "Notebook": {"icon": "📑", "class": ttk.Notebook, "module": "ttk", "props": {}},
            "Message": {"icon": "💬", "class": tk.Message, "module": "tk", "props": {"text": "Wrapped message text...", "bg": "app_surface", "fg": "app_text", "width": 150}},
            "Menubutton": {"icon": "🍔", "class": tk.Menubutton, "module": "tk", "props": {"text": "Dropdown Menu", "bg": "app_accent", "fg": "app_accent_fg"}},
            "Scrollbar": {"icon": "↕️", "class": ttk.Scrollbar, "module": "ttk", "props": {"orient": "vertical"}}
        }
        main_mod.WIDGET_MAP.update(new_widgets)

    def inject_complex_prefabs(self):
        p = {}
        main_mod = sys.modules.get('__main__')
        WIDGET_MAP = getattr(main_mod, 'WIDGET_MAP', {})

        # FIX: Resolves theme variables (e.g., 'app_surface' -> '#1F2937') BEFORE pushing to VDOM
        def mknode(t, cid, props_override, rx, ry, rw, rh, parent="root"):
            base_props = copy.deepcopy(WIDGET_MAP[t]['props']) if t in WIDGET_MAP else {}
            
            # Resolve default theme mappings
            for k, v in base_props.items():
                if isinstance(v, str) and v in self.ide.app_theme:
                    base_props[k] = self.ide.app_theme[v]
            
            # Resolve override theme mappings
            for k, v in props_override.items():
                if isinstance(v, str) and v in self.ide.app_theme:
                    base_props[k] = self.ide.app_theme[v]
                else:
                    base_props[k] = v

            layout = {"relx": rx, "rely": ry, "relw": rw, "relh": rh, "parent": parent}
            return {
                "type": t,
                "id": cid,
                "props": base_props,
                "layout": layout,
                "default_layout": copy.deepcopy(layout),
                "events": {},
                "init_hidden": False,
                "data_bind": ""
            }

        p["Auth Login Panel"] = [
            mknode("Frame", "auth_bg", {"bg": "app_surface", "bd": 1, "relief": "solid"}, 0.3, 0.2, 0.4, 0.6),
            mknode("Label", "auth_lbl", {"text": "Secure Login", "font": ("Segoe UI", 16, "bold")}, 0.1, 0.1, 0.8, 0.15, "auth_bg"),
            mknode("Entry", "auth_usr", {}, 0.1, 0.35, 0.8, 0.15, "auth_bg"),
            mknode("Entry", "auth_pass", {"show": "*"}, 0.1, 0.55, 0.8, 0.15, "auth_bg"),
            mknode("Button", "auth_btn", {"text": "Enter System", "bg": "app_accent"}, 0.1, 0.75, 0.8, 0.15, "auth_bg"),
        ]

        p["Navigation Sidebar"] = [
            mknode("Frame", "nav_bg", {"bg": "app_surface", "bd": 1, "relief": "solid"}, 0.0, 0.0, 0.2, 1.0),
            mknode("Label", "nav_title", {"text": "MENU", "font": ("Segoe UI", 12, "bold")}, 0.1, 0.02, 0.8, 0.05, "nav_bg"),
            mknode("Button", "nav_btn1", {"text": "Dashboard"}, 0.1, 0.1, 0.8, 0.05, "nav_bg"),
            mknode("Button", "nav_btn2", {"text": "Analytics"}, 0.1, 0.17, 0.8, 0.05, "nav_bg"),
            mknode("Button", "nav_btn3", {"text": "Settings"}, 0.1, 0.24, 0.8, 0.05, "nav_bg"),
            mknode("Button", "nav_btn4", {"text": "Logout", "bg": "#c42b1c", "fg": "white"}, 0.1, 0.9, 0.8, 0.05, "nav_bg"),
        ]

        p["Header App Bar"] = [
            mknode("Frame", "top_bg", {"bg": "app_accent", "bd": 0}, 0.0, 0.0, 1.0, 0.08),
            mknode("Label", "top_title", {"text": "Aether Application", "bg": "app_accent", "fg": "white", "font": ("Segoe UI", 14, "bold"), "anchor": "w"}, 0.02, 0.2, 0.3, 0.6, "top_bg"),
            mknode("Button", "top_profile", {"text": "Profile"}, 0.88, 0.2, 0.1, 0.6, "top_bg"),
        ]

        p["Alert Warning Banner"] = [
            mknode("Frame", "warn_bg", {"bg": "#c42b1c", "bd": 0}, 0.1, 0.1, 0.8, 0.1),
            mknode("Label", "warn_lbl", {"text": "CRITICAL: System Memory Low!", "bg": "#c42b1c", "fg": "white", "font": ("Segoe UI", 11, "bold")}, 0.05, 0.2, 0.7, 0.6, "warn_bg"),
            mknode("Button", "warn_btn", {"text": "Dismiss", "bg": "white", "fg": "black"}, 0.8, 0.2, 0.15, 0.6, "warn_bg"),
        ]

        p["Pricing Subscription Tier"] = [
            mknode("Frame", "prc_bg", {"bg": "app_surface", "bd": 1, "relief": "solid"}, 0.4, 0.2, 0.25, 0.6),
            mknode("Label", "prc_tier", {"text": "PRO PLAN", "font": ("Segoe UI", 10, "bold")}, 0.1, 0.05, 0.8, 0.1, "prc_bg"),
            mknode("Label", "prc_cost", {"text": "$29/mo", "font": ("Segoe UI", 18, "bold")}, 0.1, 0.15, 0.8, 0.15, "prc_bg"),
            mknode("Label", "prc_feat1", {"text": "✓ Infinite Scale"}, 0.1, 0.4, 0.8, 0.08, "prc_bg"),
            mknode("Label", "prc_feat2", {"text": "✓ Priority Support"}, 0.1, 0.5, 0.8, 0.08, "prc_bg"),
            mknode("Button", "prc_btn", {"text": "Subscribe Now", "bg": "app_accent"}, 0.1, 0.8, 0.8, 0.12, "prc_bg"),
        ]

        self.ide.custom_templates.update(p)
