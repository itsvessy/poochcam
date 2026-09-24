from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

SITE = Path(__file__).resolve().parents[1] / 'site'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = 0
        self.language = False
        self.title = False
        self.canonical = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1': self.headings += 1
        if tag == 'html': self.language = attrs.get('lang') == 'en'
        if tag == 'title': self.title = True
        if tag == 'link' and attrs.get('rel') == 'canonical': self.canonical.append(attrs['href'])
        if tag == 'meta': self.meta[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        for attribute in ['href', 'src']:
            if attribute in attrs: self.links.append(attrs[attribute])


class SiteTests(unittest.TestCase):
    def test_every_page_and_local_link(self):
        pages = list(SITE.rglob('*.html'))
        self.assertEqual(len(pages), 6)
        for page in pages:
            parser = Links()
            parser.feed(page.read_text())
            self.assertEqual(parser.headings, 1, str(page))
            self.assertTrue(parser.language and parser.title, str(page))
            for link in parser.links:
                url = urlsplit(link)
                if url.scheme or link.startswith('#'): continue
                target = ((SITE / unquote(url.path).lstrip('/')) if url.path.startswith('/')
                          else (page.parent / unquote(url.path))).resolve()
                if target.is_dir(): target /= 'index.html'
                self.assertTrue(target.is_file(), str(target))
                self.assertTrue(target.is_relative_to(SITE), str(target))

    def test_missing_page_links_work_at_any_depth(self):
        parser = Links()
        parser.feed((SITE / '404.html').read_text())
        self.assertEqual(parser.meta.get('robots'), 'noindex')
        self.assertEqual(parser.canonical, [])
        self.assertIn('/', parser.links)
        self.assertIn('/support/', parser.links)
        for missing in ['/missing', '/deep/missing/page/', '/setup/missing.html']:
            for link in parser.links:
                if urlsplit(link).scheme or link.startswith('#'): continue
                resolved = urlsplit(urljoin('https://poochcam.ca' + missing, link))
                target = SITE / unquote(resolved.path).lstrip('/')
                if target.is_dir(): target /= 'index.html'
                self.assertTrue(target.is_file(), f'{missing}: {link}')

    def test_search_metadata_matches_real_pages(self):
        descriptions = set()
        expected = set()
        for page in SITE.rglob('index.html'):
            parser = Links()
            parser.feed(page.read_text())
            route = page.parent.relative_to(SITE).as_posix()
            canonical = 'https://poochcam.ca/' + (route + '/' if route != '.' else '')
            expected.add(canonical)
            self.assertEqual(parser.canonical, [canonical])
            self.assertEqual(parser.meta.get('og:url'), canonical)
            self.assertEqual(parser.meta.get('og:description'), parser.meta.get('description'))
            self.assertTrue(parser.meta.get('og:title'))
            self.assertNotIn('noindex', parser.meta.get('robots', ''))
            descriptions.add(parser.meta['description'])
        self.assertEqual(len(descriptions), 5)
        sitemap = ET.parse(SITE / 'sitemap.xml')
        urls = [entry.text for entry in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(set(urls), expected)
        self.assertEqual(len(urls), len(expected))
        self.assertIn('Sitemap: https://poochcam.ca/sitemap.xml', (SITE / 'robots.txt').read_text())


if __name__ == '__main__':
    unittest.main()
