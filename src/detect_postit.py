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
# import urllib.request
import requests
import os
import json

DB_URL = 'http://3.112.132.206/api/v1/dummy/labelwork'
HEADERS = {
	'Content-Type':'application/json'
}
PROXY = {
	"http":"http://g3.konicaminolta.jp:8080"
}

register_labels = []
img_x_size = 0
img_y_size = 0


class LabelDetector():

	def	__init__(self,
				 db_url=None,
				 db_header=None,
				 proxy=None):
		self._db_url=db_url
		self._db_header=db_header
		self._proxy=proxy
		self._register_labels=[]
		self._image_size_x=0
		self._image_size_y=0
		self._image_path=None

	def detect(self,image_path):
		im = cv2.imread(image_path, 1)
		im_rs = cv2.resize(im,(int(im.shape[1]/4),int(im.shape[0]/4)))

		im_gray = cv2.cvtColor(im,cv2.COLOR_RGBA2GRAY)
		img_y_size,img_x_size = im_gray.shape

		brcode = decode(im_gray)

		for i in range(len(brcode)):
			leftup = (int(brcode[i].polygon[1].x/4),int(brcode[i].polygon[1].y/4))
			rightdown = (int(brcode[i].polygon[3].x/4), int(brcode[i].polygon[3].y/4))
			qr_x = int((leftup[0] + rightdown[0])/2)
			qr_y = int((leftup[1] + rightdown[1])/2)
			qr_cen.append((qr_x,qr_y))
			self._set_workData( brcode[i].data.decode('UTF-8'), qr_x, qr_y )

			im_cntrL = cv2.rectangle(im_cntrL,leftup,rightdown,(0,0,255),thickness=3)        
			im_cntrL = cv2.circle(im_cntrL,(qr_x,qr_y),4,(0,0,255),-1)            # 重心の追加

		
		rslt = self._regist_work(image_path)
		print(rslt.status_code)
		print(rslt.text)

		# 結果表示
		cv2.namedWindow('Result')
		cv2.imshow("Result",im_cntrL)

		while(1):
			key = cv2.waitKey(1)
			if key & 0xFF == ord('q'):

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


	def _regist_work(img_path):
		global DB_URL
		global HEADERS
		global PROXY
		global register_labels
		# img_name = os.path.basename(img_path)
		img_name = "debug_image_v1.png"
		data={
			'photoname':img_name,
			'labels':register_labels
		}

		response = requests.post(DB_URL,data=json.dumps(data),headers=HEADERS,proxies=PROXY)

		return response

#################################################
##
#################################################
def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
	# 左クリック押下
        # b,g,r = param[y][x]
        # br = int(b)-int(r)
        # gr = int(g)-int(r)
        # if (br>20) and (gr>20):
        #         test = 0
        # else:
        #         test = 1

        print(param[y][x])

#################################################
##
#################################################
def thr_rgb(img):
    height,width = img.shape[:2]
#     rslt_img = np.ones((height,width),cv2.THRESH_BINARY_INV)*0
    rslt_img = np.empty((height,width),dtype=np.uint8)    # グレー/2値の空画像の生成
    for i in range(height):
        for j in range(width):
                # b,g,r = img[i][j]
                # itemメソッドを使った方が処理時間が早い
                b = img.item(i,j,0)
                g = img.item(i,j,1)
                r = img.item(i,j,2)
                br = int(b)-int(r)
                gr = int(g)-int(r)
                bg = int(b)-int(g)
                if (br<-60) and (gr<-60):
                        # QR_MID1.JPG # marker
                        rslt_img.itemset((i,j),255)
                # if (br>-12) and (gr>15):
                #         # QR_S_1.JPG # green
                #         rslt_img.itemset((i,j),255)
                # if (br>20) and (gr>20):
                #         # sample3.JPG # yellow
                #         rslt_img.itemset((i,j),255)
                # elif (br<-30) and (bg<-20):
                #         # sample3.JPG # blue
                #         rslt_img.itemset((i,j),255)
                # elif (br<-20) and (gr<-20):
                #         # sample3.JPG # pink
                #         rslt_img.itemset((i,j),255)
                # elif (br<-15) and (gr<-15):
                #         # QR_S_1.JPG # pink
                #         rslt_img.itemset((i,j),255)
                else:
                        rslt_img.itemset((i,j),0)

    return rslt_img

#################################################
##
#################################################
def getRectByPoints(points):
    # prepare simple array 
    points = list(map(lambda x: x[0], points))

    points = sorted(points, key=lambda x:x[1])
    top_points = sorted(points[:2], key=lambda x:x[0])
    bottom_points = sorted(points[2:4], key=lambda x:x[0])
    points = top_points + bottom_points

    left = min(points[0][0], points[2][0])
    right = max(points[1][0], points[3][0])
    top = min(points[0][1], points[1][1])
    bottom = max(points[2][1], points[3][1])
    return (top, bottom, left, right)

