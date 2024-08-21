import sys, cv2, os, time, itertools, operator

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
SAMPLE_RADIUS = 10
ROWS_NUMBER = 7
COLS_NUMBER = 7
screenshot_path = ''


def main():
    global screenshot_path, width_fix, height_fix, vertical_fix, horizontal_fix
    mode = MODES['PLAY']
    screenshot_path = '' # here you put the screenshot path
    screenshot_path = os.getcwd() + f'/{sys.argv[1]}' if len(sys.argv) > 1 else screenshot_path
    if os.path.isfile(screenshot_path) is False:
        print(f'The file {screenshot_path} does not exist!')
        return
    try:
        mode = MODES[sys.argv[2].upper()] if len(sys.argv) > 2 else mode
    except KeyError:
        print('Invalid mode.')
        return

    if mode == MODES['DEBUG']:
        height_fix = 0
        width_fix = 0
        horizontal_fix = 0
        vertical_fix = 0

    points = get_blocks_from_image()

    if mode == MODES['DEBUG']:
        debug_program(points, print_points=False)

    if mode == MODES['PLAY']:
        play_game(points)

    if mode == MODES['SOLVE']:
        solve(points)
        os.system("say beep")

    if mode == MODES['GET_ORDER']:
        get_order(points)
        os.system("say beep")


def get_order(points, web_blocks='', web_mode=False):
    if web_mode:
        blocks_text = web_blocks
    else:
        blocks_text = input('Enter Blocks: ')
    blocks = blocks_text.split(' ')
    blocks_to_remove = []
    if len(blocks) != NUMBER_OF_BLOCKS_TO_REMOVE:
        print('Wrong number of blocks')
        return
    for block in blocks:
        i, j = convert_indexes(block)
        if i is None:
            print(f'Wrong block index. {block}')
            return
        blocks_to_remove.append([i, j])
    start = time.time()
    order = find_order(points, blocks_to_remove)
    if order is None:
        message = 'No order found.'
    else:
        message = f"The order is: {' -> '.join([REV_COL[i[1]] + str(i[0] + 1) for i in order])}"
    duration = int(time.time() - start)

    if web_mode:
        return message, duration
    else:
        print(message)
        print(f'The time it took to find: {duration} seconds.')

def debug_program(points, print_points=False):
    if print_points:
        for point in points:
            print(point)
    save_solution_as_image('debug', points, [], debug=True)


def convert_indexes(block):
    block = block.strip()
    if len(block) != 2 or block[0].upper() not in COLS or block[1].isdigit() is False or not (0 < int(block[1]) < 8):
        return None, None
    return int(block[1]) - 1, COLS[block[0].upper()]


def check_move(board, from_i, from_j, to_i, to_j):
    # start debug
    print('in check_move')
    print(board.matrix)
    print(from_i, from_j, to_i, to_j)
    # end debug
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


class Board:
    def __init__(self):
        self.matrix = [[False for _ in range(COLS_NUMBER)] for _ in range(ROWS_NUMBER)]
        self.frog = [3, 3]

    def update_board(self, points):
        for point in points:
            _, _, i, j, _, _, is_block = point
            if is_block is True:
                self.matrix[i][j] = True

    def remove_pointless_blocks(self):
        borders = get_borders(self)
        for border in borders:
            break_flag = False
            for i, row in enumerate(self.matrix):
                for j in range(len(row)):
                    # start debug
                    print('before check_move')
                    print(self.matrix)
                    print(border[0], border[1], i, j)
                    # end debug
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
                if value is True and [i, j] not in reachable_blocks and [i, j] != self.frog:
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
        priority_border_list = sorted(sorted(borders, key=operator.itemgetter(1)), key=operator.itemgetter(0),
                                      reverse=True)
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

    def show_board(self):
        for i, row in enumerate(self.matrix):
            for t in range(2):
                for j in range(len(row)):
                    if j % 2 == t and row[j]:
                        if i == self.frog[0] and j == self.frog[1]:
                            print('🐸', end='\t')
                        else:
                            print('⬣', end='\t')
                    else:
                        print(' ', end='\t')
                print()


def clear_and_show_board(board):
    os.system('cls' if os.name == 'nt' else 'clear')
    board.show_board()


