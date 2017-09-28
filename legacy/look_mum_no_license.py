""" Linear Batch dirty pico encoder,
    Automatically render .mov files from Vicon Cara .pico files
    """
import sys
import os
import re
import time
import datetime
import subprocess
import logging

from PyCara import PyPico
from timecode import Timecode
import cv2
import numpy as np

__author__ = 'Disco Hammer'
__copyright__ = 'Copyright 2017, Dragon Unit Framestore LDN 2017'
__version__ = '0.1'
__email__ = 'gsorchin@gmail.com'
__status__ = 'alpha'

# Globals

gDEBUG = True
gFONT = cv2.FONT_HERSHEY_DUPLEX
gDECODER = 'ffmpeg'  # os.path.join(os.getcwd(),'ffmpeg.exe')
gTODAY = datetime.datetime.now()
gLOG = os.path.join(os.getcwd(), '{0}-{1}-{2}_{3}{4}_batch.log'.format(gTODAY.year,
                                                                       gTODAY.month,
                                                                       gTODAY.day,
                                                                       gTODAY.hour,
                                                                       gTODAY.minute))

gPATTERN = re.compile('^(?:(?:[0-1][0-9]|[0-2][0-3]):)(?:[0-5][0-9]:){2}(?:[0-2][0-9])$')


def set_up_logger():

    # Set up the logger
    logging.basicConfig(filename=gLOG, level=logging.DEBUG)


def initialize_pico_file(path):  # Loads a .pico file in memory, returns a reader(object)

    reader = PyPico.PicoReader()
    reader.open(path)

    return reader


def get_file_properties(reader):  # Retrieves all the file's properties that we will use for the processing.

    header = reader.get_header()
    properties = reader.get_properties()

    # The Cara system stores the timecode for the last jam and starts counting from that point on,
    # Let's retrieve it and store it for future use.

    base_tc = [str(reader.get_frame(0).jamsync_timecode.hours),
               str(reader.get_frame(0).jamsync_timecode.minutes),
               str(reader.get_frame(0).jamsync_timecode.seconds),
               str(reader.get_frame(0).jamsync_timecode.frames)]

    # Dictionary that will nicely keep all of our relevant data, we'll pass it around later.

    file_properties = {'channel': None,
                       'tc': None,
                       'fps': None,
                       'in': None,
                       'out': None,
                       'zero': None,
                       'offset': None,
                       'start': None,
                       'pad': None}

    # Let's populate the dictionary.

    channel_index = 0

    while channel_index < 4:
        if properties['channels.{0}.enabled'.format(channel_index)] == 'False':
            channel_index += 1
        else:
            file_properties['channel'] = channel_index
            file_properties['tc'] = ':'.join(base_tc)
            file_properties['fps'] = float(properties['channels.{0}.framerate_measured'.format(channel_index)])
            file_properties['in'] = int(header.start_capture_frame_number)
            file_properties['out'] = int(header.stop_capture_frame_number)
            file_properties['zero'] = int(reader.read_burn_in(0))
            file_properties['offset'] = file_properties['in'] - file_properties['zero']
            file_properties['start'] = file_properties['in'] + file_properties['offset']
            file_properties['pad'] = len(str(file_properties['out'] - file_properties['in']))

            break

    return file_properties  # Exit and return our new dictionary


