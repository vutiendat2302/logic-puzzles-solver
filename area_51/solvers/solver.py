"""
Module: solver.py
Giải puzzle Area 51 bằng Gurobi MILP với subtour elimination.

Quy trình:
    1. Khởi tạo mô hình M với tất cả ràng buộc (Slitherlink, Masyu, Alien/Cactus)
    2. Giải M
    3. Kiểm tra nghiệm: nếu có nhiều hơn 1 chu trình -> thêm subtour cut -> lặp lại
    4. Trả về nghiệm duy nhất
"""

from __future__ import annotations
import os
import sys
from typing import Dict, Tuple, List, Optional

import gurobipy as gp
from gurobipy import GRB

# Thêm thư mục cha vào path để import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_loader import PuzzleData, load_puzzle
from models.constraints import (
    add_all_variables,
    add_slitherlink_constraints,
    add_inside_constraints,
    add_masyu_constraints,
)


# ---------------------------------------------------------------------------
# Hàm hỗ trợ kiểm tra chu trình
# ---------------------------------------------------------------------------

def _extract_edges(h_vals: Dict, v_vals: Dict, nR: int, nC: int):
    """
    Trích xuất danh sách cạnh đang bật từ nghiệm hiện tại.
    Trả về list of ((r1,c1),(r2,c2)).
    """
    edges = []
    for i in range(nR + 1):
        for j in range(nC):
            if h_vals[i, j] > 0.5:
                edges.append(((i, j), (i, j + 1)))
    for i in range(nR):
        for j in range(nC + 1):
            if v_vals[i, j] > 0.5:
                edges.append(((i, j), (i + 1, j)))
    return edges


def _find_cycles(edges: list):
    """
    Dùng DFS tìm tất cả các chu trình trong tập cạnh.
    Trả về list các chu trình, mỗi chu trình là list các cạnh.
    """
    from collections import defaultdict

    adj = defaultdict(list)
    for (u, v) in edges:
        adj[u].append((v, (u, v)))
        adj[v].append((u, (u, v)))

    visited_nodes = set()
    cycles = []

    def dfs_cycle(start):
        """DFS để tìm 1 chu trình bắt đầu từ start."""
        path_nodes = []
        path_edges = []
        visited_in_path = set()

        def dfs(node, came_from_edge):
            if node in visited_nodes:
                return
            if node in visited_in_path:
                # Tìm thấy chu trình
                idx = path_nodes.index(node)
                cycle_edges = path_edges[idx:]
                cycles.append(cycle_edges)
                return

            visited_in_path.add(node)
            path_nodes.append(node)

            for neighbor, edge in adj[node]:
                if edge != came_from_edge:
                    path_edges.append(edge)
                    dfs(neighbor, edge)
                    if path_edges and path_edges[-1] == edge:
                        path_edges.pop()

            path_nodes.pop()
            visited_in_path.discard(node)

        dfs(start, None)

    # Cách đơn giản hơn: tìm các thành phần liên thông
    all_nodes = set()
    for (u, v) in edges:
        all_nodes.add(u)
        all_nodes.add(v)

    adj2 = defaultdict(set)
    edge_set = set()
    for (u, v_node) in edges:
        e = (min(u, v_node), max(u, v_node))
        adj2[u].add(v_node)
        adj2[v_node].add(u)
        edge_set.add(e)

    visited = set()
    components = []

    for start in all_nodes:
        if start in visited:
            continue
        component_nodes = []
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component_nodes.append(node)
            for nb in adj2[node]:
                if nb not in visited:
                    stack.append(nb)

        # Thu thập cạnh của component này
        comp_edges = []
        for (u, v_node) in edges:
            if u in set(component_nodes):
                comp_edges.append((u, v_node))

        components.append((component_nodes, comp_edges))

    return components


def _add_subtour_cut(m: gp.Model, h, v, cycle_edges: list) -> None:
    """
    Thêm ràng buộc cắt chu trình C:
    sum_{e in C} x_e <= |C| - 1
    """
    expr = gp.LinExpr()
    count = 0

    for (u, v_node) in cycle_edges:
        i1, j1 = u
        i2, j2 = v_node
        if i1 == i2:  # cạnh ngang
            j_min = min(j1, j2)
            expr += h[i1, j_min]
        else:  # cạnh dọc
            i_min = min(i1, i2)
            expr += v[i_min, j1]
        count += 1

    if count > 0:
        m.addConstr(expr <= count - 1, name=f"subtour_cut_{m.NumConstrs}")


