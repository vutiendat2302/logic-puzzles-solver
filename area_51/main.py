import os
import argparse

from data.data_loader import load_puzzle, print_puzzle_summary
from solvers.solver import Area51Solver
from visualization.visualizer import draw_puzzle, create_solution_gif

def main():
    parser = argparse.ArgumentParser(description="Giải Area 51 Puzzle bằng Gurobi MILP")
    parser.add_argument("-f", "--file", type=str, required=True,
                        help="Đường dẫn tới file JSON chứa data puzzle")
    parser.add_argument("-o", "--output_dir", type=str, default="results",
                        help="Thư mục lưu ảnh kết quả")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="In log chi tiết của Gurobi")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[!] Lỗi: Không tìm thấy file '{args.file}'")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    gifs_dir = os.path.join(args.output_dir, "gifs")
    os.makedirs(gifs_dir, exist_ok=True)

    filename = os.path.basename(args.file).replace(".json", "")
    category = os.path.basename(os.path.dirname(args.file))

    # 3. Load dữ liệu
    print(f"\n[*] Đang nạp dữ liệu từ: {args.file} ...")
    puzzle = load_puzzle(args.file)
    print_puzzle_summary(puzzle)

    # 4. Vẽ map gốc
    print("\n[*] Đang vẽ map gốc...")
    empty_map_path = os.path.join(
            args.output_dir,
            f"{category}_{filename}_empty.png"
        )
    draw_puzzle(puzzle, title=f"Area 51 - {filename} (Empty)", save_path=empty_map_path)

    # 5. Giải
    print("\n[*] Bắt đầu giải bằng Gurobi...")
    solver = Area51Solver(puzzle, verbose=args.verbose)
    success = solver.solve()

    # 6. Kết quả
    if success:
        h_vals, v_vals, inside_vals = solver.get_solution()
        print(f"\n[+] GIẢI THÀNH CÔNG sau {solver.num_iterations} vòng lặp!")

        # Vẽ nghiệm PNG
        solution_map_path = os.path.join(
            args.output_dir,
            f"{category}_{filename}_solution.png"
        )
        print(f"[*] Đang vẽ nghiệm ra file: {solution_map_path}")
        draw_puzzle(
            puzzle,
            h_vals=h_vals,
            v_vals=v_vals,
            inside_vals=inside_vals,
            title=f"Area 51 - {filename} (Solved)",
            save_path=solution_map_path
        )

        # Tạo GIF animation nếu solver có lưu iteration_frames
        # if hasattr(solver, "iteration_frames") and solver.iteration_frames:
        #     gif_path = os.path.join(gifs_dir, f"{filename}_solve.gif")
        #     print(f"[*] Đang tạo GIF animation: {gif_path}")
        #     create_solution_gif(
        #         puzzle,
        #         iteration_frames=solver.iteration_frames,
        #         save_path=gif_path,
        #         fps=2
        #     )
        # else:
        #     print("[!] Solver không có iteration_frames — bỏ qua GIF.")

        print("Done")
    else:
        print("\n[-] Bài toán INFEASIBLE hoặc quá thời gian, không tìm được nghiệm.")

if __name__ == "__main__":
    main()