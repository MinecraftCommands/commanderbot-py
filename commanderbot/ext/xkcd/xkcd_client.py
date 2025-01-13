import random
import re
from dataclasses import dataclass
from datetime import date, datetime
from itertools import islice
from logging import Logger, getLogger
from typing import Any, AsyncIterable, Optional, Self

import aiohttp
from discord.utils import utcnow

from commanderbot.ext.xkcd.xkcd_exception import ComicNotFound
from commanderbot.ext.xkcd.xkcd_options import XKCDOptions
from commanderbot.lib import FromDataMixin, JsonObject, constants

BASE_URL: str = "https://xkcd.com"
ARCHIVE_URL: str = f"{BASE_URL}/archive/"
COMIC_URL: str = BASE_URL + "/{num}/"
API_URL: str = BASE_URL + "/{num}/info.0.json"

ARCHIVE_ENTRY_PATTERN = re.compile(
    r"<a href=\"/(?P<num>\d+)/\" title=\"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)\">(?P<title>.+?)</a><br/>"
)


@dataclass(frozen=True, slots=True)
class PartialXKCDComic(FromDataMixin):
    num: int
    title: str
    publication_date: date

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                num=int(data["num"]),
                title=data["title"],
                publication_date=date(
                    year=int(data["year"]),
                    month=int(data["month"]),
                    day=int(data["day"]),
                ),
            )

    @classmethod
    def comic_404(cls) -> Self:
        return cls(
            num=404, title="Not Found", publication_date=date(year=2008, month=4, day=1)
        )


@dataclass(frozen=True, slots=True)
class XKCDComic(FromDataMixin):
    num: int
    title: str
    description: str
    publication_date: date
    url: str
    image_url: str
    interactive: bool

    # @implements FromDataMixin
    @classmethod
    def try_from_data(cls, data: Any) -> Optional[Self]:
        if isinstance(data, dict):
            return cls(
                num=data["num"],
                title=data["title"],
                description=data["alt"],
                publication_date=date(
                    year=int(data["year"]),
                    month=int(data["month"]),
                    day=int(data["day"]),
                ),
                url=COMIC_URL.format(num=data["num"]),
                image_url=data["img"],
                interactive="extra_parts" in data,
            )

    @classmethod
    def comic_404(cls, image_url: str) -> Self:
        return cls(
            num=404,
            title="Not Found",
            description="Not found...",
            publication_date=date(year=2008, month=4, day=1),
            url=COMIC_URL.format(num=404),
            image_url=image_url,
            interactive=False,
        )


class XKCDClient:
    def __init__(self, cache_valid_for: int, comic_404_image_url: Optional[str]):
        self._log: Logger = getLogger(__name__)
        self._cache_valid_for: int = cache_valid_for
        self._comic_404_image_url: Optional[str] = comic_404_image_url

        self._archive_cache: dict[int, PartialXKCDComic] = {}
        self._comic_cache: dict[int, XKCDComic] = {}
        self._latest_comic_num: int = 0
        self._cache_retrieved: Optional[datetime] = None

    @classmethod
    def from_options(cls, options: XKCDOptions) -> Self:
        return cls(
            cache_valid_for=options.cache_valid_for,
            comic_404_image_url=options.comic_404_image_url,
        )

    async def _fetch_archive(self) -> dict[int, PartialXKCDComic]:
        self._log.debug("Fetching archive entries...")

        headers = {"User-Agent": constants.USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(ARCHIVE_URL) as response:
                # Return early if we didn't get an `OK` response
                if response.status != 200:
                    self._log.debug(
                        f"Tried to fetch the archive HTML and got a '{response.status}' status code"
                    )
                    return {}

                # Get the archive entries
                html: str = await response.text()
                archive_entries: dict[int, PartialXKCDComic] = {}
                for match in re.finditer(ARCHIVE_ENTRY_PATTERN, html):
                    entry = PartialXKCDComic.from_data(match.groupdict())
                    archive_entries[entry.num] = entry

                # Return the archive entries
                self._log.debug(f"Fetched {len(archive_entries)} archive entries")
                return archive_entries

    async def _fetch_comic(self, num: int) -> Optional[XKCDComic]:
        self._log.debug(f"Fetching comic #{num}...")

        headers = {"User-Agent": constants.USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(API_URL.format(num=num)) as response:
                # Return early if we didn't get an `OK` response
                if response.status != 200:
                    self._log.debug(
                        f"Tried to fetch the Json for comic #{num} but got a '{response.status}' status code"
                    )
                    return

                # Return the comic
                comic = XKCDComic.from_data(await response.json())
                self._log.debug(f"Fetched comic #{comic.num}")
                return comic

    async def _maybe_update_cache(self):
        # Return early if the cache is still valid
        if self._cache_retrieved:
            date_diff = utcnow() - self._cache_retrieved
            if date_diff.days < self._cache_valid_for:
                return

        # Try to fetch the archive entries
        archive_entries: dict[int, PartialXKCDComic] = await self._fetch_archive()
        if not archive_entries:
            return

        # Update caches and retrieval time
        self._archive_cache = archive_entries
        self._comic_cache.clear()
        self._cache_retrieved = utcnow()

        # Add the 404 comic if an image URL was supplied
        if self._comic_404_image_url:
            self._archive_cache[404] = PartialXKCDComic.comic_404()
            self._comic_cache[404] = XKCDComic.comic_404(self._comic_404_image_url)

        # Set the latest comic num
        self._latest_comic_num = max((c.num for c in self._archive_cache.values()))

    async def _get_comic_num(self, num: int) -> XKCDComic:
        # Return the comic if it already exists in the cache
        if cached_comic := self._comic_cache.get(num):
            return cached_comic

        # Throw an exception if the comic is not in the archive
        if num not in self._archive_cache.keys():
            raise ComicNotFound(num)

        # Try to get the comic and throw an exception if it couldn't be found
        comic: Optional[XKCDComic] = await self._fetch_comic(num)
        if not comic:
            raise ComicNotFound(num)

        # Add comic to the cache and return it
        self._comic_cache[comic.num] = comic
        return comic

    async def get_comics_matching(
        self,
        comic_filter: str,
        *,
        case_sensitive: bool = False,
        sort: bool = False,
        cap: Optional[int] = None,
    ) -> AsyncIterable[PartialXKCDComic]:
        # Update the cache
        await self._maybe_update_cache()

        # Get all comics that match the filter
        comics = []
        if comic_filter:
            comic_filter = comic_filter if case_sensitive else comic_filter.lower()
            for comic in self._archive_cache.values():
                comic_title: str = (
                    comic.title if case_sensitive else comic.title.lower()
                )
                if comic_filter in comic_title or comic_filter in str(comic.num):
                    comics.append(comic)
        else:
            comics = self._archive_cache.values()

        # Sort the comics if necessary
        maybe_sorted_comics = sorted(comics, key=lambda c: c.num) if sort else comics

        # Return all comics, or if `cap` is given, return `cap` number of comics
        for c in islice(maybe_sorted_comics, cap):
            yield c

    async def get_comic(self, num: int) -> XKCDComic:
        await self._maybe_update_cache()
        return await self._get_comic_num(num)

    async def get_latest_comic(self) -> XKCDComic:
        await self._maybe_update_cache()
        return await self._get_comic_num(self._latest_comic_num)

    async def get_random_comic(self) -> XKCDComic:
        await self._maybe_update_cache()
        return await self._get_comic_num(random.randint(1, self._latest_comic_num))
