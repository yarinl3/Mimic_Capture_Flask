import cv2, os
from PIL import Image
import numpy as np


horizontal_fix, vertical_fix, width_fix, height_fix = 0, 0, 0, 0
RELATIVE_ON_SCREEN_POSITION = 0.6015
VERTICAL_RATIO = 0.0536
HORIZONTAL_RATIO = 0.113
NUMBER_OF_BLOCKS_TO_REMOVE = 10
SAMPLE_RADIUS = 15
ROWS_NUMBER, COLS_NUMBER = 7, 7


def get_blocks_from_image(screenshot, mimic_offset_x=0, mimic_offset_y=0, vertical_offset=0, horizontal_offset=0):
    img_rgb = cv2.imread(screenshot)
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
    return points


def convert_pic(screenshot):
    im = Image.open(screenshot).convert('RGB')
    for extension in ['webp', 'jpg', 'jpeg']:
        if screenshot.endswith(f'.{extension}'):
            new_path = screenshot.replace(f'.{extension}', '.png')
            im.save(new_path, "png")
            os.remove(screenshot)
            return new_path
    return screenshot


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

        points_horizontal_distance = int((points[2][1] - points[0][1])/8)
        points_horizontal_distance_10 = points_horizontal_distance * 2
        points_vertical_distance = int((points[7][0] - points[5][0]) / 2)
        font_scale = points_horizontal_distance / 12
        thickness = int(font_scale * 2) + 1
        if block_number == NUMBER_OF_BLOCKS_TO_REMOVE - 1:
            points_horizontal_distance = points_horizontal_distance_10

        cv2.putText(img_rgb, str(block_number + 1), (int(pixel_j-points_horizontal_distance),
                                                     int(pixel_i+points_vertical_distance)), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,(255, 0, 0), thickness)
    cv2.imwrite(f'{filename} order.png', img_rgb)