def play_game(points):
    board = Board()
    board.update_board(points)
    player_moves = ''
    player_counter = 0
    while True:
        clear_and_show_board(board)
        time.sleep(1)
        player_move = input('Select a block to remove: ')
        remove_i, remove_j = convert_indexes(player_move)
        clear_and_show_board(board)
        if (remove_i is None or remove_j is None or board.matrix[remove_i][remove_j] is False
                or [remove_i, remove_j] == board.frog):
            print('Invalid block indexes.\nPlease try again.\n')
            time.sleep(1)
            continue
        player_moves += player_move.upper() + ' -> '
        board.matrix[remove_i][remove_j] = False
        player_counter += 1
        clear_and_show_board(board)
        time.sleep(1)
        is_win = board.move()
        if is_win in [True, False] or player_counter == NUMBER_OF_BLOCKS_TO_REMOVE:
            clear_and_show_board(board)
            if is_win is True:
                print('You win!')
            else:
                print('You lose!')
            print(f'Your moves: {player_moves[:-4]}')
            exit()


def find_order(points, blocks):
    board = Board()
    board.update_board(points)
    res = remove_necessary_blocks(board, blocks)
    if res is False: # no order exist
        return
    removed_blocks = res
    orders = itertools.permutations(blocks)
    # start test code
    temp_frog = board.frog.copy()
    next_i, next_j = get_next_move(board, board.frog[0], board.frog[1])
    board.frog = [next_i, next_j]
    if None not in [next_i, next_j] and [next_i, next_j] not in blocks:  # split in future code
        next_i, next_j = get_next_move(board, next_i, next_j)
        if [next_i, next_j] in blocks and board.matrix[next_i][next_j] == True:
            board.matrix[next_i][next_j] = False
            next2_i, next2_j = get_next_move(board, next_i, next_j)
            board.matrix[next_i][next_j] = True
            if [next2_i, next2_j] in blocks:
                gen1 = create_generator([next_i, next_j], [next2_i, next2_j], blocks, 0)
                gen2 = create_generator([next_i, next_j], [next2_i, next2_j], blocks, 1)
                orders = itertools.chain(gen1, gen2)
    board.frog = temp_frog.copy()
    # end test code
    while True:
        try:
            order = orders.__next__()
        except StopIteration:
            break
        copy_order = list(order)
        if board.frog in copy_order: # Frog block removal is prohibited
            continue
        copy_board = board.copy()
        while copy_order:
            i, j = copy_order.pop(0)
            copy_board.matrix[i][j] = False
            is_win = copy_board.move()
            if is_win is False or copy_board.frog in copy_order:  # Frog block removal is prohibited
                break
            if is_win is True:
                return removed_blocks + list(order)

def get_next_move(board, i, j):
    border_i, border_j = board.calculate_best_move(i, j)
    if None not in [border_i, border_j]:
        next_i, next_j = board.calculate_best_move(border_i, border_j, to_frog=True)
        return next_i, next_j
    return None, None

def create_generator(block1, block2, blocks, block_number):
    copy_blocks = blocks.copy()
    copy_blocks.remove(block1)
    copy_blocks.remove(block2)
    gen = itertools.permutations(copy_blocks)
    while True:
        try:
            yield [[block1, block2], [block2, block1]][block_number] + list(next(gen))
        except StopIteration:
            return



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



def get_borders(board):
    borders = []
    for i, row in enumerate(board.matrix):
        for j, value in enumerate(row):
            if value is True and (i in [0, 6] or j in [0, 6]):
                borders.append([i, j])
    return borders


