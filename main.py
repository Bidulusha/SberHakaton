import easyocr
import csv
import cv2

image_path = 'cheks/chek1.jpg'

reader = easyocr.Reader(['ru', 'en'])
results = reader.readtext(image_path)

image = cv2.imread(image_path)


i = 0

with open('info.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['filename', 'text']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter= '\t')

    writer.writeheader()

    for (cords, text, accuracity) in results:

        cropped = image[cords[0][1]:cords[2][1], cords[0][0]: cords[2][0]]
        cv2.imwrite('cropped/cropped' + str(i) + '.jpg', cropped)
        
        writer.writerow({'filename': 'cropped' + str(i) +  '.jpg', 'text': text})

        i += 1



