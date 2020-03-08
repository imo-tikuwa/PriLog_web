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
import prkn_app_functions as appf


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
    video_type = appf.FRAME_RESOLUTION.index((frame_width, frame_height))
except ValueError:
    video.release()
    clear_path(movie_path)

    print(appf.ERROR_NOT_SUPPORTED)
    sys.exit(1)

appf.model_init(video_type)
appf.roi_init(video_type)

n = 0.34  # n秒ごと*
ub_interval = 0

time_min = "1"
time_sec10 = "3"
time_sec1 = "0"

menu_check = False

min_roi = appf.MIN_ROI
tensec_roi = appf.TEN_SEC_ROI
onesec_roi = appf.ONE_SEC_ROI
ub_roi = appf.UB_ROI
score_roi = appf.SCORE_ROI
damage_data_roi = appf.DAMAGE_DATA_ROI

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
                work_frame = appf.edit_frame(original_frame)

                if menu_check is False:
                    menu_check, menu_loc = appf.analyze_menu_frame(work_frame, appf.MENU_DATA, appf.MENU_ROI)
                    if menu_check is True:
                        loc_diff = np.array(appf.MENU_LOC) - np.array(menu_loc)
                        roi_diff = (loc_diff[0], loc_diff[1], loc_diff[0], loc_diff[1])
                        min_roi = np.array(appf.MIN_ROI) - np.array(roi_diff)
                        tensec_roi = np.array(appf.TEN_SEC_ROI) - np.array(roi_diff)
                        onesec_roi = np.array(appf.ONE_SEC_ROI) - np.array(roi_diff)
                        ub_roi = np.array(appf.UB_ROI) - np.array(roi_diff)
                        score_roi = np.array(appf.SCORE_ROI) - np.array(roi_diff)
                        damage_data_roi = np.array(appf.DAMAGE_DATA_ROI) - np.array(roi_diff)

                        appf.analyze_anna_icon_frame(work_frame, appf.CHARACTER_ICON_ROI, characters_find)

                else:
                    if time_min is "1":
                        time_min = appf.analyze_timer_frame(work_frame, min_roi, 2, time_min)

                    time_sec10 = appf.analyze_timer_frame(work_frame, tensec_roi, 6, time_sec10)
                    time_sec1 = appf.analyze_timer_frame(work_frame, onesec_roi, 10, time_sec1)

                    ub_result = appf.analyze_ub_frame(work_frame, ub_roi, time_min, time_sec10, time_sec1,
                                                 ub_data, ub_data_value, characters_find)

                    if ub_result is appf.FOUND:
                        ub_interval = i
                        print(ub_data[-1])

                    # スコア表示の有無を確認
                    ret = appf.analyze_score_frame(work_frame, appf.SCORE_DATA, score_roi)

                    if ret is True:
                        # 総ダメージ解析
                        ret = appf.analyze_damage_frame(original_frame, damage_data_roi, tmp_damage)

                        if ret is True:
                            print("総ダメージ " + ''.join(tmp_damage))

                        break

video.release()

time_result = tm.time() - start_time
print("動画時間 : {:.3f}".format(frame_count / frame_rate) + "  sec")
print("処理時間 : {:.3f}".format(time_result) + "  sec")
