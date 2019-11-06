import re
import requests
import appdirs
from lxml import etree
from argparse import ArgumentParser
from cachelib import FileSystemCache, NullCache

CACHE_DIR = appdirs.user_cache_dir('translate_it')
CACHE_ENTRY_MAX = 128

cache = FileSystemCache(CACHE_DIR, CACHE_ENTRY_MAX, default_timeout=0)


def get_content(words):
    res = requests.get(f'https://dict.youdao.com/w/{words}')
    res.raise_for_status()
    return res.text


def parse(response):
    html = etree.HTML(response)
    contents = html.xpath('//div[@id="results-contents"]')[0]
    container = contents.xpath('//div[@class="trans-container"]/ul')
    results = []
    if len(container) > 0:
        results = container[0].xpath('li/text()')
        if len(results) > 0:
            results = [result for result in results if result.strip()]
        else:
            for word in container[0].xpath('p'):
                klass = word.xpath('string(span[1])')
                value = word.xpath('string(span[2]/a)')
                results.append(f'{klass} {value}')
    return results


def tran(words):
    words = ' '.join(words)
    results = cache.get(words)
    if not results:
        response = get_content(words)
        results = [re.sub(r'\s', '', result) for result in parse(response)]
        if results:
            cache.set(words, results)

    return results


def get_parser():

    parser = ArgumentParser(description='To help you translate')
    parser.add_argument('words', metavar='WORDS', type=str,
                        nargs='*', help='the words to translate')

    return parser


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())

    if not args['words']:
        parser.print_help()
        return

    for word in tran(args['words']):
        print(word)


if __name__ == '__main__':
    command_line_runner()
