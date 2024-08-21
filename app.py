import os, time, cv2, shutil
from flask import Flask, render_template, request, redirect
from Mimic_Capture import get_blocks_from_image, solve, get_order
from multiprocessing.dummy import Pool # test
ratio = 1
points = []
blocks_sets = []
filename = ''
app = Flask(__name__)
pool = Pool(10) # test

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/fix_points', methods=['POST'])
def fix_points():
    global ratio, points, filename, blocks_sets
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
            ratio = min(500, screen_width) / image_size[1]
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
        mimic_offset_x = int(int(request.form.get('mimic_offset_x')) / ratio)
        mimic_offset_y = int(int(request.form.get('mimic_offset_y')) / ratio)
        vertical_offset = int(int(request.form.get('vertical_offset')) / ratio)
        horizontal_offset = int(int(request.form.get('horizontal_offset')) / ratio)
        points = get_blocks_from_image(screenshot=filename, web_mode=True, mimic_offset_x=mimic_offset_x,
                                       mimic_offset_y=mimic_offset_y, vertical_offset=vertical_offset,
                                       horizontal_offset=horizontal_offset)
        #messages = solve(points, web_mode=True)
        messages = pool.apply_async(solve, [points, True]).get(timeout=100)
        if len(messages) > 1:
            dir_name = f'{filename} Solutions'
            os.remove(filename)
            for i, message in enumerate(messages):
                if i == 0:
                    benefit = message
                else:
                    blocks_set = message
                    file_name = f'{dir_name}/solution-{i}.png'
                    if os.path.isfile(file_name):
                        blocks_sets.append([file_name, blocks_set])
        return render_template("results.html", blocks_sets=blocks_sets, benefit=benefit,
                               file_number=filename.split('/')[-1].replace('.png', '')), 202
    return redirect('/'),

@app.route('/get_order', methods=['POST'])
def app_get_order():
    if request.method == 'POST':
        blocks_set_number = int(request.form.get('blocks-set-number'))
        image_path, blocks_set = blocks_sets[blocks_set_number]
        message, duration = get_order(points, web_blocks=blocks_set, web_mode=True)
        return render_template("order.html", message=message, duration=duration, image_path=image_path)
    return redirect('/')

@app.route('/delete/<int:file_number>', methods=['GET'])
def delete_files(file_number):
    try:
        shutil.rmtree(f'static/file uploading/{file_number}.png Solutions')
    except:
        print(f'Error while deleting files. Cant find {file_number}.png Solutions')
    try:
        os.remove(f'static/file uploading/{file_number}.png')
    except:
        pass
    return ''
if __name__ == '__main__':
    app.run(debug=True)
