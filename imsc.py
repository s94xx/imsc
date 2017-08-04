#coding: UTF-8

import time
import sys
import os
import urllib2
import binascii
from HTMLParser import HTMLParser
from argparse import ArgumentParser, RawTextHelpFormatter

# You may change these
booruBoards = ['futabooru', 'boob', 'catgirls', 'nekochu', 'vocalo']
# but don't change anything below

parser = ArgumentParser(prog='python imsc.py', description='\n  Available sources: google, rule34.xxx, rule34.paheal.net, danbooru,\n                     *.booru.org, hypnohub, all_boorus, all\n\n  default booru.org-boards:\n   ' + str(' '.join(booruBoards)) + '\n\n  Keyword / Tag rules:\n   rule34.xxx / rule34.paheal.net / danbooru:\n    - tags consisting of more than 1 word shouldn\'t be like this "cute neko",\n      but like this "cute_neko" (without the double-quotes)\n   google:\n    - don\'t use special characters like %00 or stuff like that', epilog='  created by s94\n', formatter_class=RawTextHelpFormatter,)
parser.add_argument('keywords', metavar='keywords', type=str, nargs='+', help='keyword(s) used for search')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False, help='output more detail')
parser.add_argument('-l', '--save-links', const='links.txt', default=None, help='save links to output file (default: links.txt)', nargs='?', dest='link_file')
parser.add_argument('-o', '--out-dir', nargs='?', default=None, help='directory in which images are saved', const=None, dest='out_dir')
parser.add_argument('-s', '--source', nargs='?', default='google', help='the site I should grab the images from (default: google)', const='google', dest='source')
parser.add_argument('-c', '--count', nargs='?', default=1, help='how many pages should I download. doesn\'t work with google (default: 1)', const=1, dest='count')
parser.add_argument('--allow-webms', action='store_true', dest='allow_webms', default=False, help='allow download of WebM files')
parser.add_argument('--search-only', action='store_true', dest='search_only', default=False, help='only collect links from sources (prevent downloading)')
args = parser.parse_args()

class LinkTagParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if (tag == 'a'):
            if (self.keyword == None):
                self.attrs = attrs
            else:
                for attr in attrs:
                    if self.keyword in attr[1]:
                        self.attrs = attrs
    def reset(self):
        HTMLParser.reset(self)
        self.attrs = None
        self.keyword = None
    def get_href_link(self):
        """
        @deprecated
        :return: href_link out ouf attrs
        """
        return str(self.attrs[1][1])
    def get_attr(self):
        return self.attrs
    def feed_with_keyword(self, source, keyword):
        HTMLParser.feed(self, source)
        self.keyword = keyword

class MediaTagParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if (tag == 'img'):
            if (self.keyword == None):
                self.attrs = attrs
            else:
                for attr in attrs:
                    if self.keyword in attr[1]:
                        self.attrs = attrs
    def reset(self):
        HTMLParser.reset(self)
        self.attrs = None
        self.keyword = None
    def get_attr(self):
        return self.attrs
    def feed_with_keyword(self, source, keyword):
        HTMLParser.feed(self, source)
        self.keyword = keyword

class STATIC():
    ITEMCOUNT = 0

def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()

def textcounter():
    sys.stdout.write(str(STATIC.ITEMCOUNT) + ' items found.' + '\r')
    sys.stdout.flush()

def download_page(url):
    version = (3,0)
    cur_version = sys.version_info
    if cur_version >= version:
        import urllib.request
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            req = urllib.request.Request(url, headers = headers)
            resp = urllib.request.urlopen(req)
            respData = str(resp.read())
            return respData
        except Exception as e:
            print(str(e))
    else:
        import urllib2
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            req = urllib2.Request(url, headers = headers)
            response = urllib2.urlopen(req)
            page = response.read()
            return page
        except:
            return"Page Not found"

def GOOGLE_images_get_next_item(s):
    start_line = s.find('rg_di')
    if start_line == -1:
        end_quote = 0
        link = "no_links"
        return link, end_quote
    else:
        start_line = s.find('"class="rg_meta"')
        start_content = s.find('"ou"',start_line+1)
        end_content = s.find(',"ow"',start_content+1)
        content_raw = str(s[start_content+6:end_content-1])
        return content_raw, end_content

def GOOGLE_images_get_all_items(page):
    items = []
    while True:
        item, end_content = GOOGLE_images_get_next_item(page)
        if item == "no_links":
            break
        else:
            items.append(item)
            time.sleep(0.1)
            page = page[end_content:]
        STATIC.ITEMCOUNT += 1
        textcounter()
    print('')
    return items

