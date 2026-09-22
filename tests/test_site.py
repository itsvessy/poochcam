from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urlsplit, unquote

SITE = Path(__file__).resolve().parents[1] / 'site'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = 0
        self.language = False
        self.title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1': self.headings += 1
        if tag == 'html': self.language = attrs.get('lang') == 'en'
        if tag == 'title': self.title = True
        for attribute in ['href', 'src']:
            if attribute in attrs: self.links.append(attrs[attribute])


class SiteTests(unittest.TestCase):
    def test_every_page_and_local_link(self):
        pages = list(SITE.rglob('*.html'))
        self.assertEqual(len(pages), 5)
        for page in pages:
            parser = Links()
            parser.feed(page.read_text())
            self.assertEqual(parser.headings, 1, str(page))
            self.assertTrue(parser.language and parser.title, str(page))
            for link in parser.links:
                url = urlsplit(link)
                if url.scheme or link.startswith('#'): continue
                target = (page.parent / unquote(url.path)).resolve()
                if target.is_dir(): target /= 'index.html'
                self.assertTrue(target.is_file(), str(target))
                self.assertTrue(target.is_relative_to(SITE), str(target))


if __name__ == '__main__':
    unittest.main()
