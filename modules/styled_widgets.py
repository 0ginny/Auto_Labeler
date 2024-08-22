from PyQt5.QtWidgets import QPushButton, QLabel, QComboBox, QLineEdit, QDockWidget
from PyQt5.QtGui import QColor

# 전역 변수 설정 (임의로 작성)
GLOBAL_FONT_SIZE = 14  # 기본 폰트 사이즈
GLOBAL_FONT_FAMILY = "Georgia"  # 기본 폰트 패밀리
GLOBAL_HEIGHT = 30  # 기본 위젯 높이
GLOBAL_FONT_COLOR = "#00000"  # 기본 폰트 색상
GLOBAL_BACKGROUND_COLOR_BUTTON = "#c5c5c5"  # 버튼 기본 배경 색상
GLOBAL_BACKGROUND_COLOR_COMBOBOX = "#F4F3F8"  # 콤보박스 기본 배경 색상
GLOBAL_BACKGROUND_COLOR_ENTITY = "#F4F3F8"  # 엔티티 기본 배경 색상
GLOBAL_BORDER_RADIUS = 3  # 기본 경계 라운드 값
GLOBAL_SIDEBAR_BACKGROUND_COLOR = "#faf8ff"  # 사이드바 배경색
GLOBAL_INPUT_BORDER_COLOR = "#000000"  # 엔티티 경계선 색상

# 전역 변수로 관리할 추가 스타일 속성
GLOBAL_BOLD = True  # 기본 볼드 여부
GLOBAL_PADDING = 0  # 기본 패딩 값
GLOBAL_MARGIN = 5  # 기본 마진 값

class StyledButton(QPushButton):
    def __init__(self,
                 text,
                 parent=None,
                 font_size=GLOBAL_FONT_SIZE,
                 font_family=GLOBAL_FONT_FAMILY,
                 height=GLOBAL_HEIGHT,
                 font_color=GLOBAL_FONT_COLOR,
                 background_color=GLOBAL_BACKGROUND_COLOR_BUTTON,
                 bold=GLOBAL_BOLD,
                 padding=GLOBAL_PADDING,
                 margin=GLOBAL_MARGIN):
        super().__init__(text, parent)
        self.default_color = background_color  # 기본 배경 색상
        self.font_size = font_size  # 폰트 사이즈
        self.font_family = font_family  # 폰트 패밀리
        self.height = height  # 높이
        self.font_color = font_color  # 폰트 색상
        self.bold = bold  # 볼드 여부
        self.padding = padding  # 패딩 설정
        self.margin = margin  # 마진 설정
        self.update_style()

    def update_style(self):
        # 스타일 적용
        font_weight = "bold" if self.bold else "normal"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.default_color};\n
                color: {self.font_color};\n
                font-size: {self.font_size}px;\n
                font-family: {self.font_family};\n
                font-weight: {font_weight};\n
                border-radius: {GLOBAL_BORDER_RADIUS}px;\n
                padding: {self.padding}px;\n
                margin: {self.margin}px;
                height: {self.height}px;
            }}
            QPushButton:hover {{
                cursor: pointer;\n
                background-color: {QColor(self.default_color).darker(120).name()};
            }}
        """)
        self.setMinimumHeight(self.height)


class StyledLabel(QLabel):
    def __init__(self,
                 text,
                 parent=None,
                 font_size=GLOBAL_FONT_SIZE,
                 font_family=GLOBAL_FONT_FAMILY,
                 font_color=GLOBAL_FONT_COLOR,
                 bold=GLOBAL_BOLD,
                 padding=GLOBAL_PADDING,
                 margin=GLOBAL_MARGIN):
        super().__init__(text, parent)
        self.font_size = font_size  # 폰트 사이즈
        self.font_family = font_family  # 폰트 패밀리
        self.font_color = font_color  # 폰트 색상
        self.bold = bold  # 볼드 여부
        self.padding = padding  # 패딩 설정
        self.margin = margin  # 마진 설정
        self.update_style()

    def update_style(self):
        # 스타일 적용
        font_weight = "bold" if self.bold else "normal"
        self.setStyleSheet(f"""
            QLabel {{
                color: {self.font_color};\n
                font-size: {self.font_size}px;\n
                font-family: {self.font_family};\n
                font-weight: {font_weight};\n
                padding: {self.padding}px;\n
                margin: {self.margin}px;
            }}
        """)


class StyledComboBox(QComboBox):
    def __init__(self,
                 parent=None,
                 font_size=GLOBAL_FONT_SIZE,
                 font_family=GLOBAL_FONT_FAMILY,
                 height=GLOBAL_HEIGHT,
                 font_color=GLOBAL_FONT_COLOR,
                 background_color=GLOBAL_BACKGROUND_COLOR_COMBOBOX,
                 bold=GLOBAL_BOLD,
                 padding=GLOBAL_PADDING,
                 margin=GLOBAL_MARGIN):
        super().__init__(parent)
        self.default_color = background_color  # 기본 배경 색상
        self.font_size = font_size  # 폰트 사이즈
        self.font_family = font_family  # 폰트 패밀리
        self.height = height  # 높이
        self.font_color = font_color  # 폰트 색상
        self.bold = bold  # 볼드 여부
        self.padding = padding  # 패딩 설정
        self.margin = margin  # 마진 설정
        self.update_style()

    def update_style(self):
        # 스타일 적용
        font_weight = "bold" if self.bold else "normal"
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.default_color};\n
                color: {self.font_color};\n
                font-size: {self.font_size}px;\n
                font-family: {self.font_family};\n
                font-weight: {font_weight};\n
                border-radius: {GLOBAL_BORDER_RADIUS}px;\n
                padding: {self.padding}px;\n
                margin: {self.margin}px;\n
                height: {self.height}px;
            }}
            QComboBox:hover {{
                cursor: pointer;\n
                background-color: {QColor(self.default_color).darker(120).name()};
            }}
        """)
        self.setMinimumHeight(self.height)


