from random import choice, randrange
import requests
from PIL import Image

CATEGORIES = ['продукт', 'животное', 'фрукт']
sp = {'продукт': ['37.6134%2C55.789&spn=0.0002,0.0002',
                  '37.658%2C55.762840&spn=0.0001,0.0001',
                  '37.73%2C55.730094&spn=0.00035,0.00035',
                  '38.9816%2C55.8021&spn=0.0001,0.0001'],
      'фрукт':  ['37.6134%2C55.789&spn=0.0002,0.0002',
                  '37.658%2C55.762840&spn=0.0001,0.0001',
                  '37.73%2C55.730094&spn=0.00035,0.00035',
                  '38.9816%2C55.8021&spn=0.0001,0.0001'],
        'овощ':  ['37.6134%2C55.789&spn=0.0002,0.0002',
                  '37.658%2C55.762840&spn=0.0001,0.0001',
                  '37.73%2C55.730094&spn=0.00035,0.00035',
                  '38.9816%2C55.8021&spn=0.0001,0.0001'],
      'животное': ['37.5783%2C55.7611&spn=0.0001,0.0001',
                   '37.626284%2C55.838928&spn=0.0001,0.0001',
                   '37.3362%2C55.60947&spn=0.0001,0.0001']}
coordinates = None


def letter_unlock(name_of_img):
    name_of_img = name_of_img.lower()
    letter_index = randrange(0, len(name_of_img))
    unlocked_letter = name_of_img[letter_index]
    new_line = ''
    for letter in name_of_img:
        if letter == unlocked_letter:
            new_line += letter
        else:
            new_line += '_'
    return (unlocked_letter, new_line)


def image_part_unlock(name_of_img, id, name):
    img = Image.open(name_of_img + '.png')
    hint_img = Image.new("RGB", (300, 100))
    pixels = img.load()
    hint_pixels =  hint_img.load()
    x, y = hint_img.size
    for i in range(x):
        for j in range(y):
            hint_pixels[i, j] = pixels[i, j]
    image_name = id[:5] + name + 'part-img' + '.png'
    hint_img.save(image_name)
    return image_name
    

def map_hint(category, name, id):
    map_file = id[:5] + name + '-map.png'
    if category in ['продукт', 'фрукт', 'овощ']:
        coordinates = choice(sp['продукт'])
        response = requests.get(f"http://static-maps.yandex.ru/1.x/?ll={coordinates}&l=map")
        with open(map_file, "wb") as file:
            file.write(response.content)
    elif category == 'животное':
        coordinates = choice(sp['животное'])
        response = requests.get(f"http://static-maps.yandex.ru/1.x/?ll={coordinates}&l=map")
        with open(map_file, "wb") as file:
            file.write(response.content)

    return map_file
