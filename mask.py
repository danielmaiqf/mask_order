from selenium import webdriver
from time import sleep
import conf

driver = webdriver.Chrome(conf.DRIVER)
driver.fullscreen_window()

driver.get("http://kz.yq.zszwfw.cn/kzyy-register/#/kz/order")

driver.find_element_by_xpath('//*[@id="app"]/div/div[4]/div/div[1]/input').send_keys(conf.PHONE)
driver.find_element_by_xpath('//*[@id="app"]/div/div[4]/div/div[2]/input').send_keys(conf.PASSWD)
sleep(3) # Wait for inputing code

while driver.current_url == "http://kz.yq.zszwfw.cn/kzyy-register/#/kz/order":
    pass
print(driver.current_url) # Jumped

while True:
    driver.find_element_by_xpath('//*[@id="hq_btn"]').click()
# sleep(10)
# driver.quit()