try:
    import selenium
    import time
    from datetime import datetime
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from fake_headers import Headers
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.keys import Keys
except ModuleNotFoundError:
    print("Please download dependencies from requirement.txt")
except Exception as ex:
    print(ex)


class Tag:
    def __init__(self, name):
        self.name = name
        self.count = 1
        self.scraped = False


class Tiktok:
    @staticmethod
    def init_driver(browser_name: str):
        def set_properties(browser_option):
            ua = Headers().generate()  # fake user agent
            browser_option.add_argument('--headless')
            browser_option.add_argument('--no-sandbox')
            browser_option.add_argument('--disable-extensions')
            browser_option.add_argument('--incognito')
            browser_option.add_argument('--disable-gpu')
            browser_option.add_argument('--log-level=3')
            browser_option.add_argument(f'user-agent={ua}')
            browser_option.add_argument('--disable-notifications')
            browser_option.add_argument('--disable-popup-blocking')

            return browser_option

        try:
            browser_name = browser_name.strip().title()

            ua = Headers().generate()  # fake user agent

            if browser_name.lower() == "chrome":
                browser_option = ChromeOptions()
                browser_option = set_properties(browser_option)
                driver = webdriver.Chrome(ChromeDriverManager().install(),
                                          options=browser_option)
            else:
                driver = "Browser Not Supported!"
            return driver
        except Exception as ex:
            print(ex)

    @staticmethod
    def scrap(driver, search_query):
        try:
            URL = f'https://www.tiktok.com/tag/{search_query}'

            try:
                driver.get(URL)

            except AttributeError:
                print("Driver is not set")
                exit()

            wait = WebDriverWait(driver, 10)

            # time.sleep(2)

            state_data = driver.execute_script("return window['SIGI_STATE']")
            parse_scraped_state_data(state_data)

        except Exception as ex:
            driver.close()
            driver.quit()
            print(ex)

    @staticmethod
    def scrape_comments(driver, post_url):
        try:

            try:
                driver.get(post_url)

            except AttributeError:
                print("Driver is not set")
                exit()

            wait = WebDriverWait(driver, 10)

            time.sleep(20)
            elements = driver.find_elements_by_xpath('//p[@data-e2e="comment-level-1"]')[:10]
            comments = [element.text for element in elements]
            comments_string = '[' + '\t'.join(comments) + ']'
            return comments_string

        except Exception as ex:
            driver.close()
            driver.quit()
            print(ex)


account = []
post_url = []
views = []
likes = []
comment_count = []
shares = []
caption = []
hashtags_list = []
date_posted = []
date_collected = []
unique_vid_list = []


def parse_scraped_state_data(input_state_data):
    post_url_format = "https://www.tiktok.com/@{}/video/{}"

    for [vid_id_key, dict_item] in input_state_data['ItemModule'].items():
        if vid_id_key not in unique_vid_list:
            unique_vid_list.append(vid_id_key)
            try:
                account.append(dict_item["author"])
                post_url.append(post_url_format.format(dict_item["author"], vid_id_key))
                views.append(dict_item["stats"]["playCount"])
                likes.append(dict_item["stats"]["diggCount"])
                comment_count.append(dict_item["stats"]["commentCount"])
                shares.append(dict_item["stats"]["shareCount"])
                caption.append(dict_item["desc"])
                hashtag_string = ""
                for tag_data in dict_item["textExtra"]:
                    current_tag_string = f'{tag_data["hashtagName"]}'
                    if len(current_tag_string) == 0:
                        continue
                    if len(hashtag_string) > 0:
                        hashtag_string = f'{hashtag_string} #{current_tag_string}'
                    else:
                        hashtag_string = f'#{current_tag_string}'
                    hashtag_ranker(current_tag_string)
                hashtags_list.append(hashtag_string)
                date_parsed = datetime.fromtimestamp(int(dict_item["createTime"]))
                date_posted.append("{}/{}/{}".format(date_parsed.month, date_parsed.day, date_parsed.year))
                date_collected.append(datetime.now().strftime('%m/%d/%Y'))
            except Exception as ex:
                print(ex)
                continue

parsed_csv_name = "parsed_data.csv"
def save_parsed_data_to_csv():
    df = pd.DataFrame(
        {'Post URL': post_url, 'Account': account, 'Views': views, 'Likes': likes, 'Comments': comment_count,
         'Shares': shares, 'Caption': caption, 'Hashtags': hashtags_list, 'Date posted': date_posted,
         'Date Collected': date_collected})
    print(f'Writing {len(unique_vid_list)} unique vids to {parsed_csv_name}')
    df.to_csv(parsed_csv_name, index=False)


tag_ranks = []

ignored_tags = ['fyp', 'foryou', 'foryoupage', 'viral', 'fypシ', 'fy', 'trend', 'funny', 'comedy', 'gramps', 'asmr', 'xyzbca', 'trending', 'tiktok']


def hashtag_ranker(hashtag):
    if hashtag in ignored_tags:
        return
    tag_found = False
    for tag_object in tag_ranks:
        if hashtag == tag_object.name:
            tag_object.count += 1
            tag_found = True
            break

    if not tag_found:
        tag_ranks.append(Tag(hashtag))


def get_next_tag():
    tag_ranks.sort(key=lambda tag: tag.count, reverse=True)
    for i in range(0, len(tag_ranks)):
        if not tag_ranks[i].scraped:
            tag_ranks[i].scraped = True
            return tag_ranks[i].name

    print("Tag list exhausted")


if __name__ == '__main__':
    browser_name = "chrome"

    driver = Tiktok.init_driver(browser_name)

    hashtag_ranker("fashion")
    while len(unique_vid_list) < 200:
        next_search_tag = get_next_tag()
        print(f'Searching for #{next_search_tag} current count of unique vids {len(unique_vid_list)}')
        Tiktok.scrap(driver, next_search_tag)

    save_parsed_data_to_csv()
    driver.close()
    driver.quit()
