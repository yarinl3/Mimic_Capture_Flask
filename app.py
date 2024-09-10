from Mimic_Capture import get_blocks_from_image, save_order_as_image
from flask import Flask, render_template, request, redirect
import os, time, cv2, operator, random

REMOVE_TIME = 60*5 # 5 min

users = dict()
POINTS, RATIO, FILENAME = 0, 1, 2

index_to_point = dict()
counter = 0
for i in range(7):
    for j in range(7):
        index_to_point[str(counter)] = [i, j]
        counter += 1
app = Flask(__name__)

@app.route('/')
def index():
    remove_old_files()
    return render_template("index.html")


@app.route('/fix_points', methods=['POST', 'GET'])
def fix_points():
    global users
    if request.method == 'POST':
        user_id = random.randint(1, 1000000000)
        points, fixed_points = [], []
        image_height, image_width = 0, 0
        filename = ''
        ratio = 1
        users[user_id] = [points, ratio, filename]
        success_flag = False
        f = request.files['file']
        screen_width = int(request.form.get('screen-width')) - 20
        extension = f.filename.split('.')[-1].lower()
        if extension in ['jpg', 'jpeg', 'png', 'webp']:
            filename = f'static/file uploading/{user_id}.{extension}'
            users[user_id][FILENAME] = filename
            f.save(filename)
            im = cv2.imread(filename)
            image_size = im.shape[:-1]
            ratio = min(400, screen_width) / image_size[1]
            users[user_id][RATIO] = ratio
            points = get_blocks_from_image(screenshot=filename)
            for point in points:
                fixed_points.append([int(point[1] * ratio), int(point[0] * ratio), point[4], point[5]])

            users[user_id][POINTS] = fixed_points
            image_height = int(image_size[0] * ratio)
            image_width = int(image_size[1] * ratio)
            success_flag = True
        return render_template("fix_points.html",user_id=user_id, filename=filename, success=success_flag,
                               image_height=image_height, image_width=image_width, points=fixed_points, ratio=ratio)
    return redirect('/')


@app.route('/update_points', methods=['POST'])
def update_points():
    global users

    if request.method == 'POST':
        true_false_list = []
        user_id = int(request.form['user_id'])
        ratio = users[user_id][RATIO]
        points = get_blocks_from_image(users[user_id][FILENAME],
                                       mimic_offset_x=int(float(request.form['mimic_offset_x']) / ratio),
                                       mimic_offset_y=int(float(request.form['mimic_offset_y']) / ratio),
                                       vertical_offset=int(float(request.form['vertical_offset']) / ratio),
                                       horizontal_offset=int(float(request.form['horizontal_offset']) / ratio))
        points = sorted(sorted(points, key=operator.itemgetter(3)), key=operator.itemgetter(2))
        users[user_id][POINTS] = points
        for point in points:
            true_false_list.append(point[-1])
        return {'success': True, 'true_false_list': true_false_list}

    return {'success': False}


@app.route('/paint_order', methods=['POST'])
def paint_order():
    global users
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        index_order = request.form.getlist('order[]')
        points_order = [index_to_point[index] for index in index_order]
        save_order_as_image(points_order, users[user_id][POINTS], users[user_id][FILENAME])
        return {'success': True}
    return {'success': False}


def remove_old_files():
    uploading_dir = 'static/file uploading'
    for file in os.listdir(uploading_dir):
        if file != 'empty_file.txt':
            file_name = uploading_dir + '/' + file
            file_create_time = int(os.path.getctime(file_name))
            if file_create_time + REMOVE_TIME < int(time.time()):
                try:
                        os.remove(file_name)
                        file_number = int(file_name.split('.')[0])
                        if file_number in users:
                            del users[file_number]
                except:
                    pass



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
