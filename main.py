import easyocr
import csv
import cv2
import os

# PATHS
cheks_folder_path = 'checks/'

index_of_image = 0

cropped_path = 'cropped/'

if not os.path.isdir(cropped_path):
    os.mkdir(cropped_path)

with open(cropped_path + 'cheksnames' + '.csv', 'w', newline = '', encoding='utf-8') as csvfileROOT:
    
    filednamesROOT = ['foldername', 'imagename']
    writerROOT = csv.DictWriter(csvfileROOT, fieldnames=filednamesROOT, delimiter='\t')

    writerROOT.writeheader()


    for file in os.listdir(cheks_folder_path):

        # PATH TO IMAGE
        image_path = cheks_folder_path + file

        # PATH TO CROPPED IMAGES
        cropped_path = 'cropped/cropped' + str(index_of_image) + '/'

        if os.path.isdir(cropped_path):
            index_of_image += 1
            continue
        # EASYOCR READER
        reader = easyocr.Reader(['ru', 'en'], gpu=True)
        results = reader.readtext(image_path)

        image = cv2.imread(image_path)

        if not os.path.isdir(cropped_path):
            os.mkdir(cropped_path)


        index_of_word = 0
        with open(cropped_path +'cropped' +'.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter= '\t')

            writer.writeheader()

            for (cords, text, accuracity) in results:

                try:
                    cropped = image[cords[0][1]:cords[2][1], cords[0][0]: cords[2][0]]
                except TypeError:
                    print(cords[0][1], cords[2][1], cords[0][0],cords[2][0])
                cv2.imwrite(cropped_path + 'cropped' + str(index_of_word) + '.jpg', cropped)
                
                writer.writerow({'filename': 'cropped' + str(index_of_word) +  '.jpg', 'text': text})

                index_of_word += 1
        
        writerROOT.writerow({'foldername': cropped_path, 'imagename': file})
        
        index_of_image += 1




