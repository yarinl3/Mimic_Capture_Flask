import os, time, cv2, shutil
from flask import Flask, render_template, request, redirect
from Mimic_Capture import get_blocks_from_image, solve, get_order, save_order_as_image, play_game_web
from pathlib import Path
ratio = 1
points = []
blocks_sets = []
frog_indexes = [None, None]
moves_counter = 0
filename = ''
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
    global ratio, points, filename, blocks_sets, frog_indexes
    frog_indexes = [3, 3]
    success_flag = False
    filename = ''
    image_height, image_width = 0, 0
    fixed_points = []
    if request.method == 'POST':
        blocks_sets = []
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

@app.route('/solve', methods=['POST'])
def app_solve():
    global points, blocks_sets
    benefit = ''
    if request.method == 'POST':
        mimic_offset_x = int(float(request.form.get('mimic_offset_x')) / ratio)
        mimic_offset_y = int(float(request.form.get('mimic_offset_y')) / ratio)
        vertical_offset = int(float(request.form.get('vertical_offset')) / ratio)
        horizontal_offset = int(float(request.form.get('horizontal_offset')) / ratio)
        points = get_blocks_from_image(screenshot=filename, web_mode=True, mimic_offset_x=mimic_offset_x,
                                       mimic_offset_y=mimic_offset_y, vertical_offset=vertical_offset,
                                       horizontal_offset=horizontal_offset)
        messages = solve(points, web_mode=True)
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
        return render_template("results.html", blocks_sets=blocks_sets, benefit=benefit,
                               file_number=filename.split('/')[-1].replace('.png', ''))
    return redirect('/')

@app.route('/get_order', methods=['POST'])
def app_get_order():
    if request.method == 'POST':
        blocks_set_number = int(request.form.get('blocks-set-number'))
        _, blocks_set = blocks_sets[blocks_set_number]
        message, duration, order = get_order(points, web_blocks=blocks_set, web_mode=True)
        image_path = save_order_as_image(order, points, filename, ratio)
        return render_template("order.html", message=message, duration=duration, image_path=image_path)
    return redirect('/')


@app.route('/play', methods=['GET', 'POST'])
def play():
    global points, frog_indexes, moves_counter
    blocks = []
    if points:
        if request.method == 'GET':
            i = request.args.get('block_i')
            j = request.args.get('block_j')
            if i:
                if frog_indexes[0] in [0,6] or frog_indexes[1] in [0,6]:
                    return redirect('/')
                i = int(i)
                j = int(j)
                status, points, frog_indexes = play_game_web(points, [i, j], frog_indexes)
                moves_counter += 1
                if moves_counter == 10 and status is not True:
                    status = False
                for point in points:
                    if point[-1] is True:
                        blocks.append(list(point[2:4]))
                return render_template("play.html", blocks=blocks, is_win=status, frog_indexes=frog_indexes)
            else:
                for point in points:
                    if point[-1] is True:
                        blocks.append(list(point[2:4]))
                return render_template("play.html", blocks=blocks, is_win=None, frog_indexes=frog_indexes)
        if request.method == 'POST':
            mimic_offset_x = int(float(request.form.get('mimic_offset_x_play')) / ratio)
            mimic_offset_y = int(float(request.form.get('mimic_offset_y_play')) / ratio)
            vertical_offset = int(float(request.form.get('vertical_offset_play')) / ratio)
            horizontal_offset = int(float(request.form.get('horizontal_offset_play')) / ratio)
            points = get_blocks_from_image(screenshot=filename, web_mode=True, mimic_offset_x=mimic_offset_x,
                                           mimic_offset_y=mimic_offset_y, vertical_offset=vertical_offset,
                                           horizontal_offset=horizontal_offset)
            return redirect('/play')

    return redirect('/')


if __name__ == '__main__':
    app.run()
