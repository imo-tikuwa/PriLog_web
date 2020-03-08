# -*- coding: utf-8 -*-
import numpy as np
import os
import re
import click
import time as tm
import cv2
import characters as cd
import after_caluculation as ac
import prkn_app_functions as appf
import subprocess
import win32gui
import ctypes
from PIL import ImageGrab

def output_result(ub_data, ub_data_value, characters_find):
    # 結果を出力
    debuff_value = ac.make_ub_value_list(ub_data_value, characters_find)

    # 結果表示
    print("---------- タイムライン ----------\n")
    for index, rec in enumerate(ub_data):
        print(rec)
        if debuff_value is not []:
            print("↓" + debuff_value[index])

    return


def main():

    # プリコネ起動→ウィンドウのハンドル取得→画面取得
    prkn_handle = win32gui.FindWindow(None, "PrincessConnectReDive")
    if prkn_handle <= 0:
        subprocess.Popen('start dmmgameplayer://priconner/cl/general/priconner', shell=True)
        tm.sleep(10) # 起動にこれくらいかかるのでとりあえず待つ

    # ウィンドウ名でハンドル取得
    while(True):
        prkn_handle = win32gui.FindWindow(None, "PrincessConnectReDive")
        if prkn_handle > 0:
            break

        print("プリコネが起動してないよー")
        tm.sleep(3)

    print("プリコネが起動してるよー")
    frame_rate = 30

    video_type = appf.RESOLUTION_16_9
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

    try:
        while(True):
            tm.sleep(n)

            rect_left,rect_top,rect_right,rect_bottom = win32gui.GetWindowRect(prkn_handle)

            # 微妙に外枠がとれちゃうので1280x720の位置補正
            cap_left = rect_left + 8
            cap_top = rect_top + 32
            cap_right = cap_left + 1280
            cap_bottom = cap_top + 720

            # 指定した領域内をクリッピング
            img = ImageGrab.grab(bbox=(cap_left,cap_top,cap_right,cap_bottom))
            frame = np.array(img) # video.read()と同等のデータ取得

            work_frame = appf.edit_frame(frame)

            if menu_check is False:
                menu_check, menu_loc = appf.analyze_menu_frame(work_frame, appf.MENU_DATA, appf.MENU_ROI)
                if menu_check is True:
                    print("画面右上のMENUが見つかったよー。\nTLの記録を開始するよー")
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
                if time_min == "1":
                    time_min = appf.analyze_timer_frame(work_frame, min_roi, 2, time_min)

                time_sec10 = appf.analyze_timer_frame(work_frame, tensec_roi, 6, time_sec10)
                time_sec1 = appf.analyze_timer_frame(work_frame, onesec_roi, 10, time_sec1)

                ub_result = appf.analyze_ub_frame(work_frame, ub_roi, time_min, time_sec10, time_sec1,
                                             ub_data, ub_data_value, characters_find)

                if ub_result is appf.FOUND:
                    tm.sleep(1.66) # 50フレーム(秒)

                # スコア表示の有無を確認(クラバト)
                ret = appf.analyze_score_frame(work_frame, appf.SCORE_DATA, score_roi)

                if ret is True:
                    # 総ダメージ解析
                    ret = appf.analyze_damage_frame(original_frame, damage_data_roi, tmp_damage)

                    if ret is True:
                        total_damage = "総ダメージ " + ''.join(tmp_damage)

                    break

        output_result(ub_data, ub_data_value, characters_find)

    except KeyboardInterrupt:
        output_result(ub_data, ub_data_value, characters_find)
        exit(0)


if __name__ == '__main__':
    main()

