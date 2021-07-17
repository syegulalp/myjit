from jit import jit, j_types as j

WIDTH = 80
HEIGHT = 40

arr_type = j.array(j.u8, (2, WIDTH, HEIGHT))
arr = arr_type()

import random

for n in range(HEIGHT):
    for m in range(WIDTH):
        arr[0][m][n] = random.random() > 0.8

# TODO: variable capture for more than one instance of captured variable is broken

@jit
def life(a: arr_type, world: int):

    current = world
    target = 1 - world

    x = 0
    y = 0

    z: j.u8 = 0
    q: j.u8 = 0

    H = HEIGHT
    W = WIDTH

    while y < H:
        x = 0
        while x < W:

            y1 = y - 1
            z = a[current][x][y]
            total = 0

            while y1 < y + 2:
                x1 = x - 1
                while x1 < x + 2:
                    if x1 == x and y1 == y:
                        x1 += 1
                        continue
                    if a[current][x1 % W][y1 % H] > 0:
                        total += 1
                    x1 += 1
                y1 += 1

            q = 0

            if z:
                if total > 1 and total < 4:
                    q = 1
            else:
                if total == 3:
                    q = 1

            a[target][x][y] = q

            x += 1

        y += 1


world = 0

while True:

    for n in range(HEIGHT):
        for m in range(WIDTH):
            print("O" if arr[world][m][n] else " ", end="")
        print()

    input()

    life(arr, world)
    world = 1 - world

