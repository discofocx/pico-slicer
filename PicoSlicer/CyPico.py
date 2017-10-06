import sys
import os
import re
import time
import datetime
import subprocess
import logging

import cv2
import numpy as np
from timecode import Timecode

try:
    from PyCara import PyPico
except RuntimeError:
    print('No valid CaraPost license found, render functions are disabled')


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
        self.jam_timecode = None
        self.raw_fps = None
        self.frame_in = None
        self.frame_out = None
        self.frame_zero = None
        self.frame_offset = None  # This one eventually turns into the frame index
        self.frame_start = None  # This one is not used anymore as the value comes from the GUI
        self.frame_padding = None
        self.total_frames = None

        # Attributes for render action
        self.output_name = None
        self.render_fps = None
        self.ref_timecode = None

    def read(self):
        """
        Loads a pico file in memory and populates it's attributes
        :return:
        """

        # Load .pico file in memory
        self.file_buffer = PyPico.PicoReader()
        self.file_buffer.open(self.file_path)

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
                channel += 1
            else:
                channel += 1

        # Get measured framerate
        self.raw_fps = float(properties['channels.{0}.framerate_measured'.format(self.channels[0])])

        # Timecode operations
        self.render_fps = int(round(self.raw_fps / 2))

        jam_timecode_str = ':'.join(self.base_timecode)
        self.jam_timecode = Timecode(self.render_fps, jam_timecode_str)

        # Set .pico file render first and last frame, can be full or by tc inputs
        if self.render_length == 'Slice':
            self.timecode_in = Timecode(self.render_fps, str(self.timecode_in))
            self.timecode_out = Timecode(self.render_fps, str(self.timecode_out))
            self.frame_in = (self.timecode_in.frames - self.jam_timecode.frames) * 2
            self.frame_out = (self.timecode_out.frames - self.jam_timecode.frames) * 2

        else:
            self.frame_in = int(self.header.start_capture_frame_number)
            self.frame_out = int(self.header.stop_capture_frame_number)
            self.timecode_in = Timecode(self.render_fps, frames=int(self.header.start_capture_frame_number))
            self.timecode_out = Timecode(self.render_fps, frames=int(self.header.stop_capture_frame_number))

        # Reference Timecode
        self.ref_timecode = Timecode(self.render_fps, frames=(self.jam_timecode.frames + (self.frame_in / 2)))

        # Get .pico file "zero" frame from the burn in
        self.frame_zero = int(self.file_buffer.read_burn_in(0))

        # .pico file frame operations
        self.frame_offset = self.frame_in - self.frame_zero
        self.frame_padding = len(str(self.frame_out - self.frame_in))
        self.total_frames = self.frame_out - self.frame_in

        # No need to mess around with the start frame, it should come from the GUI

        # if self.render_length == 'Slice':
        #     self.frame_start = self.start_frame
        # else:
        #     self.frame_start = self.frame_in - self.frame_offset

        # Set output names
        if self.override is not None:
            self.output_name = self.override
        else:
            self.output_name = self.file_path

    def report(self):
        for k, v in vars(self).iteritems():
            print(k, v)

    def validate_timecode_input(self):
        """
        Before trying to render a .pico file,
        we first need to validate the desired timecode range, for this,
        we load a frame into memory and try to get it's shape attribute, which,
        if it is a valid numpy array, will be positive.
        :return: bool
        """
        frame = self.file_buffer.get_image(self.frame_offset)
        try:
            test = frame.shape
        except Exception as e:
            print(e)
            return False
        else:
            return True
        finally:
            test = None
            frame = None

    def render(self):

        # Because we will be modifying a lot of values, instead of operating on the attributes,
        # we'll store what we need in local variables.
        render_progress_frames = 0
        render_index = self.frame_offset
        render_output_name = self.output_name.replace('.pico', '')
        render_frame_in = self.frame_in
        render_frame_out = self.frame_out
        render_start_frame = self.start_frame

        # Which Timecode are we going to render, user or file
        if self.render_length == 'Slice':
            render_tc = self.timecode_in
        else:
            render_tc = self.ref_timecode

        # Check if we are starting on a sub-frame, if so, step one frame up

        if render_frame_in % 2:  # If render_frame_in is a sub-frame
            render_frame_in += 1
            render_index += 1
            render_tc.frames += 1

        # Utility function for rotating the frame, probs, it should not be here
        def rotate_bound(image, angle):
            # grab the dimensions of the image and then determine the
            # center
            (h, w) = image.shape[:2]
            (cX, cY) = (w // 2, h // 2)

            # grab the rotation matrix (applying the negative of the
            # angle to rotate clockwise), then grab the sine and cosine
            # (i.e., the rotation components of the matrix)
            M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])

            # compute the new bounding dimensions of the image
            nW = int((h * sin) + (w * cos))
            nH = int((h * cos) + (w * sin))

            # adjust the rotation matrix to take into account translation
            M[0, 2] += (nW / 2) - cX
            M[1, 2] += (nH / 2) - cY

            # perform the actual rotation and return the image
            return cv2.warpAffine(image, M, (nW, nH))

        # Control counters (Not really control counters anymore)
        if self.frame_padding <= 3:
            self.frame_padding = 4
        else:
            pass

        # Render loop
        while render_frame_in < (render_frame_out + 2):
            # Load a new frame in memory
            frame = self.file_buffer.get_image(render_index)

            # Manipulate the frame
            cv2.rectangle(frame, (16, 40), (220, 80), (0, 0, 0), -1)
            cv2.putText(frame, str(render_tc), (20, 70), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)

            # Rotate the frame 90 degrees
            frame = rotate_bound(frame, -90)

            # Where are we going to save that new fresh frame?
            image_output_name = render_output_name + '.{0:0>{1}}.jpg'.format(render_start_frame, self.frame_padding)

            # if self.override:
            #     self.output_name = self.output_name + '.{0:0>{1}}.jpg'.format(self.frame_start, self.frame_padding)
            # else:
            #     self.output_name = self.output_name.replace('.pico', '.{0:0>{1}}.jpg'.format(self.frame_start,
            #                                                                                  self.frame_padding))

            # Save the fresh frame
            cv2.imwrite(image_output_name, frame, [cv2.IMWRITE_JPEG_QUALITY, 100])

            # Yield progress
            yield render_progress_frames

            # Prepare for the next loop
            render_index += 2
            render_frame_in += 2
            render_progress_frames += 2
            render_tc.frames += 1
            render_start_frame += 1

