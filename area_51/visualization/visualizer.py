"""
Module: visualizer.py
Trực quan hóa puzzle Area 51 và nghiệm.
- Vẽ lưới puzzle với tất cả ký hiệu
- Vẽ nghiệm với hàng rào được tô màu
- Tạo GIF animation quá trình giải (subtour elimination)
"""
 
from __future__ import annotations
import os
import sys
from typing import Dict, List, Optional
 
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.data_loader import PuzzleData
 
 
# ---------------------------------------------------------------------------
# Màu sắc & style
# ---------------------------------------------------------------------------
COLORS = {
    "bg":          "#0d1117",
    "grid":        "#21262d",
    "fence":       "#58a6ff",
    "fence_glow":  "#1f6feb",
    "inside":      "#6b7d96",
    "outside":     "#1b2330",
    "alien":       "#3fb950",
    "cactus":      "#f85149",
    "uncircled":   "#e6edf3",
    "circled_bg":  "#388bfd33",
    "circled_fg":  "#79c0ff",
    "black_node":  "#000000",
    "white_node":  "#ffffff",
    "node_border": "#8b949e",
    "text":        "#e6edf3",
    "subtitle":    "#8b949e",
}
 
CELL_SIZE = 1.0   # đơn vị chiều rộng ô trong plot
FENCE_LW  = 3.5   # độ dày cạnh hàng rào
 
# Cache ảnh icon — load mỗi file đúng 1 lần
_IMG_CACHE: Dict[str, np.ndarray] = {}
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _cell_center(i: int, j: int):
    """Tọa độ matplotlib của tâm ô (i, j). Trục y lật ngược."""
    x = j * CELL_SIZE + CELL_SIZE / 2
    y = -(i * CELL_SIZE + CELL_SIZE / 2)
    return x, y
 
 
def _node_pos(i: int, j: int):
    """Tọa độ matplotlib của điểm nút (i, j)."""
    return j * CELL_SIZE, -i * CELL_SIZE
 
 
def _load_icon(path: str) -> np.ndarray:
    """
    Load ảnh từ đĩa, cache lại, và tự động xử lý nền trắng cho JPG.
    Trả về mảng RGBA float32 trong khoảng [0, 1].
    """
    if path in _IMG_CACHE:
        return _IMG_CACHE[path]
 
    img = mpimg.imread(path)
 
    # Normalize uint8 → float32
    if img.dtype == np.uint8:
        img = img.astype(np.float32) / 255.0
 
    # Nếu chỉ có 3 channels (JPG) → thêm alpha, xóa nền sáng
    if img.ndim == 3 and img.shape[2] == 3:
        white_mask = (
            (img[:, :, 0] > 0.88) &
            (img[:, :, 1] > 0.88) &
            (img[:, :, 2] > 0.88)
        ).astype(np.float32)
        alpha = 1.0 - white_mask
        img = np.dstack([img, alpha])
 
    _IMG_CACHE[path] = img
    return img
 
 
def _icon_zoom(img: np.ndarray, fraction: float = 0.3, dpi: int = 150) -> float:
    """
    Tính zoom để ảnh chiếm `fraction` của CELL_SIZE ở dpi đã cho.
    fraction=0.5 → ảnh chiếm ~50% ô (còn khoảng trống viền).
    """
    px = img.shape[1]  # chiều rộng ảnh (pixels)
    return (CELL_SIZE * fraction * dpi) / (px * 1.0)
 
 
# ---------------------------------------------------------------------------
# Các lớp vẽ
# ---------------------------------------------------------------------------
 
def _draw_grid(ax: plt.Axes, nR: int, nC: int) -> None:
    """Vẽ lưới nền và điểm nút."""
    ax.set_facecolor(COLORS["bg"])
    for i in range(nR + 1):
        y = -i * CELL_SIZE
        ax.plot([0, nC * CELL_SIZE], [y, y],
                color=COLORS["grid"], lw=0.8, zorder=1)
    for j in range(nC + 1):
        x = j * CELL_SIZE
        ax.plot([x, x], [0, -nR * CELL_SIZE],
                color=COLORS["grid"], lw=0.8, zorder=1)
    for i in range(nR + 1):
        for j in range(nC + 1):
            x, y = _node_pos(i, j)
            ax.plot(x, y, "o", color=COLORS["grid"], markersize=3, zorder=2)
 
 
