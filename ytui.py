import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QCheckBox, 
                            QTextEdit, QPushButton)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application Interface")
        self.setGeometry(100, 100, 600, 400)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Channel URL section
        self.channel_url_layout = QHBoxLayout()
        channel_label = QLabel("Channel URL:")
        channel_label.setMinimumWidth(120)
        channel_label.setFixedHeight(30)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/@channelname")
        self.url_input.setFixedHeight(30)
        self.channel_url_layout.addWidget(channel_label)
        self.channel_url_layout.addWidget(self.url_input)
        self.main_layout.addLayout(self.channel_url_layout)
        
        # Checkbox section
        self.checkbox_layout = QHBoxLayout()
        self.checkbox = QCheckBox("Enable advanced options")
        self.checkbox.setFixedHeight(30)
        self.checkbox_layout.addWidget(self.checkbox)
        self.checkbox_layout.addStretch()
        self.main_layout.addLayout(self.checkbox_layout)
        
        # Text area section
        self.textarea_layout = QVBoxLayout()
        textarea_label = QLabel("Comments:")
        self.textarea = QTextEdit()
        self.textarea.setPlaceholderText("Enter your comments here...")
        self.textarea.setMinimumHeight(150)
        self.textarea_layout.addWidget(textarea_label)
        self.textarea_layout.addWidget(self.textarea)
        self.main_layout.addLayout(self.textarea_layout)
        
        # Button section
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedSize(100, 30)
        self.submit_button.clicked.connect(self.on_submit)
        self.button_layout.addWidget(self.submit_button)
        self.main_layout.addLayout(self.button_layout)
        
        # Add some spacing
        self.main_layout.addStretch()
    
    def on_submit(self):
        # Handle the submit action
        url = self.url_input.text()
        is_advanced = self.checkbox.isChecked()
        comments = self.textarea.toPlainText()
        
        print(f"URL: {url}")
        print(f"Advanced Options: {'Enabled' if is_advanced else 'Disabled'}")
        print(f"Comments: {comments}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())