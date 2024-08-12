import sys
import os
import cv2
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFontMetrics
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QDialog, QListWidget, QSpinBox, QAbstractSpinBox, QHBoxLayout, QLineEdit, QSplitter, QFrame

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
            elif event.key() == Qt.Key_Return and self.pixmap:
                self.parent().parent().save_and_switch_mode()  # 저장 및 모드 전환 기능 호출
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
        self.initUI()
        self.selected_camera = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None
        self.is_capturing = False
        self.save_folder = None
        self.save_counter = 1

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

        self.file_name_edit = QLineEdit(self)
        self.file_name_edit.setPlaceholderText("Enter base file name")
        sidebar_layout.addWidget(self.file_name_edit)

        self.zoom_widget = ZoomWidget(value=100)
        self.zoom_widget.valueChanged.connect(self.zoom_changed)
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_widget)
        sidebar_layout.addLayout(zoom_layout)

        sidebar_layout.addStretch()

        sidebar_widget = QFrame()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        sidebar_widget.setLineWidth(2)

        self.canvas = Canvas(self.labels, self)
        self.canvas.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.canvas.setLineWidth(2)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(1, 2)

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
            self.is_capturing = True
        else:
            print("Failed to open the selected camera.")

    def update_frame(self):
        try:
            if self.selected_camera is not None and self.selected_camera.isOpened() and self.is_capturing:
                ret, frame = self.selected_camera.read()
                if ret:
                    self.current_frame = frame
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(image)
                    self.canvas.load_pixmap(pixmap)
        except Exception as e:
            print(f"Error in update_frame: {e}")

    def save_and_switch_mode(self):
        if self.is_capturing:
            self.capture_still()
        else:
            self.save_yolo_format()

    def capture_still(self):
        try:
            if self.current_frame is not None:
                self.timer.stop()
                if self.selected_camera.isOpened():
                    self.selected_camera.release()

                captured_frame = self.current_frame.copy()
                captured_frame = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)
                image = QImage(captured_frame, captured_frame.shape[1], captured_frame.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)

                self.canvas.load_pixmap(pixmap)
                self.is_capturing = False  # 모드 전환
        except Exception as e:
            print(f"Error in capture_still: {e}")

    def save_yolo_format(self):
        try:
            if not hasattr(self, 'canvas') or not self.canvas.get_shapes():
                return

            if not self.save_folder:
                self.save_folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
                if not self.save_folder:
                    return

            images_folder = os.path.join(self.save_folder, 'images')
            labels_folder = os.path.join(self.save_folder, 'labels')

            os.makedirs(images_folder, exist_ok=True)
            os.makedirs(labels_folder, exist_ok=True)

            base_filename = self.file_name_edit.text()
            if not base_filename:
                base_filename = "image"

            image_filename, label_filename = self.generate_unique_filenames(base_filename, images_folder, labels_folder)

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

            image_path = os.path.join(images_folder, image_filename)
            label_path = os.path.join(labels_folder, label_filename)

            self.canvas.pixmap.save(image_path, "JPG")
            with open(label_path, 'w') as f:
                f.write("\n".join(yolo_data))

            self.is_capturing = True  # 웹캠 모드로 전환
            self.save_counter += 1  # 파일명 카운터 증가
            self.start_camera()  # 웹캠 다시 시작

        except Exception as e:
            print(f"Error in save_yolo_format: {e}")

    def generate_unique_filenames(self, base_filename, images_folder, labels_folder):
        image_filename = f"{base_filename}.jpg"
        label_filename = f"{base_filename}.txt"
        counter = 1

        while os.path.exists(os.path.join(images_folder, image_filename)) or os.path.exists(os.path.join(labels_folder, label_filename)):
            image_filename = f"{base_filename}_{counter}.jpg"
            label_filename = f"{base_filename}_{counter}.txt"
            counter += 1

        return image_filename, label_filename

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_Return:
                self.save_and_switch_mode()
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")

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
