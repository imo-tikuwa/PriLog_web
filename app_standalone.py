# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, Response, abort, session, redirect
from wtforms import Form, StringField, SubmitField, validators, ValidationError
import numpy as np
import os
import re
from pytube import YouTube
import sys
import time as tm
sys.path.append('/home/prilog/lib')
import cv2
import os, tkinter, tkinter.filedialog, tkinter.messagebox
import sys
import characters as cd
from prkn_app_functions import *


root = tkinter.Tk()
root.withdraw()

fTyp = [("", "*")]

iDir = os.path.abspath(os.path.dirname(__file__))
file = tkinter.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)

if file == "":
    print("No video source found")
    sys.exit(1)

movie_path = file

# 動画解析し結果をリストで返す
start_time = tm.time()
video = cv2.VideoCapture(movie_path)

frame_count = int(video.get(7))  # フレーム数を取得
frame_rate = int(video.get(5))  # フレームレート(1フレームの時間単位はミリ秒)の取得

frame_width = int(video.get(3))  # フレームの幅
frame_height = int(video.get(4))  # フレームの高さ

try:
    video_type = FRAME_RESOLUTION.index((frame_width, frame_height))
except ValueError:
    video.release()
    clear_path(movie_path)

    print(ERROR_NOT_SUPPORTED)
    sys.exit(1)

CHARACTERS_DATA, SEC_DATA, MENU_DATA, SCORE_DATA, DAMAGE_DATA, ICON_DATA = model_init(video_type)
UB_ROI, MIN_ROI, TEN_SEC_ROI, ONE_SEC_ROI, MENU_ROI, SCORE_ROI, DAMAGE_DATA_ROI, CHARACTER_ICON_ROI, MENU_LOC, FRAME_THRESH = roi_init(video_type)

n = 0.34  # n秒ごと*
ub_interval = 0

time_min = "1"
time_sec10 = "3"
time_sec1 = "0"

menu_check = False

min_roi = MIN_ROI
tensec_roi = TEN_SEC_ROI
onesec_roi = ONE_SEC_ROI
ub_roi = UB_ROI
score_roi = SCORE_ROI
damage_data_roi = DAMAGE_DATA_ROI

ub_data = []
ub_data_value = []
time_data = []
characters_find = []

tmp_damage = []
total_damage = False

cap_interval = int(frame_rate * n)
skip_frame = 5 * cap_interval

if (frame_count / frame_rate) < 600:  # 10分未満の動画しか見ない
    for i in range(frame_count):  # 動画の秒数を取得し、回す
        ret = video.grab()
        if ret is False:
            break

        if i % cap_interval is 0:
            if ((i - ub_interval) > skip_frame) or (ub_interval == 0):
                ret, original_frame = video.read()

                if ret is False:
                    break
                work_frame = edit_frame(original_frame)

                if menu_check is False:
                    menu_check, menu_loc = analyze_menu_frame(work_frame, MENU_DATA, MENU_ROI)
                    if menu_check is True:
                        loc_diff = np.array(MENU_LOC) - np.array(menu_loc)
                        roi_diff = (loc_diff[0], loc_diff[1], loc_diff[0], loc_diff[1])
                        min_roi = np.array(MIN_ROI) - np.array(roi_diff)
                        tensec_roi = np.array(TEN_SEC_ROI) - np.array(roi_diff)
                        onesec_roi = np.array(ONE_SEC_ROI) - np.array(roi_diff)
                        ub_roi = np.array(UB_ROI) - np.array(roi_diff)
                        score_roi = np.array(SCORE_ROI) - np.array(roi_diff)
                        damage_data_roi = np.array(DAMAGE_DATA_ROI) - np.array(roi_diff)

                        analyze_anna_icon_frame(work_frame, CHARACTER_ICON_ROI, characters_find)

                else:
                    if time_min is "1":
                        time_min = analyze_timer_frame(work_frame, min_roi, 2, time_min)

                    time_sec10 = analyze_timer_frame(work_frame, tensec_roi, 6, time_sec10)
                    time_sec1 = analyze_timer_frame(work_frame, onesec_roi, 10, time_sec1)

                    ub_result = analyze_ub_frame(work_frame, ub_roi, time_min, time_sec10, time_sec1,
                                                 ub_data, ub_data_value, characters_find)

                    if ub_result is FOUND:
                        ub_interval = i
                        print(ub_data[-1])

                    # スコア表示の有無を確認
                    ret = analyze_score_frame(work_frame, SCORE_DATA, score_roi)

                    if ret is True:
                        # 総ダメージ解析
                        ret = analyze_damage_frame(original_frame, damage_data_roi, tmp_damage)

                        if ret is True:
                            print("総ダメージ " + ''.join(tmp_damage))

                        break

video.release()

time_result = tm.time() - start_time
print("動画時間 : {:.3f}".format(frame_count / frame_rate) + "  sec")
print("処理時間 : {:.3f}".format(time_result) + "  sec")
