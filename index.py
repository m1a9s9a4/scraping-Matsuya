import requests
import sys
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
service_account_file = 'nourishment-9fb659a6f62b.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_file)

gs = gspread.authorize(credentials)
ss_key = '15jFzZTgcF2kq95Cx18PqkPQrPTCnwPE5WFMe_1YThLk'
sheet = gs.open_by_key(ss_key).worksheet('松屋')

base_url = "https://www.matsuyafoods.co.jp"
scrape_url = base_url + "/matsuya/menu/"

print("starting: ", sys.argv[0], ": ", scrape_url)
page = requests.get(scrape_url)
page.encoding = page.apparent_encoding

soup = BeautifulSoup(page.text, 'html.parser')

#
all_menu = soup.find(class_='w-col flex')
all_menu_links = all_menu.find_all('a')

def updateSheet(alphabet, number, value):
    sheet.update_acell(alphabet + str(number), value)

row_number = 2
for links in all_menu_links:
    # 大メニュー
    menu_name = links.find(class_="txt").text
    print('scrapping: ' + menu_name)

    time.sleep(1)
    child_menu_page = requests.get(base_url + links.get('href'))
    page.encoding = page.apparent_encoding

    child_menu_soup = BeautifulSoup(child_menu_page.text, 'html.parser')
    child_menu_list = child_menu_soup.find(class_="w-col menu_inner flex")
    child_menu_links = child_menu_list.find_all('a')

    for child_menu_link in child_menu_links:
        time.sleep(1)
        food_page = requests.get(child_menu_link.get('href'))
        updateSheet('J', row_number, child_menu_link.get('href'))
        food_page.encoding = food_page.apparent_encoding

        food_soup = BeautifulSoup(food_page.text, 'html.parser')
        # メニュー名
        food_title = food_soup.find('h1').text
        print(food_title)

        food_nourishment_ul = food_soup.find(class_="nourishment")
        food_nourishment_list = food_nourishment_ul.find_all("li")
        for food_nourishment in food_nourishment_list:
            time.sleep(1)
            # 並盛、大盛りなど
            try:
                food_type = food_nourishment.find('h3').text
                print(food_type)
                updateSheet('A', row_number, menu_name)
                updateSheet('B', row_number, food_title)
                updateSheet('C', row_number, food_type)
            except:
                print("量なし")

            # 栄養素 {栄養: 量}
            food_nourishment_element = food_nourishment.find('p')
            try:
                if food_nourishment_element is None:
                    food_nourishment_element = food_nourishment.get_text(',').split(',')

                else:
                    food_nourishment_element = food_nourishment_element.get_text(',').split(',')
            except:
                food_nourishment_element = []


            for each_nourishment in food_nourishment_element:
                tmp_nourishment = each_nourishment.split('／')
                # 0が栄養素の名前 1が量
                try:
                    tmp_name = tmp_nourishment[0]
                    print(tmp_name)
                    tmp_amount = tmp_nourishment[1]
                    print(tmp_amount)
                except:
                    tmp_name = ""
                    tmp_amount = ""

                tmp_row_select = ''
                if tmp_name == 'カロリー':
                    tmp_row_select = 'D'
                elif tmp_name == 'たんぱく質':
                    tmp_row_select = 'E'
                elif tmp_name == '脂質':
                    tmp_row_select = 'F'
                elif tmp_name == '炭水化物':
                    tmp_row_select = 'G'
                elif tmp_name == 'ナトリウム':
                    tmp_row_select = 'H'
                elif tmp_name == '食塩相当量':
                    tmp_row_select = 'I'

                if tmp_amount:
                    updateSheet(tmp_row_select, row_number, tmp_amount)
                time.sleep(1)

            row_number = row_number + 1
            time.sleep(2)

