import easyocr

reader = easyocr.Reader(['ru', 'en'])
results = reader.readtext('cheks/chek1.jpg')
    
for text in results:
    print(text)
