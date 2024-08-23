import cv2
import os
import numpy as np


class ImageAugmentation:
    def __init__(self):
        pass

    def rotate_images(self, min_angle, max_angle, step, process_folder, save_folder):
        image_folder = os.path.join(process_folder, 'images')
        label_folder = os.path.join(process_folder, 'labels')

        save_image_folder = os.path.join(save_folder, 'images')
        save_label_folder = os.path.join(save_folder, 'labels')

        os.makedirs(save_image_folder, exist_ok=True)
        os.makedirs(save_label_folder, exist_ok=True)

        angles = range(min_angle, max_angle + 1, step)

        for img_name in os.listdir(image_folder):
            if img_name.endswith(('.jpg', '.png')):
                img_path = os.path.join(image_folder, img_name)
                img = cv2.imread(img_path)

                label_name = os.path.splitext(img_name)[0] + '.txt'
                label_path = os.path.join(label_folder, label_name)

                if os.path.exists(label_path):
                    with open(label_path, 'r') as label_file:
                        labels = label_file.readlines()

                    for angle in angles:
                        # 이미지 및 라벨 회전
                        rotated_img, rotated_labels = self.rotate_image_and_labels(img, labels, angle)

                        # 회전된 이미지 저장
                        save_img_path = os.path.join(save_image_folder,
                                                     f'{os.path.splitext(img_name)[0]}_rot{angle}.jpg')
                        cv2.imwrite(save_img_path, rotated_img)

                        # 회전된 라벨 저장
                        save_label_path = os.path.join(save_label_folder,
                                                       f'{os.path.splitext(label_name)[0]}_rot{angle}.txt')
                        with open(save_label_path, 'w') as new_label_file:
                            new_label_file.writelines(rotated_labels)

    def rotate_image_and_labels(self, image, labels, angle):
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        # 회전 행렬 계산
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos_val = np.abs(matrix[0, 0])
        sin_val = np.abs(matrix[0, 1])

        # 회전된 이미지의 새로운 크기 계산
        new_w = int((h * sin_val) + (w * cos_val))
        new_h = int((h * cos_val) + (w * sin_val))

        # 회전 행렬의 이동 추가
        matrix[0, 2] += (new_w / 2) - center[0]
        matrix[1, 2] += (new_h / 2) - center[1]

        # 이미지 회전
        rotated_img = cv2.warpAffine(image, matrix, (new_w, new_h))

        rotated_labels = []

        for label in labels:
            class_id, x_center, y_center, width, height = map(float, label.strip().split())

            x_center_actual = x_center * w
            y_center_actual = y_center * h
            box_width_actual = width * w
            box_height_actual = height * h

            xmin = x_center_actual - box_width_actual / 2
            xmax = x_center_actual + box_width_actual / 2
            ymin = y_center_actual - box_height_actual / 2
            ymax = y_center_actual + box_height_actual / 2

            corners = np.array([
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax]
            ])

            ones = np.ones(shape=(len(corners), 1))
            corners_hom = np.hstack([corners, ones])
            rotated_corners = matrix.dot(corners_hom.T).T

            x_coords = rotated_corners[:, 0]
            y_coords = rotated_corners[:, 1]

            new_xmin = np.min(x_coords)
            new_xmax = np.max(x_coords)
            new_ymin = np.min(y_coords)
            new_ymax = np.max(y_coords)

            new_x_center_actual = (new_xmin + new_xmax) / 2
            new_y_center_actual = (new_ymin + new_ymax) / 2
            new_box_width_actual = new_xmax - new_xmin
            new_box_height_actual = new_ymax - new_ymin

            new_x_center = new_x_center_actual / new_w
            new_y_center = new_y_center_actual / new_h
            new_width = new_box_width_actual / new_w
            new_height = new_box_height_actual / new_h

            rotated_label = f"{class_id} {new_x_center} {new_y_center} {new_width} {new_height}"
            rotated_labels.append(rotated_label)

        return rotated_img, rotated_labels
