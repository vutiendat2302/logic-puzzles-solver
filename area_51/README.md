# AREA 51 PUZZLE

Area 51 Puzzle là một bài toán logic dạng hybrid puzzle,
kết hợp nhiều cơ chế nổi tiếng như:
- Slitherlink
- Masyu
- Corral / Cave
- Visibility Puzzle

Mục tiêu của bài toán là xây dựng một hàng rào khép kín
để bảo vệ cơ sở nghiên cứu tuyệt mật `[REDACTED]`.

Hàng rào phải:
- chứa toàn bộ người ngoài hành tinh đã bị bắt giữ,
- ngăn các sinh vật Triffid xâm nhập,
- tạo thành một vòng lặp kín duy nhất,
- và không được tự cắt tại bất kỳ vị trí nào.

Bài toán chỉ có duy nhất một nghiệm.
---

## Luật Chơi

### Aliens (Người ngoài hành tinh)

Người ngoài hành tinh (Aliens) phải nằm bên trong hàng rào.

---

### Triffids (Cây xương rồng)

Triffids là các sinh vật dạng thực vật giống xương rồng.

Tất cả Triffids phải nằm bên ngoài hàng rào.

---

### Uncircled Numbers (Số không được khoanh tròn)

Các số không được khoanh tròn biểu thị:

> Có bao nhiêu cạnh của hàng rào xuất hiện xung quanh ô chứa số đó.

Giá trị luôn nằm trong khoảng:
- 0 đến 3

Cơ chế này tương tự Slitherlink.

---

### Circled Numbers (Số được khoanh tròn)

Các số được khoanh tròn luôn nằm bên trong hàng rào.

Chúng biểu diễn điều kiện visibility:

> Con số cho biết tổng số ô có thể nhìn thấy theo bốn hướng (Tính cả ô chứa Circled Numbers):
- Bắc
- Nam
- Đông
- Tây

Ô hiện tại cũng được tính vào tổng visibility.

Visibility sẽ bị chặn khi gặp biên hàng rào.

---

### Black and White Circles (Vòng tròn đen và trắng)

Các vòng tròn đen và trắng sử dụng luật của puzzle Masyu.

Cơ chế Masyu Rules

- Black Circle (Vòng tròn đen)

    Nếu hàng rào đi qua vòng tròn đen:
    - hàng rào bắt buộc phải rẽ 90°
    - đồng thời phải đi thẳng ít nhất 2 ô ở cả hai phía trước và sau điểm rẽ

---

- White Circle (Vòng tròn trắng)

    Nếu hàng rào đi qua vòng tròn trắng:
    - hàng rào phải đi thẳng qua ô đó
    - nhưng phải rẽ 90° ngay ở ít nhất một phía liền kề

---

## Đặc Điểm Bài Toán

Puzzle này là sự kết hợp giữa:
- loop constraints,
- visibility constraints,
- region constraints,
- connectivity constraints,
- và local pattern constraints.

Do đó đây là một bài toán constraint satisfaction phức tạp,
phù hợp để mô hình hóa bằng:
- MILP,
- SAT/SMT,
- hoặc graph optimization.

---


## Hướng Giải Trong Dự Án

Dự án này mô hình hóa bài toán bằng:
- Graph Theory
- Mixed Integer Linear Programming (MILP)

và sử dụng:
- Gurobi Optimizer

để tìm nghiệm duy nhất của puzzle.

Ngoài việc giải puzzle, dự án còn tập trung vào:
- visualization,
- animation quá trình solve,
- và phân tích constraint system.



