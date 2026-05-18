"""
Module: constraints.py
Mô hình hóa tất cả ràng buộc của puzzle Area 51 bằng MILP (Gurobi).

Biến quyết định:
    h[i,j]  = 1 nếu có cạnh ngang từ điểm (i,j) đến (i,j+1)
                0 ≤ i ≤ nR, 0 ≤ j < nC
    v[i,j]  = 1 nếu có cạnh dọc từ điểm (i,j) đến (i+1,j)
                0 ≤ i < nR, 0 ≤ j ≤ nC
    p[i,j]  = 1 nếu điểm (i,j) được nối vào chu trình
                0 ≤ i ≤ nR, 0 ≤ j ≤ nC
    inside[i,j] = 1 nếu ô (i,j) nằm trong chu trình
                0 ≤ i < nR, 0 ≤ j < nC
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gurobipy import Model
    from data.data_loader import PuzzleData


def add_all_variables(m: "Model", puzzle: "PuzzleData"):
    """Thêm tất cả biến quyết định vào mô hình Gurobi."""
    import gurobipy as gp
    from gurobipy import GRB

    nR, nC = puzzle.nR, puzzle.nC

    # Cạnh ngang h[i,j]: điểm (i,j)-(i,j+1), i in [0..nR], j in [0..nC-1]
    h = m.addVars(nR + 1, nC, vtype=GRB.BINARY, name="h")

    # Cạnh dọc v[i,j]: điểm (i,j)-(i+1,j), i in [0..nR-1], j in [0..nC]
    v = m.addVars(nR, nC + 1, vtype=GRB.BINARY, name="v")

    # Điểm được nối p[i,j]: i in [0..nR], j in [0..nC]
    p = m.addVars(nR + 1, nC + 1, vtype=GRB.BINARY, name="p")

    # Ô nằm trong chu trình inside[i,j]: i in [0..nR-1], j in [0..nC-1]
    inside = m.addVars(nR, nC, vtype=GRB.BINARY, name="inside")

    m.update()
    return h, v, p, inside


def add_slitherlink_constraints(m: "Model", puzzle: "PuzzleData", h, v, p) -> None:
    """
    Ràng buộc Slitherlink:
    1. Số cạnh bao quanh ô (i,j) = uncircled[(i,j)] nếu có số.
    2. Mỗi điểm hoặc không được nối, hoặc có đúng 2 cạnh nối vào.
    3. p[i,j] = 1 iff tổng cạnh nối vào điểm (i,j) = 2.
    """
    nR, nC = puzzle.nR, puzzle.nC

    # Ràng buộc số không có vòng tròn
    for (i, j), val in puzzle.uncircled.items():
        # 4 cạnh quanh ô (i,j): top=h[i,j], bottom=h[i+1,j], left=v[i,j], right=v[i,j+1]
        m.addConstr(
            h[i, j] + h[i + 1, j] + v[i, j] + v[i, j + 1] == val,
            name=f"slither_cell_{i}_{j}"
        )

    # Ràng buộc điểm nối: tổng cạnh tại điểm (i,j) = 2*p[i,j]
    for i in range(nR + 1):
        for j in range(nC + 1):
            neighbors = []
            # Cạnh ngang sang phải: h[i,j]
            if j < nC:
                neighbors.append(h[i, j])
            # Cạnh ngang sang trái: h[i,j-1]
            if j > 0:
                neighbors.append(h[i, j - 1])
            # Cạnh dọc xuống: v[i,j]
            if i < nR:
                neighbors.append(v[i, j])
            # Cạnh dọc lên: v[i-1,j]
            if i > 0:
                neighbors.append(v[i - 1, j])

            m.addConstr(
                sum(neighbors) == 2 * p[i, j],
                name=f"node_{i}_{j}"
            )

def add_inside_constraints(m: "Model", puzzle: "PuzzleData", h, v, inside) -> None:
    """
    Ràng buộc inside[i,j]:
    - Alien, Circled numbers phải ở trong: inside[i,j] = 1
    - Cactus phải ở ngoài: inside[i,j] = 0
    - Circled numbers: Giá trị = Số ô nhìn thấy theo 4 hướng (cho đến khi đụng rào) + 1.
    """
    nR, nC = puzzle.nR, puzzle.nC
    import gurobipy as gp
    from gurobipy import GRB

    # 1. Ràng buộc Parity (Tia cắt ngang đếm số cạnh dọc)
    aux = m.addVars(nR, nC, vtype=GRB.INTEGER, lb=0, name="aux")
    for i in range(nR):
        for j in range(nC):
            cross_expr = gp.quicksum(v[i, k] for k in range(j + 1, nC + 1))
            m.addConstr(cross_expr == 2 * aux[i, j] + inside[i, j], name=f"parity_{i}_{j}")
            m.addConstr(aux[i, j] <= (nC - j) // 2 + 1, name=f"aux_ub_{i}_{j}")

    # 2. Ràng buộc vị trí Alien và Cactus
    for (i, j) in puzzle.aliens:
        m.addConstr(inside[i, j] == 1, name=f"alien_{i}_{j}")

    for (i, j) in puzzle.cactus:
        m.addConstr(inside[i, j] == 0, name=f"cactus_{i}_{j}")

    # 3. Ràng buộc tầm nhìn cho Circled Numbers (Corral)
    for (i, j), val in puzzle.circled.items():
        m.addConstr(inside[i, j] == 1, name=f"circled_inside_{i}_{j}")
        
        vis_vars = []
        
        # Nhìn Lên (Up)
        for k in range(1, i + 1):
            vis = m.addVar(vtype=GRB.BINARY, name=f"vis_u_{i}_{j}_{k}")
            vis_vars.append(vis)
            S_k = gp.quicksum(h[m, j] for m in range(i - k + 1, i + 1))
            m.addConstr(1 - S_k <= vis)
            m.addConstr(k * (1 - vis) >= S_k)
            
        # Nhìn Xuống (Down)
        for k in range(1, nR - i):
            vis = m.addVar(vtype=GRB.BINARY, name=f"vis_d_{i}_{j}_{k}")
            vis_vars.append(vis)
            S_k = gp.quicksum(h[m, j] for m in range(i + 1, i + k + 1))
            m.addConstr(1 - S_k <= vis)
            m.addConstr(k * (1 - vis) >= S_k)
            
        # Nhìn Trái (Left)
        for k in range(1, j + 1):
            vis = m.addVar(vtype=GRB.BINARY, name=f"vis_l_{i}_{j}_{k}")
            vis_vars.append(vis)
            S_k = gp.quicksum(v[i, m] for m in range(j - k + 1, j + 1))
            m.addConstr(1 - S_k <= vis)
            m.addConstr(k * (1 - vis) >= S_k)
            
        # Nhìn Phải (Right)
        for k in range(1, nC - j):
            vis = m.addVar(vtype=GRB.BINARY, name=f"vis_r_{i}_{j}_{k}")
            vis_vars.append(vis)
            S_k = gp.quicksum(v[i, m] for m in range(j + 1, j + k + 1))
            m.addConstr(1 - S_k <= vis)
            m.addConstr(k * (1 - vis) >= S_k)
            
        # Tổng số ô nhìn thấy (gồm 4 hướng + 1 ô gốc) phải bằng val
        m.addConstr(gp.quicksum(vis_vars) + 1 == val, name=f"circled_val_{i}_{j}")


def add_masyu_constraints(m: "Model", puzzle: "PuzzleData", h, v) -> None:
    """
    Ràng buộc Masyu (Tối ưu hóa không dùng Big-M để tăng tốc độ solve).
    """
    nR, nC = puzzle.nR, puzzle.nC
    import gurobipy as gp
    from gurobipy import GRB

    def _h(i, j): return h[i, j] if 0 <= i <= nR and 0 <= j < nC else 0
    def _v(i, j): return v[i, j] if 0 <= i < nR and 0 <= j <= nC else 0

    # ---- BLACK NODES ----
    for (i, j) in puzzle.black_nodes:
        # Trong Area 51, các chấm Masyu nằm trên lưới Đỉnh. Phải được đi qua.
        m.addConstr(_h(i, j - 1) + _h(i, j) + _v(i - 1, j) + _v(i, j) == 2, name=f"bk_visited_{i}_{j}")
        
        # Bắt buộc rẽ: Phải có đúng 1 ngang và 1 dọc chạm vào node
        m.addConstr(_h(i, j - 1) + _h(i, j) == 1, name=f"bk_turn_h_{i}_{j}")
        m.addConstr(_v(i - 1, j) + _v(i, j) == 1, name=f"bk_turn_v_{i}_{j}")

        # Đâm thẳng ít nhất 2 đoạn: Nếu đi mép nào, thì mép liền kề hướng đó cũng phải bật
        m.addConstr(_h(i, j - 1) <= _h(i, j - 2), name=f"bk_ext_hl_{i}_{j}")
        m.addConstr(_h(i, j) <= _h(i, j + 1), name=f"bk_ext_hr_{i}_{j}")
        m.addConstr(_v(i - 1, j) <= _v(i - 2, j), name=f"bk_ext_vu_{i}_{j}")
        m.addConstr(_v(i, j) <= _v(i + 1, j), name=f"bk_ext_vd_{i}_{j}")

    # ---- WHITE NODES ----
        for (i, j) in puzzle.white_nodes:
            m.addConstr(_h(i, j - 1) + _h(i, j) + _v(i - 1, j) + _v(i, j) == 2,
                    name=f"wh_visited_{i}_{j}")

        goes_h = m.addVar(vtype=GRB.BINARY, name=f"wh_h_{i}_{j}")

        # Chỉ cho phép đi ngang nếu có đủ 2 phía ngang
        can_go_h = int(j > 0 and j < nC)   # có cả trái lẫn phải
        can_go_v = int(i > 0 and i < nR)   # có cả trên lẫn dưới

        if can_go_h and can_go_v:
            # Bình thường — cho chọn
            m.addConstr(_h(i, j - 1) + _h(i, j) == 2 * goes_h,
                        name=f"wh_straight_h_{i}_{j}")
            m.addConstr(_v(i - 1, j) + _v(i, j) == 2 * (1 - goes_h),
                        name=f"wh_straight_v_{i}_{j}")
        elif can_go_h:
            # Nằm trên/dưới mép — chỉ có thể đi ngang
            m.addConstr(_h(i, j - 1) + _h(i, j) == 2, name=f"wh_straight_h_{i}_{j}")
        elif can_go_v:
            # Nằm trái/phải mép — chỉ có thể đi dọc
            m.addConstr(_v(i - 1, j) + _v(i, j) == 2, name=f"wh_straight_v_{i}_{j}")

        turn_h = _v(i-1,j-1)+_v(i,j-1)+_v(i-1,j+1)+_v(i,j+1)
        m.addConstr(turn_h >= goes_h, name=f"wh_turn_h_{i}_{j}")
        turn_v = _h(i-1,j-1)+_h(i-1,j)+_h(i+1,j-1)+_h(i+1,j)
        m.addConstr(turn_v >= (1 - goes_h), name=f"wh_turn_v_{i}_{j}")