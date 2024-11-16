import cv2, os, itertools, operator, time
from PIL import Image
import numpy as np


COLS = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6}
REV_COL = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G'}
MODES = {'DEBUG': 0, 'PLAY': 1, 'SOLVE': 2, 'GET_ORDER':3}
horizontal_fix, vertical_fix, width_fix, height_fix = 0, 0, 0, 0
RELATIVE_ON_SCREEN_POSITION = 0.6015
RELATIVE_ON_MIMIC_POSITION = 12 / 1225
CIRCLE_RADIUS_RATIO = 10 / 566
VERTICAL_RATIO = 0.0536
HORIZONTAL_RATIO = 0.113
NUMBER_OF_BLOCKS_TO_REMOVE = 10
SAMPLE_RADIUS = 15
ROWS_NUMBER, COLS_NUMBER = 7, 7
users_mimic = dict()
screenshot_path = ''


class Board:
    def __init__(self):
        self.matrix = [[False for _ in range(COLS_NUMBER)] for _ in range(ROWS_NUMBER)]
        self.frog = [3, 3]

    def update_board(self, points, blocks_to_remove=()):
        for point in points:
            _, _, i, j, _, _, is_block = point
            if is_block is True and [i, j] not in blocks_to_remove:
                self.matrix[i][j] = True

    def remove_pointless_blocks(self):
        borders = get_borders(self)
        for border in borders:
            break_flag = False
            for i, row in enumerate(self.matrix):
                for j in range(len(row)):
                    if [i, j] not in borders and check_move(self, border[0], border[1], i, j):
                        break_flag = True
                        break
                if break_flag:
                    break
            if break_flag is False:
                self.matrix[border[0]][border[1]] = False

    def remove_unreachable_blocks(self):
        reachable_blocks = self.get_reachable_blocks()
        for i, row in enumerate(self.matrix):
            for j, value in enumerate(row):
                if value is True and [i, j] != self.frog and [i, j] not in reachable_blocks:
                    self.matrix[i][j] = False

    def get_reachable_blocks(self):
        visited = []
        queue = [[self.frog[0], self.frog[1]]]
        offset_indexes = [[i, j] for i in range(-1, 2) for j in range(-1, 2)]
        offset_indexes.remove([0, 0])
        borders = get_borders(self)
        while queue:
            i, j = queue[0]
            visited.append(queue.pop(0))
            for offset_i, offset_j in offset_indexes:
                dest_i = i + offset_i
                dest_j = j + offset_j
                if [i, j] in borders and [dest_i, dest_j] in borders:  # cant go from border block to border block
                    continue
                if ([dest_i, dest_j] not in visited and [dest_i, dest_j] not in queue
                        and check_move(self, i, j, dest_i, dest_j)):
                    queue.append([dest_i, dest_j])
        return visited

    def copy(self):
        board_copy = Board()
        board_copy.frog = [self.frog[0], self.frog[1]]
        for i in range(ROWS_NUMBER):
            for j in range(COLS_NUMBER):
                board_copy.matrix[i][j] = self.matrix[i][j]
        return board_copy

    def move(self):
        self.remove_unreachable_blocks()
        border_i, border_j = self.calculate_best_move(self.frog[0], self.frog[1])
        if None in [border_i, border_j]:
            # The player won the game
            return True
        i, j = self.calculate_best_move(border_i, border_j, to_frog=True)
        self.frog = [i, j]
        if i == border_i and j == border_j:
            # The player lost the game
            return False
        return None

    def calculate_best_move(self, start_i, start_j, to_frog=False):
        borders = get_borders(self)
        if not borders:
            return None, None
        priority_border_list = sorted(sorted(borders, key=operator.itemgetter(1)), key=operator.itemgetter(0), reverse=True)
        [i.append(999) for i in priority_border_list]
        # calculate the shortest path from start to destination
        i, j = self.frog
        distance = None
        ranks = {(i - 1, j): 8, (i - 1, j + 1): 7, (i, j + 1): 6, (i + 1, j + 1): 5,
                 (i + 1, j): 4, (i + 1, j - 1): 3, (i, j - 1): 2, (i - 1, j - 1): 1}
        visited = []
        queue = [[start_i, start_j]]
        distance_list = [[[start_i, start_j], 0]]
        to_frog_distance_list = []
        while queue:
            i, j = queue[0]
            for element in distance_list:
                if [i, j] == element[0]:
                    distance = element[1] + 1
                    break
            visited.append(queue.pop(0))
            offset_indexes = [[i, j] for i in range(-1, 2) for j in range(-1, 2)]
            offset_indexes.remove([0, 0])
            for offset_i, offset_j in offset_indexes:
                dest_i = i + offset_i
                dest_j = j + offset_j
                if ([dest_i, dest_j] not in visited
                        and [dest_i, dest_j] not in queue
                        and check_move(self, i, j, dest_i, dest_j)):
                    if to_frog:
                        if [dest_i, dest_j] == self.frog:
                            rank = ranks[(i, j)]
                            to_frog_distance_list.append([i, j, distance, rank])
                        else:
                            queue.append([dest_i, dest_j])
                            distance_list.append([[dest_i, dest_j], distance])
                        if [i, j] == self.frog:
                            break
                    else:
                        queue.append([dest_i, dest_j])
                        distance_list.append([[dest_i, dest_j], distance])
        if to_frog:
            if len(to_frog_distance_list) == 0:
                return None, None
            arr = np.array(to_frog_distance_list)
            min_distance_to_frog = np.min(arr[:, 2])
            minimal_list = [d for d in to_frog_distance_list if d[2] == min_distance_to_frog]
            minimal_list = sorted(minimal_list, key=lambda x: x[3], reverse=True)
            i, j, _, _ = minimal_list[0]
            return i, j
        else:
            for element in priority_border_list:
                for d in distance_list:
                    if element[:-1] == d[0]:
                        element[-1] = d[1]
                        break
            arr = np.array(priority_border_list)
            min_distance_to_border = np.min(arr[:, 2])
            for border in priority_border_list:
                if border[2] == min_distance_to_border:
                    return border[0], border[1]
        return None, None


