import asyncio
import re
from logging import Logger, getLogger
from typing import Optional, Self

import mccq.errors
from mccq.query_manager import QueryManager, QueryResults
from mccq.version_database import VersionDatabase

from commanderbot.ext.mccq.mccq_exceptions import (
    FailedToLoadData,
    InvalidArguments,
    InvalidRegex,
    NoVersionsAvailable,
    QueryReturnedNoResults,
)
from commanderbot.ext.mccq.mccq_options import MCCQManagerOptions


class MCCQManager:
    def __init__(
        self,
        url: str,
        version_file: str,
        version_whitelist: list[str],
        show_versions: list[str],
        version_labels: dict[str, str],
        max_results: Optional[int],
        wiki_url: Optional[str],
        logger_name: str,
    ):
        self._log: Logger = getLogger(logger_name)
        self._version_labels: dict[str, str] = version_labels
        self._max_results: Optional[int] = max_results
        self._wiki_url: Optional[str] = wiki_url
        self._query_manager = QueryManager(
            database=VersionDatabase(
                uri=url,
                version_file=version_file,
                whitelist=version_whitelist,
            ),
            show_versions=show_versions,
        )

    @classmethod
    def from_java_options(cls, options: MCCQManagerOptions) -> Self:
        return cls(
            url=options.url,
            version_file=options.version_file,
            version_whitelist=options.version_whitelist,
            show_versions=options.show_versions,
            version_labels=options.version_labels,
            max_results=options.max_results,
            wiki_url=options.wiki_url,
            logger_name="commanderbot.ext.mccq.java_manager",
        )

    @classmethod
    def from_bedrock_options(cls, options: MCCQManagerOptions) -> Self:
        return cls(
            url=options.url,
            version_file=options.version_file,
            version_whitelist=options.version_whitelist,
            show_versions=options.show_versions,
            version_labels=options.version_labels,
            max_results=options.max_results,
            wiki_url=options.wiki_url,
            logger_name="commanderbot.ext.mccq.bedrock_manager",
        )

    async def _do_query(self, query: str) -> tuple[QueryResults, int]:
        try:
            # Get the query results
            full_results = await asyncio.to_thread(self._query_manager.results, query)
            num_full_results = sum(len(lines) for lines in full_results.values())

            # Return early if result trimming is disabled
            if not self._max_results:
                return (full_results, 0)

            # Return early if we don't need to trim any results
            if num_full_results <= self._max_results:
                return (full_results, 0)

            # Trim results
            trimmed_results = {}
            num_results = 0
            for version, lines in full_results.items():
                trimmed_results[version] = []
                for line in lines:
                    trimmed_results[version].append(line)
                    num_results += 1
                    if num_results == self._max_results:
                        break
                if num_results == self._max_results:
                    break

            num_trimmed_results = num_full_results - self._max_results
            return (trimmed_results, num_trimmed_results)

        except mccq.errors.ArgumentParserFailed:
            self._log.info(f"Failed to parse arguments for the command: {query}")
            raise InvalidArguments

        except mccq.errors.NoVersionsAvailable:
            self._log.info(f"No versions available for the command: {query}")
            raise NoVersionsAvailable

        except (mccq.errors.LoaderFailure, mccq.errors.ParserFailure):
            self._log.exception(f"Failed to load data for the command: {query}")
            raise FailedToLoadData

        except re.error:
            self._log.info(f"Invalid regex for the command: {query}")
            raise InvalidRegex

    def _get_version_label(self, version: str) -> str:
        if label := self._version_labels.get(version):
            actual_version: str = (
                self._query_manager.database.get_actual_version(version) or version
            )
            return label.format(version=version, actual=actual_version)
        return version

    async def query_command(self, query: str) -> tuple[str, Optional[str]]:
        # Get the query results
        results, num_trimmed_results = await self._do_query(query)

        # Raise an exception to let the user know there were no results
        # Note: This is different from an invalid base command
        if not results:
            raise QueryReturnedNoResults

        # If any version produced more than one command, create one paragraph per version
        formatted_results: str = ""
        if any((len(v) > 1 for v in results.values())):
            paragraphs = (
                "\n".join((f"# {self._get_version_label(version)}", *lines))
                for version, lines in results.items()
            )
            formatted_results = "\n".join(paragraphs)

        # Otherwise, if all versions produced just 1 command, create one line per version (compact)
        else:
            formatted_results = "\n".join(
                (
                    f"{lines[0]}  # {self._get_version_label(version)}"
                    for version, lines in results.items()
                    if lines
                )
            )

        # If results were trimmed, make note of them
        if num_trimmed_results:
            formatted_results += f"\n# ... trimmed {num_trimmed_results} results"

        # Try to create the wiki URL
        wiki_url: Optional[str] = None
        if self._wiki_url:
            base_commands: set[str] = set()
            for lines in results.values():
                for line in lines:
                    base_commands.add(line.split(maxsplit=1)[0])

            # Only return the wiki URL if we can unambiguously determine the base command
            if len(base_commands) == 1 and (cmd := next(iter(base_commands))):
                wiki_url = self._wiki_url.format(command=cmd)

        return (formatted_results, wiki_url)

    def reload(self):
        self._query_manager.reload()