# ---------------------------------------------------------------------------
# Hàm chính: giải puzzle
# ---------------------------------------------------------------------------

class Area51Solver:
    """
    Giải puzzle Area 51 bằng MILP + subtour elimination.
    """

    def __init__(self, puzzle: PuzzleData, verbose: bool = True):
        self.puzzle = puzzle
        self.verbose = verbose

        # Gurobi model
        self.m = gp.Model("Area51")
        if not verbose:
            self.m.setParam("OutputFlag", 0)
        self.m.setParam("TimeLimit", 2000)

        # Biến
        self.h, self.v, self.p, self.inside = add_all_variables(self.m, puzzle)

        # Ràng buộc
        add_slitherlink_constraints(self.m, puzzle, self.h, self.v, self.p)
        add_inside_constraints(self.m, puzzle, self.h, self.v, self.inside)
        add_masyu_constraints(self.m, puzzle, self.h, self.v)

        self.m.update()

        # Kết quả
        self.solution_h: Optional[Dict] = None
        self.solution_v: Optional[Dict] = None
        self.solution_inside: Optional[Dict] = None
        self.num_iterations: int = 0
        self.iteration_frames: List[Dict] = []


    def solve(self) -> bool:
        nR, nC = self.puzzle.nR, self.puzzle.nC

        while True:
            self.num_iterations += 1
            if self.verbose:
                print(f"\n[Iter {self.num_iterations}] Đang giải mô hình...")

            self.m.optimize()

            if self.m.Status == GRB.INFEASIBLE:
                if self.verbose:
                    print("Mô hình INFEASIBLE - không có nghiệm.")
                    print("Đang tính IIS...")
                    self.m.computeIIS()
                    self.m.write("infeasible.ilp")
                    print("Đã ghi file infeasible.ilp")
                    
                return False

            if self.m.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
                if self.verbose:
                    print(f"Gurobi status: {self.m.Status}")
                return False

            h_vals = {(i, j): self.h[i, j].X for i in range(nR + 1) for j in range(nC)}
            v_vals = {(i, j): self.v[i, j].X for i in range(nR) for j in range(nC + 1)}
            inside_snap = {
                (i, j): self.inside[i, j].X
                for i in range(nR) for j in range(nC)
            }

            edges = _extract_edges(h_vals, v_vals, nR, nC)
            if not edges:
                if self.verbose:
                    print("Không có cạnh nào được chọn.")
                return False

            components = _find_cycles(edges)

            # Lưu frame GIF
            self.iteration_frames.append({
                "h_vals":      h_vals,
                "v_vals":      v_vals,
                "inside_vals": inside_snap,
                "title":       f"Iter {self.num_iterations} — {len(components)} component(s)",
            })

            if self.verbose:
                print(f"  Số thành phần liên thông: {len(components)}")

            if len(components) == 1:
                if self.verbose:
                    print("✓ Tìm được nghiệm hợp lệ với 1 chu trình duy nhất!")
                self.solution_h = h_vals
                self.solution_v = v_vals
                self.solution_inside = inside_snap  # dùng lại, khỏi tính lại
                return True

            if self.verbose:
                print(f"  Phát hiện {len(components)} chu trình -> thêm subtour cuts...")
            for comp_nodes, comp_edges in components:
                if len(comp_edges) > 0:
                    _add_subtour_cut(self.m, self.h, self.v, comp_edges)

    def get_solution(self):
        """Trả về (h_vals, v_vals, inside_vals) hoặc None nếu chưa giải."""
        if self.solution_h is None:
            return None
        return self.solution_h, self.solution_v, self.solution_inside


def solve_puzzle(data_path: str, verbose: bool = True) -> Optional[Area51Solver]:
    """
    Hàm tiện ích: tải puzzle và giải.
    Trả về solver đã có nghiệm, hoặc None nếu thất bại.
    """
    puzzle = load_puzzle(data_path)
    solver = Area51Solver(puzzle, verbose=verbose)

    success = solver.solve()
    if success:
        return solver
    return None


if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "8x8.json")
    solver = solve_puzzle(data_path, verbose=True)
    if solver:
        print(f"\nGiải thành công sau {solver.num_iterations} vòng lặp!")
    else:
        print("\nKhông tìm được nghiệm.")