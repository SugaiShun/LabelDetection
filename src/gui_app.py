########################################################################
#!/usr/bin/env python3
# coding: utf-8
# モジュール名：GUI設定
# 説明：アプリケーションのGUIを設定し、入力を受け付ける
########################################################################
# 訂符          名前       日付         説明
########################################################################
# @2019/09/10    S.Sugai     初版
########################################################################
import tkinter as tk
import sys
import datetime
import re
import detect_postit

push_flag = False

root = tk.Tk()
root.geometry("400x500")
root.title("PostIt Detecter(MSK) v2.0")

lable1 = tk.Label(text=u'画像URL')
lable1.pack(anchor=tk.W,padx=5)

TextBox1 = tk.Entry(width=50)
TextBox1.insert(tk.END,"")
TextBox1.pack(anchor=tk.W,padx=5,pady=5)

button = tk.Button(root,text="検出開始",command=lambda:pushed(button))
button.pack(anchor=tk.W,padx=5,pady=5)


def pushed(self):
    global push_flag

    if push_flag:
        push_flag=False
    else:
        push_flag=True

    image_path = TextBox1.get()

    detect_postit.detectPostIt(image_path)

def app_postIt():
    global root

    root.mainloop()

if __name__ == '__main__':
    app_postIt()