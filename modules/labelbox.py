from PyQt5.QtWidgets import  QVBoxLayout, QDialog, QListWidget

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