def solve(points, user_id):
    global users_mimic
    params_list = []
    set_blocks_to_remove = []
    available_blocks = []
    board = Board()
    board.update_board(points)
    board.remove_pointless_blocks()
    board.remove_unreachable_blocks()
    borders = get_borders(board)
    users_mimic[user_id] = [199140, 0] # maximum combinations and counter for progress bar
    for i in range(ROWS_NUMBER):
        for j in range(COLS_NUMBER):
            if board.matrix[i][j] is True and [i, j] != board.frog and [i, j] not in borders:
                available_blocks.append([i, j])

    set_blocks_to_remove.append([])  # add the option of remove only borders
    # combination of one block from available blocks
    start_time = time.time()
    counter = 0 # debug
    for index in range(1, 6):  # calculate all combinations of true blocks that not in the borders and not the frog block
        for blocks_to_remove in itertools.combinations(available_blocks, index):
            counter += 1 # debug
            board = Board()
            board.update_board(points, blocks_to_remove)
            users_mimic[user_id][1] += 1 # count iterations for progress bar
            board.remove_unreachable_blocks()
            borders = get_borders(board)
            amount_of_blocks = len(borders) + len(blocks_to_remove)

            if amount_of_blocks <= NUMBER_OF_BLOCKS_TO_REMOVE:
                true_blocks = len(blocks_to_remove)
                for i in range(ROWS_NUMBER):
                    for j in range(COLS_NUMBER):
                        if board.matrix[i][j] is True:
                            true_blocks += 1
                benefit = true_blocks - amount_of_blocks
                blocks_to_remove = list(blocks_to_remove) + borders
                params_list.append([blocks_to_remove, benefit])
        if index >= 5:
            params_list = sorted(params_list, key=operator.itemgetter(1), reverse=True) # sort by benefit
            print(f'Debug: time taken to get solve results = {time.time() - start_time}')
            print(f'Debug: best result = {params_list[0]}')
            print(f'Debug: counter = {counter}')
            for params in params_list:
                blocks_to_remove, benefit = params
                print(f'Debug: blocks to remove before order = {blocks_to_remove}')
                print(f'Debug: benefit = {benefit}\n')
                order = find_order(points, blocks_to_remove)
                if order:
                    return order, benefit
            params_list = []
    return None, None


