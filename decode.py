#!usr/bin/env python
import Image
import math

base_image = Image.open("test_picture.jpg")
max_count = base_image.size[0] * base_image.size[1]/64/64
x = 0
y = 0
z = 64
k = 64
number = 0
size_of_table = int(math.sqrt(max_count))
plaintext = ""
ls_in_hex = ""

list_name = ['_phys_1.jpg', '_class_2.jpg' , '_class_2b.jpg' , '_resist_4.jpg' , '_class_3a.jpg' , '_feral_4a.jpg' ,'_feral_5.jpg' , '_feral_6.jpg' , '_hand_1.jpg' , '_hand_5.jpg' , '_nature_4.jpg' , '_nature_6.jpg' , '_nature_7.jpg' , '_orb_1.jpg' , '_orb_4.jpg' , '_feral_2.jpg']

wordindex = {'_phys_1.jpg' : '0' ,'_class_2.jpg' : '1' ,'_class_2b.jpg' : '2' ,'_resist_4.jpg' : '3' ,'_class_3a.jpg' : '4' ,'_feral_4a.jpg' : '5' ,'_feral_5.jpg' : '6' ,'_feral_6.jpg' : '7' ,'_hand_1.jpg' : '8' ,'_hand_5.jpg' : '9' ,'_nature_4.jpg' : 'a' ,'_nature_6.jpg' : 'b' ,'_nature_7.jpg' : 'c' ,'_orb_1.jpg' : 'd' , '_orb_4.jpg' : 'e' , '_feral_2.jpg' : 'f'}

for i in xrange(0, max_count):
	if(number>=size_of_table):
                x = 0
                z = 64
                y += 64
                k += 64
                number = 0
        current_image = base_image.crop([x , y , z , k])
        number += 1
        x += 64
        z += 64
        current_im = current_image.load()
	for j in xrange(0 ,len(list_name)):
		image_for_compare = Image.open(list_name[j])
		im_for_compare = image_for_compare.load()
		f = 0
		for l in xrange (0 , image_for_compare.size[0]):
			if ((current_im[l,l][0] == im_for_compare[l,l][0]) or (current_im[l,l][1] == im_for_compare[l,l][1]) or (current_im[l,l][2] == im_for_compare[l,l][2])):
				if ((current_im[l,l][0] != 255) and (current_im[l,l][1] != 255) and (current_im[l,l][1] != 255)):
					f += 1
		if f>20:
			ls_in_hex += wordindex[list_name[j]]

for i in xrange(0 , len(ls_in_hex),2):
	plaintext += chr(int(str(ls_in_hex[i:i+2]), 16))

print plaintext

			