def _draw_inside_cells(ax: plt.Axes, nR: int, nC: int,
                       inside_vals: Optional[Dict]) -> None:
    """Tô màu các ô bên trong hàng rào."""
    if inside_vals is None:
        return
    for i in range(nR):
        for j in range(nC):
            if inside_vals.get((i, j), 0) > 0.5:
                x = j * CELL_SIZE
                y = -(i + 1) * CELL_SIZE
                rect = plt.Rectangle(
                    (x, y), CELL_SIZE, CELL_SIZE,
                    color=COLORS["inside"], zorder=0.5, lw=0
                )
                ax.add_patch(rect)
 
 
def _draw_fence(ax: plt.Axes,
                h_vals: Optional[Dict],
                v_vals: Optional[Dict],
                nR: int, nC: int) -> None:
    """Vẽ hàng rào (các cạnh đang bật)."""
    if h_vals is None:
        return
 
    def _edge(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2],
                color=COLORS["fence"], lw=FENCE_LW,
                solid_capstyle="round", zorder=5)
        ax.plot([x1, x2], [y1, y2],
                color=COLORS["fence_glow"], lw=FENCE_LW + 4,
                solid_capstyle="round", alpha=0.3, zorder=4)
 
    for i in range(nR + 1):
        for j in range(nC):
            if h_vals.get((i, j), 0) > 0.5:
                x1, y1 = _node_pos(i, j)
                x2, y2 = _node_pos(i, j + 1)
                _edge(x1, y1, x2, y2)
 
    for i in range(nR):
        for j in range(nC + 1):
            if v_vals.get((i, j), 0) > 0.5:
                x1, y1 = _node_pos(i, j)
                x2, y2 = _node_pos(i + 1, j)
                _edge(x1, y1, x2, y2)
 
 
def _draw_symbols(ax: plt.Axes, puzzle: PuzzleData) -> None:
    """Vẽ tất cả ký hiệu trong ô: số thường, số có vòng tròn, Alien, Cactus."""
 
    _dir        = os.path.dirname(os.path.abspath(__file__))
    alien_path  = os.path.join(_dir, "alien.jpg")
    cactus_path = os.path.join(_dir, "cactus.png")
 
    # ── Số không có vòng tròn ────────────────────────────────────────────────
    for (i, j), val in puzzle.uncircled.items():
        x, y = _cell_center(i, j)
        ax.text(x, y, str(val),
                ha="center", va="center",
                fontsize=13, fontweight="bold",
                color=COLORS["uncircled"], zorder=10,
                fontfamily="monospace")
 
    # ── Số có vòng tròn ──────────────────────────────────────────────────────
    for (i, j), val in puzzle.circled.items():
        x, y = _cell_center(i, j)
        circ = Circle((x, y), 0.32,
                      color=COLORS["circled_bg"],
                      ec=COLORS["circled_fg"], lw=1.5, zorder=9)
        ax.add_patch(circ)
        ax.text(x, y, str(val),
                ha="center", va="center",
                fontsize=11, fontweight="bold",
                color=COLORS["circled_fg"], zorder=10)
 
    # ── Alien ────────────────────────────────────────────────────────────────
    if puzzle.aliens:
        alien_img  = _load_icon(alien_path)
        alien_zoom = _icon_zoom(alien_img)
        for (i, j) in puzzle.aliens:
            x, y = _cell_center(i, j)
            im = OffsetImage(alien_img, zoom=alien_zoom)
            ab = AnnotationBbox(im, (x, y), frameon=False, zorder=10)
            ax.add_artist(ab)
 
    # ── Cactus ───────────────────────────────────────────────────────────────
    if puzzle.cactus:
        cactus_img  = _load_icon(cactus_path)
        cactus_zoom = _icon_zoom(cactus_img)
        for (i, j) in puzzle.cactus:
            x, y = _cell_center(i, j)
            im = OffsetImage(cactus_img, zoom=cactus_zoom)
            ab = AnnotationBbox(im, (x, y), frameon=False, zorder=10)
            ax.add_artist(ab)
 
 
def _draw_masyu_nodes(ax: plt.Axes, puzzle: PuzzleData) -> None:
    """Vẽ black/white nodes Masyu trên ma trận đỉnh."""
    r = 0.13
    for (i, j) in puzzle.black_nodes:
        x, y = _node_pos(i, j)
        ax.add_patch(Circle((x, y), r,
                            color=COLORS["black_node"],
                            ec=COLORS["black_node"], lw=1.5, zorder=8))
    for (i, j) in puzzle.white_nodes:
        x, y = _node_pos(i, j)
        ax.add_patch(Circle((x, y), r,
                            color=COLORS["white_node"],
                            ec=COLORS["node_border"], lw=1.5, zorder=8))
 
 
