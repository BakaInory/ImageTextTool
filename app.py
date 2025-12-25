import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLabel, QFileDialog, QPushButton,
                           QGridLayout, QScrollArea, QProgressBar, QLineEdit)
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPixmap, QWheelEvent
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

class ImageTextViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.files_list = []
        self.current_page = 0
        self.items_per_page = 4
        self.zoom_factor = 1.0
        self.text_cache = {}
        
        # 添加自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.initUI()
        self.installEventFilter(self)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder_path:
            # 获取所有文本文件
            files = os.listdir(folder_path)
            text_files = sorted([f for f in files if f.endswith('.txt')])  # 添加排序
            self.files_list = []
            self.text_cache.clear()  # 清空缓存
            
            # 匹配文本文件和图片文件
            for text_file in text_files:
                base_name = text_file.rsplit('.', 1)[0]
                text_path = os.path.join(folder_path, text_file)
                image_path = None
                
                # 查找对应的图片文件
                for ext in ['.png', '.jpg', '.jpeg']:
                    temp_path = os.path.join(folder_path, base_name + ext)
                    if os.path.exists(temp_path):
                        image_path = temp_path
                        break
                
                if image_path:
                    # 预先读取文本内容到缓存
                    try:
                        with open(text_path, 'r', encoding='utf-8') as f:
                            self.text_cache[text_path] = f.read()
                    except Exception as e:
                        print(f"读取文件时出错: {str(e)}")
                        self.text_cache[text_path] = ""
                        
                    self.files_list.append((text_path, image_path))
            
            # 重置页面和更新UI
            self.current_page = 0
            self.update_page()
            
            # 在这里启动自动保存定时器
            self.auto_save_timer.start(600000)  # 10分钟
            
            # 更新按钮状态
            self.save_button.setEnabled(True)
            self.update_navigation_buttons()

    def save_all_texts(self):
        try:
            # 先保存当前页面的修改到缓存
            for i in range(self.items_per_page):
                if self.file_paths[i]:
                    current_text = self.text_edits[i].toPlainText()
                    self.text_cache[self.file_paths[i]] = current_text
            
            # 保存所有文件
            for text_path, _ in self.files_list:
                if text_path in self.text_cache:
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(self.text_cache[text_path])
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")

    def append_to_all_files(self):
        append_text = self.append_input.text()
        if not append_text:
            return
        
        # 先保存当前页面的修改到缓存
        for i in range(self.items_per_page):
            if self.file_paths[i]:
                current_text = self.text_edits[i].toPlainText()
                self.text_cache[self.file_paths[i]] = current_text
        
        # 处理所有文件
        for text_path, _ in self.files_list:
            if text_path in self.text_cache:
                current_text = self.text_cache[text_path]
                new_text = current_text + '\n' + append_text
                self.text_cache[text_path] = new_text
                
                # 如果是当前页面的文件，更新显示
                for i, file_path in enumerate(self.file_paths):
                    if file_path == text_path:
                        self.text_edits[i].setText(new_text)
        
        # 立即保存所有更改到文件
        self.save_all_texts()

    def auto_save(self):
        try:
            self.save_all_texts()
        except Exception as e:
            print(f"自动保存时出错: {str(e)}")

    def search_text(self):
        search_text = self.search_input.text()
        if not search_text:
            return
        
        for text_edit in self.text_edits:
            cursor = text_edit.textCursor()
            format = QTextCharFormat()
            format.setBackground(QColor("yellow"))
            
            # 重置光标位置
            cursor.setPosition(0)
            text_edit.setTextCursor(cursor)
            
            while text_edit.find(search_text):
                cursor = text_edit.textCursor()
                cursor.mergeCharFormat(format)

    def delete_searched_text(self):
        search_text = self.search_input.text()
        if not search_text:
            return
            
        # 保存当前页面的修改到缓存
        for i in range(self.items_per_page):
            if self.file_paths[i]:
                current_text = self.text_edits[i].toPlainText()
                self.text_cache[self.file_paths[i]] = current_text
        
        # 处理所有文件
        for text_path, _ in self.files_list:
            if text_path in self.text_cache:
                text = self.text_cache[text_path]
                new_text = text.replace(search_text, '')
                self.text_cache[text_path] = new_text
                
                # 如果是当前页面的文件，更新显示
                for i, file_path in enumerate(self.file_paths):
                    if file_path == text_path:
                        self.text_edits[i].setText(new_text)

    def initUI(self):
        self.setWindowTitle('图片文本对照查看器')
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建按钮区域
        # 修改按钮区域
        button_layout = QHBoxLayout()
        self.open_button = QPushButton('打开文件夹')
        self.first_button = QPushButton('第一页')
        self.prev_button = QPushButton('上一页')
        self.next_button = QPushButton('下一页')
        self.last_button = QPushButton('最后一页')
        self.save_button = QPushButton('保存所有文本')
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.first_button)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.last_button)
        button_layout.addWidget(self.save_button)
        
        # 连接所有按钮信号
        self.open_button.clicked.connect(self.open_folder)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.save_button.clicked.connect(self.save_all_texts)
        self.first_button.clicked.connect(self.first_page)
        self.last_button.clicked.connect(self.last_page)
        
        # 初始化禁用所有按钮
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.first_button.setEnabled(False)
        self.last_button.setEnabled(False)
        
        # 添加进度条到布局
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        
        # 将进度条添加到主布局
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        
        # 创建图文对的容器
        self.image_labels = []
        self.text_edits = []
        self.file_paths = []
        
        # 初始化4对图文组件
        for i in range(self.items_per_page):
            # 创建图片标签
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setMinimumSize(300, 300)
            
            # 创建文本编辑框
            text_edit = QTextEdit()
            text_edit.setMinimumSize(300, 300)
            
            # 将组件添加到网格布局
            self.grid_layout.addWidget(image_label, i, 0)
            self.grid_layout.addWidget(text_edit, i, 1)
            
            self.image_labels.append(image_label)
            self.text_edits.append(text_edit)
            self.file_paths.append(None)
        
        scroll_area.setWidget(scroll_content)
        
        # 添加所有组件到主布局
        # 添加搜索和批量操作区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入搜索内容')
        self.search_button = QPushButton('搜索')
        self.delete_text_button = QPushButton('删除搜索内容')
        self.append_input = QLineEdit()
        self.append_input.setPlaceholderText('输入要添加的文本')
        self.append_button = QPushButton('添加到所有文件末尾')
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.delete_text_button)
        search_layout.addWidget(self.append_input)
        search_layout.addWidget(self.append_button)
        
        # 连接新按钮信号
        self.search_button.clicked.connect(self.search_text)
        self.delete_text_button.clicked.connect(self.delete_searched_text)
        self.append_button.clicked.connect(self.append_to_all_files)
        
        # 将搜索布局添加到主布局
        main_layout.addLayout(search_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(scroll_area)

    # 添加新的页面导航方法
    def first_page(self):
        if self.current_page != 0:
            self.current_page = 0
            self.update_page()
            self.update_navigation_buttons()
    
    def last_page(self):
        max_pages = (len(self.files_list) - 1) // self.items_per_page + 1
        if self.current_page != max_pages - 1:
            self.current_page = max_pages - 1
            self.update_page()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        # 更新现有方法
        self.first_button.setEnabled(self.current_page > 0)
        self.prev_button.setEnabled(self.current_page > 0)
        max_pages = (len(self.files_list) - 1) // self.items_per_page + 1
        self.next_button.setEnabled(self.current_page < max_pages - 1)
        self.last_button.setEnabled(self.current_page < max_pages - 1)
        
        # 更新进度条
        if len(self.files_list) > 0:
            progress = (self.current_page * self.items_per_page + self.items_per_page) / len(self.files_list) * 100
            progress = min(100, progress)  # 确保不超过100%
            self.progress_bar.setValue(int(progress))
        else:
            self.progress_bar.setValue(0)
        
    def update_page(self):
        try:
            start_idx = self.current_page * self.items_per_page
            
            # 清空所有显示前先保存当前页面内容
            for i in range(self.items_per_page):
                if self.file_paths[i]:
                    current_text = self.text_edits[i].toPlainText()
                    self.text_cache[self.file_paths[i]] = current_text
            
            # 断开信号连接并清空显示
            for i in range(self.items_per_page):
                try:
                    self.text_edits[i].textChanged.disconnect()
                except:
                    pass
                self.image_labels[i].clear()
                self.text_edits[i].clear()
                self.file_paths[i] = None
            
            # 显示新页面内容
            for i in range(self.items_per_page):
                idx = start_idx + i
                if idx < len(self.files_list):
                    text_path, image_path = self.files_list[idx]
                    self.file_paths[i] = text_path
                    
                    # 从缓存读取文本
                    if text_path in self.text_cache:
                        text_content = self.text_cache[text_path]
                    else:
                        try:
                            with open(text_path, 'r', encoding='utf-8') as f:
                                text_content = f.read()
                                self.text_cache[text_path] = text_content
                        except Exception as e:
                            print(f"读取文件时出错: {str(e)}")
                            text_content = ""
                    
                    self.text_edits[i].setText(text_content)
                    
                    # 加载图片
                    try:
                        pixmap = QPixmap(image_path)
                        scaled_pixmap = pixmap.scaled(300, 300, 
                                                    Qt.KeepAspectRatio, 
                                                    Qt.SmoothTransformation)
                        self.image_labels[i].setPixmap(scaled_pixmap)
                    except Exception as e:
                        print(f"加载图片时出错: {str(e)}")
                    
                    # 使用正确的方式连接信号
                    def make_signal_handler(index):
                        def handler():
                            self.on_text_changed(index)
                        return handler
                    self.text_edits[i].textChanged.connect(make_signal_handler(i))
                    
        except Exception as e:
            print(f"更新页面时出错: {str(e)}")

    def prev_page(self):
        if self.current_page > 0:
            # 移除 save_all_texts 调用，改为直接更新缓存
            for i in range(self.items_per_page):
                if self.file_paths[i]:
                    current_text = self.text_edits[i].toPlainText()
                    self.text_cache[self.file_paths[i]] = current_text
            
            self.current_page -= 1
            self.update_page()
            self.update_navigation_buttons()

    def next_page(self):
        max_pages = (len(self.files_list) - 1) // self.items_per_page + 1
        if self.current_page < max_pages - 1:
            # 移除 save_all_texts 调用，改为直接更新缓存
            for i in range(self.items_per_page):
                if self.file_paths[i]:
                    current_text = self.text_edits[i].toPlainText()
                    self.text_cache[self.file_paths[i]] = current_text
            
            self.current_page += 1
            self.update_page()
            self.update_navigation_buttons()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '保存确认',
                                   '是否保存所有更改？',
                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                   QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_all_texts()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

    def on_text_changed(self, index):
        if self.file_paths[index]:
            self.text_cache[self.file_paths[index]] = self.text_edits[index].toPlainText()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        viewer = ImageTextViewer()
        viewer.show()  # 这行代码会立即显示窗口
        sys.exit(app.exec_())
    except Exception as e:
        print(f"程序运行出错: {str(e)}")