def get_borders(board):
    borders = []
    for i, row in enumerate(board.matrix):
        for j, value in enumerate(row):
            if value is True and (i in [0, 6] or j in [0, 6]):
                borders.append([i, j])
    return borders


def check_move(board, from_i, from_j, to_i, to_j):
    for index in [from_i, from_j, to_i, to_j]:
        if not 0 <= index <= 6:
            return False
    if False in [board.matrix[to_i][to_j], board.matrix[from_i][from_j]]:
        return False
    if from_j - 1 <= to_j <= from_j + 1:
        if from_j % 2 == 0:
            if from_i - 1 <= to_i < from_i + 1 or (to_i == from_i + 1 and to_j == from_j):
                return True
        else:
            if from_i - 1 < to_i <= from_i + 1 or (to_i == from_i - 1 and to_j == from_j):
                return True
    return False


def get_blocks_from_image(screenshot=None, web_mode=False, mimic_offset_x=0, mimic_offset_y=0, vertical_offset=0, horizontal_offset=0):
    global screenshot_path
    if web_mode is False:
        mimic_offset_x = width_fix
        mimic_offset_y = height_fix
        vertical_offset = vertical_fix
        horizontal_offset = horizontal_fix
    screenshot_path = convert_pic(screenshot if web_mode else screenshot_path)
    img_rgb = cv2.imread(screenshot_path)
    screenshot_h, screenshot_w = img_rgb.shape[:-1]
    mimic_center_i = int(screenshot_h * RELATIVE_ON_SCREEN_POSITION) + mimic_offset_y
    mimic_center_j = int(screenshot_w/2) + mimic_offset_x

    # Places points in the center of the blocks relative to the mimic treasure
    vertical_offset = screenshot_w * VERTICAL_RATIO + vertical_offset
    horizontal_offset = screenshot_w * HORIZONTAL_RATIO + horizontal_offset
    offsets = []
    for i in range(-ROWS_NUMBER, ROWS_NUMBER):
        if i % 2 != 0:
            for j in [-3, -1, 1, 3]:
                offsets.append((i, j))
        else:
            for j in [-2, 0, 2]:
                offsets.append((i, j))
    # remove mimic treasure point because it's dark like non-block
    offsets.remove((0, 0))
    # finds non-blocks by color
    points = []
    for offset in offsets:
        offset_i, offset_j = offset
        square = SAMPLE_RADIUS  # the size from the center of the sample
        point_i, point_j = (int(mimic_center_i + offset_i*vertical_offset), int(mimic_center_j + offset_j*horizontal_offset))
        cropped_image = img_rgb[point_i-square:point_i+square, point_j-square:point_j+square]  # take block sample
        # calculates dominant color of sample
        pixels = np.float32(cropped_image.reshape(-1, 3))
        n_colors = 5
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
        _, counts = np.unique(labels, return_counts=True)
        dominant = palette[np.argmax(counts)]
        point_matrix_i, point_matrix_j = (int((offset_i+ROWS_NUMBER)/2), offset_j+3)
        # point by pixels, point by matrix index, is there a block at the point
        points.append([point_i, point_j, point_matrix_i, point_matrix_j, offset_i, offset_j, bool(dominant[2] > 140)])
    points.append([mimic_center_i, mimic_center_j, 3, 3, 0, 0, True])  # adds mimic treasure block
    return points, screenshot_path


def convert_pic(screenshot):
    im = Image.open(screenshot).convert('RGB')
    for extension in ['webp', 'jpg', 'jpeg']:
        if screenshot.endswith(f'.{extension}'):
            new_path = screenshot.replace(f'.{extension}', '.png')
            im.save(new_path, "png")
            os.remove(screenshot)
            return new_path
    return screenshot


