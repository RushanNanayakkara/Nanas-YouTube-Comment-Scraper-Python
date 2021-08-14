import time
import json
import os
import argparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class Reply:
    def __init__(self, owner, reply):
        self.__owner = owner
        self.__reply = reply

    def get_owner(self):
        return self.__owner

    def set_owner(self, owner):
        self.__owner = owner

    def get_reply(self):
        return self.__reply

    def set_reply(self, reply):
        self.__reply = reply


class Comment:
    def __init__(self, owner, comment):
        self.__owner = owner
        self.__comment = comment
        self.__replies = []

    def get_owner(self):
        return self.__owner

    def set_owner(self, owner):
        self.__owner = owner

    def get_comment(self):
        return self.__comment

    def set_comment(self, comment):
        self.__comment = comment

    def get_replies(self):
        return self.__replies

    def add_reply(self, reply):
        self.__replies.append(reply)


def scrape_comments(url_file_path, out_file_path, out_file_name):
    driver = webdriver.Chrome()

    urls = []

    with open(url_file_path, 'r', encoding="utf-8") as url_file:
        for url in url_file:
            urls.append(url)

    selectors = {
        "comment": "#comment #body #main #expander #content #content-text",
        "view_replies": "#replies ytd-comment-replies-renderer #expander #more-replies a #button yt-icon",
        "more_replies": "#replies ytd-comment-replies-renderer #expander #expander-contents #contents "
                        "ytd-continuation-item-renderer #button yt-icon",
        "reply_list": "#replies ytd-comment-replies-renderer #expander #expander-contents #contents "
                      "ytd-comment-renderer",
        "reply_from_reply_container": "#body #main #expander #content #content-text",
        "reply_text_span": "#author-text > span"
    }

    x_paths = {
        'title': '/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[6]/div['
                 '2]/ytd-video-primary-info-renderer/div/h1/yt-formatted-string',
        'comment-thread-renderer': '/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div['
                                   '1]/div/ytd-comments/ytd-item-section-renderer/div[3]//ytd-comment-thread-renderer',
        'comment-thread-renderer-to-comment': 'ytd-comment-renderer/div[3]/div['
                                              '2]/ytd-expander/div/yt-formatted-string[2]',
        'comment-thread-renderer-to-comment-owner': 'ytd-comment-renderer/div[3]/div[2]/div[1]/div[2]/h3/a/span',
        'comment-thread-renderer-to-comment-reply-renderer': 'div/ytd-comment-replies-renderer/div[1]/div/div['
                                                             '1]//ytd-comment-renderer',
        'comment-reply-renderer-to-reply-comment': 'div[3]/div[2]/ytd-expander/div/yt-formatted-string[2]',
        'comment-reply-renderer-to-reply-owner': 'div[3]/div[2]/div[1]/div[2]/h3/a/span'
    }

    comments = []
    for url in urls:
        url_comments = []
        print(f"Starting scraping {url}")
        driver.get(url)
        time.sleep(4)

        url_title = driver.find_element_by_xpath(x_paths['title']).text

        driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        while True:
            # Wait to load page
            time.sleep(4)
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        ytd_comment_thread_renderers = driver.find_elements_by_xpath(x_paths["comment-thread-renderer"])

        for i in range(len(ytd_comment_thread_renderers)):
            renderer = ytd_comment_thread_renderers[i]
            comment_owner = renderer.find_element_by_xpath(x_paths['comment-thread-renderer-to-comment-owner']).text
            comment_text = renderer.find_element_by_css_selector(selectors['comment']).text
            comment = Comment(comment_owner, comment_text)
            if len(renderer.find_elements_by_css_selector(selectors['view_replies'])) > 0:
                view_reply_button = renderer.find_element_by_css_selector(selectors['view_replies'])
                # noinspection DuplicatedCode
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'})", view_reply_button)
                time.sleep(2)
                view_reply_button.click()
                time.sleep(2)
                ytd_comment_thread_renderers = driver.find_elements_by_css_selector("ytd-comment-thread-renderer")
                renderer = ytd_comment_thread_renderers[i]
                more_replies_button_list = renderer.find_elements_by_css_selector(selectors["more_replies"])
                while len(more_replies_button_list) > 0:
                    more_replies_button = more_replies_button_list[0]
                    # noinspection DuplicatedCode
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'})", more_replies_button)
                    time.sleep(2)
                    more_replies_button.click()
                    time.sleep(2)
                    ytd_comment_thread_renderers = driver.find_elements_by_css_selector("ytd-comment-thread-renderer")
                    renderer = ytd_comment_thread_renderers[i]
                    more_replies_button_list = renderer.find_elements_by_css_selector(selectors["more_replies"])
                reply_containers = renderer.find_elements_by_xpath(
                    x_paths['comment-thread-renderer-to-comment-reply-renderer']
                )
                for reply_container in reply_containers:
                    reply_owner = \
                        reply_container.find_element_by_xpath(x_paths["comment-reply-renderer-to-reply-owner"]).text
                    reply = reply_container.find_element_by_css_selector(selectors["reply_from_reply_container"]).text
                    comment.add_reply(Reply(reply_owner, reply))
            url_comments.append(comment)
            i += 1
        comments.append({'title': url_title, 'url': url, 'comments': url_comments})

    with open(f"{out_file_path}/{out_file_name}.json", "w+", encoding="utf-8") as out_file:
        s = json.dumps(comments, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)
        out_file.writelines(s)
        out_file.close()

    print("Scraping completed successfully")
    driver.close()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("inFile", help="input text file with links to scrape")
    arg_parser.add_argument("-op", "--outPath", help="Output file path")
    arg_parser.add_argument("-of", "--outputFileName", help="Output file path")

    args = arg_parser.parse_args()

    input_file = args.inFile
    output_path = "Out" if args.outPath is None else args.outPath
    output_file = "out" if args.outputFileName is None else args.outputFileName

    os.makedirs(output_path, exist_ok=True)
    scrape_comments(input_file, output_path, output_file)
