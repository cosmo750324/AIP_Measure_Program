import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Paths to config files
PROJECTS_PATH = r"D:\Claude_AI\Python Program\cfg\projects.json"
TEST_PROGRAMS_PATH = r"D:\Claude_AI\Python Program\cfg\test_programs.json"

def load_json(path):
    """Load a JSON file and return its content (list or dict).
    In headless mode we avoid tkinter dialogs and simply return an empty list on error.
    """
    if not os.path.exists(path):
        # No GUI – just return empty and let caller handle
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

class ConfigViewer(tk.Tk):
    def __init__(self):
        try:
            super().__init__()
            self.title("Config Viewer")
            # Set window size to 1/4 of screen (half width, half height)
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{screen_w // 2}x{screen_h // 2}")
            self._create_widgets()
            self._populate()
        except Exception as e:
            # Headless fallback: output to console
            print("[INFO] GUI cannot be launched (likely headless). Printing data to console instead.")
            # Projects
            proj_data = load_json(PROJECTS_PATH) or []
            codes = [item.get("code") for item in proj_data if isinstance(item, dict) and item.get("code") and item.get("code") != "NA"]
            print("Project Codes:")
            for c in sorted(codes):
                print(c)
            # Test programs
            test_data = load_json(TEST_PROGRAMS_PATH) or []
            names = [item.get("name") for item in test_data if isinstance(item, dict) and item.get("Executable") == "Y"]
            print("\nExecutable Test Names:")
            for n in sorted(names):
                print(n)
            sys.exit(0)

    def _create_widgets(self):
        # Top control bar with Update and Confirm buttons
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, pady=5)
        ttk.Button(ctrl, text="Update", command=self._populate).pack(side=tk.LEFT, padx=5)
        self.confirm_btn = ttk.Button(ctrl, text="Confirm", command=self._confirm_selection, state="disabled")
        self.confirm_btn.pack(side=tk.LEFT, padx=5)

        # Main paned window for the two lists
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Projects pane
        proj_frame = ttk.Labelframe(paned, text="projects.json")
        paned.add(proj_frame, weight=1)
        self.proj_tree = self._make_tree(proj_frame)
        # Bind selection event
        self.proj_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Test programs pane
        test_frame = ttk.Labelframe(paned, text="test_programs.json")
        paned.add(test_frame, weight=1)
        self.test_tree = self._make_tree(test_frame)
        self.test_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _make_tree(self, parent):
        # Single column tree, column header "Key"
        tree = ttk.Treeview(parent, columns=("Key",), show="headings")
        tree.heading("Key", text="Key")
        tree.column("Key", anchor="w", width=200)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def _populate(self):
        # Clear existing items
        for i in self.proj_tree.get_children():
            self.proj_tree.delete(i)
        for i in self.test_tree.get_children():
            self.test_tree.delete(i)

        # Projects: extract sorted 'code' values (exclude empty or "NA")
        proj_data = load_json(PROJECTS_PATH) or []
        codes = [item.get("code") for item in proj_data if isinstance(item, dict) and item.get("code") and item.get("code") != "NA"]
        for c in sorted(codes):
            self.proj_tree.insert("", "end", values=(c,))

        # Test programs: show 'name' where Executable == "Y"
        test_data = load_json(TEST_PROGRAMS_PATH) or []
        names = [item.get("name") for item in test_data if isinstance(item, dict) and item.get("Executable") == "Y"]
        for n in sorted(names):
            self.test_tree.insert("", "end", values=(n,))

        # Reset confirm button (since selection may be cleared)
        self.confirm_btn.configure(state="disabled")
        # Reset stored selections
        self.selected_project = None
        self.selected_test = None

    def _on_tree_select(self, event=None):
        """Enable confirm button only when both a project code and a test name are selected."""
        # Project selection
        proj_sel = self.proj_tree.selection()
        if proj_sel:
            self.selected_project = self.proj_tree.item(proj_sel[0])["values"][0]
        else:
            self.selected_project = None
        # Test selection
        test_sel = self.test_tree.selection()
        if test_sel:
            self.selected_test = self.test_tree.item(test_sel[0])["values"][0]
        else:
            self.selected_test = None
        # Enable confirm when both are present
        if self.selected_project and self.selected_test:
            self.confirm_btn.configure(state="normal")
        else:
            self.confirm_btn.configure(state="disabled")

    def _confirm_selection(self):
        """Save the chosen project code and test name to a JSON file for later use."""
        if not (self.selected_project and self.selected_test):
            messagebox.showwarning("Incomplete", "Please select both a project and a test before confirming.")
            return
        data = {
            "project_code": self.selected_project,
            "test_name": self.selected_test,
        }
        # Save next to the script for easy retrieval
        save_path = os.path.join(os.path.dirname(__file__), "selected_config.json")
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Saved", f"Selection saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save selection: {e}")

if __name__ == "__main__":
    app = ConfigViewer()
    app.mainloop()
