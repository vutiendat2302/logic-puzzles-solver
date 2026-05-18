import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json

with open("../data/easy/8x8.json", "r",  encoding="utf-8") as f:
    data = json.load(f)


def draw_grid(matrix, title):
    n = len(matrix)
    m = len(matrix[0])

    fig, ax = plt.subplots()
    ax.set_title(title)

    ax.set_xlim(0, m)
    ax.set_ylim(0, n)
    ax.set_aspect('equal')
    ax.invert_yaxis()

    # draw grid
    for i in range(n):
        for j in range(m):
            cell = matrix[i][j]

            # background color
            color = "white"

            if isinstance(cell, dict):
                color = "#d1f2eb" if cell.get("circled") else "#f0f0f0"
            elif cell == "A":
                color = "#ffcccc"
            elif cell == "C":
                color = "#d5f5e3"

            rect = patches.Rectangle((j, i), 1, 1,
                                     linewidth=1,
                                     edgecolor="black",
                                     facecolor=color)
            ax.add_patch(rect)

            # text
            text = ""
            if isinstance(cell, dict):
                text = str(cell["value"]) + "○"
            elif cell is not None:
                text = str(cell)

            ax.text(j + 0.5, i + 0.5, text,
                    ha='center', va='center', fontsize=12)

    plt.show()


draw_grid(data["matrix_1"]["data"], "Matrix 1")
draw_grid(data["matrix_2"]["data"], "Matrix 2")