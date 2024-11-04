#!/usr/bin/env python
"""
Convert Zwift workout files to ERG file format.
The user will be prompted to choose a directory containing workout files to process.
Output files are written to the same directory, with .erg extension.
Note: Zwift format tags like category and subcategory are not translated.Some of these tags have no equivalent in .mrc

author = Robert Drohan
copyright = Copyright 2024, Robert Drohan
license = GPLv3
version = 0.9.1
status = Development
"""

import sys
if sys.version_info[0] < 3:
    raise Exception("Aborting. Python 3 must be installed!")
import os
import errno
import tkinter as tk
from tkinter.filedialog import askdirectory
import xml.etree.ElementTree as ElTr


msg_dur = '3'  # Seconds to display message
deci2p = "{0:.2f}"  # Format to 2 decimal places
power_data = ''  # Initialise power data
msg_list = []  # Initialise messages
t_start_seg = 0  # initialise start time


def seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc):
    global power_data, msg_list, t_start_seg
    # Add line for segment start, specifying start time and percent FTP. Add a segment message about cadnc.
    seg_start = deci2p.format(t_start_seg) + '\t' + perc_start_pwr + '\n'
    if cadnc == 0:
        cad_txt = 'any'
    else:
        cad_txt = str(int(cadnc))
    msg_list.append(str(int(t_start_seg * 60)) + ' Pedal at ' + cad_txt + ' RPM ' + msg_dur + '\n')
    power_data += seg_start

    t_end_seg = t_start_seg + (seg_dur / 60)
    # Add line for segment end, specifying end time and percent FTP.
    seg_end = deci2p.format(t_end_seg) + '\t' + perc_end_pwr + '\n'
    power_data += seg_end
    t_start_seg = t_end_seg


def make_num(in_string):
    # Convert a string to int, or 0 if non-numeric
    if in_string.isnumeric():
        out_num = int(float(in_string))
    else:
        out_num = 0  # Not a number, set to default
    return out_num


def open_dir_dialog(user_msg):
    # Ask user to specify a directory.
    initd = 'C:\\'
    sel_dir = askdirectory(title = user_msg, initialdir = initd)
    if (sel_dir is not None) and (sel_dir != ''):
        return sel_dir
    else:
        exit('No directory selected.')


def zone_pwr(zone):
    # Convert workout zone number to %FTP (mid-zone figure)
    # Zone												Nom% FTP
    # 1 Active Recovery	< 55% FTP	    2 / Recovery		48
    # 2 Endurance	55% – 75% FTP	    6 / Easy-Moderate	65
    # 3 Tempo	76% – 87% FTP	        7 / Moderate		81
    # 4 Sweet Spot	88% – 94% FTP	    7 / Moderate		91
    # 5 Threshold	95% – 105% FTP	    8 / Moderate-Hard   100
    # 6 VO2 Max	106% – 120% FTP	        9 / Hard			113
    # 7 Anaerobic Capacity	> 120% FTP	10 / All-Out	    128

    midz_pwr = 0
    if zone > 0:
        match zone:
            case 1:
                midz_pwr = 0.48
            case 2:
                midz_pwr = 0.65
            case 3:
                midz_pwr = 0.81
            case 4:
                midz_pwr = 0.91
            case 5:
                midz_pwr = 1.00
            case 6:
                midz_pwr = 1.13
            case 7:
                midz_pwr = 1.28
            case _:
                midz_pwr = 0
    return midz_pwr


