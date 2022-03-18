from PIL import Image
import os
 
 
def rea(path, pdf_name):

    ## change all png into jpg & delete the .png files
    names=os.listdir(path)
    for name in names:
        img=Image.open(path+'/'+name)
        name=name.split(".")
        if name[-1] == "png":
            name[-1] = "jpg"
            name_jpg = str.join(".", name)
            r,g,b,a=img.split()              
            img=Image.merge("RGB",(r,g,b))   
            to_save_path = path + '/'+name_jpg
            img.save(to_save_path)
            os.remove(path+'/'+name[0]+'.png')
        else:
            continue

    ## add jpg and jpeg to     
    file_list = os.listdir(path)
    
    pic_name = []
    im_list = []
    for x in file_list:
        if "jpg" in x or 'jpeg' in x:
            pic_name.append(x)

    pic_name.sort()  #sorted
    new_pic = []
 
    for x in pic_name:
        if "jpg" in x:
            new_pic.append(x)
 
 
    im1 = Image.open(os.path.join(path, new_pic[0]))
    new_pic.pop(0)
    for i in new_pic:
        img = Image.open(os.path.join(path, i))
        # im_list.append(Image.open(i))
        if img.mode == "RGBA":
            r,g,b,a=img.split()
            img=Image.merge("RGB",(r,g,b))
            img = img.convert('RGB')
            im_list.append(img)
        else:
            im_list.append(img)
    
    im1.save(pdf_name, "PDF", resolution=100.0, save_all=True, append_images=im_list)
    print("输出文件名称：", pdf_name)
 
 
if __name__ == '__main__':
     # input the name for pdf like xxx.pdf
    pdf_name = 'image2pdf.pdf'
    mypath='./pic'
    if ".pdf" in pdf_name:
        rea(mypath, pdf_name=pdf_name)
    else:
        rea(mypath, pdf_name="{}.pdf".format(pdf_name))