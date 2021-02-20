import cv2
import numpy as np
import time
from pyzbar.pyzbar import decode
import csv
import requests
import os
import json
import math

DB_URL = 'your url'
HEADERS = {
'Content-Type':'application/json'
}
PROXY = {
"your proxy"
}

def _transRotation(src,radian):
    rotation_matrix=np.matrix([
        [math.cos(radian),math.sin(radian)],
        [-math.sin(radian),math.cos(radian)]
    ])
    dst = np.dot(rotation_matrix,src)
    return dst

def transRotation(ori,src,radian):
    dst_origin = _transRotation(src,radian)
    return ori + dst_origin

def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        print(y,x)
        # print(param[y][x])

class LabelDetector():

    def	__init__(self,db_url=None,db_header=None,proxy=None):
        self._db_url=db_url
        self._db_header=db_header
        self._proxy=proxy
        self._register_labels=[]
        self._register_positions=[]
        self._image_size_x=0
        self._image_size_y=0
        self._image_path=None

        self._label_size_x=150*4
        self._label_size_y=90*4

    def detect(self,image_path):
        im = cv2.imread(image_path, 1)
        im_rs = cv2.resize(im,(int(im.shape[1]/4),int(im.shape[0]/4)))
        im_gray = cv2.cvtColor(im,cv2.COLOR_RGBA2GRAY)

        self._image_size_y,self._image_size_x = im_gray.shape
        brcode = decode(im_gray)

        qr_cen = []
        im_cntrL = im_rs.copy()
        for i in range(len(brcode)):
            leftup = (int(brcode[i].polygon[3].x/4),int(brcode[i].polygon[3].y/4))
            rightdown = (int(brcode[i].polygon[1].x/4), int(brcode[i].polygon[1].y/4))
            qr_x = int((leftup[0] + rightdown[0])/2)
            qr_y = int((leftup[1] + rightdown[1])/2)
            qr_cen.append((qr_x,qr_y))

            self._set_workData( brcode[i].data.decode('UTF-8'), qr_x, qr_y )

            qr0 = (brcode[i].polygon[0].x, brcode[i].polygon[0].y)
            qr1 = (brcode[i].polygon[1].x, brcode[i].polygon[1].y)
            qr2 = (brcode[i].polygon[2].x, brcode[i].polygon[2].y)
            qr3 = (brcode[i].polygon[3].x, brcode[i].polygon[3].y)
            qr_lu,qr_ru = self._sort_fixType([qr0,qr1,qr2,qr3])
            label_lu,label_ru,label_ld,label_rd = self._set_workData_labelposition( qr_lu, qr_ru )

            im_cntrL = cv2.circle(im_cntrL,qr_lu,4,(255,0,0),-1)
            im_cntrL = cv2.circle(im_cntrL,qr_ru,4,(0,255,0),-1)

            im_cntrL = cv2.circle(im_cntrL,(qr_x,qr_y),4,(0,0,255),-1)
            im_cntrL = cv2.line(im_cntrL,(int(label_lu[0]/4),int(label_lu[1]/4)),(int(label_ru[0]/4),int(label_ru[1]/4)),(0,0,255),4,lineType=cv2.LINE_4)
            im_cntrL = cv2.line(im_cntrL,(int(label_lu[0]/4),int(label_lu[1]/4)),(int(label_ld[0]/4),int(label_ld[1]/4)),(0,0,255),4,lineType=cv2.LINE_4)
            im_cntrL = cv2.line(im_cntrL,(int(label_ld[0]/4),int(label_ld[1]/4)),(int(label_rd[0]/4),int(label_rd[1]/4)),(0,0,255),4,lineType=cv2.LINE_4)
            im_cntrL = cv2.line(im_cntrL,(int(label_ru[0]/4),int(label_ru[1]/4)),(int(label_rd[0]/4),int(label_rd[1]/4)),(0,0,255),4,lineType=cv2.LINE_4)

        res,rslt = self._regist_work(image_path)
        cv2.namedWindow('Result')
        cv2.setMouseCallback('Result',mouse_event,im_rs)
        cv2.imshow("Result",im_cntrL)

        while(1):
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break

        return rslt

    def _sort_fixType(self,qr_points):
        dis = [(qr_points[0][0] + qr_points[0][1]),
                (qr_points[1][0] + qr_points[1][1]),
                (qr_points[2][0] + qr_points[2][1]),
                (qr_points[3][0] + qr_points[3][1])]
        min_val = min(dis)
        min_index = dis.index(min_val)
        qr0 = qr_points.pop(min_index)

        dis_qr0 = [ math.sqrt((qr0[1] - i[1])**2) for i in qr_points ]
        min_qr0_dis = min(dis_qr0)
        min_qr0_index = dis_qr0.index(min_qr0_dis)
        qr1 = qr_points[min_qr0_index]

        return qr0,qr1

    def _set_workData(self,qr_name,x_position,y_position):
        label_x_posi, label_y_posi = self._cal_label_position(x_position,y_position)

        qr_data = [ i.strip() for i in qr_name.split(',') if not i.strip() == '']
        qr_id = int(qr_data[0])

        label_data={
            'article_id':qr_id,
            'xcoord':label_x_posi,
            'ycoord':label_y_posi
        }
        self._register_labels.append(label_data)

    def _cal_label_position(self,x_position,y_position):
        x_posi = x_position/self._image_size_x
        y_posi = y_position/self._image_size_y
        return x_posi, y_posi


    def _set_workData_labelposition(self, qr_leftup, qr_rightup):
        delta_x = qr_rightup[0] - qr_leftup[0]
        delta_y = qr_rightup[1] - qr_leftup[1]
        radian = math.atan2(delta_y,delta_x)

        leftup_np = np.array((qr_leftup[1],qr_leftup[0]))

        base_rightup_np = np.array((0,self._label_size_x))
        rightup_np = transRotation(leftup_np,base_rightup_np,radian)
        rightup = rightup_np.tolist()[0]
        rightup.reverse()

        base_leftdown_np = np.array((self._label_size_y,0))
        leftdown_np = transRotation(leftup_np,base_leftdown_np,radian)
        leftdown = leftdown_np.tolist()[0]
        leftdown.reverse()

        base_rightdown_np = np.array((self._label_size_y,self._label_size_x))
        rightdown_np = transRotation(leftup_np,base_rightdown_np,radian)
        rightdown = rightdown_np.tolist()[0]
        rightdown.reverse()

        # label_data_raw={
        #     'leftup_x':leftup[0],
        #     'leftup_y':leftup[1],
        #     'rightup_x':,
        #     'rightup_y':,
        #     'leftdown_x':,
        #     'leftdwon_y':,
        #     'rightdown_x':,
        #     'rightdown_y':
        # }
        # self._register_positions.append(label_data_raw)

        return qr_leftup,rightup,leftdown,rightdown


    def _regist_work(self,img_path):
        img_name = os.path.basename(img_path)
        # img_name = "debug_image_v3.png"
        data={
            'photoname':img_name,
            'labels':register_labels
        }

        try:
            response = requests.post(self._db_url,data=json.dumps(data),headers=self._db_header,proxies=self._proxy)
            rslt = True
            print(response.status_code)
            print(response.text)
        except Exception as e:
            print("Connection Error")
            print(e)
            response = None
            rslt = False

        return response,rslt

if __name__ == '__main__':

    detecter = LabelDetector(DB_URL,HEADERS,PROXY)
    # img_path = './image/20190716/IMG_1972.JPG'
    # img_path = '../image/DSC07007_35.JPG'
    img_path = './image/DSC07007_35.JPG'
    rslt = detecter.detect(img_path)