def make_path(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def main():
    global power_data, msg_list, t_start_seg
    file_count = 0
    root = tk.Tk()
    root.withdraw()
    # Ask user for source directory containing workout files.
    inp_dir_top = open_dir_dialog('Select .zwo input directory')
    # Ask user for output directory.
    out_dir_top = open_dir_dialog('Select .erg output directory')

    for dirpath, dirnames, filenames in os.walk(inp_dir_top, topdown = True):
        print(f'Processing directory: {dirpath}')
        for filex in filenames:
            # Process each workout file
            fullpath = os.path.join(dirpath, filex)
            f_name, f_ext = os.path.splitext(filex)
            if f_ext == '.zwo' or f_ext == '.xml':
                # Parse the workout file
                try:
                    tree = ElTr.parse(fullpath)
                    root = tree.getroot()
                except IOError as e:
                    print("[IO] I/O Error %d: %s" % (e.errno, e.strerror))
                    raise e
                else:
                    # File can be parsed. Convert each workout to mrc format.
                    out_dir_name = dirpath.split(inp_dir_top)[1].strip('\\')
                    out_dir_path = os.path.join(out_dir_top , out_dir_name)
                    outfile_name = os.path.join(out_dir_path, f_name + '.mrc')
                    make_path(out_dir_path)

                    power_data = ''  # Init
                    msg_list = []  # Init
                    t_start_seg = 0  # Init

                    power_data += '[COURSE HEADER]\n'
                    power_data += 'FTP = 200\n' \
                                  'VERSION = 2\n' \
                                  'UNITS = METRIC\n'

                    temp_desc = getattr(root.find("description"), 'text', None)
                    wo_desc = str(temp_desc).replace('\n', ' ')

                    power_data += 'DESCRIPTION = ' + wo_desc + '\n'
                    power_data += 'FILE NAME = ' + f_name + '.mrc\n'
                    power_data += 'MINUTES  PERCENT\n' \
                                  '[END COURSE HEADER]\n' \
                                  '[COURSE DATA]\n'

                    wko = root.find("workout")
                    wko_list = list(wko)
                    for child in wko_list:
                        ch_tag = child.tag
                        ch_attr = child.attrib

                        if ch_tag == 'IntervalsT':
                            # Create interval segments with alternating 'on' high effort and 'off' lower effort.
                            repeats = int(float(ch_attr.get('Repeat', '1')))
                            itvl_on_dur = int(float(ch_attr.get('OnDuration', '0')))
                            itvl_off_dur = int(float(ch_attr.get('OffDuration', '0')))
                            itvl_on_pwr = float(ch_attr.get('OnPower', '0'))
                            itvl_off_pwr = float(ch_attr.get('OffPower', '0'))
                            itvl_on_pwr_hi = float(ch_attr.get('PowerOnHigh', '0'))
                            itvl_on_pwr_lo = float(ch_attr.get('PowerOnLow', '0'))
                            itvl_off_pwr_hi = float(ch_attr.get('PowerOffHigh', '0'))
                            itvl_off_pwr_lo = float(ch_attr.get('PowerOffLow', '0'))
                            if itvl_on_pwr_hi > 0 and itvl_on_pwr_lo > 0:
                                itvl_on_pwr = (itvl_on_pwr_hi + itvl_on_pwr_lo) / 2
                            if itvl_off_pwr_hi > 0 and itvl_off_pwr_lo > 0:
                                itvl_off_pwr = (itvl_off_pwr_hi + itvl_off_pwr_lo) / 2
                            cad_on = (ch_attr.get('Cadence', '0'))
                            cad_off = (ch_attr.get('CadenceResting', '0'))
                            for i in range(repeats):
                                seg_dur = itvl_on_dur
                                cadnc = make_num(cad_on)
                                perc_start_pwr = str(deci2p.format(itvl_on_pwr * 100))
                                perc_end_pwr = perc_start_pwr
                                seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                                seg_dur = itvl_off_dur
                                cadnc = make_num(cad_off)
                                perc_start_pwr = str(deci2p.format(itvl_off_pwr * 100))
                                perc_end_pwr = perc_start_pwr
                                seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                        elif ch_tag == 'Warmup' or ch_tag == 'Cooldown':
                            # Create a segment that ramps up or down in effort.
                            seg_dur = int(float(ch_attr.get('Duration', '0')))
                            start_pwr = float(ch_attr.get('PowerLow', '0'))  # PowerLow actually means start power
                            end_pwr = float(ch_attr.get('PowerHigh', '0'))  # PowerHigh actually means end power
                            zone = (int(float(ch_attr.get('Zone', '0'))))
                            if zone > 0:
                                start_pwr = zone_pwr(zone)
                                end_pwr = start_pwr
                            cadnc = make_num(ch_attr.get('Cadence', '0'))
                            perc_start_pwr = str(deci2p.format(start_pwr * 100))
                            perc_end_pwr = str(deci2p.format(end_pwr * 100))
                            seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                        elif ch_tag == 'SteadyState':
                            # Create a segment with steady state effort.
                            seg_dur = int(float(ch_attr.get('Duration', '0')))
                            ss_pwr = float(ch_attr.get('Power', '0'))
                            ss_hipwr = float(ch_attr.get('PowerHigh', '0'))
                            ss_lopwr = float(ch_attr.get('PowerLow', '0'))
                            if ss_hipwr > 0 and ss_lopwr > 0:
                                ss_pwr = (ss_hipwr + ss_lopwr) / 2
                            zone = (int(float(ch_attr.get('Zone', '0'))))
                            if zone > 0:
                                ss_pwr = zone_pwr(zone)
                            cadnc = make_num(ch_attr.get('Cadence', '0'))
                            cad_hi = make_num(ch_attr.get('CadenceHigh', '0'))
                            cad_lo = make_num(ch_attr.get('CadenceLow', '0'))
                            if cad_hi > 0 and cad_lo > 0:
                                cadnc = (cad_hi + cad_lo) / 2

                            perc_start_pwr = str(deci2p.format(ss_pwr * 100))
                            perc_end_pwr = perc_start_pwr
                            seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                        elif ch_tag == 'FreeRide':
                            seg_dur = int(float(ch_attr.get('Duration', '0')))
                            perc_start_pwr = '40'  # Interpret 'FreeRide' as 40% FTP
                            perc_end_pwr = perc_start_pwr
                            cadnc = make_num(ch_attr.get('Cadence', '0'))
                            seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                power_data += '[END COURSE DATA]\n'
                power_data += '[COURSE TEXT]\n'
                for txt_line in msg_list:
                    power_data += txt_line
                power_data += '[END COURSE TEXT]\n'

                with open(outfile_name, 'w+', encoding='utf-8') as f_out:
                    # Write workout to .mrc file.
                    f_out.write(power_data)
                file_count = file_count + 1

    print('Processed ' + str(file_count) + ' files')


if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # Clean exit
    main()
