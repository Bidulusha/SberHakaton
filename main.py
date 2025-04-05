import easyocr
import os

reader = easyocr.Reader(['ru'])

file_folder = "./cheks"

for  filename in os.listdir(file_folder):
    if filename.lower().endswith(".jpg"):
        image_path = os.path.join(file_folder, filename)

        result = reader.readtext(image_path)

        print("Current file is " + image_path)

        for i in result:
            print(i)
