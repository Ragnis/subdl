import re
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import http.client, urllib.parse
from query import Query
from subtitle_result import SubtitleResult
from subtitle_source import SubtitleSource
import util

class SubScene(SubtitleSource):
    def _convert_lang(self, lang):
        langs = {'et': 'estonian', 'en': 'english'}
        if lang in langs:
            return langs[lang]
        else:
            return 'english'

    def _find_movie_by_name(self, query, soup):
        sub_links = []

        for link in soup.find_all("a"):
            if not link.string:
                continue

            score = SequenceMatcher(None, query.name, link.string.lower()).ratio()
            if score < 0.5:
                continue

            sub_links.append({
                "url": link.get("href"),
                "score": score
            })

        sub_links = sorted(sub_links, key=lambda v: v["score"], reverse=True)

        if not sub_links:
            return None

        return sub_links[0]["url"]

    def _extract_rating(self, input):
        match = re.match(r".*(?P<rating>\d+)", input)

        if match:
            return int(match.group("rating"))

        return 0

    def find(self, query, lang=None):
        lang = self._convert_lang(lang)

        search = str(query)

        if query.filename and not query.pointer:
            search = query.filename

        params = urllib.parse.urlencode({"q": search})

        if not query.pointer and query.filename == query.name:
            soup = util.connect("subscene.com", "/subtitles/title?" + params)
            sub_links_page = self._find_movie_by_name(query, soup)
        else:
            sub_links_page = "/subtitles/release?" + params

        if not sub_links_page:
            return []

        soup = util.connect("subscene.com", sub_links_page)

        sub_links = []
        for sub in soup.find_all("a"):
            if lang not in sub.get("href"):
                continue

            spans = sub.find_all("span")
            if len(spans) <= 1 or not spans[0].contents:
                continue

            link_name = spans[1].contents[0].strip()
            link_query = Query.parse(link_name)

            if str(link_query.pointer) != str(query.pointer):
                continue

            if SequenceMatcher(None, query.name, link_query.name).ratio() < 0.8:
                continue

            sub_links.append({
                "filename": link_name + ".srt",
                "url": sub.get("href"),
                "score": SequenceMatcher(None, query.filename, link_name.lower()).ratio()
            })

        sub_links = sorted(sub_links, key=lambda v: v["score"], reverse=True)
        ret = []
        i = 0

        for item in sub_links:
            soup = util.connect("subscene.com", item["url"])
            dl_button = soup.find(id="downloadButton")
            dl_link = dl_button.get("href")

            rating = 0
            rating_title = soup.find("span", class_="rating-bar")

            if rating_title:
                rating = self._extract_rating(rating_title["title"])

            score = (rating / 10) * 0.15 + 0.6 * item["score"]
            result = SubtitleResult("http://subscene.com" + dl_link, score)
            result.target_name = item["filename"]
            result.zipped = True

            ret.append(result)
            i += 1
            if i == 10:
                break

        return ret
