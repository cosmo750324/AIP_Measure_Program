import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


class JsonTreeEditor(ttk.Frame):
    """Registry-editor-style widget for viewing/editing arbitrary JSON data.

    Dict/list containers expand and collapse; double-click a leaf's value to
    edit it in place (type is inferred from what you type: null/true/false/
    numbers fall back to string); right-click any node to add or delete
    fields. No JSON syntax to get wrong — to_json() always returns something
    valid since it's built from the tree structure itself.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, columns=("value",), show="tree headings")
        self.tree.heading("#0", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=220)
        self.tree.column("value", width=260)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)

        self._node_kind = {}  # iid -> "dict" | "list" | "leaf"

    # ---------------- load / dump ----------------
    def load(self, data):
        self.tree.delete(*self.tree.get_children())
        self._node_kind.clear()
        if isinstance(data, dict):
            for k, v in data.items():
                self._insert_node("", k, v)
        elif isinstance(data, list):
            for i, v in enumerate(data):
                self._insert_node("", f"[{i}]", v)

    def to_json(self):
        """Top-level is always treated as a dict (our config.json convention)."""
        return {self.tree.item(c, "text"): self._dump_node(c) for c in self.tree.get_children("")}

    def _insert_node(self, parent_iid, key, value):
        if isinstance(value, dict):
            iid = self.tree.insert(parent_iid, "end", text=str(key), values=("{...}",))
            self._node_kind[iid] = "dict"
            for k, v in value.items():
                self._insert_node(iid, k, v)
        elif isinstance(value, list):
            iid = self.tree.insert(parent_iid, "end", text=str(key), values=("[...]",))
            self._node_kind[iid] = "list"
            for i, v in enumerate(value):
                self._insert_node(iid, f"[{i}]", v)
        else:
            iid = self.tree.insert(parent_iid, "end", text=str(key), values=(self._fmt_leaf(value),))
            self._node_kind[iid] = "leaf"
        return iid

    def _dump_node(self, iid):
        kind = self._node_kind.get(iid, "leaf")
        children = self.tree.get_children(iid)
        if kind == "dict":
            return {self.tree.item(c, "text"): self._dump_node(c) for c in children}
        if kind == "list":
            return [self._dump_node(c) for c in children]
        values = self.tree.item(iid, "values")
        return self._parse_leaf(values[0] if values else "")

    @staticmethod
    def _fmt_leaf(value):
        """Strings show quoted (like JSON) so e.g. "33638220" doesn't silently
        turn into a number on the next edit/save."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    @staticmethod
    def _parse_leaf(text):
        t = text.strip()
        if t == "null":
            return None
        if t == "true":
            return True
        if t == "false":
            return False
        if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
            try:
                return json.loads(t)
            except Exception:
                return t[1:-1]
        try:
            return int(t)
        except ValueError:
            pass
        try:
            return float(t)
        except ValueError:
            pass
        return text

    # ---------------- inline value editing ----------------
    def _on_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid or self._node_kind.get(iid) != "leaf":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        self._start_edit(iid)

    def _start_edit(self, iid):
        bbox = self.tree.bbox(iid, "value")
        if not bbox:
            return
        x, y, w, h = bbox
        entry = tk.Entry(self.tree)
        entry.insert(0, self.tree.set(iid, "value"))
        entry.select_range(0, "end")
        entry.focus()
        entry.place(x=x, y=y, width=w, height=h)

        def commit(_event=None):
            if entry.winfo_exists():
                self.tree.set(iid, "value", entry.get())
                entry.destroy()

        def cancel(_event=None):
            entry.destroy()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", cancel)

    # ---------------- add / delete via right-click ----------------
    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            kind = self._node_kind.get(iid, "leaf")
            container = iid if kind in ("dict", "list") else self.tree.parent(iid)
        else:
            container = ""

        suffix = "項目" if self._node_kind.get(container) == "list" else "欄位"
        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label=f"新增{suffix}(文字)", command=lambda: self._add_field(container, ""))
        menu.add_command(label=f"新增{suffix}(物件)", command=lambda: self._add_field(container, {}))
        menu.add_command(label=f"新增{suffix}(陣列)", command=lambda: self._add_field(container, []))
        if iid:
            menu.add_separator()
            menu.add_command(label="刪除", command=lambda: self._delete_node(iid))
        menu.tk_popup(event.x_root, event.y_root)

    def _add_field(self, container_iid, default_value):
        if self._node_kind.get(container_iid) == "list":
            key = f"[{len(self.tree.get_children(container_iid))}]"
        else:
            key = simpledialog.askstring("新增欄位", "欄位名稱:", parent=self)
            if not key:
                return
        self._insert_node(container_iid, key, default_value)
        if container_iid:
            self.tree.item(container_iid, open=True)
        self._renumber_list(container_iid)

    def _delete_node(self, iid):
        if not messagebox.askyesno("刪除", f'確定要刪除「{self.tree.item(iid, "text")}」嗎?'):
            return
        parent = self.tree.parent(iid)
        self._node_kind.pop(iid, None)
        self.tree.delete(iid)
        self._renumber_list(parent)

    def _renumber_list(self, container_iid):
        if self._node_kind.get(container_iid) != "list":
            return
        for i, child in enumerate(self.tree.get_children(container_iid)):
            self.tree.item(child, text=f"[{i}]")
