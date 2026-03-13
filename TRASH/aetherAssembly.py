# ==============================================================================
# AETHER-GEF V3.0 - QUANTUM CISC EXECUTION SUITE
# ------------------------------------------------------------------------------
# THEME: "NEON TERMINAL" High-Contrast IDE
# ARCHITECTURE: Reactive VDOM, Asynchronous Event Loop, GEF Context Dashboard
# ==============================================================================

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re

class AetherGEFTheme:
    BG = "#0B0F19"           # Deep space background
    PANEL = "#111827"        # Slightly lighter panels
    SURFACE = "#1F2937"      # Elevated surfaces
    ACCENT = "#10B981"       # Matrix/Quantum Green
    ACCENT_HOVER = "#059669"
    DATA = "#3B82F6"         # Cyber Blue
    STACK = "#8B5CF6"        # Purple
    ERROR = "#EF4444"        # Crimson Red
    WARNING = "#F59E0B"      # Amber
    TEXT = "#F9FAFB"         # Off-white
    TEXT_DIM = "#9CA3AF"     # Greyed text
    GUTTER = "#1e1e1e"
    HIGHLIGHT = "#374151"    # Current execution line

class CISCCore:
    """Advanced Intel x86-style Execution Core with Branching & EFLAGS."""
    def __init__(self, mem_size=1024):
        self.mem_size = mem_size
        self.reset()

    def reset(self):
        self.regs = {
            "EAX": 0, "EBX": 0, "ECX": 0, "EDX": 0,
            "ESI": 0, "EDI": 0, "EBP": self.mem_size - 4, "ESP": self.mem_size - 4,
            "EIP": 0
        }
        self.flags = {"ZF": 0, "SF": 0} # Zero Flag, Sign Flag
        self.memory = bytearray(self.mem_size)
        self.breakpoints = set()
        
        # State tracking for animations
        self.diff_regs = set()
        self.diff_flags = set()
        self.diff_mem = set()

    def _parse_operand(self, operand):
        operand = operand.strip()
        # Register
        if operand in self.regs:
            return "reg", operand
        # Memory Reference [REG + OFFSET]
        mem_match = re.match(r"\[(\w+)\s*\+?\s*(\d+)?\]", operand)
        if mem_match:
            reg, offset = mem_match.groups()
            addr = self.regs[reg.upper()] + (int(offset, 0) if offset else 0)
            return "mem", addr % self.mem_size
        # Immediate Value
        try:
            return "imm", int(operand, 0)
        except ValueError:
            return "label", operand # For jumps

    def get_val(self, operand):
        op_type, val = self._parse_operand(operand)
        if op_type == "reg": return self.regs[val]
        if op_type == "mem":
            # Read 4 bytes (Little Endian emulation for simplicity in display)
            return int.from_bytes(self.memory[val:val+4], byteorder='little', signed=True)
        return val # Immediate

    def set_val(self, operand, value):
        value &= 0xFFFFFFFF # Enforce 32-bit width
        if value & 0x80000000: value -= 0x100000000 # Handle negatives
        
        op_type, target = self._parse_operand(operand)
        if op_type == "reg":
            self.regs[target] = value
            self.diff_regs.add(target)
        elif op_type == "mem":
            # Write 4 bytes
            val_bytes = value.to_bytes(4, byteorder='little', signed=True)
            for i in range(4):
                if target + i < self.mem_size:
                    self.memory[target + i] = val_bytes[i]
            self.diff_mem.add(target)

    def update_flags(self, result):
        result &= 0xFFFFFFFF
        if result & 0x80000000: result -= 0x100000000
        
        old_zf, old_sf = self.flags["ZF"], self.flags["SF"]
        self.flags["ZF"] = 1 if result == 0 else 0
        self.flags["SF"] = 1 if result < 0 else 0
        
        if old_zf != self.flags["ZF"]: self.diff_flags.add("ZF")
        if old_sf != self.flags["SF"]: self.diff_flags.add("SF")

