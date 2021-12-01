import numpy as np
import cv2

"定位二维码"

def detecte(image):
    '''提取所有轮廓'''
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    _,gray=cv2.threshold(gray,0,255,cv2.THRESH_OTSU+cv2.THRESH_BINARY_INV)
    contours,hierachy=cv2.findContours(gray,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return image,contours,hierachy
def compute_1(contours,i,j):
    '''最外面的轮廓和子轮廓的比例'''
    area1 = cv2.contourArea(contours[i])
    area2 = cv2.contourArea(contours[j])
    if area2==0:
        return False
    ratio = area1 * 1.0 / area2
    if abs(ratio - 49.0 / 25):
        return True
    return False
def compute_2(contours,i,j):
    '''子轮廓和子子轮廓的比例'''
    area1 = cv2.contourArea(contours[i])
    area2 = cv2.contourArea(contours[j])
    if area2==0:
        return False
    ratio = area1 * 1.0 / area2
    if abs(ratio - 25.0 / 9):
        return True
    return False
def compute_center(contours,i):
    '''计算轮廓中心点'''
    M=cv2.moments(contours[i])
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    return cx,cy
def detect_contours(vec):
    '''判断这个轮廓和它的子轮廓以及子子轮廓的中心的间距是否足够小'''
    distance_1=np.sqrt((vec[0]-vec[2])**2+(vec[1]-vec[3])**2)
    distance_2=np.sqrt((vec[0]-vec[4])**2+(vec[1]-vec[5])**2)
    distance_3=np.sqrt((vec[2]-vec[4])**2+(vec[3]-vec[5])**2)
    if sum((distance_1,distance_2,distance_3))/3<15:
        return True
    return False
def juge_angle(rec):
    '''判断寻找是否有三个点可以围成等腰直角三角形'''
    if len(rec)<3:
        return -1,-1,-1
    for i in range(len(rec)):
        for j in range(i+1,len(rec)):
            for k in range(j+1,len(rec)):
                distance_1 = np.sqrt((rec[i][0] - rec[j][0]) ** 2 + (rec[i][1] - rec[j][1]) ** 2)
                distance_2 = np.sqrt((rec[i][0] - rec[k][0]) ** 2 + (rec[i][1] - rec[k][1]) ** 2)
                distance_3 = np.sqrt((rec[j][0] - rec[k][0]) ** 2 + (rec[j][1] - rec[k][1]) ** 2)
                if abs(distance_1-distance_2)<15:
                    if abs(np.sqrt(np.square(distance_1)+np.square(distance_2))-distance_3)<15:
                        return i,j,k
                elif abs(distance_1-distance_3)<15:
                    if abs(np.sqrt(np.square(distance_1)+np.square(distance_3))-distance_2)<15:
                        return i,j,k
                elif abs(distance_2-distance_3)<15:
                    if abs(np.sqrt(np.square(distance_2)+np.square(distance_3))-distance_1)<15:
                        return i,j,k
    return -1,-1,-1
def find_QR_position(image,contours,hierachy,root=0):
    '''找到符合要求的轮廓'''
    rec=[]
    for i in range(len(hierachy)):
        child = hierachy[i][2]
        child_child=hierachy[child][2]
        if child!=-1 and hierachy[child][2]!=-1:
            if compute_1(contours, i, child) and compute_2(contours,child,child_child):
                cx1,cy1=compute_center(contours,i)
                cx2,cy2=compute_center(contours,child)
                cx3,cy3=compute_center(contours,child_child)
                if detect_contours([cx1,cy1,cx2,cy2,cx3,cy3]):
                    rec.append([cx1,cy1,cx2,cy2,cx3,cy3,i,child,child_child])
    '''计算得到所有在比例上符合要求的轮廓中心点'''
    i,j,k=juge_angle(rec)
    res=[]
    while(i!=-1 and j!=-1 and k!=-1):
        ts = np.concatenate((contours[rec[i][6]], contours[rec[j][6]], contours[rec[k][6]]))
        rect = cv2.minAreaRect(ts)
        box = cv2.boxPoints(rect)
        #print(rect)
        box = np.int0(box)
        #print(box)
        # 获取四个顶点坐标
        left_point_x = np.min(box[:, 0])
        right_point_x = np.max(box[:, 0])
        top_point_y = np.min(box[:, 1])
        bottom_point_y = np.max(box[:, 1])
        res.append([left_point_x,top_point_y,right_point_x-left_point_x,bottom_point_y-top_point_y])
        #更新
        rec.pop(i)
        rec.pop(j-1)
        rec.pop(k-2)
        i,j,k=juge_angle(rec)
    return res
    
if __name__ == '__main__':

    image = cv2.imread(r'questionnaire/questionnaire3_sanc1_correct.jpg')
    image, contours, hierachy = detecte(image)
    res = find_QR_position(image, contours, np.squeeze(hierachy))
    print(res)