#################################################
##
#################################################
def getPartImageByRect(rect, img):
    return img[rect[0]*4:rect[1]*4, rect[2]*4:rect[3]*4]


#################################################
## メイン関数
#################################################
def detectPostIt(image_path):
	global img_y_size
	global img_x_size

	# 画像の読み込み
	im = cv2.imread(image_path, 1)
	im_rs = cv2.resize(im,(int(im.shape[1]/4),int(im.shape[0]/4)))

	im_gray = cv2.cvtColor(im,cv2.COLOR_RGBA2GRAY)
	img_y_size,img_x_size = im_gray.shape

	# バーコード読取
	brcode = decode(im_gray)
	# brcode = decode(im)

	# 画像の2値化（オリジナル）
	start = time.time()
	ret = thr_rgb(im_rs)
	elapsed_time = time.time() - start
	print("elapsed time:{0}".format(elapsed_time) + "[sec]")
	# 輪郭抽出
	contours = cv2.findContours(ret, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
	im_cntr = im_rs.copy()
	im_cntr = cv2.drawContours(im_cntr, contours, -1, (0,255,0), 3)
	# 輪郭の周囲長が画像の1/50以上なら磁石とする
	th_area = im_rs.shape[0] * im_rs.shape[1] / 1000
	contours_large = list(filter(lambda c:cv2.contourArea(c) > th_area, contours))

	# 輪郭から元の画像から切り抜く（ポストイットを画像で保存）
	# outputs = []
	# rects = []
	# approxes = []
	# for (i,cnt) in enumerate(contours_large):
	#     arclen = cv2.arcLength(cnt, True)                   # 周囲長の取得
	#     approx = cv2.approxPolyDP(cnt, 0.02*arclen, True)   # 輪郭の近似
	#     if len(approx) < 4:
	#         continue
	#     approxes.append(approx)
	#     rect = getRectByPoints(approx)                      # 輪郭から4点のみを抽出
	#     rects.append(rect)
	#     output = getPartImageByRect(rect,im)
	#     outputs.append(output)
	#     cv2.imwrite('./out/output'+str(i)+'.jpg', output)

	im_cntrL = im_rs.copy()
	im_cntrL = cv2.drawContours(im_cntrL, contours_large, -1, (0,255,0), 3)

	# 重心を求める
	# mu = cv2.moments(contours_large[0])
	# mkr_x,mkr_y= int(mu["m10"]/mu["m00"]) , int(mu["m01"]/mu["m00"]) # マーカーの重心
	# im_cntrL = cv2.circle(im_cntrL,(mkr_x,mkr_y),4,(0,0,255),-1) # 重心の表示

	# QRコード検出結果の表示
	output_csv = []
	qr_cen = []
	for i in range(len(brcode)):
			leftup = (int(brcode[i].polygon[1].x/4),int(brcode[i].polygon[1].y/4))
			rightdown = (int(brcode[i].polygon[3].x/4), int(brcode[i].polygon[3].y/4))
			qr_x = int((leftup[0] + rightdown[0])/2)
			qr_y = int((leftup[1] + rightdown[1])/2)
			qr_cen.append((qr_x,qr_y))
			set_workData( brcode[i].data.decode('UTF-8'), qr_x, qr_y )

			# import pdb;pdb.set_trace() # debug

			im_cntrL = cv2.rectangle(im_cntrL,leftup,rightdown,(0,0,255),thickness=3)        
			im_cntrL = cv2.circle(im_cntrL,(qr_x,qr_y),4,(0,0,255),-1)            # 重心の追加
			# im_cntrL = cv2.line(im_cntrL,(mkr_x,mkr_y),(qr_x,qr_y),(0,0,255),1)   # 直線の追加

			# CSV出力用に保存
			# rel_x = qr_x - mkr_x
			# rel_y = qr_y - mkr_y
			# output_csv.append( (rel_x,rel_y,brcode[i].data.decode('UTF-8')) )

	# 結果表示
	cv2.namedWindow('Result')
	cv2.setMouseCallback('Result',mouse_event,im_rs)
	# cv2.imshow("Original",im_rs)
	# cv2.imshow("Threshold",ret)
	# cv2.imshow("countours",im_cntr)
	cv2.imshow("Result",im_cntrL)

	# CSV出力
	# with open(r'\\150.17.244.201\msk\XY_Data\xy_data.csv','w') as f:
	# 		writer = csv.writer(f,lineterminator='\n')
	# 		writer.writerows(output_csv)

	rslt = regist_work(image_path)
	print(rslt.status_code)
	print(rslt.text)

	while(1):
			key = cv2.waitKey(1)
			if key & 0xFF == ord('q'):
					break

	# 2値化（部分に応じて適応的に閾値を決定する）　第5引数：閾値の決定に用いる範囲、第6引数：決まった閾値から引く値
	# th2 = cv2.adaptiveThreshold(im_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 3)

if __name__ == '__main__':
        # img_path = './image/20190716/IMG_1972.JPG'
        img_path = '../image/DSC07007_35.JPG'

        detectPostIt(img_path)