def render_file(file, reader, file_properties, bmp_dir):

    # How many frames are we rendering? This is the stop frame - start frame
    control_in = file_properties['in']
    control_out = file_properties['out']
    total_frames = control_out - control_in

    # Control counters
    progress_frames = 0
    frame_number = 0
    sub_frame_counter = None
    index = file_properties['offset']

    # Figure out and set-up the correct timecode
    render_fps = round(file_properties['fps'], 2)
    tc_fps = round(render_fps / 2, 2)
    base_tc = Timecode(str(tc_fps), file_properties['tc'])
    ref_tc = base_tc.frames + (control_in/ 2)
    tc = Timecode(str(tc_fps), frames=ref_tc)

    # Is the first frame a sub-frame?
    if not control_in % 2:
        sub_frame_counter = 0
    else:
        sub_frame_counter = 1

    # Time Control
    time_stamp = time.time()

    # TODO - Catch exceptions if the .pico file is corrupt, return True of False
    # Render loop
    while control_in < control_out:

        # Load a new frame in memory
        image = reader.get_image(index)

        # Manipulate that frame (Draw Timecode)
        cv2.rectangle(image, (16, 40), (220, 80), (0, 0, 0), -1)
        cv2.putText(image, str(tc), (20, 70), gFONT, 1, (255, 255, 255), 2)

        # Where are we going to save that new fresh frame?
        bmp_write = os.path.join(bmp_dir, os.path.basename(file))
        bmp_write = bmp_write.replace('.pico', '_{0:0>{1}}.jpg'.format(frame_number, file_properties['pad']))

        # Save the fresh frame
        cv2.imwrite(bmp_write, image)

        # Prepare for the next loop
        if sub_frame_counter < 1:
            index += 1
            control_in += 1
            sub_frame_counter += 1
            progress_frames += 1
            frame_number += 1
        else:
            index += 1
            control_in += 1
            tc.frames += 1
            sub_frame_counter = 0
            progress_frames += 1
            frame_number += 1

        # Update the user with the render progress
        current_progress = (progress_frames * 100) / total_frames
        sys.stdout.write('\r{0} %'.format(current_progress))
        sys.stdout.flush()

    # Inform the user with the rendering time
    print('\nRendered in {0} seconds'.format(round(time.time()-time_stamp)))

    return True


def rename_bmp(bmp_name, new_name):

    path = os.path.dirname(bmp_name)
    tail = os.path.basename(bmp_name).split('_')[-1]
    new_file = '_'.join([new_name, tail])
    new_path = os.path.join(path, new_file)
    os.rename(bmp_name, new_path)


def get_file_properties_from_input(reader, control_in, control_out, start_frame=0000, file_name=False):

    # header = reader.get_header()
    properties = reader.get_properties()

    # The Cara system stores the timecode for the last jam and starts counting from that point on,
    # Let's retrieve it and store it for future use.

    base_tc = [str(reader.get_frame(0).jamsync_timecode.hours),
               str(reader.get_frame(0).jamsync_timecode.minutes),
               str(reader.get_frame(0).jamsync_timecode.seconds),
               str(reader.get_frame(0).jamsync_timecode.frames)]

    # Dictionary that will nicely keep all of our relevant data, we'll pass it around later.

    file_properties = {'channel': None,
                       'tc': None,
                       'fps': None,
                       'in': None,
                       'out': None,
                       'zero': None,
                       'start': None,
                       'name': None}

    # Let's populate the dictionary.

    channel_index = 0

    while channel_index < 4:
        if properties['channels.{0}.enabled'.format(channel_index)] == 'False':
            channel_index += 1
        else:
            file_properties['channel'] = channel_index
            file_properties['tc'] = ':'.join(base_tc)
            file_properties['fps'] = float(properties['channels.{0}.framerate_measured'.format(channel_index)])
            file_properties['in'] = str(control_in)
            file_properties['out'] = str(control_out)
            file_properties['zero'] = int(reader.read_burn_in(0))
            file_properties['start'] = int(start_frame)
            file_properties['name'] = file_name

            break

    return file_properties  # Exit and return our new dictionary


