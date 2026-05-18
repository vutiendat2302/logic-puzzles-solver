"""
Module: data_loader.py
Đọc và parse dữ liệu puzzle từ file JSON.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any


@dataclass
class PuzzleData:
    """Chứa toàn bộ dữ liệu của puzzle Area 51."""
    nR: int  # số hàng
    nC: int  # số cột

    # Slitherlink: các ô có số (không có vòng tròn)
    # F[(i,j)] = giá trị số
    uncircled: Dict[Tuple[int, int], int] = field(default_factory=dict)

    # Visibility: các ô có số có vòng tròn (circled)
    # K[(i,j)] = giá trị số
    circled: Dict[Tuple[int, int], int] = field(default_factory=dict)

    # Vị trí Alien (phải nằm trong hàng rào)
    aliens: List[Tuple[int, int]] = field(default_factory=list)

    # Vị trí Cactus/Triffid (phải nằm ngoài hàng rào)
    cactus: List[Tuple[int, int]] = field(default_factory=list)

    # Masyu nodes trên ma trận đỉnh (nR+1) x (nC+1)
    black_nodes: List[Tuple[int, int]] = field(default_factory=list)
    white_nodes: List[Tuple[int, int]] = field(default_factory=list)


def load_puzzle(filepath: str) -> PuzzleData:
    """
    Đọc file JSON và parse thành PuzzleData.

    Args:
        filepath: Đường dẫn đến file .json chứa dữ liệu puzzle.

    Returns:
        PuzzleData chứa toàn bộ thông tin ràng buộc.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cell_data: List[List[Any]] = raw["matrix_1"]["data"]
    node_data: List[List[Any]] = raw["matrix_2"]["data"]

    nR = len(cell_data)
    nC = len(cell_data[0])

    puzzle = PuzzleData(nR=nR, nC=nC)

    # Parse ma trận ô
    for i, row in enumerate(cell_data):
        for j, cell in enumerate(row):
            if cell is None:
                continue
            elif cell == "A":
                puzzle.aliens.append((i, j))
            elif cell == "C":
                puzzle.cactus.append((i, j))
            elif isinstance(cell, dict):
                # Circled number
                puzzle.circled[(i, j)] = cell["value"]
            elif isinstance(cell, (int, float)):
                puzzle.uncircled[(i, j)] = int(cell)

    # Parse ma trận đỉnh
    for i, row in enumerate(node_data):
        for j, node in enumerate(row):
            if node == "B":
                puzzle.black_nodes.append((i, j))
            elif node == "W":
                puzzle.white_nodes.append((i, j))

    return puzzle


def print_puzzle_summary(puzzle: PuzzleData) -> None:
    """In tóm tắt dữ liệu puzzle để kiểm tra."""
    print(f"=== PUZZLE AREA 51 ({puzzle.nR}x{puzzle.nC}) ===")
    print(f"Uncircled numbers: {puzzle.uncircled}")
    print(f"Circled numbers  : {puzzle.circled}")
    print(f"Aliens (inside)  : {puzzle.aliens}")
    print(f"Cactus (outside) : {puzzle.cactus}")
    print(f"Black nodes      : {puzzle.black_nodes}")
    print(f"White nodes      : {puzzle.white_nodes}")


if __name__ == "__main__":
    import os
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "easy", "8x8.json")
    puzzle = load_puzzle(data_path)
    print_puzzle_summary(puzzle)