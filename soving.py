from io import StringIO, BytesIO
import psycopg2
from PIL import Image
from time import sleep
import os
# query and show image
dsn = os.getenv("postgresdsn")
with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        command = "select img from captchas where answer is null;"
        cur.execute(command)
        res = cur.fetchall()
        for image in res:
            img = Image.open(BytesIO(image[0]))
            img.show()
            result = input("captcha:")
            cur.execute(
                "update captchas set answer=%s where img_sha=sha256(%s)", (result, image))
        conn.commit()
