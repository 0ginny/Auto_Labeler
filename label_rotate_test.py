import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt


def rotate_image_and_labels(image, labels, angle):
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
        # YOLO 형식 라벨을 실제 좌표로 변환
        class_id, x_center, y_center, width, height = map(float, label.strip().split())

        # 박스의 4개의 모서리 좌표 계산
        x_center_actual = x_center * w
        y_center_actual = y_center * h
        box_width_actual = width * w
        box_height_actual = height * h

        xmin = x_center_actual - box_width_actual / 2
        xmax = x_center_actual + box_width_actual / 2
        ymin = y_center_actual - box_height_actual / 2
        ymax = y_center_actual + box_height_actual / 2

        # 모서리 좌표 리스트
        corners = np.array([
            [xmin, ymin],
            [xmax, ymin],
            [xmax, ymax],
            [xmin, ymax]
        ])

        # 회전 행렬 적용하여 모서리 좌표 회전
        ones = np.ones(shape=(len(corners), 1))
        corners_hom = np.hstack([corners, ones])  # 동차 좌표로 변환
        rotated_corners = matrix.dot(corners_hom.T).T

        # 회전된 좌표들로부터 새로운 바운딩 박스 계산
        x_coords = rotated_corners[:, 0]
        y_coords = rotated_corners[:, 1]

        new_xmin = np.min(x_coords)
        new_xmax = np.max(x_coords)
        new_ymin = np.min(y_coords)
        new_ymax = np.max(y_coords)

        # 새로운 중심 좌표 및 크기 계산
        new_x_center_actual = (new_xmin + new_xmax) / 2
        new_y_center_actual = (new_ymin + new_ymax) / 2
        new_box_width_actual = new_xmax - new_xmin
        new_box_height_actual = new_ymax - new_ymin

        # 새 좌표를 YOLO 형식으로 정규화
        new_x_center = new_x_center_actual / new_w
        new_y_center = new_y_center_actual / new_h
        new_width = new_box_width_actual / new_w
        new_height = new_box_height_actual / new_h

        # 새로운 라벨 추가
        rotated_label = f"{class_id} {new_x_center} {new_y_center} {new_width} {new_height}"
        rotated_labels.append(rotated_label)

    return rotated_img, rotated_labels


class ImageRotationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Rotation and YOLO Label Adjustment')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.label1 = QLabel('Select the folder containing images and labels', self)
        self.label1.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label1)

        self.btn1 = QPushButton('Select Folder to Process', self)
        self.btn1.clicked.connect(self.selectProcessFolder)
        layout.addWidget(self.btn1)

        self.label2 = QLabel('Select the folder to save processed files', self)
        self.label2.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label2)

        self.btn2 = QPushButton('Select Save Folder', self)
        self.btn2.clicked.connect(self.selectSaveFolder)
        layout.addWidget(self.btn2)

        # 회전 범위와 간격을 설정할 수 있는 입력 필드
        angle_layout = QHBoxLayout()

        self.min_angle_label = QLabel('Min Angle:')
        self.min_angle_input = QLineEdit(self)
        self.min_angle_input.setText('10')  # 기본값 설정

        self.max_angle_label = QLabel('Max Angle:')
        self.max_angle_input = QLineEdit(self)
        self.max_angle_input.setText('80')  # 기본값 설정

        self.step_label = QLabel('Step:')
        self.step_input = QLineEdit(self)
        self.step_input.setText('10')  # 기본값 설정

        angle_layout.addWidget(self.min_angle_label)
        angle_layout.addWidget(self.min_angle_input)
        angle_layout.addWidget(self.max_angle_label)
        angle_layout.addWidget(self.max_angle_input)
        angle_layout.addWidget(self.step_label)
        angle_layout.addWidget(self.step_input)

        layout.addLayout(angle_layout)

        self.process_folder = ''
        self.save_folder = ''

        self.btnProcess = QPushButton('Process and Save', self)
        self.btnProcess.clicked.connect(self.processImages)
        layout.addWidget(self.btnProcess)

        self.setLayout(layout)

    def selectProcessFolder(self):
        self.process_folder = QFileDialog.getExistingDirectory(self, 'Select Folder to Process')
        self.label1.setText(f'Selected: {self.process_folder}')

    def selectSaveFolder(self):
        self.save_folder = QFileDialog.getExistingDirectory(self, 'Select Save Folder')
        self.label2.setText(f'Selected: {self.save_folder}')

    def processImages(self):
        if not self.process_folder or not self.save_folder:
            self.label1.setText('Please select both folders.')
            return

        image_folder = os.path.join(self.process_folder, 'images')
        label_folder = os.path.join(self.process_folder, 'labels')

        save_image_folder = os.path.join(self.save_folder, 'images')
        save_label_folder = os.path.join(self.save_folder, 'labels')

        os.makedirs(save_image_folder, exist_ok=True)
        os.makedirs(save_label_folder, exist_ok=True)

        # 회전 각도 설정
        min_angle = int(self.min_angle_input.text())
        max_angle = int(self.max_angle_input.text())
        step = int(self.step_input.text())

        for img_name in os.listdir(image_folder):
            if img_name.endswith(('.jpg', '.png')):
                img_path = os.path.join(image_folder, img_name)
                img = cv2.imread(img_path)

                label_name = os.path.splitext(img_name)[0] + '.txt'
                label_path = os.path.join(label_folder, label_name)

                if os.path.exists(label_path):
                    with open(label_path, 'r') as label_file:
                        labels = label_file.readlines()

                    for angle in range(min_angle, max_angle + 1, step):
                        # 이미지 및 라벨 회전
                        rotated_img, rotated_labels = rotate_image_and_labels(img, labels, angle)

                        # 회전된 이미지 저장
                        save_img_path = os.path.join(save_image_folder,
                                                     f'{os.path.splitext(img_name)[0]}_rot{angle}.jpg')
                        cv2.imwrite(save_img_path, rotated_img)

                        # 회전된 라벨 저장
                        save_label_path = os.path.join(save_label_folder,
                                                       f'{os.path.splitext(label_name)[0]}_rot{angle}.txt')
                        with open(save_label_path, 'w') as new_label_file:
                            new_label_file.writelines(rotated_labels)

        self.label1.setText('Processing completed and files saved.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageRotationApp()
    ex.show()
    sys.exit(app.exec_())
