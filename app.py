from Mimic_Capture import get_blocks_from_image, solve, save_order_as_image, users_mimic
from flask import Flask, render_template, request, redirect
import os, time, cv2, shutil, threading

REMOVE_TIME = 60*5 # 5 min

users = dict()
POINTS, BLOCKS_SETS, RATIO, FILENAME, FROG_INDEXES, MOVES_COUNTER  = 0, 1, 2, 3, 4, 5
MIMIC_OFFSET_X, MIMIC_OFFSET_Y, VERTICAL_OFFSET, HORIZONTAL_OFFSET = 6, 7, 8, 9
SOLVE_RESULT, ORDER_RESULT, = 10, 11

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
        filename = ''
        ratio = 1
        users[user_id] = [points, blocks_sets, ratio, filename, frog_indexes, moves_counter, mimic_offset_x,
                          mimic_offset_y, vertical_offset, horizontal_offset, solve_result, order_result]

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
        users[user_id][POINTS] = get_points(user_id)
        t1 = threading.Thread(target=thread_solve, args=(user_id,))
        t1.start()
        return {'status': False}
    return redirect('/')


def thread_solve(user_id):
    users[user_id][SOLVE_RESULT].append(solve(users[user_id][POINTS], user_id))


@app.route('/check_result', methods=['POST', 'GET'])
def check_result():
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        if users[user_id][SOLVE_RESULT]:
            order, benefit = users[user_id][SOLVE_RESULT][0]
            image_path = save_order_as_image(order, users[user_id][POINTS], users[user_id][FILENAME])
            page_template = render_template("order.html", image_path=image_path, benefit=benefit)
            return {'status': True, 'html': page_template}
        return {'status': False, 'counter': users_mimic[user_id][1], 'combinations': users_mimic[user_id][0]}
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
