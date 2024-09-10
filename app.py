from Mimic_Capture import get_blocks_from_image, solve, get_order, save_order_as_image, play_game_web, Board, users_mimic
from flask import Flask, render_template, request, redirect
import os, time, cv2, shutil, threading

REMOVE_TIME = 60*5 # 5 min

users = dict()
POINTS, BLOCKS_SETS, RATIO, FILENAME, FROG_INDEXES, MOVES_COUNTER  = 0, 1, 2, 3, 4, 5
MIMIC_OFFSET_X, MIMIC_OFFSET_Y, VERTICAL_OFFSET, HORIZONTAL_OFFSET = 6, 7, 8, 9
SOLVE_RESULT, ORDER_RESULT, CHECKBOX, START_TIME = 10, 11, 12, 13

app = Flask(__name__)

@app.route('/')
def index():
    remove_old_files()
    return render_template("index.html")


@app.route('/fix_points', methods=['POST', 'GET'])
def fix_points():
    global users
    if request.method == 'POST':
        user_id = int(time.time())
        points, blocks_sets, solve_result, order_result, fixed_points = [], [], [], [], []
        mimic_offset_x, mimic_offset_y, vertical_offset, horizontal_offset = 0, 0, 0, 0
        checkbox, success_flag = False, False
        image_height, image_width = 0, 0
        frog_indexes = [3, 3]
        moves_counter = 0
        start_time = 0
        filename = ''
        ratio = 1
        users[user_id] = [points, blocks_sets, ratio, filename, frog_indexes, moves_counter, mimic_offset_x,
                          mimic_offset_y, vertical_offset, horizontal_offset, solve_result, order_result, checkbox, start_time]

        f = request.files['file']
        screen_width = int(request.form.get('screen-width')) - 20
        extension = f.filename.split('.')[-1]
        if extension in ['jpg', 'jpeg', 'png', 'webp']:
            filename = f'static/file uploading/{user_id}.{extension}'
            f.save(filename)
            im = cv2.imread(filename)
            image_size = im.shape[:-1]
            ratio = min(400, screen_width) / image_size[1]
            users[user_id][RATIO] = ratio
            points, filename = get_blocks_from_image(screenshot=filename, web_mode=True)
            users[user_id][FILENAME] = filename
            users[user_id][POINTS] = points
            for point in points:
                fixed_points.append([int(point[1] * ratio), int(point[0] * ratio), point[4], point[5]])
            image_height = int(image_size[0] * ratio)
            image_width = int(image_size[1] * ratio)
            success_flag = True
        return render_template("fix_points.html",user_id=user_id, filename=filename, success=success_flag,
                               image_height=image_height, image_width=image_width, points=fixed_points, ratio=ratio)
    return redirect('/')


def update_offsets(req, user_id):
    ratio = users[user_id][RATIO]
    users[user_id][MIMIC_OFFSET_X] = int(float(req.form['mimic_offset_x']) / ratio)
    users[user_id][MIMIC_OFFSET_Y] = int(float(req.form['mimic_offset_y']) / ratio)
    users[user_id][VERTICAL_OFFSET] = int(float(req.form['vertical_offset']) / ratio)
    users[user_id][HORIZONTAL_OFFSET] = int(float(req.form['horizontal_offset']) / ratio)


@app.route('/solve', methods=['POST', 'GET'])
def app_solve():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        update_offsets(request, user_id)
        specific_benefit = request.form['specific_benefit']
        users[user_id][START_TIME] = int(time.time())
        users[user_id][POINTS] = get_points(user_id)
        if specific_benefit and specific_benefit.isdigit() and int(specific_benefit) > 0:
            specific_benefit = int(specific_benefit)
            t1 = threading.Thread(target=thread_solve, args=(user_id, specific_benefit))
        else:
            t1 = threading.Thread(target=thread_solve, args=(user_id, None))
        t1.start()
        return {'status': False}
    return redirect('/')


@app.route('/check_solve_result', methods=['POST', 'GET'])
def check_solve_result():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        if users[user_id][SOLVE_RESULT]:
            filename = users[user_id][FILENAME]
            messages = users[user_id][SOLVE_RESULT][0]
            benefit = ''
            if len(messages) > 1:
                dir_name = f'{filename} Solutions'
                for i, message in enumerate(messages):
                    if i == 0:
                        benefit = message
                    else:
                        blocks_set = message
                        solution_file = f'{dir_name}/solution-{i}.png'
                        if os.path.isfile(solution_file):
                            users[user_id][BLOCKS_SETS].append([solution_file, blocks_set])
            return {'solve_status': True,
                    'html': render_template("results.html", blocks_sets=users[user_id][BLOCKS_SETS],
                                            benefit=benefit, user_id=user_id)}
        return {'solve_status': False, 'counter': users_mimic[user_id][1], 'combinations': users_mimic[user_id][0]}
    return redirect('/')


@app.route('/get_first_order', methods=['POST', 'GET'])
def get_first_order():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        t2 = threading.Thread(target=thread_get_first_order, args=(users[user_id][SOLVE_RESULT][0], user_id))
        t2.start()
        return {'order_status': False}
    return redirect('/')


@app.route('/get_order', methods=['POST', 'GET'])
def app_get_order():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        benefit = request.form['benefit']
        blocks_set_number = int(request.form['blocks-set-number'])
        _, blocks_set = users[user_id][BLOCKS_SETS][blocks_set_number]
        t3 = threading.Thread(target=thread_get_order, args=(blocks_set, blocks_set_number, benefit, user_id))
        t3.start()
        return {'order_status': False}
    return redirect('/')


