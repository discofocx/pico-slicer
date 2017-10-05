import sys
import os
import re
import time
import datetime
import subprocess
import logging

import cv2
import numpy
# from PyCara import PyPico
from timecode import Timecode


class PicoFile(object):
    def __init__(self):
        """
        Base class for all the Pico processing functionality
        """
        # Attributes from GUI or caller
        self.file_path = None
        self.override = None
        self.start_frame = None
        self.render_length = None
        self.timecode_in = None
        self.timecode_out = None

        # Attributes from Pico file in memory
        self.file_buffer = None

        self.header = None
        self.base_timecode = None

        self.channels = None  # Not entirely sure we need this - Scratch that, we do need it.
        self.timecode = None
        self.raw_fps = None
        self.frame_in = None
        self.frame_out = None
        self.frame_zero = None
        self.frame_offset = None  # This one eventually turns into the frame index
        self.frame_start = None
        self.frame_padding = None
        self.total_frames = None

        # Attributes for render action
        self.output_name = None
        self.render_fps = 24  # Hardcoded to 24, eventually we'll support other bases

    def read(self):
        """
        Loads a pico file in memory and populates it's attributes
        :return:
        """

        # Load .pico file in memory
        self.file_buffer = None  # PyPico.PicoReader().open(self.file_path)

        # Get .pico file header
        self.header = self.file_buffer.get_header()

        # Get .pico file last timecode jam
        self.base_timecode = [str(self.file_buffer.get_frame(0).jamsync_timecode.hours),
                              str(self.file_buffer.get_frame(0).jamsync_timecode.minutes),
                              str(self.file_buffer.get_frame(0).jamsync_timecode.seconds),
                              str(self.file_buffer.get_frame(0).jamsync_timecode.frames)]

        # Get .pico file properties
        properties = self.file_buffer.get_properties()

        # Get .pico file active channels
        self.channels = []
        channel = 0
        while channel < 4:
            if properties['channels.{0}.enabled'.format(channel)] == 'True':
                self.channels.append(channel)
            else:
                channel += 1

        # Format last timecode jam
        self.timecode = ':'.join(self.base_timecode)

        # Get measured framerate
        self.raw_fps = float(properties['channels.{0}.framerate_measured'.format(self.channels[0])])


        # Set .pico file render first and last frame, can be full or by tc inputs
        if self.render_length == 'Slice':
            self.frame_in = self.timecode_in
            self.frame_out = self.timecode_out
            self.frame_start = self.start_frame
        else:
            self.frame_in = int(self.header.start_capture_frame_number)
            self.frame_out = int(self.header.stop_capture_frame_number)
            self.frame_start = self.frame_in - self.frame_offset

        # Get .pico file "zero" frame from the burn in
        self.frame_zero = int(self.file_buffer.read_burn_in(0))

        # .pico file frame operations
        self.frame_offset = self.frame_in - self.frame_zero
        self.frame_padding = len(str(self.frame_out - self.frame_in))
        self.total_frames = self.frame_out - self.frame_in

        # Set output names
        if self.override is not None:
            self.output_name = self.override
        else:
            self.output_name = self.file_path

    def validate_timecode_input(self):
        pass

    def render(self):
        pass