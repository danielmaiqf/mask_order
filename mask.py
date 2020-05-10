from selenium import webdriver
from time import sleep
import psycopg2
import requests
from selenium.common.exceptions import ElementClickInterceptedException
import os


dsn = os.getenv("postgresdsn")

conn = psycopg2.connect(dsn)
cur = conn.cursor()
# get phone and password, than create a session
cur.execute('''
    lock users;
    lock orders;
    lock order_sessions;
    select * from users
    where not phone in (
        select phone from orders
        union
        select phone from order_sessions
    )
    limit 1;
''')
phone, password = cur.fetchone()
cur.execute("insert into order_sessions (phone) values (%s)", (phone, ))
conn.commit()


try:
    # start a driver
    opts = webdriver.chrome.options.Options()
    opts.headless = True
    driver = webdriver.Chrome(options=opts)
    # init driver
    driver.set_window_size(width=414, height=700)
    driver.get("http://kz.yq.zszwfw.cn/kzyy-register/#/kz/order")
    size = driver.find_element_by_id("app").size
    driver.set_window_size(width=414, height=size["height"]+100)
    # type phone and password
    print("STEP: sending keys phone", phone, " password", password)
    driver.find_elements_by_tag_name("input")[0].send_keys(phone)
    driver.find_elements_by_tag_name("input")[1].send_keys(password)
    # get captcha answer image from db
    sleep(5)
    answer = None
    while answer == None:
        # store captcha image into db
        print("STEP: store captcha image into db")
        captcha_url = driver.find_element_by_id(
            "loginCodeId").get_attribute("src")
        print("INFO: captcha url: ", captcha_url)
        captcha_img = psycopg2.Binary(requests.get(captcha_url).content)

        cur = conn.cursor()
        cur.execute('''
            insert into captchas (img_sha, img) values (sha256(%s), %s);
            update order_sessions set captcha1=sha256(%s) where phone = %s;
        ''', (captcha_img, captcha_img, captcha_img, phone))
        conn.commit()
        # checking if the answer of the captcha is already in the db
        checked_times = 1
        print("STEP: checking if the answer of the captcha is already in the db")
        for i in range(20):
            sleep(1)
            print("INFO: checking.. x", checked_times)

            cur = conn.cursor()
            cur.execute(
                "select answer from captchas where img_sha = sha256(%s)", (captcha_img,))
            answer = cur.fetchone()[0]
            conn.commit()

            if answer == None:
                print("INFO: answer not found")
            else:
                print("INFO: got answer: ", answer)
                break
            checked_times += 1

    # type captcha answer, login and wait
    driver.find_elements_by_tag_name("input")[2].send_keys(answer)
    driver.find_element_by_tag_name("button").click()
    # get captcha answer image from db
    sleep(5)
    checked_times = 1
    answer = None
    while answer == None:
        # store captcha image into db
        print("STEP: store captcha image into db")
        captcha_url = driver.find_element_by_id(
            "loginCodeId2").get_attribute("src")
        print("INFO: captcha url: ", captcha_url)
        captcha_img = psycopg2.Binary(requests.get(captcha_url).content)

        cur = conn.cursor()
        cur.execute("""
            insert into captchas (img_sha, img) values (sha256(%s), %s);
            update order_sessions set captcha2=sha256(%s) where phone = %s;
        """, (captcha_img, captcha_img, captcha_img, phone))
        conn.commit()
        # checking if the answer of the captcha is already in the db
        print("STEP: checking if the answer of the captcha is already in the db")
        for i in range(30):
            sleep(10)
            print("INFO: checking.. x", checked_times)

            cur = conn.cursor()
            cur.execute(
                "select answer from captchas where img_sha = sha256(%s)", (captcha_img,))
            answer = cur.fetchone()[0]
            conn.commit()
            if answer == None:
                print("INFO: answer not found")
            else:
                print("INFO: got answer: ", answer)
                break
            checked_times += 1

    # type captcha answer
    driver.find_elements_by_tag_name("input")[0].send_keys(answer)
    # rob
    while True:
        try:
            driver.find_element_by_id("hq_btn").click()
        except ElementClickInterceptedException:
            break
    # choose
    driver.refresh()
    sleep(5)

    driver.find_element_by_id("zhengjian").click()
    div = driver.find_element_by_xpath(
        '/html/body//div[@class="weui-picker__item" and text() = "五桂山"]')
    sleep(5)
    webdriver.ActionChains(driver).move_to_element(
        div).click(div).perform()
    driver.find_elements_by_class_name(
        "weui-picker__action")[1].click()

    driver.find_element_by_id("wuzi").click()
    div = driver.find_element_by_xpath(
        '/html/body//div[@class="weui-picker__item" and text() = "中智大药房五桂山御龙山药房"]')
    sleep(1)
    webdriver.ActionChains(driver).move_to_element(
        div).click(div).perform()
    driver.find_elements_by_xpath(
        '//*[@id="app"]/div/div[4]/div/div/div[4]/div[2]/div[1]/div[2]')[0].click()

    driver.find_element_by_class_name("back_but").click()
    '''
    # follow th link
    driver.find_element_by_xpath(
        '//*[@id="app"]//table[@class="check_table"]/tbody/tr[1]/td[4]').click()
    # take a screenshot, store into the db and save in localhost
    driver.set_window_size(width=300, height=3000)
    '''
    driver.refresh()
    screenshot = driver.get_screenshot_as_png()

    # change the session to the order
    cur = conn.cursor()
    cur.execute("delete from order_sessions where phone = %s", (phone, ))
    cur.execute("insert into orders(phone, img) values(%s, %s);",
                (phone, psycopg2.Binary(screenshot)))
    conn.commit()
except Exception as error:
    # delete the session
    print("ERROR: ", error)
    driver.save_screenshot("error.png")
    conn.rollback()

finally:
    print("STEP: removing order session")
    cur = conn.cursor()
    cur.execute("delete from order_sessions where phone = %s", (phone, ))
    conn.commit()
    print("STEP: closing connection")
    conn.close()

