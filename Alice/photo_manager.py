from PIL import Image, ImageDraw
import requests
from random import randrange
import time
from multiprocessing import Process

class ChangedImage():
    def __init__(self, image_name):
        self.image = Image.open(image_name + '.png').convert('RGB')
        self.image_name = image_name
        self.image = self.image.resize((300, 300))
    def change_color_theme(self, r, g, b, color, i, j):
        if color == 'reverse':
            r = 255 - r
            b = 255 - b
            g = 255 - g
        
        elif color == 'loud':
            if j % 2 == 0:
                r = 255
                b = 255
                g = 255
        return (r, g, b)

    def set_square(self, squares, pixels):
        for _ in range(squares):
            square_x0 = randrange(0, 149)
            square_y0 = randrange(0, 149)
            for i in range(square_x0, square_x0 + 80):
                for j in range(square_y0, square_y0 + 80):
                    pixels[i, j] = 0, 0, 0

    def change_picture(self, color, squares):
        
        pixels = self.image.load()
        x, y = self.image.size

        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]

                pixels[i, j] = self.change_color_theme(r, g, b, color, i, j)

        self.set_square(squares=squares, pixels=pixels)

        self.image.save(self.image_name + '-new' + '.png')
        self.image.close()


def load_image(text, image_name):
    key = '22985140-6d424a41e0c4fe1cd0bdfcd0c'
    url_photo = requests.get(f'https://pixabay.com/api/', params={'key': key, 'q': text}).json()

    taken_photo = requests.get(url_photo['hits'][0]['webformatURL'])
    with open(image_name + '.png', 'wb') as image:
        image.write(taken_photo.content)


if __name__ == '__main__':
    t1 = time.time()
    a = ChangedImage('img20')
    a.change_picture('reverse', 1)
    print(time.time() - t1)