def solve(points, web_mode=False):
    maximum_benefit = 0
    web_messages = []
    benefit_list = []
    blocks_to_remove = []
    available_blocks = []
    board = Board()
    board.update_board(points)
    board.remove_pointless_blocks()
    board.remove_unreachable_blocks()
    borders = get_borders(board)
    for i in range(ROWS_NUMBER):
        for j in range(COLS_NUMBER):
            if board.matrix[i][j] is True and [i, j] != board.frog and [i, j] not in borders:
                available_blocks.append([i, j])

    blocks_to_remove.append([])  # add the option of remove only borders
    # combination of one block from available blocks
    for i in range(1, 11):  # add all combinations of true blocks that not in the borders and not the frog block
        blocks_to_remove += list(itertools.combinations(available_blocks, i))
    for block_to_remove in blocks_to_remove:
        board = Board()
        board.update_board(points)
        for block in block_to_remove:
            i, j = block
            board.matrix[i][j] = False

        # Checks if one of the blocks to be removed cannot be reached when the other blocks are removed.
        # This causes a double solution.
        continue_flag = False
        for block in block_to_remove:
            i, j = block
            board.matrix[i][j] = True
            board.remove_unreachable_blocks()
            if board.matrix[i][j] is False:
                continue_flag = True
                break
            board.matrix[i][j] = False
        if continue_flag is True:
            continue

        board.remove_pointless_blocks()
        board.remove_unreachable_blocks()
        borders = get_borders(board)
        amount_of_blocks = len(borders) + len(block_to_remove)

        if amount_of_blocks <= NUMBER_OF_BLOCKS_TO_REMOVE:
            true_blocks = len(block_to_remove)
            for i in range(ROWS_NUMBER):
                for j in range(COLS_NUMBER):
                    if board.matrix[i][j] is True:
                        true_blocks += 1
            benefit = true_blocks - amount_of_blocks

            if benefit >= maximum_benefit:
                maximum_benefit = benefit
                blocks_to_remove_with_maximum_benefit = list(block_to_remove) + borders
                benefit_list.append([benefit, blocks_to_remove_with_maximum_benefit])

    counter = 1
    if len(benefit_list) != 0:
        if web_mode:
            web_messages.append(maximum_benefit)
        print(f'The maximum benefit is {maximum_benefit}.')
        for item in benefit_list:
            if item[0] == maximum_benefit:
                blocks_set = ' '.join([REV_COL[i[1]] + str(i[0] + 1) for i in item[1]])
                if web_mode:
                    web_messages.append(blocks_set)
                else:
                    print(f'Blocks to remove: {blocks_set}')
                save_solution_as_image(counter, points, item[1])
                counter += 1
    return web_messages


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


def convert_pic(screenshot):
    im = Image.open(screenshot).convert('RGB')
    for extension in ['webp', 'jpg', 'jpeg']:
        if screenshot.endswith(f'.{extension}'):
            new_path = screenshot.replace(f'.{extension}', '.png')
            im.save(new_path, "png")
            os.remove(screenshot)
            return new_path
    return screenshot


def get_blocks_from_image(screenshot=None, web_mode=False, mimic_offset_x=width_fix, mimic_offset_y=height_fix,
                          vertical_offset=vertical_fix, horizontal_offset=horizontal_fix):
    global screenshot_path
    mimic_path = f"{'/'.join(__file__.split('/')[:-1])}/mimic_treasure.png"
    screenshot_path = convert_pic(screenshot if web_mode else screenshot_path)
    img_rgb = cv2.imread(screenshot_path)
    screenshot_h, screenshot_w = img_rgb.shape[:-1]

    # Finds the mimic treasure in the picture
    template = cv2.imread(mimic_path)
    template_w, template_h = template.shape[:-1]
    res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    threshold = .5
    loc = np.where(res >= threshold)
    pts = list(zip(*loc[::-1]))
    if len(pts) > 0:
        pt = pts[0]
        mimic_center = (int(pt[1] + template_h/2 + screenshot_h * RELATIVE_ON_MIMIC_POSITION) + mimic_offset_y,
                        int(screenshot_w/2)+mimic_offset_x)
    else:
        print("Error: Can't find Mimic Treasure.")
        mimic_center = int(screenshot_h * RELATIVE_ON_SCREEN_POSITION) + mimic_offset_y, int(screenshot_w/2) + mimic_offset_x
    mimic_center_i, mimic_center_j = mimic_center
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
        i, j = offset
        square = SAMPLE_RADIUS  # the size from the center of the sample
        point_i, point_j = (int(mimic_center_i + i*vertical_offset), int(mimic_center_j + j*horizontal_offset))
        cropped_image = img_rgb[point_i-square:point_i+square, point_j-square:point_j+square]  # take block sample
        # calculates dominant color of sample
        pixels = np.float32(cropped_image.reshape(-1, 3))
        n_colors = 5
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
        _, counts = np.unique(labels, return_counts=True)
        dominant = palette[np.argmax(counts)]
        point_matrix_i, point_matrix_j = (int((i+ROWS_NUMBER)/2), j+3)
        # point by pixels, point by matrix index, is there a block at the point
        points.append((point_i, point_j, point_matrix_i, point_matrix_j, i, j, bool(dominant[2] > 140)))
    points.append((mimic_center_i, mimic_center_j, 3, 3, 0, 0, True))  # adds mimic treasure block
    return points


if __name__ == '__main__':
    main()
