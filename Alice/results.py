from PIL import Image, ImageDraw, ImageFont


def make_a_score_picture(id, name, wins, loses):
    color = (255, 204, 0)
    wins = str(wins)
    loses = str(loses)
    img = Image.new("RGB", (300, 300))
    drawer = ImageDraw.Draw(img)
    drawer.rectangle([0, 0, 300, 300], color)
    fnt = ImageFont.truetype("data\\YandexSansText-Regular.ttf", 30)
    drawer.text((10, 100), "Алиса:", font=fnt, fill=(0, 0, 0))
    drawer.text((200, 100), name + ':', font=fnt, fill=(0, 0, 0))
    drawer.text((120, 150), loses + ' - ' + wins, font=fnt, fill=(0, 0, 0))
    img_name = id[:5] + name + '.png'
    img.save(img_name)
    return img_name


if __name__ == '__main__':
    make_list_of_best('131', [('wrw', 1000), ('131', 1500)])