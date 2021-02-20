##################################################
# ポストイット検出プログラム
##################################################
# 
##################################################

import cv2
import numpy as np
import time
from pyzbar.pyzbar import decode
import csv
import sys

class QRcode:
    def __init__(self,info,x,y):
        self.info = info
        self.x = x
        self.y = y

#################################################
## メイン関数
#################################################
def detectPostIt(image_path):
    window_name = 'frame'
    cap = cv2.VideoCapture(image_path)
    if not cap.isOpened():
        sys.exit()
    
    qr_memory = []
    output_csv = []
    base_qrId = []

    while True:
        ret, frame = cap.read() # 動画のキャプチャ

        if ret:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

        # 90°回転
        frame_rt = cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
        # グレースケール化
        frame_gray = cv2.cvtColor(frame_rt,cv2.COLOR_RGBA2GRAY)
        # QR読取
        qrcode = decode(frame_gray)
        # ベースQR読取チェック
        baseInitChk = False
        if len(base_qrId) == 0:
            baseInitChk = True
        
        im_rs = cv2.resize(frame_rt,(int(frame_rt.shape[1]/4),int(frame_rt.shape[0]/4)))

        base_id_memory = 0
        base_x = 0
        base_y = 0
        new_qrs = []
        baseChk = False
        for i in range(len(qrcode)):
            info = qrcode[i].data.decode('UTF-8') # QR情報
            new_flag = True
            # 中心位置の計算
            leftup = (int(qrcode[i].polygon[1].x),int(qrcode[i].polygon[1].y))
            rightdown = (int(qrcode[i].polygon[3].x), int(qrcode[i].polygon[3].y))
            qr_x = int((leftup[0] + rightdown[0])/2) # QR中心 X座標
            qr_y = int((leftup[1] + rightdown[1])/2) # QR中心 Y座標
            for j in range(len(qr_memory)):
            # メモリを探索
                if qr_memory[j].info == info:
                    baseChk = True
                    new_flag = False
                    base_id_memory = j
                    base_x = qr_x
                    base_y = qr_y
                    break
            if new_flag:
                qr_new = QRcode(info,qr_x,qr_y)
                new_qrs.append(qr_new)
            
            draw_color = (0,0,255)
            im_rs = cv2.rectangle(im_rs,(int(leftup[0]/4),int(leftup[1]/4)),(int(rightdown[0]/4),int(rightdown[1]/4)),draw_color,thickness=3)        
            im_rs = cv2.circle(im_rs,(int(qr_x/4),int(qr_y/4)),4,draw_color,-1)

        for new_qr in new_qrs:
            if baseInitChk:
                qr_new = QRcode(new_qr.info,new_qr.x,new_qr.y)
                # 座標計算のベースとなるQRコードをメモリ
                base_qrId.append(new_qr.info)
                # メモリに保存
                qr_memory.append(qr_new)
                print("base:")
                print(new_qr.info)
                output_csv.append( (qr_new.x,qr_new.y,qr_new.info) )

            if baseChk:
                qr_new_x = qr_memory[base_id_memory].x + ( new_qr.x - base_x )
                qr_new_y = qr_memory[base_id_memory].y + ( new_qr.y - base_y )
                qr_new = QRcode(new_qr.info,qr_new_x,qr_new_y)
                # メモリに保存
                qr_memory.append(qr_new)
                print("memory:")
                print(qr_memory[base_id_memory].info)
                print("base:")
                print(base_x)
                print(base_y)
                print("now:")
                print(new_qr.x)
                print(new_qr.y)
                output_csv.append( (qr_new.x,qr_new.y,new_qr.info) )

        cv2.imshow(window_name,im_rs)

        
    # CSV出力
    with open(r'xy_data.csv','w') as f:
            writer = csv.writer(f,lineterminator='\n')
            writer.writerows(output_csv)
    cv2.destroyWindow(window_name)


if __name__ == '__main__':
    # img_path = './image/20190716/IMG_1972.JPG'
    # img_path = '../image/0910_3.jpg'
    img_path = '../image/movie2.MOV'
    detectPostIt(img_path)