def save_solution_as_image(solution_number, points, blocks_to_remove, screenshot=None, debug=False):
    screenshot = screenshot if screenshot is not None else screenshot_path
    solutions_dir_path = f'{os.path.dirname(screenshot)}/{screenshot.split("/")[-1]} Solutions'
    os.makedirs(solutions_dir_path, exist_ok=True)
    img_rgb = cv2.imread(screenshot)
    screenshot_w = img_rgb.shape[1]
    for point in points:
        pixel_i, pixel_j, matrix_i, matrix_j, _, _, is_block = point
        if [matrix_i, matrix_j] in blocks_to_remove or debug:
            cv2.circle(img_rgb, (pixel_j, pixel_i), int(screenshot_w * CIRCLE_RADIUS_RATIO), (255, 0, 0), -1)
    cv2.imwrite(f'{solutions_dir_path}/solution-{solution_number}.png', img_rgb)


def convert_indexes(block):
    block = block.strip()
    if len(block) != 2 or block[0].upper() not in COLS or block[1].isdigit() is False or not (0 < int(block[1]) < 8):
        return None, None
    return int(block[1]) - 1, COLS[block[0].upper()]


def run_game_with_order(order, board, removed_blocks):
    copy_order = list(order)
    board = board.copy()
    if board.frog in copy_order:  # Frog block removal is prohibited
        return
    while copy_order:
        i, j = copy_order.pop(0)
        board.matrix[i][j] = False
        is_win = board.move()
        if is_win is False or board.frog in copy_order:  # Frog block removal is prohibited
            return
        if is_win is True:
            return removed_blocks + list(order)


def find_order(points, blocks_to_remove):
    board = Board()
    board.update_board(points)

    # if next move is block to remove is it necessary to remove it and move the mimic to next move (repeat as much as possible)
    removed_blocks = remove_necessary_blocks(board, blocks_to_remove)
    # re-order blocks from bottom-right to top-left to optimize get_order finder
    blocks_to_remove = sorted(sorted(blocks_to_remove, key=operator.itemgetter(1), reverse=True), key=operator.itemgetter(0), reverse=True)
    print(f'Debug: find_order, blocks_to_remove: {blocks_to_remove}')
    print(f'Debug: find_order, removed_blocks: {removed_blocks}')
    if removed_blocks is False: # no order exist
        return
    orders = itertools.permutations(blocks_to_remove)

    counter = 0
    for order in orders:
        counter += 1
        result = run_game_with_order(order, board, removed_blocks)
        if result:
            print(f'Debug: find_order, succeeded, calculated orders: {counter}')
            return result
    print(f'Debug: find_order, failed, calculated orders: {counter}')

def get_next_move(board, i, j):
    border_i, border_j = board.calculate_best_move(i, j)
    if None not in [border_i, border_j]:
        next_i, next_j = board.calculate_best_move(border_i, border_j, to_frog=True)
        return next_i, next_j
    return None, None


def remove_necessary_blocks(board, blocks_to_remove):
    removed_blocks = []
    while True:
        next_i, next_j = get_next_move(board, board.frog[0], board.frog[1])
        if None not in [next_i, next_j] and [next_i, next_j] in blocks_to_remove:
            blocks_to_remove.remove([next_i, next_j])
            removed_blocks.append([next_i, next_j])
            board.matrix[next_i][next_j] = False
            is_win = board.move()
            if is_win is False:
                return False
            if is_win is True:
                return removed_blocks
        else:
            return removed_blocks

def save_order_as_image(order, points, filename):
    img_rgb = cv2.imread(filename)
    if order is None:
        order = []
    for block_number, block in enumerate(order):
        pixel_i, pixel_j = 0, 0
        for point in points:
            if block == list(point[2:4]):
                pixel_i, pixel_j = point[:2]
                break
        points_horizontal_distance = int((points[1][1] - points[0][1])/8)
        points_horizontal_distance_10 = points_horizontal_distance * 2
        points_vertical_distance = int((points[7][0] - points[6][0]) / 2)
        font_scale = points_horizontal_distance / 12
        thickness = int(font_scale * 2) + 1
        if block_number == NUMBER_OF_BLOCKS_TO_REMOVE - 1:
            points_horizontal_distance = points_horizontal_distance_10

        cv2.putText(img_rgb, str(block_number + 1), (int(pixel_j-points_horizontal_distance),
                                                     int(pixel_i+points_vertical_distance)), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,(255, 0, 0), thickness)
    image_name = f'{filename} order.png'
    cv2.imwrite(image_name, img_rgb)
    return image_name