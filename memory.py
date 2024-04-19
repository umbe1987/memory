import os, sys, glob, math, random
from PyQt5.QtWidgets import (QMainWindow, QWidget,
                             QGridLayout, QPushButton, QApplication,
                             QAction, QFileDialog, QMessageBox)
from PyQt5.QtGui import QPixmap, QIcon, QCloseEvent
from PyQt5.QtMultimedia import QSound
from PyQt5 import QtCore

APP_DIR = os.path.dirname(__file__)
DATA_DIR = 'data'
BACK_CARD_IMG = 'back'
SOUND_FOLDER = 'sound'
SOUND_SUCCESS = 'success.wav'
SOUND_FAIL = 'fail.wav'
SOUND_END = 'end.wav'
IMAGE_FOLDER = 'img'

class MemoryGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.back_card = os.path.join(APP_DIR, DATA_DIR, BACK_CARD_IMG)  # remove the extension from the image name if present
        self.status = {}
        self.cell_width = 100
        self.cell_height = 150
        self.initUI()

    def initUI(self):
        self.statusBar()

        self.sounds = {
            'success': QSound(os.path.join(APP_DIR, DATA_DIR, SOUND_FOLDER, SOUND_SUCCESS)),
            'fail': QSound(os.path.join(APP_DIR, DATA_DIR, SOUND_FOLDER, SOUND_FAIL)),
            'end': QSound(os.path.join(APP_DIR, DATA_DIR, SOUND_FOLDER, SOUND_END))
        }

        openFile = QAction('Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Search image folder')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        self.fileMenu.addAction(openFile)

        self.gridWidget = QWidget(self)
        self.gridLayout = QGridLayout(self.gridWidget)
        self.setCentralWidget(self.gridWidget)

        self.setGeometry(0, 0, 350, 300)
        self.setWindowTitle('Memory Game!')
        self.show()
        # self.showFullScreen()

    def showDialog(self):
        """Search for a folder of images, and create two dictionaries:
        - one with grid_position : image
        - one with grid_position : back_card"""

        if self.status:
            self.status = {}

        folder = str(QFileDialog.getExistingDirectory(self,
                                                      "Select Directory",
                                                      os.path.join(APP_DIR, DATA_DIR, IMAGE_FOLDER),
                                                      QFileDialog.ShowDirsOnly))

        # if the user selected a folder
        if folder:
            self.list_images(folder)

            # if the selected foldser contains images, limit the number to 16
            if self.n_img > 0:
                if self.n_img > 16:
                    del self.images[16:]
                self.fill_dict(self.images)  # create the grid_position:image Dict
                self.empty_dict()
                self.init_grid()

    def list_images(self, folder):
        """List the (JPEG) images within the selected folder"""
        extensions = ('.jpg', '.jpeg', '.gif', '.png')
        images = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(extensions)]
        n_img = len(images)

        self.images = images
        self.n_img = n_img

    def fill_dict(self, images):
        grid_cell = images * 2
        random.shuffle(grid_cell)
        self.card_dict = {}
        n_cols = math.ceil(math.sqrt(len(grid_cell)))
        n_rows = math.ceil(math.sqrt(len(grid_cell)))
        max_rows = 4
        if n_rows > max_rows:
            n_cols += n_rows - max_rows
            n_rows = max_rows

        positions = [(i, j) for i in range(n_rows) for j in range(n_cols)]
        for p, cell in zip(positions, grid_cell):
            if cell == '':
                continue
            self.card_dict[p] = cell

    def empty_dict(self):
        # copy the card_dict to make a back_dict (with the back_card)
        self.back_dict = dict(self.card_dict)
        for k in self.back_dict:
            self.back_dict[k] = self.back_card

    def init_grid(self):
        """Initialize the grid according to the number of images
        found in the selected folder."""

        for pos, img in self.back_dict.items():
            btn = QPushButton(self)
            btn.clicked.connect(self.buttonClicked)
            pixmap = QPixmap(self.back_dict[pos])
            scaled = pixmap.scaled(self.cell_width, self.cell_height)
            btn.setIcon(QIcon(scaled))
            btn.setIconSize(scaled.rect().size())
            btn.setFixedSize(scaled.rect().size())
            del (pixmap)

            self.gridLayout.addWidget(btn, *pos)

    def restart(self):
        self.status = {}
        self.init_grid()

        return

    def turn_card(self, btn, location):
        """When a button (image) is clicked, turn the card."""

        pixmap = QPixmap(self.card_dict[location])
        scaled = pixmap.scaled(self.cell_width, self.cell_height)
        btn.setIcon(QIcon(scaled))
        btn.setIconSize(scaled.rect().size())
        btn.setFixedSize(scaled.rect().size())
        del (pixmap)

        n_cards = len(self.status.keys())

        # if game just started, turn the card
        if n_cards == 0:
            self.status[location] = self.card_dict[location]

            return

        # if the number of card is odd
        elif n_cards % 2 != 0:
            # if card already present, keep it...
            if self.card_dict[location] in self.status.values() and location not in self.status.keys():
                self.status[location] = self.card_dict[location]
                if self.status == self.card_dict:
                    self.end_game()
                    return
                self.sounds['success'].play()
                return

            # if the same card is clicked, do nothing...
            elif location in self.status.keys():
                pass
            # ...otherwise restart the grid
            else:
                ''' wait 1 sec and restart (second argument MUST be a method;
                cannot use time.sleep, because GUI freezes)'''
                QtCore.QTimer.singleShot(1000, self.restart)
                self.sounds['fail'].play()
                return

        self.status[location] = self.card_dict[location]

    def buttonClicked(self):
        button = self.sender()
        idx = self.gridLayout.indexOf(button)
        location = self.gridLayout.getItemPosition(idx)
        self.turn_card(button, location[:2])

    def end_game(self):
        self.sounds['end'].play()

        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("!!!You won!!!")
        msgBox.setInformativeText("What's next now?")
        quit = msgBox.addButton('quit', QMessageBox.RejectRole)
        restartBtn = msgBox.addButton('play again', QMessageBox.ActionRole)
        changeBtn = msgBox.addButton('change cards', QMessageBox.ActionRole)
        msgBox.setDefaultButton(restartBtn)

        msgBox.exec_()
        msgBox.deleteLater()

        if msgBox.clickedButton() == quit:
            self.close()
        elif msgBox.clickedButton() == restartBtn:
            self.restart()
        elif msgBox.clickedButton() == changeBtn:
            self.showDialog()

        return

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MemoryGame()
    sys.exit(app.exec_())