def R34XXX_fetch_media_url(s):
    for line in s.splitlines():
        if '//img.rule34.xxx//images' in line:
            temp_parser = LinkTagParser()
            temp_parser.feed(line)
            return 'http:' + temp_parser.get_attr()[0][1]

def R34XXX_media_get_all_items(page):
    items = []
    parser = LinkTagParser()
    for line in page.splitlines():
        if 'class="preview"' in line:
            parser.feed(line)
            items.append(R34XXX_fetch_media_url(download_page('http://rule34.xxx/' + parser.get_href_link())))
            STATIC.ITEMCOUNT += 1
            if (args.verbose or args.search_only):
                print('Found new link at: ' + items[-1])
            else:
                textcounter()
    print('')
    return items

def PAHEAL_media_get_all_items(page):
    items = []
    parser = LinkTagParser()
    for line in page.splitlines():
        if '.paheal.net/_images/' in line:
            parser.feed(line[:-82])
            attr = parser.get_attr()[0][1]
            if (attr != '#'):
                items.append(attr)
                STATIC.ITEMCOUNT += 1
                if (args.verbose):
                    print('Found new link at: ' + str(parser.get_attr()[0][1]))
                else:
                    textcounter()
    print('')
    return items

def DANBOR_fetch_media_url(s):
    for line in s.splitlines():
        if (('src="/data' in line) and (not ('itemprop="thumbnailUrl"' in line))):
            temp_parser = MediaTagParser()
            temp_parser.feed(line)
            return 'http://danbooru.donmai.us' + temp_parser.get_attr()[-1][1]

def DANBOR_media_get_all_items(page):
    items = []
    parser = LinkTagParser()
    for line in page.splitlines():
        if '<a href="/posts/' in line:
            parser.feed(line)
            items.append(DANBOR_fetch_media_url(download_page('http://danbooru.donmai.us' + parser.get_attr()[0][1])))
            STATIC.ITEMCOUNT += 1
            if (args.verbose):
                print('Found new link at: ' + items[-1])
            else:
                textcounter()
    print('')
    return items

def create_valid_url_str():
    return str(urllib2.quote(str('____PLUS____'.join(args.keywords))).replace('____PLUS____', '+'))

def create_booru_url(base_addr):
    return 'http://' + base_addr + '/index.php?page=post&s=list&tags=' + create_valid_url_str()

def XBOORU_fetch_media_url(s):
    for line in s.splitlines():
        if (('<img alt="img" src="http://img.booru.org/' in line) and (not ('itemprop="thumbnailUrl"' in line))):
            temp_parser = MediaTagParser()
            temp_parser.feed(line)
            return temp_parser.get_attr()[1][1]

def XBOORU_media_get_all_items(page, base_addr):
    items = []
    parser = LinkTagParser()
    for line in page.splitlines():
        if (('<a id="p' in line) and ('href="index.php?page=post&s=view&id=' in line)):
            parser.feed(line)
            items.append(XBOORU_fetch_media_url(download_page('http://' + base_addr + '/' + parser.get_attr()[1][1])))
            STATIC.ITEMCOUNT += 1
            if (args.verbose):
                print('Found new link at: ' + items[-1])
            else:
                textcounter()
    print('')
    return items

def HYPHUB_media_get_all_items(page):
    items = []
    parser = LinkTagParser()
    for line in page.splitlines():
        if 'href="//hypnohub.net//data/image/' in line:
            parser.feed(line)
            attr = 'http:' + parser.get_attr()[1][1]
            if (attr != '#'):
                items.append(attr)
                STATIC.ITEMCOUNT += 1
                if (args.verbose):
                    print('Found new link at: ' + attr)
                else:
                    textcounter()
    print('')
    return items

def get_booru_buffer(board):
    buffer = []
    url = create_booru_url(board + '.booru.org')
    if (args.verbose):
        print('Query URL = ' + url)
    i = 0
    while i < int(args.count):
        raw_html = (download_page(url + '&page=' + str(i + 1)))
        time.sleep(0.1)
        page_buffer = XBOORU_media_get_all_items(raw_html, args.source)
        if (len(page_buffer) < 1):
            break
        buffer += page_buffer
        i += 1
    return buffer

t0 = time.time()

items = []
iteration = "Current Query Keywords = " + str(' '.join(args.keywords))
print (iteration)
print ("Evaluating...")

if (not args.search_only):
    try:
        if (args.out_dir == None):
            os.makedirs(str(urllib2.unquote(str(' '.join(args.keywords)))))
        else:
            os.makedirs(args.out_dir)
    except OSError, e:
        if e.errno != 17:
            raise
        pass

