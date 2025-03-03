"""
1024 游戏
一个基于命令行的 1024 游戏实现
"""

import random

class Game:
    def __init__(self):
        """
        初始化游戏
        创建一个 4x4 的游戏板，并在随机位置放置两个数字
        """
        self.board = [[0] * 4 for _ in range(4)]
        self.add_new_tile()
        self.add_new_tile()
    
    def add_new_tile(self):
        """
        在空位置随机添加一个新的数字（2或4）
        """
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board[i][j] = random.choice([2, 4])
    
    def display(self):
        """
        显示当前游戏板状态
        """
        print("\n" + "=" * 25)
        for row in self.board:
            print("|", end=" ")
            for num in row:
                print(f"{num:4}", end=" ")
            print("|")
        print("=" * 25)
    def move_left(self):
        """
        向左移动并合并数字
        """
        changed = False
        for row in range(4):
            # 合并相同的数字
            for col in range(3):
                for k in range(col + 1, 4):
                    if self.board[row][k] != 0:
                        if self.board[row][col] == 0:
                            self.board[row][col] = self.board[row][k]
                            self.board[row][k] = 0
                            changed = True
                            break
                        elif self.board[row][col] == self.board[row][k]:
                            self.board[row][col] *= 2
                            self.board[row][k] = 0
                            changed = True
                            break
                        break
        return changed

    def move_right(self):
        """
        向右移动并合并数字
        """
        # 翻转棋盘，使用移动左的逻辑，再翻转回来
        for row in self.board:
            row.reverse()
        changed = self.move_left()
        for row in self.board:
            row.reverse()
        return changed

    def move_up(self):
        """
        向上移动并合并数字
        """
        changed = False
        # 转置矩阵
        self.board = list(map(list, zip(*self.board)))
        changed = self.move_left()
        self.board = list(map(list, zip(*self.board)))
        return changed

    def move_down(self):
        """
        向下移动并合并数字
        """
        changed = False
        # 转置矩阵
        self.board = list(map(list, zip(*self.board)))
        changed = self.move_right()
        self.board = list(map(list, zip(*self.board)))
        return changed

# 修改主游戏循环
def main():
    """
    主游戏循环
    """
    game = Game()
    moves = {
        'w': game.move_up,
        's': game.move_down,
        'a': game.move_left,
        'd': game.move_right
    }
    
    while True:
        game.display()
        move = input("请输入移动方向 (W:上, S:下, A:左, D:右, Q:退出): ").lower()
        
        if move == 'q':
            print("游戏结束！")
            break
            
        if move in moves:
            if moves[move]():
                game.add_new_tile()

if __name__ == "__main__":
    main()

# 创建游戏实例
game = Game()
game.display()