def render_file_from_input(file, reader, file_properties, bmp_dir):

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

    # Figure out and set-up the correct timecode TODO So far timecode is somewhat consistent, need to elaborate on this

    capture_fps = round(file_properties['fps'], 2)
    print capture_fps
    tc_fps = 24 #round(capture_fps/2, 2)

    tc_in = Timecode(str(tc_fps), file_properties['in'])
    print tc_in
    tc_out = Timecode(str(tc_fps), file_properties['out'])
    print tc_out

    base_tc = Timecode(str(tc_fps), file_properties['tc'])
    print base_tc

    # How many frames are we rendering? This is the timecode out frames - timecode in frames
    frames_in = (tc_in.frames - base_tc.frames) * 2
    print frames_in
    frames_out = (tc_out.frames - base_tc.frames) * 2
    print frames_out
    total_frames = frames_out - frames_in
    print total_frames

    # Control counters
    progress_frames = 0
    frame_number = file_properties['start']
    index = frames_in - file_properties['zero']

    # File padding
    padding = frame_number + (total_frames / 2)
    padding = len(str(padding))

    if padding <= 3:
        padding = 4
    else:
        pass

    # Time Control
    time_stamp = time.time()

    # TODO - Catch exceptions if the .pico file is corrupt, return True or False
    # Render loop
    while frames_in < (frames_out + 2):

        # Load a new frame in memory
        image = reader.get_image(index)

        # Manipulate that frame (Draw Timecode)
        cv2.rectangle(image, (16, 40), (220, 80), (0, 0, 0), -1)
        cv2.putText(image, str(tc_in), (20, 70), gFONT, 1, (255, 255, 255), 2)
        # Rotate the frame 90 degrees
        image = rotate_bound(image, -90)

        # Where are we going to save that new fresh frame?
        bmp_write = os.path.join(bmp_dir, os.path.basename(file))
        bmp_write = bmp_write.replace('.pico', '_{0:0>{1}}.jpg'.format(frame_number, padding))

        # Save the fresh frame
        cv2.imwrite(bmp_write, image, [cv2.IMWRITE_JPEG_QUALITY, 100])

        # Check if we need to rename file, if so, do it.
        if file_properties['name']:
            rename_bmp(bmp_write, file_properties['name'])

        # Prepare for the next loop
        index += 2
        frames_in += 2
        progress_frames += 2
        tc_in.frames += 1
        frame_number += 1

        # Update the user with the render progress
        current_progress = abs((progress_frames * 100) / total_frames)
        sys.stdout.write('\r{0} %'.format(current_progress))
        sys.stdout.flush()

    # Inform the user with the rendering time
    print('\nRendered in {0} seconds'.format(round(time.time() - time_stamp)))

    return True


