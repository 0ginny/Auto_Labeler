import sys
import os
import cv2
from PyQt5.QtCore import Qt, QTimer, QPointF,QEvent
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QDialog, QListWidget, QSpinBox, QAbstractSpinBox, QHBoxLayout, QLineEdit, QSplitter, QFrame, QSizePolicy, QScrollArea

from canvas import Canvas
from zoom import ZoomWidget


from ultralytics import YOLO

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.labels = self.load_labels("classes.txt")
        self.yolo_model = None
        self.selected_preprocessing = "Normal"  # 초기 전처리 상태 추가
        self.initUI()
        self.selected_camera = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None
        self.output_folder = None
        self.save_count = 0
        self.captured = False  # 캡처 상태 플래그

        # 전역 이벤트 필터 설치
        QApplication.instance().installEventFilter(self)

    def load_labels(self, filename):
        with open(filename, "r") as f:
            return [line.strip() for line in f.readlines()]

    def initUI(self):
        self.setWindowTitle("Camera Selector")

        # 메인 레이아웃 설정
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # 사이드바 레이아웃 설정
        sidebar_layout = QVBoxLayout()

        self.comboBox = QComboBox(self)
        self.comboBox.addItems(self.find_cameras())
        sidebar_layout.addWidget(QLabel("Select Camera:"))
        sidebar_layout.addWidget(self.comboBox)

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_camera)
        sidebar_layout.addWidget(self.start_button)

        self.yolo_load_button = QPushButton("Load YOLO Model", self)
        self.yolo_load_button.clicked.connect(self.load_yolo_model)
        sidebar_layout.addWidget(self.yolo_load_button)

        self.model_label = QLabel("AI Labeling OFF")
        self.model_label.setFixedHeight(30)
        sidebar_layout.addWidget(self.model_label)

        self.save_button = QPushButton("Save Dataset", self)
        self.save_button.clicked.connect(self.save_yolo_format)
        sidebar_layout.addWidget(self.save_button)

        self.zoom_widget = ZoomWidget(value=100)
        self.zoom_widget.valueChanged.connect(self.zoom_changed)
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_widget)
        sidebar_layout.addLayout(zoom_layout)

        self.save_name_input = QLineEdit(self)
        self.save_name_input.setPlaceholderText("Enter base save name")
        sidebar_layout.addWidget(self.save_name_input)

        self.preprocessing_combo = QComboBox(self)
        self.preprocessing_combo.addItems(["Normal", "Increase Brightness", "Image Pyramids", "Color Space Conversion"])
        self.preprocessing_combo.currentTextChanged.connect(self.change_preprocessing)
        sidebar_layout.addWidget(QLabel("Select Preprocessing:"))
        sidebar_layout.addWidget(self.preprocessing_combo)

        sidebar_layout.addStretch()

        sidebar_widget = QFrame()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        sidebar_widget.setLineWidth(2)
        sidebar_widget.setFixedWidth(200)  # 사이드바의 너비를 고정

        # 캔버스(웹캠 화면) 설정
        self.canvas = Canvas(self.labels, self)
        self.canvas.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.canvas.setLineWidth(2)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 캔버스가 창 크기에 맞게 확장되도록 설정

        # QSplitter 설정
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(self.canvas)

        # 사이드바는 고정된 너비, 웹캠 화면은 확장되도록 설정
        splitter.setStretchFactor(0, 0)  # 사이드바는 고정 크기
        splitter.setStretchFactor(1, 1)  # 웹캠 화면은 확장

        main_layout.addWidget(splitter)

        # 메인 창 크기 조정 정책 설정
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 600)  # 최소 창 크기 설정 (필요에 따라 조정 가능)

    def change_preprocessing(self, text):
        self.selected_preprocessing = text

    def apply_preprocessing(self, frame):
        """전처리 적용"""
        if self.selected_preprocessing == "Increase Brightness":
            return self.increase_brightness(frame, beta=50)
        elif self.selected_preprocessing == "Image Pyramids":
            higher_reso = self.image_pyramids(frame)
            return higher_reso  # 고해상도 이미지를 반환
        elif self.selected_preprocessing == "Color Space Conversion":
            return self.color_space_converted(frame)
        else:
            return frame

    def increase_brightness(self, image, beta):
        """이미지의 밝기를 증가시키는 함수"""
        bright_image = cv2.convertScaleAbs(image, alpha=1, beta=beta)
        return bright_image

    def image_pyramids(self, image):
        """이미지의 해상도를 높이는 함수 (피라미드 업샘플링)"""
        higher_reso = cv2.pyrUp(image)
        return higher_reso

    def color_space_converted(self, image):
        """이미지를 BGR에서 HSV 색 공간으로 변환하는 함수"""
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        return hsv_image

    def zoom_changed(self, value):
        self.canvas.scale_factor = value / 100.0
        self.canvas.update_image_offset()
        self.canvas.update()

    def find_cameras(self):
        index = 0
        arr = []
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                break
            else:
                arr.append(f"Camera {index}")
            cap.release()
            index += 1
        return arr

    def start_camera(self):
        index = self.comboBox.currentIndex()
        if self.selected_camera is not None:
            self.selected_camera.release()

        self.selected_camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if self.selected_camera.isOpened():
            self.timer.start(30)
            self.captured = False  # 캡처 상태 초기화
        else:
            print("Failed to open the selected camera.")

    def update_frame(self):
        try:
            if self.selected_camera is not None and self.selected_camera.isOpened():
                ret, frame = self.selected_camera.read()
                if ret:
                    # 선택된 전처리 적용
                    frame = self.apply_preprocessing(frame)
                    self.current_frame = frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV 이미지를 RGB로 변환
                    image = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(image)

                    # 비디오 프레임은 항상 창 크기에 맞춰 조정
                    self.canvas.load_pixmap(pixmap)
        except Exception as e:
            print(f"Error in update_frame: {e}")

    def capture_still(self):
        try:
            if self.current_frame is not None:
                self.timer.stop()  # 타이머를 멈춰 비디오 입력을 중지
                if self.selected_camera.isOpened():
                    self.selected_camera.release()  # 비디오 스트리밍을 중지

                captured_frame = self.current_frame.copy()  # current_frame을 복사하여 사용
                captured_frame_rgb = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)
                image = QImage(captured_frame_rgb, captured_frame_rgb.shape[1], captured_frame_rgb.shape[0],
                               QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)

                # 캡처된 이미지는 사용자가 줌할 수 있도록 함
                self.canvas.load_pixmap(pixmap)
                self.canvas.scale_factor = 1.0  # 캡처 후 기본 줌 레벨을 100%로 설정

                # 객체 탐지 및 라벨링
                if self.yolo_model:
                    results = self.yolo_model(captured_frame)
                    for result in results:
                        for box in result.boxes:
                            x_min, y_min, x_max, y_max = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls[0])
                            label_name = self.labels[class_id]
                            shape = [QPointF(x_min, y_min), QPointF(x_max, y_max)]
                            self.canvas.shapes.append((shape, label_name))
                            self.canvas.labeling_done = True  # AI에 의한 라벨링도 완료로 설정
                            self.canvas.update()

                self.captured = True  # 캡처 완료 상태
                self.selected_camera = None  # 선택된 카메라를 해제

        except Exception as e:
            print(f"Error in capture_still: {e}")

    def save_yolo_format(self):
        try:
            if not hasattr(self, 'canvas') or not self.canvas.get_shapes():
                return

            if not self.output_folder:
                self.output_folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
                if not self.output_folder:
                    return

            images_folder = os.path.join(self.output_folder, "images")
            labels_folder = os.path.join(self.output_folder, "labels")

            os.makedirs(images_folder, exist_ok=True)
            os.makedirs(labels_folder, exist_ok=True)

            base_name = self.save_name_input.text()
            if not base_name:
                base_name = "capture"

            # 중복 파일 이름 체크 및 카운트
            while True:
                img_save_path = os.path.join(images_folder, f"{base_name}_{self.save_count}.jpg")
                label_save_path = os.path.join(labels_folder, f"{base_name}_{self.save_count}.txt")
                if not os.path.exists(img_save_path) and not os.path.exists(label_save_path):
                    break
                self.save_count += 1

            # 이미지 저장
            cv2.imwrite(img_save_path, self.current_frame)

            # 라벨 저장
            img_size = (self.canvas.pixmap().height(), self.canvas.pixmap().width())
            yolo_data = []
            for shape, label in self.canvas.get_shapes():
                x_min = min(shape[0].x(), shape[1].x())
                y_min = min(shape[0].y(), shape[1].y())
                x_max = max(shape[0].x(), shape[1].x())
                y_max = max(shape[0].y(), shape[1].y())

                x_center = (x_min + x_max) / 2 / img_size[1]
                y_center = (y_min + y_max) / 2 / img_size[0]
                width = (x_max - x_min) / img_size[1]
                height = (y_max - y_min) / img_size[0]

                label_index = self.labels.index(label)
                yolo_data.append(f"{label_index} {x_center} {y_center} {width} {height}")

            with open(label_save_path, 'w') as f:
                f.write("\n".join(yolo_data))

            # 데이터셋을 위한 YAML 파일 생성
            yaml_path = os.path.join(self.output_folder, "dataset.yaml")
            with open(yaml_path, 'w') as f:
                yaml_content = f"""train: ./images
val: ./images

nc: {len(self.labels)}
names: {self.labels}
"""
                f.write(yaml_content)

            self.save_count += 1
            self.reset_to_video_feed()  # 저장 후 다시 비디오 피드로 돌아감

        except Exception as e:
            print(f"Error in save_yolo_format: {e}")

    def reset_to_video_feed(self):
        self.current_frame = None
        self.canvas.shapes = []
        self.canvas.labeling_done = False  # 라벨링 상태 초기화
        self.start_camera()
        self.captured = False  # 캡처 상태 초기화

    def load_yolo_model(self):
        try:
            model_path, _ = QFileDialog.getOpenFileName(self, "Select YOLO Model", "", "PyTorch Models (*.pt)")
            if model_path:
                self.yolo_model = YOLO(model_path)
                self.model_label.setText("AI Labeling ON")
        except Exception as e:
            print(f"Error in load_yolo_model: {e}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return:
                if not self.captured:
                    self.capture_still()
                else:
                    if not self.canvas.labeling_done:  # 라벨링이 완료되지 않았으면 저장 없이 복귀
                        self.reset_to_video_feed()
                    else:
                        self.save_yolo_format()
                return True
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        try:
            if self.selected_camera is not None:
                self.selected_camera.release()
        except Exception as e:
            print(f"Error in closeEvent: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CameraApp()
    ex.show()
    sys.exit(app.exec_())