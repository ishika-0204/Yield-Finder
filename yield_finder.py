import tkinter as tk
from tkinter import filedialog, messagebox


# =========================================================
# PARSE TREE VALIDATION AND CREATION
# =========================================================

def parse_tree(text):
    """
    Converts bracketed input into a nested parse-tree structure.

    Example:
    S(NP(Det(The),N(student)),VP(V(studies)))
    """

    text = text.strip()

    if not text:
        raise ValueError("Input cannot be empty.")

    index = 0

    def skip_spaces():
        nonlocal index
        while index < len(text) and text[index].isspace():
            index += 1

    def read_label():
        nonlocal index

        skip_spaces()
        start = index

        while index < len(text) and text[index] not in "(),":
            index += 1

        label = text[start:index].strip()

        if not label:
            raise ValueError("A node is missing its label.")

        return label

    def parse_node():
        nonlocal index

        skip_spaces()
        label = read_label()
        skip_spaces()

        # A label without parentheses is a leaf / terminal.
        if index >= len(text) or text[index] != "(":
            return (label, [])

        index += 1
        children = []
        skip_spaces()

        if index < len(text) and text[index] == ")":
            raise ValueError(
                "Invalid tree: a node must contain at least one child."
            )

        while True:
            skip_spaces()

            if index >= len(text):
                raise ValueError("Invalid tree: missing closing ')'.")

            if text[index] in ",)":
                raise ValueError("Invalid tree: a child is missing.")

            child = parse_node()
            children.append(child)
            skip_spaces()

            if index >= len(text):
                raise ValueError("Invalid tree: missing closing ')'.")

            if text[index] == ",":
                index += 1
                skip_spaces()

                if index >= len(text) or text[index] == ")":
                    raise ValueError(
                        "Invalid tree: a child is missing after the comma."
                    )
                continue

            if text[index] == ")":
                index += 1
                break

            raise ValueError("Invalid tree: expected ',' or ')'.")

        return (label, children)

    root = parse_node()
    skip_spaces()

    if index != len(text):
        raise ValueError("Invalid tree: extra characters found after the tree.")

    return root


# =========================================================
# TRAVERSAL, YIELD, AND VISUALIZATION HELPERS
# =========================================================

def get_yield_and_steps(node):
    """Return terminal labels and a readable left-to-right step list."""
    label, children = node
    terminals = []
    steps = []

    steps.append(f"Visiting node: {label}")

    if not children:
        terminals.append(label)
        steps.append(f"Found terminal: {label}")
        return terminals, steps

    for child in children:
        child_terminals, child_steps = get_yield_and_steps(child)
        terminals.extend(child_terminals)
        steps.extend(child_steps)

    return terminals, steps


def tree_layout(node, depth=0, x_positions=None, counter=None, edges=None):
    """Build simple coordinates for drawing the tree on a Canvas."""
    if x_positions is None:
        x_positions = {}
    if counter is None:
        counter = [0]
    if edges is None:
        edges = []

    label, children = node

    if not children:
        x = counter[0]
        counter[0] += 1
    else:
        child_xs = []
        for child in children:
            child_x = tree_layout(
                child, depth + 1, x_positions, counter, edges
            )
            child_xs.append(child_x)
        x = (child_xs[0] + child_xs[-1]) / 2

    x_positions[id(node)] = (x, depth)

    for child in children:
        edges.append((node, child))

    return x


def draw_tree(tree):
    tree_canvas.delete("all")

    positions = {}
    edges = []
    tree_layout(tree, x_positions=positions, edges=edges)

    leaf_count = max(1, sum(1 for _ in iter_leaves(tree)))
    width = max(tree_canvas.winfo_width(), leaf_count * 100, 500)
    depth = max((d for _, d in positions.values()), default=0)
    height = max(220, (depth + 1) * 90 + 40)

    tree_canvas.configure(scrollregion=(0, 0, width, height))

    margin_x = 50
    usable_width = max(width - 100, 1)
    max_x = max((x for x, _ in positions.values()), default=1)
    max_x = max(max_x, 1)

    coords = {}
    for node_id, (x, depth_value) in positions.items():
        px = margin_x + (x / max_x) * usable_width
        py = 35 + depth_value * 90
        coords[node_id] = (px, py)

    for parent, child in edges:
        x1, y1 = coords[id(parent)]
        x2, y2 = coords[id(child)]
        tree_canvas.create_line(x1, y1 + 18, x2, y2 - 18, width=2, fill="#6B7A90")

    for node_id, (x, y) in coords.items():
        node_label = find_label_by_id(tree, node_id)
        tree_canvas.create_oval(
            x - 34, y - 18, x + 34, y + 18,
            fill="#DCEBFA", outline="#12355B", width=2
        )
        tree_canvas.create_text(
            x, y, text=node_label, font=("Arial", 10, "bold"),
            fill="#12355B"
        )


def iter_leaves(node):
    label, children = node
    if not children:
        yield label
    else:
        for child in children:
            yield from iter_leaves(child)


def find_label_by_id(node, target_id):
    if id(node) == target_id:
        return node[0]
    for child in node[1]:
        result = find_label_by_id(child, target_id)
        if result is not None:
            return result
    return None


# =========================================================
# APPLICATION ACTIONS
# =========================================================

last_result_text = ""


