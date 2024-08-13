import sys
import os
import cv2
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize, QEvent
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QBrush, QFontMetrics
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QDialog, QListWidget, QSpinBox, QAbstractSpinBox, QHBoxLayout, QLineEdit, QSplitter, QFrame

from ultralytics import YOLO  # YOLO 모델 로드용

class ZoomWidget(QSpinBox):
    def __init__(self, value=100):
        super(ZoomWidget, self).__init__()
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setRange(1, 500)
        self.setSuffix(' %')
        self.setValue(value)
        self.setToolTip('Zoom Level')
        self.setStatusTip(self.toolTip())
        self.setAlignment(Qt.AlignCenter)

    def minimumSizeHint(self):
        height = super(ZoomWidget, self).minimumSizeHint().height()
        fm = QFontMetrics(self.font())
        width = fm.width(str(self.maximum())) + 10
        return QSize(width, height)

class LabelDialog(QDialog):
    def __init__(self, labels, parent=None):
        super(LabelDialog, self).__init__(parent)
        self.setWindowTitle("Select Label")

        self.layout = QVBoxLayout(self)

        self.list_widget = QListWidget(self)
        self.list_widget.addItems(labels)
        self.layout.addWidget(self.list_widget)

        self.list_widget.itemClicked.connect(self.item_selected)

    def item_selected(self, item):
        self.selected_label = item.text()
        self.accept()

    def get_label(self):
        return self.selected_label