class StyledDockWidget(QDockWidget):
    def __init__(self,
                 title,
                 parent=None,
                 background_color=GLOBAL_SIDEBAR_BACKGROUND_COLOR,
                 border_radius=GLOBAL_BORDER_RADIUS,
                 padding=GLOBAL_PADDING,
                 margin=GLOBAL_MARGIN):
        super().__init__(title, parent)
        self.background_color = background_color
        self.border_radius = border_radius
        self.padding = padding
        self.margin = margin
        self.update_style()

    def update_style(self):
        # 스타일 적용
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {self.background_color};\n
                border-radius: {self.border_radius}px;\n
                padding: {self.padding}px;\n
                margin: {self.margin}px;
            }}
            QDockWidget::title {{
                background-color: {GLOBAL_BACKGROUND_COLOR_BUTTON};\n
                font-size: {GLOBAL_FONT_SIZE}px;\n
                font-family: {GLOBAL_FONT_FAMILY};\n
                color: {GLOBAL_FONT_COLOR};\n
                text-align: center;\n
                padding: 5px;
            }}
        """)


class StyledLineEdit(QLineEdit):
    def __init__(self,
                 parent=None,
                 font_size=GLOBAL_FONT_SIZE,
                 font_family=GLOBAL_FONT_FAMILY,
                 height=GLOBAL_HEIGHT,
                 font_color=GLOBAL_FONT_COLOR,
                 border_color=GLOBAL_INPUT_BORDER_COLOR,
                 bold=GLOBAL_BOLD,
                 padding=GLOBAL_PADDING,
                 margin=GLOBAL_MARGIN):
        super().__init__(parent)
        self.font_size = font_size
        self.font_family = font_family
        self.height = height
        self.font_color = font_color
        self.border_color = border_color
        self.bold = bold  # 볼드 여부
        self.padding = padding  # 패딩 설정
        self.margin = margin  # 마진 설정
        self.update_style()

    def update_style(self):
        # 스타일 적용
        font_weight = "bold" if self.bold else "normal"
        self.setStyleSheet(f"""
            QLineEdit {{
                color: {self.font_color};\n
                font-size: {self.font_size}px;\n
                font-family: {self.font_family};\n
                font-weight: {font_weight};\n
                border: 1px solid {self.border_color};\n
                border-radius: {GLOBAL_BORDER_RADIUS}px;\n
                padding: {self.padding}px;\n
                margin: {self.margin}px;\n
                height: {self.height}px;
            }}
        """)
        self.setMinimumHeight(self.height)