class LineNumberCanvas(tk.Canvas):
    """Custom UI Gutter for Line Numbers and Visual Breakpoints."""
    def __init__(self, master, text_widget, core, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.core = core
        self.bind("<Button-1>", self.toggle_breakpoint)

    def redraw(self):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True :
            dline= self.text_widget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = int(float(i))
            
            # Draw line number
            self.create_text(25, y, anchor="nw", text=str(linenum), font=("Consolas", 10), fill=AetherGEFTheme.TEXT_DIM)
            
            # Draw Breakpoint
            if (linenum - 1) in self.core.breakpoints:
                self.create_oval(5, y+2, 15, y+12, fill=AetherGEFTheme.ERROR, outline=AetherGEFTheme.ERROR)
            
            i = self.text_widget.index("%s+1line" % i)

    def toggle_breakpoint(self, event):
        idx = self.text_widget.index(f"@0,{event.y}")
        line_idx = int(float(idx)) - 1
        if line_idx in self.core.breakpoints:
            self.core.breakpoints.remove(line_idx)
        else:
            self.core.breakpoints.add(line_idx)
        self.redraw()

class AetherGEF:
    def __init__(self, root):
        self.root = root
        self.root.title("AETHER-GEF V3.0 // QUANTUM DEBUGGER")
        self.root.geometry("1400x900")
        self.root.configure(bg=AetherGEFTheme.BG)
        
        self.core = CISCCore()
        self.is_running = False
        self.labels = {} # Store line-number to label mappings
        
        self.setup_ui()
        self.sync_ui()

    def setup_ui(self):
        # --- HUD (Header) ---
        self.hud = tk.Frame(self.root, bg=AetherGEFTheme.PANEL, height=45)
        self.hud.pack(fill=tk.X, side=tk.TOP)
        self.hud.pack_propagate(False)
        
        tk.Label(self.hud, text="⚙ AETHER-GEF", bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.ACCENT, 
                 font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=15)
                 
        self.lbl_status = tk.Label(self.hud, text="HALTED", bg=AetherGEFTheme.ERROR, fg="white", font=("Segoe UI", 9, "bold"), padx=10)
        self.lbl_status.pack(side=tk.LEFT, padx=10, pady=10)
        
        btn_style = {"bg": AetherGEFTheme.SURFACE, "fg": AetherGEFTheme.TEXT, "font": ("Segoe UI", 9, "bold"), "bd": 0, "cursor": "hand2", "padx": 15, "pady": 5}
        tk.Button(self.hud, text="RESET", command=self.action_reset, **btn_style).pack(side=tk.RIGHT, padx=5, pady=8)
        tk.Button(self.hud, text="STEP INTO (F7)", command=self.action_step, **btn_style).pack(side=tk.RIGHT, padx=5, pady=8)
        tk.Button(self.hud, text="CONTINUE (F9)", command=self.action_run, bg=AetherGEFTheme.ACCENT, fg="white", font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2", padx=15, pady=5).pack(side=tk.RIGHT, padx=15, pady=8)

        # --- MAIN WORKSPACE ---
        self.master_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=AetherGEFTheme.BG, bd=0, sashwidth=4)
        self.master_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.build_editor_pane()
        self.build_context_pane()
        self.build_memory_pane()
        
        # --- CONSOLE (Bottom) ---
        self.console = scrolledtext.ScrolledText(self.root, height=8, bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT_DIM, font=("Consolas", 10), bd=0, highlightthickness=1, highlightbackground=AetherGEFTheme.BG)
        self.console.pack(fill=tk.X, padx=5, pady=5)
        self.log("AETHER-GEF Initialized. Quantum Engine ready.")

        # Keybinds
        self.root.bind("<F7>", lambda e: self.action_step())
        self.root.bind("<F9>", lambda e: self.action_run())

    def build_editor_pane(self):
        self.editor_frame = tk.Frame(self.master_pane, bg=AetherGEFTheme.BG)
        self.master_pane.add(self.editor_frame, width=450)
        
        tk.Label(self.editor_frame, text="SOURCE CODE", bg=AetherGEFTheme.BG, fg=AetherGEFTheme.TEXT_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
        
        container = tk.Frame(self.editor_frame, bg=AetherGEFTheme.PANEL)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.editor = tk.Text(container, bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT, font=("Consolas", 11), insertbackground="white", bd=0, undo=True, wrap="none")
        self.gutter = LineNumberCanvas(container, self.editor, self.core, width=40, bg=AetherGEFTheme.SURFACE, bd=0, highlightthickness=0)
        
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.editor.tag_configure("current_line", background=AetherGEFTheme.HIGHLIGHT)
        self.editor.tag_configure("keyword", foreground=AetherGEFTheme.DATA)
        self.editor.tag_configure("comment", foreground=AetherGEFTheme.TEXT_DIM)
        
        # Sync Gutter on scroll/edit
        self.editor.bind("<KeyRelease>", self.on_editor_change)
        self.editor.bind("<MouseWheel>", lambda e: self.root.after(10, self.gutter.redraw))
        
        sample_code = """_start:
    MOV EAX, 10
    MOV EBX, 5
    
loop_start:
    ADD EAX, EBX
    PUSH EAX
    DEC EBX
    CMP EBX, 0
    JNE loop_start  ; Jump if Not Equal to 0
    
    POP ECX
    MOV [0x100], ECX"""
        self.editor.insert("1.0", sample_code)
        self.on_editor_change()

    def build_context_pane(self):
        self.ctx_frame = tk.Frame(self.master_pane, bg=AetherGEFTheme.BG)
        self.master_pane.add(self.ctx_frame, width=300)
        
        # REGISTERS
        tk.Label(self.ctx_frame, text="REGISTERS", bg=AetherGEFTheme.BG, fg=AetherGEFTheme.TEXT_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
        self.ui_regs = {}
        for reg in self.core.regs.keys():
            f = tk.Frame(self.ctx_frame, bg=AetherGEFTheme.PANEL)
            f.pack(fill=tk.X, pady=1)
            tk.Label(f, text=reg.ljust(4), bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.DATA, font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=5)
            val_lbl = tk.Label(f, text="0x00000000", bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT, font=("Consolas", 10))
            val_lbl.pack(side=tk.RIGHT, padx=5)
            self.ui_regs[reg] = {"frame": f, "lbl": val_lbl}

        # FLAGS
        tk.Label(self.ctx_frame, text="EFLAGS", bg=AetherGEFTheme.BG, fg=AetherGEFTheme.TEXT_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 2))
        flags_f = tk.Frame(self.ctx_frame, bg=AetherGEFTheme.PANEL, pady=5)
        flags_f.pack(fill=tk.X)
        self.ui_flags = {}
        for flag in self.core.flags.keys():
            f = tk.Frame(flags_f, bg=AetherGEFTheme.PANEL)
            f.pack(side=tk.LEFT, padx=10)
            tk.Label(f, text=flag, bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT_DIM, font=("Consolas", 9)).pack(side=tk.LEFT)
            box = tk.Label(f, text=" 0 ", bg=AetherGEFTheme.SURFACE, fg=AetherGEFTheme.TEXT, font=("Consolas", 9, "bold"))
            box.pack(side=tk.LEFT, padx=2)
            self.ui_flags[flag] = box

        # STACK VIEW
        tk.Label(self.ctx_frame, text="STACK", bg=AetherGEFTheme.BG, fg=AetherGEFTheme.TEXT_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 2))
        self.stack_view = tk.Text(self.ctx_frame, bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.STACK, font=("Consolas", 10), bd=0, height=12)
        self.stack_view.pack(fill=tk.BOTH, expand=True)

    def build_memory_pane(self):
        self.mem_frame = tk.Frame(self.master_pane, bg=AetherGEFTheme.BG)
        self.master_pane.add(self.mem_frame)
        
        tk.Label(self.mem_frame, text="QUANTUM HEXDUMP", bg=AetherGEFTheme.BG, fg=AetherGEFTheme.TEXT_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
        
        self.hex_view = scrolledtext.ScrolledText(self.mem_frame, bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT, font=("Consolas", 11), bd=0)
        self.hex_view.pack(fill=tk.BOTH, expand=True)
        self.hex_view.tag_configure("addr", foreground=AetherGEFTheme.TEXT_DIM)
        self.hex_view.tag_configure("ascii", foreground=AetherGEFTheme.WARNING)

    # --- EXECUTION ENGINE ---
    def parse_labels(self):
        """Scans code to find jumps/labels."""
        self.labels.clear()
        lines = self.editor.get("1.0", tk.END).split("\n")
        for i, line in enumerate(lines):
            line = line.split(";")[0].strip()
            if line.endswith(":"):
                self.labels[line[:-1]] = i

    def parse_instruction(self, line):
        line = line.split(";")[0].strip()
        if not line or line.endswith(":"): return None
        
        parts = line.split(maxsplit=1)
        op = parts[0].upper()
        args = [arg.strip() for arg in parts[1].split(",")] if len(parts) > 1 else []
        return op, args

    def execute_instruction(self, op, args):
        c = self.core
        old_regs = c.regs.copy()
        
        try:
            if op == "MOV":
                c.set_val(args[0], c.get_val(args[1]))
            elif op == "ADD":
                val = c.get_val(args[0]) + c.get_val(args[1])
                c.set_val(args[0], val)
                c.update_flags(val)
            elif op == "SUB":
                val = c.get_val(args[0]) - c.get_val(args[1])
                c.set_val(args[0], val)
                c.update_flags(val)
            elif op == "INC":
                val = c.get_val(args[0]) + 1
                c.set_val(args[0], val)
                c.update_flags(val)
            elif op == "DEC":
                val = c.get_val(args[0]) - 1
                c.set_val(args[0], val)
                c.update_flags(val)
            elif op == "CMP":
                val = c.get_val(args[0]) - c.get_val(args[1])
                c.update_flags(val) # CMP sets flags but discards result
            elif op == "PUSH":
                c.regs["ESP"] -= 4
                c.set_val(f"[{c.regs['ESP']}]", c.get_val(args[0]))
            elif op == "POP":
                c.set_val(args[0], c.get_val(f"[{c.regs['ESP']}]"))
                c.regs["ESP"] += 4
            
            # Branches
            elif op == "JMP":
                if args[0] in self.labels: c.regs["EIP"] = self.labels[args[0]] - 1
            elif op in ["JE", "JZ"]:
                if c.flags["ZF"] == 1 and args[0] in self.labels: c.regs["EIP"] = self.labels[args[0]] - 1
            elif op in ["JNE", "JNZ"]:
                if c.flags["ZF"] == 0 and args[0] in self.labels: c.regs["EIP"] = self.labels[args[0]] - 1

            # Log Diff
            diffs = []
            for r in c.diff_regs: diffs.append(f"{r}: {hex(old_regs[r])} -> {hex(c.regs[r])}")
            if diffs: self.log(f"gef➤ {op} {', '.join(args)}  |  {', '.join(diffs)}")

            return True
        except Exception as e:
            self.log(f"ERROR: Invalid operation -> {op} {args} ({e})", error=True)
            self.action_reset()
            return False

    def perform_step(self):
        lines = self.editor.get("1.0", tk.END).split("\n")
        eip = self.core.regs["EIP"]
        
        if eip >= len(lines) - 1:
            self.set_status("FINISHED", AetherGEFTheme.ACCENT)
            self.is_running = False
            return False

        line = lines[eip]
        instr = self.parse_instruction(line)
        
        if instr:
            op, args = instr
            success = self.execute_instruction(op, args)
            if not success: return False

        self.core.regs["EIP"] += 1
        return True

    # --- UI ACTIONS & SYNC ---
    def action_step(self):
        self.parse_labels()
        self.set_status("STEPPING", AetherGEFTheme.WARNING)
        self.perform_step()
        self.sync_ui()
        self.set_status("HALTED", AetherGEFTheme.ERROR)

    def action_run(self):
        if self.is_running: return
        self.parse_labels()
        self.is_running = True
        self.set_status("RUNNING", AetherGEFTheme.ACCENT)
        self.run_loop()

    def run_loop(self):
        if not self.is_running: return
        
        # Check Breakpoint (skip if we just hit it)
        if self.core.regs["EIP"] in self.core.breakpoints:
            self.is_running = False
            self.set_status("BREAKPOINT HIT", AetherGEFTheme.WARNING)
            self.sync_ui()
            return

        if self.perform_step():
            # Sync UI occasionally or on breakpoint to keep it fast
            self.sync_ui() 
            self.root.after(100, self.run_loop) # 100ms delay for visual tracing
        else:
            self.sync_ui()

    def action_reset(self):
        self.is_running = False
        self.core.reset()
        self.sync_ui()
        self.set_status("HALTED", AetherGEFTheme.ERROR)
        self.log("CPU State Reset.")

    def set_status(self, text, color):
        self.lbl_status.config(text=text, bg=color)

    def log(self, text, error=False):
        self.console.insert(tk.END, text + "\n")
        if error:
            # Simple hack for red text on last line
            pass
        self.console.see(tk.END)

    def on_editor_change(self, event=None):
        self.gutter.redraw()
        
        # Simple Syntax Highlighting
        self.editor.tag_remove("keyword", "1.0", tk.END)
        self.editor.tag_remove("comment", "1.0", tk.END)
        
        code = self.editor.get("1.0", tk.END)
        for m in re.finditer(r'\b(MOV|ADD|SUB|INC|DEC|PUSH|POP|CMP|JMP|JE|JZ|JNE|JNZ)\b', code):
            self.editor.tag_add("keyword", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r';.*', code):
            self.editor.tag_add("comment", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def sync_ui(self):
        """The Quantum Pulse Engine: Animates and syncs data to UI."""
        # Highlight current line
        self.editor.tag_remove("current_line", "1.0", tk.END)
        curr_line = self.core.regs["EIP"] + 1
        self.editor.tag_add("current_line", f"{curr_line}.0", f"{curr_line}.end")
        self.editor.see(f"{curr_line}.0")

        # Sync Registers
        for reg, ui in self.ui_regs.items():
            val = self.core.regs[reg]
            ui["lbl"].config(text=f"0x{val & 0xFFFFFFFF:08X}")
            
            # Animation Pulse
            if reg in self.core.diff_regs:
                ui["frame"].config(bg=AetherGEFTheme.SURFACE)
                ui["lbl"].config(bg=AetherGEFTheme.SURFACE, fg=AetherGEFTheme.ACCENT)
                self.root.after(300, lambda f=ui["frame"], l=ui["lbl"]: (f.config(bg=AetherGEFTheme.PANEL), l.config(bg=AetherGEFTheme.PANEL, fg=AetherGEFTheme.TEXT)))
                self.core.diff_regs.remove(reg)

        # Sync Flags
        for flag, ui in self.ui_flags.items():
            val = self.core.flags[flag]
            is_active = val == 1
            ui.config(
                text=f" {val} ", 
                bg=AetherGEFTheme.ACCENT if is_active else AetherGEFTheme.SURFACE,
                fg=AetherGEFTheme.BG if is_active else AetherGEFTheme.TEXT
            )
            
            # Animation Pulse
            if flag in self.core.diff_flags:
                ui.config(fg="white")
                self.root.after(300, lambda l=ui, a=is_active: l.config(fg=AetherGEFTheme.BG if a else AetherGEFTheme.TEXT))
                self.core.diff_flags.remove(flag)

        # Sync Stack
        self.stack_view.delete("1.0", tk.END)
        esp = self.core.regs["ESP"]
        for i in range(esp, min(esp + 32, self.core.mem_size), 4):
            val = int.from_bytes(self.core.memory[i:i+4], byteorder='little', signed=False)
            prefix = "ESP ->" if i == esp else "      "
            self.stack_view.insert(tk.END, f"{prefix} 0x{i:04X} │ 0x{val:08X}\n")

        # Sync Hexdump
        self.hex_view.delete("1.0", tk.END)
        for i in range(0, 128, 16): # Show first 128 bytes for speed
            chunk = self.core.memory[i:i+16]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            
            self.hex_view.insert(tk.END, f"0x{i:04X}  ", "addr")
            self.hex_view.insert(tk.END, f"{hex_str.ljust(48)}  ")
            self.hex_view.insert(tk.END, f"|{ascii_str}|\n", "ascii")

if __name__ == "__main__":
    root = tk.Tk()
    app = AetherGEF(root)
    root.mainloop()