def generate_yield():
    global last_result_text

    text = input_box.get("1.0", tk.END).strip()

    try:
        tree = parse_tree(text)
        terminals, steps = get_yield_and_steps(tree)

        yield_text = " ".join(terminals)
        traversal_text = " → ".join(terminals)

        result_text = (
            "LEFT-TO-RIGHT TERMINAL TRAVERSAL\n"
            "--------------------------------\n"
            f"{traversal_text}\n\n"
            "TERMINAL YIELD\n"
            "--------------\n"
            f"{yield_text}\n\n"
            f"Total terminals: {len(terminals)}\n\n"
            "STEP-BY-STEP ANALYSIS\n"
            "--------------------\n"
            + "\n".join(
                f"{number}. {step}"
                for number, step in enumerate(steps, start=1)
            )
        )

        output_box.config(state="normal", fg="#12355B")
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, result_text)
        output_box.config(state="disabled")

        status_label.config(text="✓ Valid Parse Tree", fg="green")
        last_result_text = result_text

        draw_tree(tree)

    except (ValueError, RecursionError) as error:
        output_box.config(state="normal", fg="red")
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, f"INVALID INPUT\n\n{error}")
        output_box.config(state="disabled")

        status_label.config(text="✗ Invalid Parse Tree", fg="red")
        tree_canvas.delete("all")
        last_result_text = ""


def clear_all():
    global last_result_text

    input_box.delete("1.0", tk.END)

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.config(state="disabled")

    tree_canvas.delete("all")
    status_label.config(text="Enter a parse tree to begin.", fg="#555555")
    last_result_text = ""


def load_example():
    example = "S(NP(Det(The),N(student)),VP(V(studies),NP(N(TOC))))"
    input_box.delete("1.0", tk.END)
    input_box.insert("1.0", example)
    status_label.config(
        text="Example loaded. Click Generate Yield.",
        fg="#555555"
    )


def export_result():
    if not last_result_text:
        messagebox.showinfo(
            "No Result",
            "Generate a valid terminal yield before exporting."
        )
        return

    file_path = filedialog.asksaveasfilename(
        title="Save Yield Finder Result",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not file_path:
        return

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(last_result_text)
        messagebox.showinfo("Export Successful", "Your result was saved.")
    except OSError as error:
        messagebox.showerror("Export Failed", str(error))


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()
root.title("Yield Finder - Parse Tree Terminal Analyzer")
root.geometry("1050x850")
root.minsize(850, 700)
root.configure(bg="#F4F7FB")

title_label = tk.Label(
    root, text="YIELD FINDER", font=("Arial", 24, "bold"),
    bg="#F4F7FB", fg="#12355B"
)
title_label.pack(pady=(18, 3))

subtitle_label = tk.Label(
    root, text="Parse Tree Terminal Yield Analyzer",
    font=("Arial", 12), bg="#F4F7FB", fg="#555555"
)
subtitle_label.pack(pady=(0, 12))

input_title = tk.Label(
    root, text="Enter Complete Parse Tree:",
    font=("Arial", 12, "bold"), bg="#F4F7FB", fg="#222222"
)
input_title.pack(anchor="w", padx=28)

input_box = tk.Text(
    root, height=4, font=("Consolas", 11),
    wrap="word", relief="solid", borderwidth=1
)
input_box.pack(fill="x", padx=28, pady=(6, 7))

help_label = tk.Label(
    root,
    text="Example format: S(NP(Det(The),N(student)),VP(V(studies)))",
    font=("Arial", 9), bg="#F4F7FB", fg="#666666"
)
help_label.pack(anchor="w", padx=28)

button_frame = tk.Frame(root, bg="#F4F7FB")
button_frame.pack(pady=10)

tk.Button(
    button_frame, text="Generate Yield", command=generate_yield,
    font=("Arial", 10, "bold"), bg="#12355B", fg="white",
    padx=15, pady=7, cursor="hand2"
).pack(side="left", padx=5)

tk.Button(
    button_frame, text="Load Example", command=load_example,
    font=("Arial", 10), padx=12, pady=7, cursor="hand2"
).pack(side="left", padx=5)

tk.Button(
    button_frame, text="Export Result", command=export_result,
    font=("Arial", 10), padx=12, pady=7, cursor="hand2"
).pack(side="left", padx=5)

tk.Button(
    button_frame, text="Clear", command=clear_all,
    font=("Arial", 10), padx=12, pady=7, cursor="hand2"
).pack(side="left", padx=5)

status_label = tk.Label(
    root, text="Enter a parse tree to begin.",
    font=("Arial", 10, "bold"), bg="#F4F7FB", fg="#555555"
)
status_label.pack(pady=(0, 8))

panels = tk.Frame(root, bg="#F4F7FB")
panels.pack(fill="both", expand=True, padx=28, pady=(0, 18))

left_panel = tk.Frame(panels, bg="#F4F7FB")
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

right_panel = tk.Frame(panels, bg="#F4F7FB")
right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))

tk.Label(
    left_panel, text="Parse Tree Visualization",
    font=("Arial", 11, "bold"), bg="#F4F7FB", fg="#222222"
).pack(anchor="w", pady=(0, 5))

tree_frame = tk.Frame(left_panel, bg="white", relief="solid", borderwidth=1)
tree_frame.pack(fill="both", expand=True)

tree_canvas = tk.Canvas(
    tree_frame, bg="white", highlightthickness=0,
    scrollregion=(0, 0, 600, 400)
)
tree_scrollbar = tk.Scrollbar(
    tree_frame, orient="vertical", command=tree_canvas.yview
)
tree_canvas.configure(yscrollcommand=tree_scrollbar.set)
tree_scrollbar.pack(side="right", fill="y")
tree_canvas.pack(side="left", fill="both", expand=True)

tk.Label(
    right_panel, text="Analysis and Terminal Yield",
    font=("Arial", 11, "bold"), bg="#F4F7FB", fg="#222222"
).pack(anchor="w", pady=(0, 5))

output_box = tk.Text(
    right_panel, font=("Consolas", 10), wrap="word",
    relief="solid", borderwidth=1, state="disabled"
)
output_box.pack(fill="both", expand=True)

root.mainloop()
