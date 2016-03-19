#!usr/bin/env python
from PIL import Image
import random
import os

directory = os.path.join(os.path.dirname(__file__), "icons")
wordindex = {'0' : '_phys_1.jpg' , '1' : '_class_2.jpg' , '2' : '_class_2b.jpg' , '3' : '_resist_4.jpg' , '4' : '_class_3a.jpg' , '5' : '_feral_4a.jpg' , '6' : '_feral_5.jpg' , '7' : '_feral_6.jpg' , '8' : '_hand_1.jpg' , '9' : '_hand_5.jpg' , 'a' : '_nature_4.jpg' , 'b' : '_nature_6.jpg' , 'c' : '_nature_7.jpg' , 'd' : '_orb_1.jpg' , 'e' : '_orb_4.jpg' , 'f' : '_feral_2.jpg'}
second_list = ["_animal_1.jpg" , "_class_2a.jpg", "_class_3b.jpg" , "_feral_1.jpg" , "_feral_3.jpg" , "_feral_4b.jpg" , "_nature_1.jpg" , "_nature_2.jpg" , "_nature_5.jpg"  , "_nature_8.jpg"]

wordindex = dict((k, os.path.join(directory, v)) for k, v in wordindex.iteritems())
second_list = [os.path.join(directory, x) for x in second_list]

def encode(plaintext , filename):
	ls_in_hex = plaintext.encode('hex')
	size_of_table = int(len(ls_in_hex)**0.5)+1

	base_image = Image.new("RGB", (size_of_table * 64, size_of_table * 64), (255,255,255))
	count_of_picture = size_of_table ** 2

	x = 0
	y = 0
	z = 64
	k = 64
	number = 0

	for i in xrange(0 , count_of_picture):
        	if(number>=size_of_table):
                	x = 0
                	z = 64
                	y += 64
                	k += 64
                	number = 0
		if (i<len(ls_in_hex)):
        		image = Image.open(wordindex[ls_in_hex[i]])
		else:
			image = Image.open(second_list[random.randint(0,len(second_list)-1)])
        	base_image.paste(image , (x,y,z,k))
        	number += 1
        	x += 64
        	z += 64

	base_image.save(filename)
