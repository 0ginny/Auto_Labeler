from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QFrame
from labelbox import LabelDialog


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
        self.image_offset = QPointF(0, 0)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.hovered_vertex = None
        self.vertex_radius = 5
        self.labeling_done = False  # 라벨링 완료 여부 변수 추가

    def load_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.update_image_offset()
        self.update()

    def update_image_offset(self):
        """이미지의 오프셋을 계산하여 중앙에 맞게 설정"""
        if self.pixmap:
            scaled_pixmap_size = self.pixmap.size() * self.scale_factor
            self.image_offset = QPointF(
                (self.width() - scaled_pixmap_size.width()) / 2,
                (self.height() - scaled_pixmap_size.height()) / 2
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.pixmap:
            # 스케일링된 픽스맵을 화면에 그리기
            scaled_pixmap = self.pixmap.scaled(
                self.pixmap.size() * self.scale_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(self.image_offset, scaled_pixmap)

            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # 기존의 라벨링된 사각형을 그리기
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

            # 현재 그리는 중인 사각형을 그리기
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

                # 기존 사각형의 꼭지점 또는 내부를 클릭했는지 확인
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

                # 새로운 사각형 그리기 시작
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
                        if label_name:  # 라벨이 선택된 경우에만 저장
                            self.shapes.append((self.current_shape, label_name))
                            self.labeling_done = True  # 라벨링 완료로 설정
                        else:
                            self.labeling_done = False  # 라벨이 없으면 False로 설정
                    self.current_shape = None
                    self.drawing = False
                    if not self.labeling_done:  # 라벨이 선택되지 않으면 비디오 피드로 복귀
                        self.parent().parent().reset_to_video_feed()
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
                old_scale_factor = self.scale_factor
                delta = event.angleDelta().y() / 120
                self.scale_factor += delta * 0.1
                self.scale_factor = max(0.1, min(self.scale_factor, 5.0))

                # 마우스 위치를 캔버스 내의 이미지 좌표로 변환
                mouse_pos = event.pos()
                old_image_pos = (mouse_pos - self.image_offset) / old_scale_factor

                # 새로운 스케일에 맞게 이미지 오프셋 재계산
                self.update_image_offset()

                # 마우스를 기준으로 이미지의 새로운 오프셋 설정
                new_image_pos = old_image_pos * self.scale_factor
                self.image_offset = mouse_pos - new_image_pos

                self.update()
        except Exception as e:
            print(f"Error in wheelEvent: {e}")

    def _is_within_vertex(self, pos, vertex):
        return (pos - vertex).manhattanLength() < self.vertex_radius * 2

    def get_shapes(self):
        return self.shapes
