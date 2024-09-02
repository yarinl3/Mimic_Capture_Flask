import os, time, cv2, shutil
from flask import Flask, render_template, request, redirect
from Mimic_Capture import get_blocks_from_image, solve, get_order, save_order_as_image, play_game_web, Board
from pathlib import Path
import threading

ratio = 1
checkbox = False
points = []
blocks_sets = []
solve_result = []
order_result = []
frog_indexes = [None, None]
moves_counter = 0
filename = ''
mimic_offset_x = 0
mimic_offset_y = 0
vertical_offset = 0
horizontal_offset = 0

app = Flask(__name__)

@app.route('/')
def index():
    try:
        file_uploading_path = "static/file uploading"
        Path(file_uploading_path).mkdir(parents=True, exist_ok=True)
        shutil.rmtree(file_uploading_path)
        os.mkdir(file_uploading_path)
    except:
        pass
    open('static/file uploading/empty_file.txt', 'w').close()
    return render_template("index.html")

@app.route('/fix_points', methods=['POST'])
def fix_points():
    global ratio, points, filename, blocks_sets, frog_indexes, moves_counter, mimic_offset_x, mimic_offset_y,\
        vertical_offset, horizontal_offset, checkbox, solve_result, order_result
    frog_indexes = [3, 3]
    moves_counter = 0
    mimic_offset_x = 0
    mimic_offset_y = 0
    vertical_offset = 0
    horizontal_offset = 0
    checkbox = False
    solve_result = []
    order_result = []
    image_height, image_width = 0, 0
    success_flag = False
    filename = ''
    fixed_points = []
    if request.method == 'POST':
        blocks_sets = []
        print(request.data)
        f = request.files['file']

        screen_width = int(request.form.get('screen-width')) - 20
        extension = f.filename.split('.')[-1]
        if extension in ['jpg', 'jpeg', 'png', 'webp']:
            filename = f'static/file uploading/{int(time.time())}.{extension}'
            f.save(filename)
            im = cv2.imread(filename)
            image_size = im.shape[:-1]
            ratio = min(400, screen_width) / image_size[1]
            points = get_blocks_from_image(screenshot=filename, web_mode=True)
            for point in points:
                fixed_points.append([int(point[1] * ratio), int(point[0] * ratio), point[4], point[5]])
            image_height = int(image_size[0] * ratio)
            image_width = int(image_size[1] * ratio)
            success_flag = True
        return render_template("fix_points.html", filename=filename, success=success_flag,
                               image_height=image_height, image_width=image_width, points=fixed_points, ratio=ratio)
    return redirect('/')

def update_offsets(req):
    global mimic_offset_x, mimic_offset_y, vertical_offset, horizontal_offset
    mimic_offset_x = int(float(req.form['mimic_offset_x']) / ratio)
    mimic_offset_y = int(float(req.form['mimic_offset_y']) / ratio)
    vertical_offset = int(float(req.form['vertical_offset']) / ratio)
    horizontal_offset = int(float(req.form['horizontal_offset']) / ratio)

def thread_solve(specific_benefit):
    global solve_result
    solve_result.append(solve(points, web_mode=True, specific_benefit=specific_benefit))

def thread_get_order(messages):
    global order_result
    for blocks_set in messages[1:]:
        benefit = messages[0]
        page_template, found = get_order_template(blocks_set, benefit)
        if found:
            order_result.append(page_template)
            return
    order_result.append(None)

@app.route('/solve', methods=['POST', 'GET'])
def app_solve():
    global points, checkbox
    if request.method == 'POST':
        update_offsets(request)
        specific_benefit = request.form['specific_benefit']
        checkbox = True if request.form['get_order'] == 'true' else False
        points = get_points()
        if specific_benefit and specific_benefit.isdigit() and int(specific_benefit) > 0:
            specific_benefit = int(specific_benefit)
            t1 = threading.Thread(target=thread_solve, args=(specific_benefit,))
        else:
            t1 = threading.Thread(target=thread_solve, args=(None,))
        t1.start()
        return {'status': False}
    return redirect('/')


@app.route('/check_solve_result', methods=['POST', 'GET'])
def check_solve_result():
    global blocks_sets
    if request.method == 'POST':
        if solve_result:
            messages = solve_result[0]
            benefit = ''
            if checkbox:
                t2 = threading.Thread(target=thread_get_order, args=(messages,))
                t2.start()
                return {'solve_status': True, 'order_status': False}
            if len(messages) > 1:
                dir_name = f'{filename} Solutions'
                for i, message in enumerate(messages):
                    if i == 0:
                        benefit = message
                    else:
                        blocks_set = message
                        file_name = f'{dir_name}/solution-{i}.png'
                        if os.path.isfile(file_name):
                            blocks_sets.append([file_name, blocks_set])
            return {'solve_status': True,
                    'html': render_template("results.html", blocks_sets=blocks_sets, benefit=benefit)}
        return {'solve_status': False}
    return redirect('/')


@app.route('/check_order_result', methods=['POST', 'GET'])
def check_order_result():
    if request.method == 'POST':
        if order_result:
            page_template = order_result[0]
            if not page_template:
                return {'order_status': True,
                        'html': render_template("order.html", message='No order found.', duration=0,
                                                image_path=filename, benefit=0)}
            return {'order_status': True, 'html': page_template}
        return {'order_status': False}
    return redirect('/')

@app.route('/get_order', methods=['POST', 'GET'])
def app_get_order(blocks_set=None, benefit=None):
    if request.method == 'POST':
        if benefit is None:
            benefit = request.form.get('benefit')
        if blocks_set is None:
            blocks_set_number = int(request.form.get('blocks-set-number'))
            _, blocks_set = blocks_sets[blocks_set_number]
        return get_order_template(blocks_set, benefit)[0]
    return redirect('/')

def get_order_template(blocks_set, benefit):
    with app.app_context():
        message, duration, order = get_order(points, web_blocks=blocks_set, web_mode=True)
        image_path = save_order_as_image(order, points, filename, ratio)
        found = False if message == 'No order found.' else True
        if blocks_set:
            return render_template("order.html", message=message, duration=duration, image_path=image_path,
                                   benefit=benefit), found
        return render_template("order.html", message=message, duration=duration, image_path=image_path,
                               benefit=benefit), found

@app.route('/restart', methods=['GET'])
def restart():
    global points, frog_indexes, moves_counter
    frog_indexes = [3, 3]
    moves_counter = 0
    points = get_points()
    return redirect('/play')

@app.route('/play', methods=['GET', 'POST'])
def play():
    global points, frog_indexes, moves_counter, mimic_offset_x, mimic_offset_y, vertical_offset, horizontal_offset
    blocks = []
    benefit = 0
    if points:
        if request.method == 'GET':
            i = request.args.get('block_i')
            j = request.args.get('block_j')
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

                return render_template("play.html", blocks=blocks, is_win=status,
                                       frog_indexes=frog_indexes, moves_counter=moves_counter, benefit=benefit)
            else:
                for point in points:
                    if point[-1] is True:
                        blocks.append(list(point[2:4]))
                return render_template("play.html", blocks=blocks, is_win=None, frog_indexes=frog_indexes,
                                       moves_counter=moves_counter, benefit=0)
        if request.method == 'POST':
            update_offsets(request)
            points = get_points()
            return redirect('/play')
    return redirect('/')

def get_points():
    return get_blocks_from_image(screenshot=filename, web_mode=True, mimic_offset_x=mimic_offset_x,
                          mimic_offset_y=mimic_offset_y, vertical_offset=vertical_offset,
                          horizontal_offset=horizontal_offset)

if __name__ == '__main__':
    app.run()