def _setup_axes(ax: plt.Axes, nR: int, nC: int) -> None:
    """Thiết lập axes chung."""
    ax.set_facecolor(COLORS["bg"])
    ax.set_xlim(-0.5, nC * CELL_SIZE + 0.5)
    ax.set_ylim(-nR * CELL_SIZE - 0.5, 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
 
 
def _add_legend(ax: plt.Axes) -> None:
    """Thêm legend vào góc dưới phải."""
    legend_elements = [
        mpatches.Patch(facecolor=COLORS["alien"],  label="Alien (inside)"),
        mpatches.Patch(facecolor=COLORS["cactus"], label="Cactus (outside)"),
        Line2D([0], [0], color=COLORS["fence"], lw=2, label="Fence"),
        mpatches.Patch(facecolor=COLORS["inside"], label="Inside region"),
    ]
    ax.legend(handles=legend_elements, loc="upper right",
              facecolor=COLORS["grid"], edgecolor=COLORS["subtitle"],
              labelcolor=COLORS["text"], fontsize=8,
              bbox_to_anchor=(1.0, 0.0))
 
 
# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
 
def draw_puzzle(puzzle: PuzzleData,
                h_vals: Optional[Dict] = None,
                v_vals: Optional[Dict] = None,
                inside_vals: Optional[Dict] = None,
                title: str = "Area 51 Puzzle",
                save_path: Optional[str] = None) -> plt.Figure:
    """
    Vẽ puzzle (và nghiệm nếu có).
 
    Args:
        puzzle:      Dữ liệu puzzle.
        h_vals:      Giá trị cạnh ngang từ nghiệm (None = chưa có nghiệm).
        v_vals:      Giá trị cạnh dọc từ nghiệm.
        inside_vals: Giá trị inside từ nghiệm.
        title:       Tiêu đề hình.
        save_path:   Đường dẫn lưu hình (None = không lưu).
 
    Returns:
        matplotlib Figure.
    """
    nR, nC = puzzle.nR, puzzle.nC
    fig, ax = plt.subplots(
        figsize=(nC * CELL_SIZE + 1.5, nR * CELL_SIZE + 1.5),
        facecolor=COLORS["bg"]
    )
    _setup_axes(ax, nR, nC)
 
    _draw_inside_cells(ax, nR, nC, inside_vals)
    _draw_grid(ax, nR, nC)
    _draw_fence(ax, h_vals, v_vals, nR, nC)
    _draw_symbols(ax, puzzle)
    _draw_masyu_nodes(ax, puzzle)
    _add_legend(ax)
 
    ax.set_title(title, color=COLORS["text"], fontsize=14,
                 fontweight="bold", pad=10, fontfamily="monospace")
 
    plt.tight_layout()
 
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=COLORS["bg"])
        print(f"Đã lưu hình: {save_path}")
 
    return fig
 
 
def create_solution_gif(puzzle: PuzzleData,
                        iteration_frames: List[Dict],
                        save_path: str,
                        fps: int = 2) -> None:
    """
    Tạo GIF animation từ các frame qua từng iteration subtour elimination.
 
    Args:
        puzzle:           Dữ liệu puzzle.
        iteration_frames: List các dict {h_vals, v_vals, inside_vals, title}.
        save_path:        Đường dẫn lưu .gif.
        fps:              Số frame mỗi giây.
    """
    import matplotlib.animation as animation
 
    nR, nC = puzzle.nR, puzzle.nC
    fig, ax = plt.subplots(
        figsize=(nC * CELL_SIZE + 1.5, nR * CELL_SIZE + 1.5),
        facecolor=COLORS["bg"]
    )
 
    def render_frame(frame_data: Dict) -> None:
        ax.clear()
        _setup_axes(ax, nR, nC)
        _draw_inside_cells(ax, nR, nC, frame_data.get("inside_vals"))
        _draw_grid(ax, nR, nC)
        _draw_fence(ax, frame_data.get("h_vals"), frame_data.get("v_vals"), nR, nC)
        _draw_symbols(ax, puzzle)
        _draw_masyu_nodes(ax, puzzle)
        ax.set_title(frame_data.get("title", "Area 51"),
                     color=COLORS["text"], fontsize=13,
                     fontweight="bold", fontfamily="monospace")
 
    def animate(frame_idx: int):
        render_frame(iteration_frames[frame_idx])
        return []
 
    ani = animation.FuncAnimation(
        fig, animate,
        frames=len(iteration_frames),
        interval=1000 // fps,
        repeat=True
    )
 
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    ani.save(save_path, writer="pillow", fps=fps,
             savefig_kwargs={"facecolor": COLORS["bg"]})
    plt.close(fig)
    print(f"Đã lưu GIF: {save_path}")