class Canvas(QFrame):
    def __init__(self, labels, parent=None):
        super(Canvas, self).__init__(parent)
        self.labels = labels
        self.pixmap = None
        self.shapes = []
        self.current_shape = None
        self.drawing = False
        self.selected_shape = None
        self.selected_vertex = None
        self.hovered_shape = None
        self.dragging_shape = None
        self.scale_factor = 1.0
        self.canvas_size = QSize(720, 480)
        self.image_offset = QPointF(0, 0)
        self.setFixedSize(self.canvas_size)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.hovered_vertex = None
        self.vertex_radius = 5

    def load_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.update_image_offset()
        self.update()

    def update_image_offset(self):
        if self.pixmap:
            scaled_pixmap_size = self.pixmap.size() * self.scale_factor
            self.image_offset = QPointF(
                (self.canvas_size.width() - scaled_pixmap_size.width()) / 2,
                (self.canvas_size.height() - scaled_pixmap_size.height()) / 2
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.pixmap:
            scaled_pixmap = self.pixmap.scaled(
                self.pixmap.size() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(self.image_offset, scaled_pixmap)

            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            for shape, label in self.shapes:
                scaled_shape = [point * self.scale_factor + self.image_offset for point in shape]
                if shape == self.hovered_shape:
                    painter.setBrush(QColor(255, 0, 0, 25))
                else:
                    painter.setBrush(Qt.NoBrush)

                painter.setPen(QPen(QColor(0, 255, 0), 2))
                painter.drawRect(QRectF(scaled_shape[0], scaled_shape[1]))
                self._draw_vertices(painter, scaled_shape)

                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(QRectF(scaled_shape[0], scaled_shape[1]), Qt.AlignCenter, label)

            if self.current_shape:
                scaled_shape = [point * self.scale_factor + self.image_offset for point in self.current_shape]
                pen.setColor(QColor(255, 0, 0))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRectF(scaled_shape[0], scaled_shape[1]))
                self._draw_vertices(painter, scaled_shape)

    def _draw_vertices(self, painter, shape):
        vertices = [
            shape[0],
            QPointF(shape[1].x(), shape[0].y()),
            shape[1],
            QPointF(shape[0].x(), shape[1].y())
        ]
        for i, vertex in enumerate(vertices):
            radius = self.vertex_radius * 2 if (self.hovered_shape and self.hovered_vertex == i) else self.vertex_radius
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(vertex, radius, radius)

    def mousePressEvent(self, event):
        try:
            self.setFocus()
            if event.button() == Qt.LeftButton and self.pixmap:
                self.selected_vertex = None
                self.selected_shape = None
                self.dragging_shape = None

                click_pos = (event.pos() - self.image_offset) / self.scale_factor

                for shape, _ in self.shapes:
                    vertices = [
                        shape[0],
                        QPointF(shape[1].x(), shape[0].y()),
                        shape[1],
                        QPointF(shape[0].x(), shape[1].y())
                    ]
                    for i, vertex in enumerate(vertices):
                        if self._is_within_vertex(click_pos, vertex):
                            self.selected_shape = shape
                            self.selected_vertex = i
                            break
                    if self.selected_shape:
                        break

                if self.selected_shape is None:
                    for shape, _ in self.shapes:
                        if QRectF(shape[0], shape[1]).contains(click_pos):
                            self.selected_shape = shape
                            self.offset = click_pos - shape[0]
                            self.dragging_shape = shape
                            break

                if self.selected_shape is None:
                    if QRectF(QPointF(0, 0), QPointF(self.pixmap.size().width(), self.pixmap.size().height())).contains(click_pos):
                        self.current_shape = [click_pos, click_pos]
                        self.drawing = True

                self.update()
        except Exception as e:
            print(f"Error in mousePressEvent: {e}")

    def mouseMoveEvent(self, event):
        try:
            if self.drawing and self.current_shape:
                self.current_shape[1] = (event.pos() - self.image_offset) / self.scale_factor
                self.update()
            elif self.selected_vertex is not None and self.selected_shape:
                click_pos = (event.pos() - self.image_offset) / self.scale_factor
                if self.selected_vertex == 0:
                    self.selected_shape[0] = click_pos
                elif self.selected_vertex == 1:
                    self.selected_shape[0].setY(click_pos.y())
                    self.selected_shape[1].setX(click_pos.x())
                elif self.selected_vertex == 2:
                    self.selected_shape[1] = click_pos
                elif self.selected_vertex == 3:
                    self.selected_shape[0].setX(click_pos.x())
                    self.selected_shape[1].setY(click_pos.y())
                self.update()
            elif self.dragging_shape:
                click_pos = (event.pos() - self.image_offset) / self.scale_factor
                top_left = click_pos - self.offset
                bottom_right = top_left + (self.dragging_shape[1] - self.dragging_shape[0])
                self.dragging_shape[0] = top_left
                self.dragging_shape[1] = bottom_right
                self.update()
            else:
                self.hovered_vertex = None
                self.hovered_shape = None
                click_pos = (event.pos() - self.image_offset) / self.scale_factor
                for shape, _ in self.shapes:
                    vertices = [
                        shape[0],
                        QPointF(shape[1].x(), shape[0].y()),
                        shape[1],
                        QPointF(shape[0].x(), shape[1].y())
                    ]
                    for i, vertex in enumerate(vertices):
                        if self._is_within_vertex(click_pos, vertex):
                            self.hovered_vertex = i
                            self.hovered_shape = shape
                            self.update()
                            break
                    if self.hovered_vertex is not None:
                        break

                if self.hovered_shape is None:
                    for shape, _ in self.shapes:
                        if QRectF(shape[0], shape[1]).contains(click_pos):
                            self.hovered_shape = shape
                            break

                self.update()
        except Exception as e:
            print(f"Error in mouseMoveEvent: {e}")

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                if self.drawing and self.current_shape:
                    self.current_shape[1] = (event.pos() - self.image_offset) / self.scale_factor
                    dialog = LabelDialog(self.labels, self)
                    if dialog.exec_():
                        label_name = dialog.get_label()
                        self.shapes.append((self.current_shape, label_name))
                    self.current_shape = None
                    self.drawing = False
                elif self.selected_vertex is not None:
                    self.selected_vertex = None
                elif self.dragging_shape:
                    self.dragging_shape = None

                self.update()
        except Exception as e:
            print(f"Error in mouseReleaseEvent: {e}")

    def mouseDoubleClickEvent(self, event):
        try:
            if self.selected_shape:
                dialog = LabelDialog(self.labels, self)
                if dialog.exec_():
                    label_name = dialog.get_label()
                    for i, (shape, _) in enumerate(self.shapes):
                        if shape == self.selected_shape:
                            self.shapes[i] = (shape, label_name)
                            break
                self.update()
        except Exception as e:
            print(f"Error in mouseDoubleClickEvent: {e}")

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_Delete and self.selected_shape:
                self.shapes = [s for s in self.shapes if s[0] != self.selected_shape]
                self.selected_shape = None
                self.update()
            elif event.key() == Qt.Key_Return and self.pixmap:  # Enter 키로 캡처 기능 대체
                self.parent().parent().capture_still()  # 캡처 기능 호출
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")

    def wheelEvent(self, event):
        try:
            if event.modifiers() == Qt.ControlModifier:
                delta = event.angleDelta().y() / 120
                self.scale_factor += delta * 0.1
                self.scale_factor = max(0.1, min(self.scale_factor, 5.0))
                self.update_image_offset()
                self.update()
        except Exception as e:
            print(f"Error in wheelEvent: {e}")

    def _is_within_vertex(self, pos, vertex):
        return (pos - vertex).manhattanLength() < self.vertex_radius * 2

    def get_shapes(self):
        return self.shapes

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.labels = self.load_labels("classes.txt")
        self.yolo_model = None
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

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

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
        self.model_label.setFixedHeight(30)  # 크기 고정
        sidebar_layout.addWidget(self.model_label)

        self.save_button = QPushButton("Save Dataset", self)  # 버튼 이름 변경
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

        sidebar_layout.addStretch()  # 사이드바 아래 부분에 공간 추가

        sidebar_widget = QFrame()  # QFrame으로 변경
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        sidebar_widget.setLineWidth(2)

        self.canvas = Canvas(self.labels, self)
        self.canvas.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.canvas.setLineWidth(2)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(1, 2)  # 캔버스가 더 많은 공간을 차지하도록 설정

        main_layout.addWidget(splitter)

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
                    self.current_frame = frame
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(image)
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
                image = QImage(captured_frame_rgb, captured_frame_rgb.shape[1], captured_frame_rgb.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                self.canvas.load_pixmap(pixmap)

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
            captured_frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(img_save_path, captured_frame_rgb)

            # 라벨 저장
            img_size = (self.canvas.pixmap.height(), self.canvas.pixmap.width())
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
