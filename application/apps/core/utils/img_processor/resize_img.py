from io import BytesIO

from PIL import Image


async def resize_img(url):
    img = Image.open(url)

    h, w = img.size
    scale = 120 / max(h, w)
    img.resize((int(h * scale), int(w * scale)), Image.ANTIALIAS)

    temp = BytesIO()
    img.save(temp, format="png")
    temp.seek(0)
    return Image.open(temp)
