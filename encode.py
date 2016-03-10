#!usr/bin/env python
import math
import Image
wordindex = {'0' : '_phys_1.jpg' , '1' : '_class_2.jpg' , '2' : '_class_2b.jpg' , '3' : '_resist_4.jpg' , '4' : '_class_3a.jpg' , '5' : '_feral_4a.jpg' , '6' : '_feral_5.jpg' , '7' : '_feral_6.jpg' , '8' : '_hand_1.jpg' , '9' : '_hand_5.jpg' , 'a' : '_nature_4.jpg' , 'b' : '_nature_6.jpg' , 'c' : '_nature_7.jpg' , 'd' : '_orb_1.jpg' , 'e' : '_orb_4.jpg' , 'f' : '_feral_2.jpg'}

plaintext = "any string"

ls_in_hex = ""
for i in xrange(0 , len(plaintext)):
        s = hex(ord(plaintext[i]))
        ls_in_hex += s[2:]
size_of_table = int(math.sqrt(len(ls_in_hex)))+1
base_image = Image.new("RGB", (size_of_table * 64, size_of_table * 64), (255,255,255))

x = 0
y = 0
z = 64
k = 64
number = 0

for i in xrange(0, len(ls_in_hex)):
        if(number>=size_of_table):
                x = 0
                z = 64
                y += 64
                k += 64
                number = 0
        image = Image.open(wordindex[ls_in_hex[i]])
        base_image.paste(image , (x,y,z,k))
        number += 1
        x += 64
        z += 64

base_image.save("test_picture.jpg")
