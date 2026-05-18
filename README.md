# Puzzle Solver

- Giải các bài toán logic và puzzle bằng các kỹ thuật tối ưu hóa toán học và thuật toán 
- Dự án tập trung vào việc mô hình hóa các puzzle phức tạp thành hệ ràng buộc. 


## Mục tiêu dự án là nghiên cứu cách áp dụng:
- MILP (Mixed Integer Linear Programming)
- Heuristic Algorithms
- Các kỹ thuật tối ưu hóa tổ hợp 

để giải tự động các bài toán puzzle logic. 

## Các Puzzle hiện có: 

### 1. Area 51 Puzzle

- Chi tiết bài toán: 
[Area 51 README](./area_51/README.md)

- Area 51 Puzzle là một bài toán logic dạng hybrid puzzle,
kết hợp nhiều cơ chế nổi tiếng như:
    - Slitherlink
    - Masyu
    - Corral / Cave
    - Visibility Puzzle


- Mục tiêu của bài toán là xây dựng một hàng rào khép kín duy nhất: 
    - Bao toàn bộ người ngoài hành tinh
    - Ngăn các sinh vật TRIFFDS xâm nhập
    - Tạo thành một vòng lặp khép kín duy nhất
    - Không được tự cắt tại bất kỳ vị trí nào

- Bài toán chỉ có duy nhất một nghiệm

---

## Cấu Trúc Repository

```text
ConstraintPuzzleSolver/
│
├── README.md/                 # Tài liệu mô tả
│
├── area51/
│   ├── models/           # Mô hình ràng buộc
│   ├── solver/           # Thuật toán giải
|   |── gifs /            # # GIF mô phỏng
│   ├── visualization/    # Vẽ và trực quan hóa
│   ├── data/    # Vẽ và trực quan hóa
│   ├── reports/ # Báo cáo và Slide      
│   └── results/          # Kết quả sinh ra
│
└── slitherlink/

```


--- 
## Hướng dẫn cài đặt:

- Yêu cầu hệ thống 
> Python 3.10+, pip, Gurobi Optimmmizer

> numpy, networkx, pandas

> matplotlib

- Cài đặt thư viện: 

```bash
pip install -r requirements.txt
```























--- 
## Nguồn tham khảo: 

- Nguồn gốc câu đố (Original puzzle source):
    1. Area 51: [https://krazydad.com/area51/]


- Thiết kế puzzle và các luật chơi thuộc về tác giả gốc của bài toán.
- Repository này chỉ tập trung vào:
    - Mô hình hóa toán học
    - Tối ưu hóa
    - Giải tự động bài toán
    - Trực quan hóa quá trình giải 