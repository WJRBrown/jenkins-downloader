import os
import time
import sys
import requests
from jenkins import Jenkins_Scaper
from subprocess import call
from PyQt6.QtWidgets import QFileDialog, QApplication, QLineEdit, QLabel, QWidget, QPushButton, QComboBox, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QListWidget
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt

class ProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setMinimum(0)
        self.setValue(0)
        self.currentValue = 0
        self._active = False

    def updateBar(self, i):
        self.currentValue = i
        self.setValue(self.currentValue)
        app.processEvents()

class PopUpWindow(QWidget):
    def __init__(self, title, label):
        super().__init__()
        self.title = title
        self.label = label
        layout = QVBoxLayout()
        self.setWindowTitle(self.title)
        layout.addWidget(QLabel(self.label))
        self.setLayout(layout)
        self.move(634.75, 350.5)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.scraper = None
        self.download_path = None

        self.setWindowTitle("Jenkins Downloader")
        self.url_title = QLabel("Jenkins URL:")
        self.url = QLineEdit()
        self.url.setPlaceholderText(" Enter Jenkins URL ") # /job/project
        self.connect = QPushButton("Connect")
        self.branch_title = QLabel("Branch:")
        self.branch = QComboBox()
        self.build_title = QLabel("Build:")
        self.build = QComboBox()
        self.file_title = QLabel("Artifact:")
        self.file = QComboBox()
        self.changes = QPushButton("Open Changelist")
        self.download = QPushButton("Download")
        self.open = QPushButton("Open Build")
        self.progressBar = ProgressBar()
        self.message = QListWidget()

        self.mainLayout = QVBoxLayout()
        self.layout = QGridLayout()
        self.layout2 = QHBoxLayout()
        self.layout.addWidget(self.connect, 0, 0)
        self.layout.addWidget(self.branch_title, 1, 0)
        self.layout.addWidget(self.build_title, 2, 0)
        self.layout.addWidget(self.file_title, 3, 0)
        self.layout.addWidget(self.url, 0, 1)
        self.layout.addWidget(self.branch, 1, 1)
        self.layout.addWidget(self.build, 2, 1)
        self.layout.addWidget(self.file, 3, 1)
        self.layout2.addWidget(self.download)
        self.layout2.addWidget(self.open)
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addWidget(self.changes)
        self.mainLayout.addLayout(self.layout2)
        self.mainLayout.addWidget(self.progressBar)
        self.mainLayout.addWidget(self.message)
        widget = QWidget()
        widget.setLayout(self.mainLayout)
        self.setCentralWidget(widget)

        self.progressBar.hide()
        self.message.hide()

        self.connect.clicked.connect(self.initJenkins)
        self.changes.clicked.connect(self.updateMessage)
        self.download.clicked.connect(self.downloadBuild)
        self.download.clicked.connect(lambda status, n=10: self.progressBar.updateBar(n))
        self.open.clicked.connect(self.openFinder)

        self.setFixedSize(self.mainLayout.sizeHint())

    def initJenkins(self):
        try:
            url = self.url.text()
            self.branch.clear()
            self.scraper = Jenkins_Scaper(url)
            branches = self.scraper.get_branch_list()

            self.build.currentIndexChanged.connect(self.updateFiles)
            self.branch.currentIndexChanged.connect(self.updateBuilds)
            self.branch.addItems(branches)
            try:
                self.branch.setCurrentText('main')
            except:
                pass
        except:
            self.popUpWindow("Connection Error", "Make sure the URL is correct and you are connected to the VPN")
    
    def popUpWindow(self, title, message):
        self.w = PopUpWindow(title, message)
        self.w.show()

    def updateBuilds(self):
        self.build.clear()
        encoded = self.branch.currentText().replace('/', '%252F')
        path = os.path.join(os.path.join(self.url.text(), 'job'), encoded)
        builds = self.scraper.get_build_list(path)
        if builds:
            self.build.addItems(builds)
    
    def updateFiles(self):
        self.file.clear()
        encoded = self.branch.currentText().replace('/', '%252F')
        path = os.path.join(os.path.join(os.path.join(self.url.text(), 'job'), encoded), self.build.currentText())
        files = self.scraper.get_file_list(path)
        if files:
            self.file.addItems(files)
    
    def updateMessage(self):
        if self.message.isVisible():
            self.message.clear()
            self.message.hide()
            self.changes.setText("Open Changelist")
            self.setFixedSize(self.mainLayout.sizeHint())
        else:
            self.changes.setText("Close Changelist")
            self.message.show()
            self.message.clear()
            try:
                path = "%sjob/%s/%s/changes" % (self.url.text(), self.branch.currentText(), self.build.currentText())
                cl = self.scraper.get_change_list(path)
                for id, change in enumerate(cl):
                    self.message.addItem("%s: %s" % (id+1, change))
                self.setFixedSize(self.mainLayout.sizeHint())
            except:
                self.message.addItem("No changes found")
                self.setFixedSize(self.mainLayout.sizeHint())

    def openFinder(self):
        if os.path.exists(self.download_path):
            call(["open", self.download_path])
        else:
            self.popUpWindow("Open Error", "Cannot find build")
    
    def downloadBuild(self):
        chunkSize = 1024

        response = str(QFileDialog.getExistingDirectory(
            parent = self, 
            caption = "Select Directory")
        )
        self.download_path = str(response)
        try:
            dir = os.path.join(self.download_path, self.file.currentText())
            print("======")
            print(self.download_path)
            print(self.file.currentText())
            print(dir)
            print("======")
            branch = self.branch.currentText().replace('/', '%252F')
            build = self.build.currentText()
            file = self.file.currentText()
            url = os.path.join(os.path.join(os.path.join(self.url.text(),'job'), branch), build)

            if os.path.exists(os.path.join(dir, file)):
                self.popUpWindow("File Exists", "File already downloaded")
                return
            
            artifact = self.scraper.file_dict[self.file.currentText()]
            with requests.get(artifact, stream=True) as r:
                print("Downloading %s" % artifact)
                try:
                    fileSize = int(r.headers["Content-Length"])
                    self.progressBar.show()
                    self.setFixedSize(self.mainLayout.sizeHint())
                    num_bars = (fileSize / chunkSize)
                    time.sleep(3)
                    self.progressBar.setMaximum(num_bars)

                    with open(dir, "wb") as f:
                        for i, chunk in enumerate(r.iter_content(chunk_size=chunkSize)):
                                self.progressBar.updateBar(i)
                                f.write(chunk)
                                if i >= int(num_bars):
                                    self.progressBar.hide()
                                    self.setFixedSize(self.mainLayout.sizeHint())
                except KeyError:
                    self.popUpWindow("Build Error", "Error downloading build")
                    print('Error')

                return   
        except:
            return
            

app = QApplication([])
app.setStyle("Fusion")

window = MainWindow()
window.show()

sys.exit(app.exec())