if (args.count < 1):
    raise ValueError, 'count must be at least 1'
if (args.source == 'google' or args.source == 'all'):
    url = 'https://www.google.com/search?q=' + str('%20'.join(args.keywords)) + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
    if (args.verbose):
        print('Query URL = ' + url)
    raw_html =  (download_page(url))
    time.sleep(0.1)
    items = items + (GOOGLE_images_get_all_items(raw_html))
if (args.source == 'rule34.xxx' or args.source == 'all'):
    url = create_booru_url('rule34.xxx')
    if (args.verbose):
        print('Query URL = ' + url)
    i = 0
    while i < int(args.count):
        raw_html = (download_page(url + '&pid=' + str(i * 42)))
        time.sleep(0.1)
        buffer = R34XXX_media_get_all_items(raw_html)
        if (len(buffer) < 1):
            break
        items += buffer
        i += 1
if (args.source == 'rule34.paheal.net' or args.source == 'all'):
    url = 'http://rule34.paheal.net/post/list/' + str(urllib2.quote(' '.join(args.keywords))) + '/'
    if (args.verbose):
        print('Query URL = ' + url)
    i = 0
    while i < int(args.count):
        raw_html = (download_page(url + str(i + 1)))
        time.sleep(0.1)
        buffer = PAHEAL_media_get_all_items(raw_html)
        if (len(buffer) < 1):
            break
        items += buffer
        i += 1
if (args.source == 'danbooru' or args.source == 'all'):
    url = 'http://danbooru.donmai.us/posts?tags=' + create_valid_url_str()
    if (args.verbose):
        print('Query URL = ' + url)
    i = 0
    while i < int(args.count):
        raw_html = (download_page(url + '&page=' + str(i + 1)))
        time.sleep(0.1)
        buffer = DANBOR_media_get_all_items(raw_html)
        if (len(buffer) < 1):
            break
        items += buffer
        i += 1
if (args.source != 'danbooru' and args.source[-9:] == 'booru.org'):
    items += get_booru_buffer(args.source[:-10])
if (args.source == 'all' or args.source == 'all_boorus'):
    for board in booruBoards:
        items += get_booru_buffer(board)
if (args.source == 'hypnohub' or args.source == 'all'):
    url = 'http://hypnohub.net/post?tags=' + create_valid_url_str()
    if (args.verbose):
        print('Query URL = ' + url)
    i = 0
    while i < int(args.count):
        raw_html = (download_page(url + '&page=' + str(i + 1)))
        time.sleep(0.1)
        buffer = HYPHUB_media_get_all_items(raw_html)
        if (len(buffer) < 1):
            break
        items += buffer
        i += 1
#if (args.verbose): print ("Image Links = " + str(items))
print ("Total Image Links = " + str(len(items)))

if (args.link_file != None):
    info = open(args.link_file, 'a')
    info.write(str(args.keywords) + ": " + str(items) + "\n\n\n")
    info.close()

t1 = time.time()
total_time = t1 - t0
print("\nTotal time taken: " + str(total_time) + " Seconds")

if (args.search_only):
    sys.exit(0)

print ("Starting Download...")

k = 0
errorCount = 0
skipCount = 0
successCount = 0
while(k < len(items)):
    from urllib2 import Request, urlopen
    from urllib2 import URLError, HTTPError

    try:
        fextension = items[k].split('.')[-1].lower()
        if (fextension == 'webm'):
            if (not args.allow_webms):
                print("skipped -> image " + str(k + 1))
                skipCount += 1
                k += 1
                continue
        req = Request(items[k], headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req, None, 15)
        output_file = open(str(' '.join(args.keywords)) + "/" + str(binascii.b2a_hex(os.urandom(15))) + "." + fextension, 'wb')

        data = response.read()
        output_file.write(data)
        response.close()
        if (args.verbose):
            print("downloaded -> image " + str(k + 1))
        successCount += 1
    except IOError:
        errorCount += 1
        if (args.verbose):
            print("IOError -> image " + str(k + 1))
    except HTTPError as e:
        errorCount += 1
        if (args.verbose):
            print("HTTPError -> image " + str(k + 1))
    except URLError as e:
        errorCount += 1
        if (args.verbose):
            print("URLError -> image " + str(k + 1))
    k += 1
    if (not args.verbose):
        progress(k, len(items), "download progress")
print('')
if (successCount == 0):
    print("all downloads failed!")
else:
    print(str(len(items) - errorCount) + " / " + str(len(items)) + " downloads successful.")
    if (skipCount > 0):
        print(str(skipCount) + " skipped.")
    print('')