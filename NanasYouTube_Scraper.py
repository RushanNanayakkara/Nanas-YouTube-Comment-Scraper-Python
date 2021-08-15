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
    comments = []

    with open(url_file_path, 'r', encoding='utf-8') as url_file:
        for url in url_file:
            urls.append(url)

    x_paths = {
        'title': '/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[6]/div['
                 '2]/ytd-video-primary-info-renderer/div/h1/yt-formatted-string',
        'comment-thread-renderer': '/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div['
                                   '1]/div/ytd-comments/ytd-item-section-renderer/div[3]//ytd-comment-thread-renderer',
        'comment-thread-renderer-to-comment': 'ytd-comment-renderer/div[3]/div['
                                              '2]/ytd-expander/div/yt-formatted-string[2]',
        'comment-thread-renderer-to-comment-owner': 'ytd-comment-renderer/div[3]/div[2]/div[1]/div[2]/h3/a/span',
        'comment-thread-renderer-to-comment-owner-author': 'ytd-comment-renderer/div[3]/div[2]/div[1]/div[2]/span['
                                                           '1]/ytd-author-comment-badge-renderer/a/ytd-channel-name'
                                                           '/div/div/yt-formatted-string',
        'comment-thread-renderer-to-comment-reply-renderer': 'div/ytd-comment-replies-renderer/div[1]/div/div['
                                                             '1]//ytd-comment-renderer',
        'comment-reply-renderer-to-reply-comment': 'div[3]/div[2]/ytd-expander/div/yt-formatted-string[2]',
        'comment-reply-renderer-to-reply-owner': 'div[3]/div[2]/div[1]/div[2]/h3/a/span',
        'comment-reply-renderer-to-reply-owner-author': 'div[3]/div[2]/div[1]/div[2]/span['
                                                        '1]/ytd-author-comment-badge-renderer/a/ytd-channel-name/div'
                                                        '/div/yt-formatted-string',
        'comment-reply-renderer-to-view-replies': 'div/ytd-comment-replies-renderer/div[1]/ytd-button-renderer['
                                                  '1]/a/tp-yt-paper-button/yt-icon ',
        'comment-reply-renderer-to-more-replies': 'div/ytd-comment-replies-renderer/div[1]/div/div['
                                                  '1]/ytd-continuation-item-renderer/div['
                                                  '2]/ytd-button-renderer/a/tp-yt-paper-button/yt-icon '
    }

    for url in urls:
        print(f'Starting scraping {url}')
        url_comments = []  # List of comments under current url
        driver.get(url)
        time.sleep(4)

        url_title = driver.find_element_by_xpath(x_paths['title']).text

        # using both page down and scroll effect because for some reason it doesn't work without both, can't figure
        # out why
        driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
        last_height = driver.execute_script('return document.documentElement.scrollHeight')

        # Scrolling down to bottom until no longer scrollable
        while True:
            # Wait to load page
            time.sleep(4)
            driver.execute_script('window.scrollTo(0, document.documentElement.scrollHeight);')
            new_height = driver.execute_script('return document.documentElement.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

        ytd_comment_thread_renderers = driver.find_elements_by_xpath(x_paths['comment-thread-renderer'])

        for i in range(len(ytd_comment_thread_renderers)):
            renderer = ytd_comment_thread_renderers[i]

            comment_owner = renderer.find_element_by_xpath(x_paths['comment-thread-renderer-to-comment-owner']).text
            # because in author comments, owner name is in a different tag
            if len(comment_owner.strip()) == 0:
                comment_owner = renderer\
                    .find_element_by_xpath(x_paths['comment-thread-renderer-to-comment-owner-author']).text
                comment_owner += '[Author]'
            comment_text = renderer.find_element_by_xpath(x_paths['comment-thread-renderer-to-comment']).text
            comment = Comment(comment_owner, comment_text)

            view_reply_buttons = renderer.find_elements_by_xpath(x_paths['comment-reply-renderer-to-view-replies'])

            # if view replies button exists scraping the replies
            if len(view_reply_buttons) > 0:
                # noinspection DuplicatedCode
                view_reply_button = view_reply_buttons[0]
                # scrolling the view reply button to the middle of the screen
                driver.execute_script(
                    'arguments[0].scrollIntoView({block: "center", inline: "nearest"})', view_reply_button)
                time.sleep(2)

                view_reply_button.click()
                time.sleep(2)

                # reloading comment thread renderers because after view-reply button click the content of the comment
                # thread renderer changes
                ytd_comment_thread_renderers = driver.find_elements_by_xpath(x_paths['comment-thread-renderer'])
                renderer = ytd_comment_thread_renderers[i]

                more_replies_button_list = \
                    renderer.find_elements_by_xpath(x_paths['comment-reply-renderer-to-more-replies'])

                # until a more reply button exists clicking and expanding the reply section
                while len(more_replies_button_list) > 0:
                    # noinspection DuplicatedCode
                    more_replies_button = more_replies_button_list[0]
                    # scrolling to the center
                    driver.execute_script(
                        'arguments[0].scrollIntoView({block: "center", inline: "nearest"})', more_replies_button)

                    more_replies_button.click()
                    time.sleep(2)

                    # reloading comment thread renderers because after more-reply button click the content of the
                    # comment thread renderer changes
                    ytd_comment_thread_renderers = driver.find_elements_by_xpath(x_paths['comment-thread-renderer'])
                    renderer = ytd_comment_thread_renderers[i]
                    more_replies_button_list = \
                        renderer.find_elements_by_xpath(x_paths['comment-reply-renderer-to-more-replies'])

                # ytd-comment-renderers that contain the replies
                reply_containers = renderer\
                    .find_elements_by_xpath(x_paths['comment-thread-renderer-to-comment-reply-renderer'])

                for reply_container in reply_containers:
                    reply_owner = reply_container\
                        .find_element_by_xpath(x_paths['comment-reply-renderer-to-reply-owner']).text
                    # because in author replies, owner name is in a different tag
                    if len(reply_owner.strip()) == 0:
                        reply_owner = reply_container\
                            .find_element_by_xpath(x_paths['comment-reply-renderer-to-reply-owner-author']).text
                        reply_owner += '[Author]'
                    reply = reply_container\
                        .find_element_by_xpath(x_paths['comment-reply-renderer-to-reply-comment']).text
                    comment.add_reply(Reply(reply_owner, reply))

            url_comments.append(comment)
            i += 1
        comments.append({'title': url_title, 'url': url, 'comments': url_comments})

    with open(f'{out_file_path}/{out_file_name}.json', 'w+', encoding='utf-8') as out_file:
        s = json.dumps(comments, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)
        out_file.writelines(s)
        out_file.close()

    print('Scraping completed successfully')
    driver.close()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('inputFile', help='input text file with links to scrape')
    arg_parser.add_argument('-op', '--outputPath', help='Output file path')
    arg_parser.add_argument('-of', '--outputFileName', help='Output file path')

    args = arg_parser.parse_args()

    input_file = args.inputFile
    output_path = 'Out' if args.outputPath is None else args.outputPath
    output_file = 'out' if args.outputFileName is None else args.outputFileName

    os.makedirs(output_path, exist_ok=True)
    scrape_comments(input_file, output_path, output_file)
