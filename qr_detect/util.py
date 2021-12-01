
import re
import numpy as np
import cv2


class CorrectColorError(Exception):
    def __str__(self) -> str:
        return "颜色矫正出错，出现了认为不可能出现的情况"

def BGR2Hex(color: tuple):
    B, G, R = color
    B = str(hex(B))[-2:].replace('x', '0').upper()
    G = str(hex(G))[-2:].replace('x', '0').upper()
    R = str(hex(R))[-2:].replace('x', '0').upper()

    return f"#{R}{G}{B}"


def correct_color(color):
    B, G, R = color
    if B > G > R:
        B = 255
        G = (G//5)*5+2
        R = 0
    elif R > G > B:
        R = 255
        G = (G//5)*5+2
        B = 0
    elif G > R > B:
        G = 255
        R = (R//5)*5+2
        B = 0
    elif G > B > R:
        G = 255
        B = (B//5)*5+2
        R = 0
    elif B > R > G:
        B = 255
        R = (R//5)*5+2
        G = 0
    elif R > B > G:
        R = 255
        B = (B//5)*5+2
        G = 0
    else:
        raise CorrectColorError()

    return BGR2Hex((B, G, R))


def a_where_is_b(a, b):
    """a:(x,y,w,h) -> 探索到的新框 b:(x,y,w,h) -> 已经检测到的框 """
    if (a[0] + a[1]) <= (b[0]+b[1]) and sum(a) >= sum(b):
        # 情况一 b在a中
        return 0, b
    elif (a[0] + a[1]) >= (b[0]+b[1]) and sum(a) <= sum(b):
        # 情况一 a在b中
        return 0, a
    elif (a[0]+a[2] < b[0]) or (a[0] > b[0]+b[2]) or (a[1]+a[3] < b[1]) or (a[1] > b[1]+b[3]):
        # a 与 b不相交
        return 1, a
    else:
        # a与b 相交但不包含
        
        return 2, a if a[2]*a[3]>b[2]*b[3] else b


def overlap(box1, box2):
    # 判断两个矩形是否相交
    # 思路来源于:https://www.cnblogs.com/avril/archive/2013/04/01/2993875.html
    # 然后把思路写成了代码
    minx1, miny1, maxx1, maxy1 = box1
    minx2, miny2, maxx2, maxy2 = box2
    minx = max(minx1, minx2)
    miny = max(miny1, miny2)
    maxx = min(maxx1, maxx2)
    maxy = min(maxy1, maxy2)
    if minx > maxx or miny > maxy:
        return False
    else:
        return True

def a_b_intersect_s(a,b):
    """a:(x,y,w,h) b:(x,y,w,h)   计算a,b box相交的面积"""
    x1,y1,x2,y2 = (a[0],a[1],a[0]+a[2],a[1]+a[3])
    x1,x2 = min(x1,x2),max(x1,x2)
    y1,y2= min(y1,y2),max(y1,y2)

    x3,y3,x4,y4 = (b[0],b[1],b[0]+b[2],b[1]+b[3])
    x3,x4 = min(x3,x4),max(x3,x4)
    y3,y4 = min(y3,y4),max(y3,y4)


    if (x2<=x3 or x4<=x1) and (y2 <= y3 or y4<=y1):
        return 0
    else:
        lens = min(x2, x4) - max(x1, x3)
        wide = min(y2, y4) - max(y1, y3)
        return lens*wide

def sort_point_bycos(circle_list: list):
    """根据点的 cos值，给点排序，cos值越小，角度越大"""
    point_pair = [(0, 1, 2), (1, 0, 2), (2, 0, 1)]
    circle_list_np = np.array(circle_list).astype(np.float32)
    cos_list = [getcos(circle_list_np[i], circle_list_np[j],
                       circle_list_np[k]) for i, j, k in point_pair]
    id_list = np.argsort(cos_list)
    return [circle_list[i] for i in id_list]


def getcos(p1, p2, p3):
    a = p2-p1
    b = p3-p1
    num = np.sum(np.multiply(a, b))
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return num / denom

def getContours(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(
        edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def getHorizontalandVertical(src_img):
    h,w = src_img.shape
    src_img[:2,:] = 0
    src_img[-2:,:] = 0
    src_img[:,:2] = 0
    src_img[:,w-2:] = 0   
    src_img1 = cv2.bitwise_not(src_img)

    AdaptiveThreshold = cv2.adaptiveThreshold(src_img1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)

    horizontal = AdaptiveThreshold.copy()
    vertical = AdaptiveThreshold.copy()
    scale = 6

    horizontalSize = int(horizontal.shape[1] / scale)
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalSize, 1))
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)
    
    
    verticalsize = int(vertical.shape[1] / scale)
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    vertical = cv2.erode(vertical, verticalStructure, (-1, -1))
    vertical = cv2.dilate(vertical, verticalStructure, (-1, -1))
    
    return horizontal,vertical

def check_has_answer(imgpath):
    s_min = 50  # 最小轮廓面，用于过滤那些可能存在的污点，10对应大概是句号那样大小的面积。
    max_rate = 0.9  # 发现轮廓的框，w，h占到 图片w,h的百分比，比这个值大，说明可能是长直线。
    img = cv2.imread(imgpath)

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(
        binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for i in contours:
        box = cv2.boundingRect(i)
        s = cv2.contourArea(i)
        if s <= s_min:
            continue
        if box[2] / w < max_rate or box[3] / h < max_rate:
            print(box[2] / w, box[3] / h,box,w,h)
            # cv2.drawContours(img,[i],-1,(0,0,250),1)
            # cv2.imwrite(imgpath[:-4]+"_contours.jpg",img)
            return True
    # cv2.imwrite(imgpath[:-4]+"_contours.jpg",img)
    return False
    # cv2.imwrite(imgpath[:-4]+"_contours.jpg",img)

class PageNoDecoder:
    "页码解析器"
    #这些参数都是和模板的size有关
    s_pageno_s_max = 800#模版页码解析块的面积
    s_pageno_s_min = s_pageno_s_max / 8
    s_page_r = 30
    def __call__(self,page_imgcut):
        # 页码解析
        page_no_list = []
        contours = self.getContours(page_imgcut)
        
        #显示一些检测到了那些 轮廓
        # cv2.drawContours(page_imgcut,contours,-1,(0,0,255),1)
        # cv2.imshow("c",page_imgcut)
        # cv2.waitKey(0)
        for i in contours:
            # s = cv2.contourArea(i)
            x,y,w,h = cv2.boundingRect(i)
            s = w*h
            if self.s_pageno_s_min < s <= self.s_pageno_s_max:
                contours_np = np.array((int(x+w/2),int(y+h/2)))
                centre = np.around(contours_np).astype(np.int16)
                page_no_list.append(centre)
        page_no_list.sort(key=lambda item: item[0])
        #合并一下 挨着很近的的中心点
        final_page_list = []
        for point1 in page_no_list:
            if not len(final_page_list):
                final_page_list.append(point1)
            else:
                point2 = final_page_list[-1]
                if np.linalg.norm(point1-point2) > self.s_page_r:
                    final_page_list.append(point1)
        # print(final_page_list)

        if len(final_page_list) >= 8:
            final_page_list = final_page_list[:8]
            b_str = "".join(["0" if sum(page_imgcut[y, x]) > 255 *3 /2  else "1" for x, y in final_page_list])
            # print(b_str)
            return int(b_str,2)
        else:
            
            return ""

    def getContours(self,img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(
            binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours

class AnswerISWhat_ForAnswerCard:
    "用于判断涂卡的答题卡选择的答案是什么"
    has_answer_threshold = 600
    def __init__(self,test_num=5):
        self.test_num = test_num

    def __call__(self,img_cut):
        _,w = img_cut.shape[:2]
        stand_w = w // self.test_num
    
        group = {}
        answerId = -1
        max_s = -1

        for i in range(self.test_num):
            #截中截图
            img_cut_cut = img_cut[:,i*stand_w:(i+1)*stand_w,:]
            # cv2.imwrite(f"{i}.jpg",img_cut_cut)
            # contours = getContours(img_cut_cut)
            #s

            s = np.sum(img_cut_cut < 172)
            print(s)

            if not i in group:
                group[i] = s
            else:
                group[i] += s
            if group[i] >= max_s:
                answerId = i
                max_s = group[i]   
        
                          
        # 没写答案求和
        if max_s - min([group[i] for i in group]) < self.has_answer_threshold:
            print(group,"没写答案")
            return -1           
        print(group,answerId+1)
        return answerId+1  

def getWidth(x,y,w,h,img,clearV=True,e_h=10):
    '''
    失败时不要放缩，按原图裁剪
    '''
    e_h = e_h
    new_y = y
    new_h = h
    new_y -= e_h
    new_h += 2*e_h

    img_cut = img[new_y:new_y+new_h,x:x+w].copy()
    
    gray = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # edged = cv2.Canny(blur, 50, 200,None,3)
    _,edged =  cv2.threshold(blur,150,255,cv2.THRESH_BINARY_INV)
    
    #清除垂直方向
    if clearV:
        w_np = np.mean(edged,axis=0)
        for i in  np.where(w_np>150)[0]:
            y1 = max(0,i-2)
            y3 = min(len(w_np),i+2)
            edged[:,y1:y3] = 255

    x_bool = np.mean(edged,axis=1) > 0
    # x_bool = np.mean(edged,axis=1) > 20
    x_bool = [False] + list(x_bool) +[False]
    r = []
    find = True
    for i,v in enumerate(x_bool):
        if v == find:
            r.append(i-1)
            find = not find
    assert len(r) % 2 == 0
    res = {}
    for i in range(len(r) // 2):
        left = r[2*i]
        rigth = r[2*i+1]
        res[rigth-left] = (left,rigth)
    if res:
        k = max(res.keys())
        y = new_y + res[k][0]
        h = k
    return x,y,w,h

def getHeight(x,y,w,h,blank_img,clearV=True,e_h_up=10,e_h_down=10):
    '''
    失败时不要放缩，按原图裁剪
    '''
    # e_h = e_h
    new_y = y
    new_h = h
    new_y -= e_h_up
    new_h += e_h_up+e_h_down

    img_cut = blank_img
    gray = cv2.cvtColor(img_cut, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _,edged =  cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    kernel = np.ones((5, 5))
    # 先扩张 再腐蚀 平滑去噪
    edged = cv2.dilate(edged, kernel)
    edged = cv2.erode(edged, kernel)

    #清除垂直方向
    if clearV:
        w_np = np.mean(edged,axis=0)
        for i in  np.where(w_np>200)[0]:
            y1 = max(0,i-2)
            y3 = min(len(w_np),i+2)
            edged[:,y1:y3] = 255
    contours, _ = cv2.findContours(
        edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    points = []
    for c in contours:
        bx, by, bw, bh = cv2.boundingRect(c)
        if 20 <= bw <= 100:

            points.append([by, by+bh])
        elif bh > 20 :
        
            points.append([by, by+bh])
        else:
            pass
    points.sort(key=lambda item: item[0])
    if points:
        # 调整框不要贴太紧
        ep = 5
        y += points[0][0] -e_h_up - ep
        h = np.max(points) - points[0][0] +2*ep
    return x,y,w,h

def getBinary(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return binary

def get_dilationImage(img):
    # 二值化
    b1 = getBinary(img)
    #膨胀连接 
    kernel = np.ones((5,5),np.uint8)
    dilation = cv2.dilate(b1,kernel,iterations = 2)
    return dilation

if __name__ == "__main__":
    import os
    a = AnswerISWhat_ForAnswerCard(4)
    root = 'select/cut'
    for imgname in os.listdir(root):
        if imgname.endswith("contours.jpg"):
            continue
        imgpath = os.path.join(root, imgname)
        print(imgpath)
        img = cv2.imread(imgpath)
        print(a(img))
