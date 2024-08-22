from PyQt5.QtWidgets import QVBoxLayout, QDialog, QListWidget, QPushButton, QLineEdit, QHBoxLayout, QMessageBox
import os

class LabelDialog(QDialog):
    def __init__(self, labels, parent=None):
        super(LabelDialog, self).__init__(parent)
        self.setWindowTitle("Manage Labels")

        self.labels = labels
        self.selected_label = None
        self.delete_mode = False  # 삭제 모드 플래그

        self.layout = QVBoxLayout(self)

        # 라벨 리스트
        self.list_widget = QListWidget(self)
        self.list_widget.addItems(self.labels)
        self.layout.addWidget(self.list_widget)

        self.list_widget.itemClicked.connect(self.item_clicked)

        # 라벨 추가/삭제 UI
        label_input_layout = QHBoxLayout()
        self.label_input = QLineEdit(self)
        self.label_input.setPlaceholderText("Enter new label")
        self.add_label_button = QPushButton("Add Label", self)
        self.delete_label_button = QPushButton("Delete Label", self)

        label_input_layout.addWidget(self.label_input)
        label_input_layout.addWidget(self.add_label_button)
        label_input_layout.addWidget(self.delete_label_button)

        self.layout.addLayout(label_input_layout)

        # 버튼 클릭 이벤트 연결
        self.add_label_button.clicked.connect(self.add_label)
        self.delete_label_button.clicked.connect(self.toggle_delete_mode)

    def item_clicked(self, item):
        if self.delete_mode:
            self.delete_label(item)
        else:
            self.selected_label = item.text()
            self.accept()  # OK 버튼 없이 다이얼로그 닫기

    def get_label(self):
        return self.selected_label

    def add_label(self):
        new_label = self.label_input.text().strip()
        if new_label and new_label not in self.labels:
            self.labels.append(new_label)
            self.list_widget.addItem(new_label)
            self.label_input.clear()
            self.update_classes_file()
        elif new_label in self.labels:
            QMessageBox.warning(self, "Duplicate Label", "This label already exists.")
        else:
            QMessageBox.warning(self, "Invalid Label", "Label cannot be empty.")

    def toggle_delete_mode(self):
        if self.delete_mode:
            self.delete_mode = False
            self.delete_label_button.setText("Delete Label")
        else:
            self.delete_mode = True
            self.delete_label_button.setText("Cancel")
            QMessageBox.information(self, "Delete Mode", "Click on a label to delete it.")

    def delete_label(self, item):
        label = item.text()
        self.labels.remove(label)
        self.list_widget.takeItem(self.list_widget.row(item))
        self.update_classes_file()
        self.toggle_delete_mode()  # 삭제 후 삭제 모드 비활성화

    def update_classes_file(self):
        try:
            with open("classes.txt", "w") as f:
                for label in self.labels:
                    f.write(f"{label}\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update classes.txt: {e}")