def encode_file(file, file_properties, bmp_dir):
    bmp_list = [bmp for _, _, f in os.walk(bmp_dir) for bmp in f if bmp.endswith('bmp')]
    padding = len(str(len(bmp_list)))

    if padding <= 3:
        padding = 4
    else:
        pass

    # Encoding framerate, we grab it from our file properties
    fps = round(file_properties['fps'] / 2, 2)
    print(fps)

    # From where do we load our image sequence?
    frame_sequence_in = os.path.join(bmp_dir, os.path.basename(file))
    frame_sequence_in = frame_sequence_in.replace('.pico', '_%0{0}d.jpg'.format(padding))

    # To where do we write our new encoded vid?
    vid_out = file.replace('.pico', '.mov')

    # Start encoding operation, we will use FFMPEG under a python subprocess call
    print('Encoding...')

    ffmpeg = subprocess.Popen('{0} -start_number {1} -f image2 -r {2} -i {3} -vcodec libx264 -pix_fmt yuv422p -crf 0 -preset ultrafast -y {4}'.format(gDECODER, file_properties['start'], fps, frame_sequence_in, vid_out), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    out, err = ffmpeg.communicate()
    exit = ffmpeg.returncode

    if not exit:
        return True
    else:
        print(err)
        return False

if __name__ == '__main__':

    print(58 * '=')
    print('Framestore Capturelab Dirty Pico to Quicktime encoder v0.1')
    print('Author: Disco-Hammer')
    print(58* '=')
    print('Scanning your directory for .pico files...\n')
    time.sleep(1)

    if gDEBUG:
        root = 'G:\\capturelab\\jb\\ScanOrders\\0334'
    else:
        root = os.getcwd()

    queue = list()

    for path, _subdirs, files in os.walk(root):
        for name in files:
            if name.endswith('.pico') and not os.path.isdir(path + '\\' + name.replace('.pico', '_bmp')):
                file = os.path.join(path, name)
                queue.append(file)
                print file

    if not len(queue):
        print('\nZero pico files could be found, try a different directory, bye.')
    else:
        print '\n{0} Pico file(s) have been found for encoding, do you want to proceed?\n' \
              'Yes (1), No (0)'.format(len(queue))

        while True:
            user = input()

            if user > 1:
                print('Please choose between 1 and 0')

            elif user == '':
                print('Please choose between 1 and 0')

            else:
                break

        if user:
            print('\nProcess full file (1) or by timecode inputs (0) ?')

            while True:
                action = raw_input()

                if action > '1':
                    print('Please choose between 1 and 0')
                else:
                    break

            # Run full-file processing.
            if action == '1':
                start_time = time.time()
                process_index = 1
                set_up_logger()
                logging.info('Batch Process started')  # TODO - Write a more detailed log (Include other props)

                for file in queue:
                    bmp_dir = file.replace('.pico', '_bmp')
                    if not os.path.isdir(bmp_dir):
                        os.mkdir(bmp_dir)

                    print('\nFile {0} of {1}'.format(process_index, len(queue)))
                    print('Rendering... {0}'.format(file.split('\\')[-1]))
                    reader = initialize_pico_file(file)
                    file_properties = get_file_properties(reader)
                    render_status = render_file(file, reader, file_properties, bmp_dir)

                    # TODO - Account in the log and in the process_index for any files that failed rendering (bad .picos)
                    if render_status:
                        reader = None  # Unload .pico reader from memory
                        encode_status = encode_file(file, file_properties, bmp_dir)

                        if encode_status:
                            print 'Finished {0} in {1} seconds'.format(file.replace('.pico','.mov'), (round(time.time() - start_time)))
                            logging.info('File {0} of {1} {2}'.format(process_index, len(queue), file))
                            process_index += 1

            # Run by timecode inputs.
            else:
                start_time = time.time()
                process_index = 1
                set_up_logger()
                logging.info('Batch Process started')  # TODO - Write a more detailed log (Include other props)

                # For every file that we've found
                for file in queue:
                    print('Working on file {0}'.format(os.path.basename(file)))

                    # Ask the user if he wants to rename the output
                    print('\nDo you want to rename the output? Yes(1) No(0)')
                    while True:
                        name_in = input()

                        if name_in > 1:
                                print('Please choose between 1 and 0')
                                continue

                        else:
                            break

                    if not name_in:
                        file_name = False

                    else:
                        print('Type in the new name')

                        while True:
                            new_name = raw_input()

                            if new_name == '':
                                print('Please type a valid new name')

                            else:
                                break

                        file_name = new_name
                        print(file_name)

                    # Ask the user for the timecode in
                    print('\nSupply a TC in: (##:##:##:##)')
                    while True:
                        user_in = raw_input()

                        if not gPATTERN.match(user_in):
                            print('That is not a valid timecode format, ##:##:##:## try again')
                        else:
                            break

                    # Ask the user for the timecode out
                    print('\nSupply a TC out: (##:##:##:##)')
                    while True:
                        user_out = raw_input()

                        if not gPATTERN.match(user_out):
                            print('That is not a valid timecode format, ##:##:##:## try again')
                        else:
                            break

                    # Ask for the first frame of the rendered sequence
                    print('\nSupply the first frame of the image sequence:')
                    while True:
                        start_frame = raw_input()

                        try:
                            start_frame = int(start_frame)
                        except ValueError:
                            print('Please provide a valid frame number (int)')
                            continue
                        else:
                            break

                    # Target bmp directory to store the rendered frames
                    bmp_dir = file.replace('.pico', '_bmp')
                    if not os.path.isdir(bmp_dir):  # Check if exists, if not, create one.
                        os.mkdir(bmp_dir)

                    # Get to work!
                    print('\nFile {0} of {1}'.format(process_index, len(queue)))
                    print('Rendering... {0}'.format(file.split('\\')[-1]))
                    reader = initialize_pico_file(file)
                    file_properties = get_file_properties_from_input(reader, user_in, user_out, start_frame, file_name)
                    render_status = render_file_from_input(file, reader, file_properties, bmp_dir)

                    # TODO - Account in the log and in the process_index for any bad .picos
                    if render_status:
                        reader = None  # Unload .pico reader from memory
                        #encode_status = encode_file(file, file_properties, bmp_dir)

                        #if encode_status:
                            #print 'Finished {0} in {1} seconds'.format(file.replace('.pico', '.mov'),
                            #                                           (round(time.time() - start_time)))
                        logging.info('File {0} of {1} {2}'.format(process_index, len(queue), file))
                        process_index += 1

        else:
            print'Abort'
