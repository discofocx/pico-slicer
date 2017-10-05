# -*- coding: utf-8 -*-

# Info
__author__ = 'Disco Hammer'
__copyright__ = 'Copyright 2017,  Dragon Unit Framestore LDN 2017'
__version__ = '0.1'
__email__ = 'gsorchin@framestore.com'
__status__ = 'Prototype'

import os
import sys

import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
import PyQt5.QtWidgets as qw

from PicoSlicer import CyPico

# - Globals - #
gDIALOG = None
gROOT = os.getcwd()


class PicoSlicer(qw.QDialog):
    def __init__(self):
        super(PicoSlicer, self).__init__()
        self.setWindowTitle('Pico Slicer 0.1')
        self.setMinimumWidth(512)
        self.setMinimumHeight(168)

        # -- Attributes -- #
        self.pico_files = list()

        self.draw()

    def __call__(self, *args, **kwargs):
        self.show()

    def draw(self):

        # - Main Window Layout - #
        self.setLayout(qw.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        scroll_area = qw.QScrollArea()
        scroll_area.setFrameStyle(qw.QFrame.Plain | qw.QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(qc.Qt.NoFocus)
        scroll_area.setHorizontalScrollBarPolicy(qc.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(scroll_area)

        main_widget = qw.QWidget()
        main_layout = qw.QVBoxLayout()
        main_layout.setContentsMargins(2, 5, 2, 5)
        main_layout.setAlignment(qc.Qt.AlignTop)
        main_widget.setLayout(main_layout)
        scroll_area.setWidget(main_widget)

        new_widget = PicoTrack()
        main_layout.addWidget(new_widget)

        # ------ Footer ------ #
        footer_widget = Footer()
        self.layout().addWidget(footer_widget)


class PicoTrack(qw.QFrame):
    def __init__(self):
        super(PicoTrack, self).__init__()
        self.setLayout(qw.QVBoxLayout())

        # ------ Attributes ------- #
        self.pico = CyPico.PicoFile()

        # ------ GUI ------ #
        self._draw()

    def _draw(self):
        # ------ Track Header ------ #
        self.header = PicoTrackHeader('TRACK')
        self.layout().addWidget(self.header)

        # ------ Browse for Pico ------ #
        browse_lyt = qw.QHBoxLayout()
        browse_lyt.setContentsMargins(0, 0, 0, 0)
        browse_lyt.setSpacing(4)
        pico_lbl = qw.QLabel()
        pico_lbl.setText('Source:   ')
        self.pico_le = qw.QLineEdit()
        self.pico_le.setEnabled(False)
        self.pico_le.setPlaceholderText('Browse for a .pico file...')
        self.pico_btn = qw.QPushButton()
        self.pico_btn.setText('Browse')
        browse_lyt.addWidget(pico_lbl)
        browse_lyt.addWidget(self.pico_le)
        browse_lyt.addWidget(self.pico_btn)
        self.layout().addLayout(browse_lyt)

        # ------ Override Save ------ #
        override_lyt = qw.QHBoxLayout()
        override_lyt.setContentsMargins(0, 0, 0, 0)
        override_lyt.setSpacing(4)
        override_lbl = qw.QLabel()
        override_lbl.setText('Override:')
        self.override_le = qw.QLineEdit()
        self.override_le.setEnabled(False)
        self.override_le.setPlaceholderText('Change output name and location...')
        self.override_btn = qw.QPushButton()
        self.override_btn.setText('Set New')
        self.override_btn.setEnabled(False)
        override_lyt.addWidget(override_lbl)
        override_lyt.addWidget(self.override_le)
        override_lyt.addWidget(self.override_btn)
        self.layout().addLayout(override_lyt)

        # ------ Render Length ------ #
        self.render_lyt = PicoRenderLength()
        self.layout().addLayout(self.render_lyt)

        # ------ Progress and Run ------ #
        progress_lyt = qw.QHBoxLayout()
        progress_lyt.setContentsMargins(0, 0, 0, 0)
        progress_lyt.setSpacing(0)
        self.progress_bar = qw.QProgressBar()
        self.check_btn = qw.QPushButton()
        self.check_btn.setText('Check')
        self.check_btn.setEnabled(False)
        self.check_btn.setMaximumWidth(self.check_btn.fontMetrics().boundingRect('Check').width() + 24)
        self.run_btn = qw.QPushButton()
        self.run_btn.setText('Run')
        self.run_btn.setEnabled(False)
        self.run_btn.setMaximumWidth(self.run_btn.fontMetrics().boundingRect('Check').width() + 24)
        self.run_btn.clicked.connect(self._download)
        progress_lyt.addWidget(self.progress_bar)
        progress_lyt.addWidget(self.check_btn)
        progress_lyt.addWidget(self.run_btn)
        self.layout().addLayout(progress_lyt)

        # ------ Connections ------ #
        self.pico_btn.clicked.connect(self._browse)
        self.override_btn.clicked.connect(self._override)
        self.render_lyt.full_radio.toggled.connect(lambda: self._render_state(self.render_lyt.full_radio))
        self.render_lyt.slice_radio.toggled.connect(lambda: self._render_state(self.render_lyt.slice_radio))
        self.render_lyt.tc_in.textChanged.connect(self._check_gui_requirements)
        self.render_lyt.tc_out.textChanged.connect(self._check_gui_requirements)
        self.check_btn.clicked.connect(self.check)
        self.run_btn.clicked.connect(self.run)

    def _browse(self):
        pico_file_name, _ = qw.QFileDialog.getOpenFileName(self,
                                                           'Select a valid .pico file',
                                                           gROOT,
                                                           'Vicon Cara Pico (*.pico)')
        if pico_file_name == '':
            self.pico_le.clear()
            self._check_gui_requirements()
        else:
            self.pico_le.setText(pico_file_name)
            self._check_gui_requirements()

    def _override(self):
        new_file_name, _ = qw.QFileDialog.getSaveFileName(self,
                                                          'Select a new save location',
                                                          gROOT,
                                                          'All Files (*)')
        if new_file_name == '':
            self.override_le.clear()
            self._check_gui_requirements()
        else:
            self.override_le.setText(new_file_name)
            self._check_gui_requirements()

    def _check_gui_requirements(self):
        if self.pico_le.text() != '':
            self.override_btn.setEnabled(True)

            if self.render_lyt.length == 'Slice':
                if self.render_lyt.tc_in.hasAcceptableInput() and self.render_lyt.tc_out.hasAcceptableInput():
                    if self.render_lyt.tc_in.text() != self.render_lyt.tc_out.text():
                        self.check_btn.setEnabled(True)
                        # self.run_btn.setEnabled(True)
                    else:
                        self.check_btn.setEnabled(False)
                else:
                    self.check_btn.setEnabled(False)
                    # self.run_btn.setEnabled(False)
            elif self.render_lyt.length == 'Full':
                self.check_btn.setEnabled(True)
                # self.run_btn.setEnabled(True)

        else:
            self.override_btn.setEnabled(False)

    def _render_state(self, b):
        if b.text() == 'Full' and b.isChecked():
            self.render_lyt.length = 'Full'
            print(self.render_lyt.length)
            self.render_lyt.tc_in.setEnabled(False)
            self.render_lyt.tc_out.setEnabled(False)
            self._check_gui_requirements()

        elif b.text() == 'Slice' and b.isChecked():
            self.render_lyt.length = 'Slice'
            print(self.render_lyt.length)
            self.render_lyt.tc_in.setEnabled(True)
            self.render_lyt.tc_out.setEnabled(True)
            self._check_gui_requirements()

    def _map_values_from_gui(self):
        """
        Connects GUI values to the PicoFile instance
        :return:
        """
        self.pico.file_path = str(self.pico_le.text())

        if self.override_le.text() != '':
            self.pico.override = str(self.override_le.text())

        if self.render_lyt.start_frame_le.text() != '':
            self.pico.start_frame = str(self.render_lyt.start_frame_le.text())
        else:
            self.pico.start_frame = str(self.render_lyt.start_frame_le.placeholderText())

        self.pico.render_length = self.render_lyt.get_length()

        if self.render_lyt.tc_in.text() != '':
            self.pico.timecode_in = str(self.render_lyt.tc_in.text())

        if self.render_lyt.tc_out.text() != '':
            self.pico.timecode_out = str(self.render_lyt.tc_out.text())

    def check(self):
        # Connect GUI values to PicoFile instance
        self._map_values_from_gui()
        check_thread = PicoCheckThread(self.pico)


        self.run_btn.setEnabled(True)

    def run(self):
        for k, v in vars(self.pico).iteritems():
            print(k, v)

    def _download(self):
        # self.pico = CyPico.PicoFile()
        # self.completed = 0
        # while self.completed < 100:
        #     self.completed += 0.0001
        #     self.progress_bar.setValue(self.completed)
        pass


# ----------------------------------------------------- #

class PicoCheckThread(qc.QThread):
    def __init__(self, pico_instance):
        super(PicoCheckThread, self).__init__()
        self.pico_instance = pico_instance

    def __del__(self):
        self.wait()

    def run(self):
        # Process Shit
        pass


# ----------------------------------------------------- #


class PicoRunThread(qc.QThread):
    def __init__(self, pico_instance):
        super(PicoRunThread, self).__init__()
        self.pico_instance = pico_instance

    def __del__(self):
        self.wait()

    def run(self):
        # Process Shit
        pass

# ----------------------------------------------------- #


class PicoTrackHeader(qw.QWidget):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):
        super(PicoTrackHeader, self).__init__()

        self.setMinimumHeight(2)
        self.setLayout(qw.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(qc.Qt.AlignVCenter)

        self.first_line = qw.QFrame()
        self.first_line.setFrameStyle(qw.QFrame.HLine)
        self.layout().addWidget(self.first_line)

        main_color = 'rgba(%s, %s, %s, 255)' % color
        shadow_color = 'rgba(45, 45, 45, 255)'

        bottom_border = ''

        if shadow:
            bottom_border = 'border-bottom:2px solid %s' % shadow_color

        style_sheet = "border:0px solid rgba(0,0,0,0); \
                                   background-color: %s; \
                                   max-height:2px; \
                                   %s" % (main_color, bottom_border)

        self.first_line.setStyleSheet(style_sheet)

        if text is None:
            return

        self.first_line.setMaximumWidth(5)

        font = qg.QFont()
        font.setBold(True)
        font.setItalic(True)

        text_width = qg.QFontMetrics(font)
        # text_width.inFont(font)
        width = text_width.width(text) + 16

        label = qw.QLabel()
        label.setText(text)
        label.setFont(font)
        label.setMaximumWidth(width)
        label.setAlignment(qc.Qt.AlignCenter | qc.Qt.AlignVCenter)

        self.layout().addWidget(label)

        second_line = qw.QFrame()
        second_line.setFrameStyle(qw.QFrame.HLine)
        self.layout().addWidget(second_line)

        second_line.setStyleSheet(style_sheet)

    # ----------------------------------------------------- #


# ----------------------------------------------------- #


class PicoRenderLength(qw.QHBoxLayout):
    def __init__(self):
        super(PicoRenderLength, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(4)
        self.setAlignment(qc.Qt.AlignVCenter)

        # -- Attributes -- #
        self.length = 'Full'  # Default behaviour
        self.tc_reg_ex = qc.QRegExp('^(?:(?:[0-1][0-9]|[0-2][0-3]):)(?:[0-5][0-9]:){2}(?:[0-2][0-9])$')

        # -- Draw -- #
        self._home()

    def _home(self):
        start_frame_lbl = qw.QLabel()
        start_frame_lbl.setText('Start Frame:')
        self.start_frame_le = qw.QLineEdit()
        self.start_frame_le.setFixedWidth(36)
        # TODO Validate input with a RegEx
        self.start_frame_le.setPlaceholderText('1001')

        render_lbl = qw.QLabel()
        render_lbl.setText('Length:')

        self.full_radio = qw.QRadioButton()
        self.full_radio.setText('Full')
        self.full_radio.setChecked(True)

        self.slice_radio = qw.QRadioButton()
        self.slice_radio.setText('Slice')
        self.slice_radio.setChecked(False)

        self.tc_in = qw.QLineEdit()
        self.tc_in.setEnabled(False)
        self.tc_in.setPlaceholderText('TC in...')
        in_le_validator = qg.QRegExpValidator(self.tc_reg_ex, self.tc_in)
        self.tc_in.setValidator(in_le_validator)

        self.tc_out = qw.QLineEdit()
        self.tc_out.setEnabled(False)
        self.tc_out.setPlaceholderText('TC out...')
        out_le_validator = qg.QRegExpValidator(self.tc_reg_ex, self.tc_out)
        self.tc_out.setValidator(out_le_validator)

        self.layout().addWidget(start_frame_lbl)
        self.layout().addWidget(self.start_frame_le)
        self.addSpacing(16)
        self.layout().addWidget(render_lbl)
        self.layout().addWidget(self.full_radio)
        self.layout().addWidget(self.slice_radio)
        self.layout().addWidget(self.tc_in)
        self.layout().addWidget(self.tc_out)

    # @property
    def get_length(self):
        return self.length


# ----------------------------------------------------- #


class PicoFileDialog(qw.QFileDialog):
    def __init__(self):
        super(PicoFileDialog, self).__init__()
        self.setFileMode(QFileDialog_FileMode=2)
        self.setFilter("Pico files (*.pico)")


# ----------------------------------------------------- #


class Footer(qw.QWidget):
    def __init__(self):
        super(Footer, self).__init__()
        self.setLayout(qw.QVBoxLayout())
        self.layout().setContentsMargins(4, 4, 16, 4)
        self.layout().setSpacing(2)
        self.layout().setAlignment(qc.Qt.AlignRight)
        self.setSizePolicy(qw.QSizePolicy.Minimum,
                           qw.QSizePolicy.Fixed)

        self.lbl = qw.QLabel()
        self.lbl.setText('© 2017 Dragon Unit - Framestore LDN')
        self.layout().addWidget(self.lbl)


def run():
    """
    Main execution
    """
    app = qw.QApplication(sys.argv)
    slicer = PicoSlicer()
    slicer()

    sys.exit(app.exec_())


run()