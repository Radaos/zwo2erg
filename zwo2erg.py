#!/usr/bin/env python
"""
Convert Zwift workout files to ERG file format.
The user will be prompted to choose a directory containing workout files to process.
Output files are written to the same directory, with .erg extension.
TODO: Zwift format tags like category and subcategory are not translated.Some of these tags have no equivalent in .mrc
TODO: Zwift format textevents are not translated.

author = Robert Drohan
copyright = Copyright 2024, Robert Drohan
license = GPLv3
version = 0.9.0
status = Development
"""

import sys
if sys.version_info[0] < 3:
    raise Exception("Aborting. Python 3 must be installed!")
import os
import tkinter as tk
from tkinter.filedialog import askdirectory
import xml.etree.ElementTree as ElTr

msg_dur = ' 3\n'  # Seconds to display message
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
    msg_list.append(str(int(t_start_seg * 60)) + ' Pedal at ' + cad_txt + ' RPM' + msg_dur)
    power_data += seg_start

    t_end_seg = t_start_seg + (seg_dur / 60)
    # Add line for segment end, specifying end time and percent FTP.
    seg_end = deci2p.format(t_end_seg) + '\t' + perc_end_pwr + '\n'
    power_data += seg_end
    t_start_seg = t_end_seg


def make_num(in_string):
    # Convert a string to int, or 0 if non-numeric
    if in_string.isnumeric():
        out_num = int(in_string)
    else:
        out_num = 0  # Not a number, set to default
    return out_num


def open_dir_dialog():
    # Ask user for input directory path
    init_dir = 'C:\\'
    wo_dir = askdirectory(title='Select workout directory', initialdir=init_dir)
    if (wo_dir is not None) and (wo_dir != ''):
        return wo_dir
    else:
        exit('No directory selected.')


def zone_pwr(zone):
    # Convert workout zone number to %FTP (mid-zone figure)
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


def main():
    global power_data, msg_list, t_start_seg
    # Ask user for source directory containing workout files.
    root = tk.Tk()
    root.withdraw()
    init_dir = open_dir_dialog()
    os.chdir(init_dir)
    file_count = 0

    for dir_file in os.listdir(init_dir):
        # Process each workout file in the chosen directory.
        filepath = os.fsdecode(dir_file)
        f_name, f_ext = os.path.splitext(filepath)
        if f_ext == '.zwo' or f_ext == '.xml':
            # Parse the workout file
            try:
                tree = ElTr.parse(filepath)
                root = tree.getroot()
            except IOError as e:
                print("[IO] I/O Error %d: %s" % (e.errno, e.strerror))
                raise e
            else:
                # File is parsed. Convert each workout segment to mrc format.
                outfile_name = (f_name + '.mrc')
                power_data = ''  # Init
                msg_list = []  # Init
                t_start_seg = 0  # Init

                power_data += '[COURSE HEADER]\n'
                power_data += 'FTP = 200\n' \
                              'VERSION = 2\n' \
                              'UNITS = METRIC\n'
                wo_desc = str(root.find("description").text).replace('\n', ' ')
                power_data += 'DESCRIPTION = ' + wo_desc + '\n'
                power_data += 'FILE NAME = ' + outfile_name + '\n'
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
                        repeats = int(ch_attr.get('Repeat', '1'))
                        itvl_on_dur = int(ch_attr.get('OnDuration', '0'))
                        itvl_off_dur = int(ch_attr.get('OffDuration', '0'))
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
                        seg_dur = int(ch_attr.get('Duration', '0'))
                        start_pwr = float(ch_attr.get('PowerLow', '0'))  # PowerLow actually means start power
                        end_pwr = float(ch_attr.get('PowerHigh', '0'))  # PowerHigh actually means end power
                        zone = (int(ch_attr.get('Zone', '0')))
                        if zone > 0:
                            start_pwr = zone_pwr(zone)
                            end_pwr = start_pwr
                        cadnc = make_num(ch_attr.get('Cadence', '0'))
                        perc_start_pwr = str(deci2p.format(start_pwr * 100))
                        perc_end_pwr = str(deci2p.format(end_pwr * 100))
                        seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

                    elif ch_tag == 'SteadyState':
                        # Create a segment with steady state effort.
                        seg_dur = int(ch_attr.get('Duration', '0'))
                        ss_pwr = float(ch_attr.get('Power', '0'))
                        ss_hipwr = float(ch_attr.get('PowerHigh', '0'))
                        ss_lopwr = float(ch_attr.get('PowerLow', '0'))
                        if ss_hipwr > 0 and ss_lopwr > 0:
                            ss_pwr = (ss_hipwr + ss_lopwr) / 2
                        zone = (int(ch_attr.get('Zone', '0')))
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
                        seg_dur = int(ch_attr.get('Duration', '0'))
                        perc_start_pwr = '40'  # Interpret 'FreeRide' as 40% FTP
                        perc_end_pwr = perc_start_pwr
                        cadnc = make_num(ch_attr.get('Cadence', '0'))
                        seg_build(seg_dur, perc_start_pwr, perc_end_pwr, cadnc)

            power_data += '[END COURSE DATA]\n'
            power_data += '[COURSE TEXT]\n'
            for txt_line in msg_list:
                power_data += txt_line
            power_data += '[END COURSE TEXT]\n'

            with open(outfile_name, 'w', encoding='utf-8') as f_out:
                # Write workout to .mrc file.
                f_out.write(power_data)
            file_count = file_count + 1

    print('Processed ' + str(file_count) + ' files')


if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # Clean exit
    main()
