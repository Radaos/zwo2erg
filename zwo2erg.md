# Project Specification Document

##Project Title: zwo2erg

## Purpose: To convert Zwift ZWO workout files (XML format) into ERG files — a plain-text format used by other training platforms like TrainerRoad, Wahoo SYSTM, or GoldenCheetah. The tool ensures interoperability across indoor cycling ecosystems.

##Functional Requirements
1. File Selection & Input Handling\
FR1.1: The system shall provide a graphical file picker to select one or more .zwo files.
FR1.2: The system shall allow users to select a folder to process multiple workouts in batch mode.
FR1.3: The system shall validate selected files for correct ZWO XML structure before conversion begins.

2. Output Configuration
FR2.1: The system shall prompt the user with a destination folder picker for ERG output.
FR2.2: The system shall display a summary of converted files upon completion, including success and error status.

3. Conversion Workflow
FR3.1: The system shall parse ZWO workout elements (<Warmup>, <Cooldown>, <SteadyState>, <Ramp>, <IntervalsT>).
FR3.2: The system shall convert FTP-relative values to ERG-compatible format.
FR3.3: The system shall generate .erg files named based on the workout title or original filename.

4. User Feedback
FR4.1: The system shall show progress indicators during file parsing and conversion.
FR4.2: The system shall display a log window or modal detailing parsed intervals and any conversion warnings.
FR4.3: The system shall offer a “View Output Folder” button post-conversion for quick access.

## Design Specifications

GUI Components
Component				Purpose
Input File Picker		Select ZWO files or input folder
Output Folder Picker	Specify location to save ERG files

File Mapping Logic
ZWO workout intervals (XML elements) → ERG line items

FTP percentage → ERG unit scaling (static or user-supplied FTP value)
Interval durations → hh:mm:ss time format
Workout title → ERG file name
Descriptive text → Comments in ERG file

Technical Architecture
Language: Python with Tkinter GUI toolkit

Dependencies:
xml.etree.ElementTree for ZWO parsing
datetime, os for file handling
GUI framework Tkinter


