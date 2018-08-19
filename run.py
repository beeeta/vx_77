from seven.core import vx,crawl_words,crawl_pic
import sys

if __name__ == '__main__':
    # if len(sys.argv) > 1 and 'reload' in sys.argv:
    crawl_words()
    crawl_pic()
    vx()