def get_order_template(blocks_set, benefit, user_id, blocks_set_number, first_order):
    with app.app_context():
        found, order = get_order(users[user_id][POINTS], web_blocks=blocks_set, web_mode=True)
        image_path = save_order_as_image(order, users[user_id][POINTS], users[user_id][FILENAME], blocks_set_number)

        if first_order:
            return render_template("order.html",
                                   duration=int(time.time()) - users[user_id][START_TIME],
                                   image_path=image_path, benefit=benefit), found
        return image_path, found


@app.route('/check_order_result', methods=['POST', 'GET'])
def check_order_result():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        if 'blocks-set-number' in request.form:
            blocks_set_number = request.form['blocks-set-number']
            blocks_set_number = int(blocks_set_number)
            for order_result in users[user_id][ORDER_RESULT]:
                order_block_set_number, image_path, found = order_result
                if order_block_set_number == blocks_set_number:
                    return {'order_status': True, 'image_path': image_path, 'found': found}

        elif users[user_id][ORDER_RESULT]:
            _, page_template = users[user_id][ORDER_RESULT][0]
            if not page_template:
                page_template = render_template("order.html", duration=0,
                                                image_path=users[user_id][FILENAME], benefit=0)
            return {'order_status': True, 'html': page_template}

        return {'order_status': False}
    return redirect('/')


@app.route('/restart', methods=['GET'])
def restart():
    if request.method == 'GET':
        user_id = int(request.args.get('user_id'))
        users[user_id][FROG_INDEXES] = [3, 3]
        users[user_id][MOVES_COUNTER] = 0
        users[user_id][POINTS] = get_points(user_id)
        return redirect(f'/play?user_id={user_id}')
    return redirect('/')


@app.route('/play', methods=['GET', 'POST'])
def play():
    blocks = []
    benefit = 0
    if request.method == 'GET':
        i = request.args.get('block_i')
        j = request.args.get('block_j')
        user_id = int(request.args.get('user_id'))
        points = users[user_id][POINTS]
        if not points:
            return redirect('/')
        frog_indexes = users[user_id][FROG_INDEXES]
        moves_counter = users[user_id][MOVES_COUNTER]
        if i:
            if frog_indexes[0] in [0,6] or frog_indexes[1] in [0,6] or moves_counter == 10:
                return redirect('/')
            i = int(i)
            j = int(j)
            status, points, frog_indexes = play_game_web(points, [i, j], frog_indexes)
            if [i, j] != frog_indexes:
                moves_counter += 1
            if moves_counter == 10 and status is not True:
                status = False
            for point in points:
                if point[-1] is True:
                    blocks.append(list(point[2:4]))
            if status is True:
                board = Board()
                board.update_board(points)
                board.frog = frog_indexes
                reachable_blocks = board.get_reachable_blocks()
                benefit = len(reachable_blocks)
            users[user_id][FROG_INDEXES] = frog_indexes
            users[user_id][MOVES_COUNTER] = moves_counter
            return render_template("play.html", blocks=blocks, is_win=status,
                                   frog_indexes=frog_indexes, moves_counter=moves_counter, benefit=benefit, user_id=user_id)
        else:
            for point in points:
                if point[-1] is True:
                    blocks.append(list(point[2:4]))
            return render_template("play.html", blocks=blocks, is_win=None, frog_indexes=frog_indexes,
                                   moves_counter=moves_counter, benefit=0, user_id=user_id)
    if request.method == 'POST':
        user_id = int(request.form.get('user_id'))
        update_offsets(request, user_id)
        users[user_id][POINTS] = get_points(user_id)
        return redirect(f'/play?user_id={user_id}')
    return redirect('/')


def get_points(user_id):
    points, _ = get_blocks_from_image(screenshot=users[user_id][FILENAME], web_mode=True,
                                   mimic_offset_x=users[user_id][MIMIC_OFFSET_X],
                                   mimic_offset_y=users[user_id][MIMIC_OFFSET_Y],
                                   vertical_offset=users[user_id][VERTICAL_OFFSET],
                                   horizontal_offset=users[user_id][HORIZONTAL_OFFSET])
    return points


def remove_old_files():
    uploading_dir = 'static/file uploading'
    for file in os.listdir(uploading_dir):
        if file != 'empty_file.txt':
            file_name = uploading_dir + '/' + file
            file_create_time = int(os.path.getctime(file_name))
            if file_create_time + REMOVE_TIME < int(time.time()):
                try:
                    if os.path.isdir(file_name):
                        shutil.rmtree(file_name)
                    else:
                        os.remove(file_name)
                        file_number = int(file_name.split('.')[0])
                        if file_number in users:
                            del users[file_number]
                except:
                    pass


def thread_solve(user_id, specific_benefit):
    users[user_id][SOLVE_RESULT].append(solve(users[user_id][POINTS], users[user_id][FILENAME],
                                              web_mode=True, specific_benefit=specific_benefit, user_id=user_id))


def thread_get_first_order(messages, user_id):
    for blocks_set in messages[1:]:
        benefit = messages[0]
        page_template, found = get_order_template(blocks_set, benefit, user_id, 0, first_order=True)
        if found:
            users[user_id][ORDER_RESULT].append([None, page_template])
            return
    users[user_id][ORDER_RESULT].append([None, None])

def thread_get_order(blocks_set, blocks_set_number, benefit, user_id):
    image_path, found = get_order_template(blocks_set, benefit, user_id, blocks_set_number, first_order=False)
    users[user_id][ORDER_RESULT].append([blocks_set_number, image_path, found])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
