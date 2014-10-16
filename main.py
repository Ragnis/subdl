import argparse
import locale
import os
import sys
from downloader import Downloader
from query import Query
from subclub import SubClub

if __name__ == "__main__":
    default_lang = locale.getdefaultlocale()[0][:2]

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Name or file to search")
    parser.add_argument("-c", "--count", type=int, default=1, help="Maximum number of files to download")
    parser.add_argument("-l", "--lang", default=default_lang, help="Language of the subtitles")

    args = parser.parse_args()

    name = args.file
    root = os.getcwd()
    is_file = os.path.isfile(name)

    if is_file:
        root = os.path.abspath(os.path.dirname(name))
        name = os.path.basename(name)

    query = Query.parse(name, is_file=is_file)

    if not query:
        print("Could not parse the query")
        sys.exit(1)

    print("Searching for matches...", end="", flush=True)

    dl = Downloader([
        SubClub()
    ])
    results = dl.get(query, args.count, args.lang)

    print(" found %i" % len(results))
    for file in results:
        print("Writing %s" % file.write(root))
