"""
Script to update a GitHub Gist with stats for a Code::Stats user.

Uses code stats api to fetch stats.
Supports various stats types, all resulting in different content for the gist.
Meant for Gists to be pinned on GitHub profile.

Test with
    python codestats_box.py test <codestats-user> <stats-type>
to only print content. To also test gist update, use:
    python codestats_box.py test <codestats-user> <stats-type> <gist-id> <github-token>
"""

import datetime
import math
import os
import sys
from collections import namedtuple
from itertools import takewhile
from typing import Any, Callable, Dict, List

import requests
from github import Github
from github.InputFileContent import InputFileContent

LabelAndValue = namedtuple("LabelAndValue", "title value")

# Type of stats
STATS_TYPE_LEVEL = "level-xp"
STATS_TYPE_RECENT_XP = "recent-xp"
STATS_TYPE_XP = "xp"
ALLOWED_STATS_TYPES = [
    STATS_TYPE_RECENT_XP,
    STATS_TYPE_XP,
    STATS_TYPE_LEVEL,
]
DEFAULT_STATS_TYPE = STATS_TYPE_LEVEL
# Dicts for stats type dependent values
VALUE_FORMAT = {
    STATS_TYPE_LEVEL: "lvl {level:>3} ({xp:>9,} XP)",
    STATS_TYPE_RECENT_XP: "lvl {level:>3} ({xp:>9,} XP) (+{recent_xp:>6,})",
    STATS_TYPE_XP: "{xp:>9,} XP",
}
GIST_TITLE = {
    STATS_TYPE_LEVEL: "💻 My Code::Stats XP (Top Languages)",
    STATS_TYPE_RECENT_XP: "💻 My Code::Stats XP (Recent Languages)",
    STATS_TYPE_XP: "💻 My Code::Stats XP (Top Languages)",
}
# Other configurable values
TOP_LANGUAGES_COUNT = 10
WIDTH_JUSTIFICATION_SEPARATOR = ":"
RECENT_STATS_SEPARATOR = " + "
TOTAL_XP_TITLE = "Total XP"
NO_RECENT_XP_LINES = [
    LabelAndValue("Not been coding recently", "🙈"),
    LabelAndValue("Probably busy with something else", "🗓"),
    LabelAndValue("Or just taking a break", "🌴"),
    LabelAndValue("But would be back to it soon!", "🤓"),
]
# Internal constants
MAX_LINE_LENGTH = 54
ENV_VAR_GIST_ID = "GIST_ID"
ENV_VAR_GITHUB_TOKEN = "GH_TOKEN"
ENV_VAR_CODE_STATS_USERNAME = "CODE_STATS_USERNAME"
ENV_VAR_STATS_TYPE = "STATS_TYPE"
REQUIRED_ENVS = [
    ENV_VAR_GIST_ID,
    ENV_VAR_GITHUB_TOKEN,
    ENV_VAR_CODE_STATS_USERNAME,
]
# Code stats API constants
CODE_STATS_URL_FORMAT = "https://codestats.net/api/users/{user}"
CODE_STATS_DATE_KEY = "dates"
CODE_STATS_TOTAL_XP_KEY = "total_xp"
CODE_STATS_TOTAL_NEW_XP_KEY = "new_xp"
CODE_STATS_LANGUAGES_KEY = "languages"
CODE_STATS_LANGUAGES_XP_KEY = "xps"
CODE_STATS_LANGUAGES_NEW_XP_KEY = "new_xps"
XP_TO_LEVEL = lambda xp: math.floor(0.025 * math.sqrt(xp))


def validate_and_init() -> bool:
    """Check environment variables present and valid."""
    env_vars_absent = [
        env
        for env in REQUIRED_ENVS
        if env not in os.environ or len(os.environ[env]) == 0
    ]
    if env_vars_absent:
        print(f"Please define {env_vars_absent} in your github secrets. Aborting...")
        return False

    if not (
        ENV_VAR_STATS_TYPE in os.environ
        and len(os.environ[ENV_VAR_STATS_TYPE]) > 0
        and os.environ[ENV_VAR_STATS_TYPE] in ALLOWED_STATS_TYPES
    ):
        print(f"Using default stats type: {DEFAULT_STATS_TYPE}")
        os.environ[ENV_VAR_STATS_TYPE] = DEFAULT_STATS_TYPE

    return True


def get_code_stats_response(user: str) -> Dict[str, Any]:
    """Get statistics from codestats for user."""
    return requests.get(CODE_STATS_URL_FORMAT.format(user=user)).json()


def __get_formatted_value(
    xp: int, recent_xp_supplier: Callable[[], int], stats_type: str
) -> str:
    """Get formatted value with xp and/or recent xp depending on stats type."""
    value_format = VALUE_FORMAT[stats_type]
    if stats_type == STATS_TYPE_LEVEL:
        return value_format.format(level=XP_TO_LEVEL(xp), xp=xp)
    elif stats_type == STATS_TYPE_RECENT_XP:
        recent_xp = recent_xp_supplier()
        formatted_value = value_format.format(
            level=XP_TO_LEVEL(xp), xp=xp, recent_xp=recent_xp
        )
        return formatted_value if recent_xp > 0 else formatted_value[:-9]
    elif stats_type == STATS_TYPE_XP:
        return value_format.format(xp=xp)
    raise RuntimeError(f"Unknown stats type {stats_type}")


def get_total_xp_line(
    code_stats_response: Dict[str, Any], stats_type: str
) -> LabelAndValue:
    """Get label and formatted value for total xp.

    Something along the lines of ("Total XP", "lvl  26 (1,104,152 XP)")
    """
    total_xp = code_stats_response[CODE_STATS_TOTAL_XP_KEY]
    recent_total_xp_supplier = lambda: code_stats_response[CODE_STATS_TOTAL_NEW_XP_KEY]
    formatted_value = __get_formatted_value(
        total_xp, recent_total_xp_supplier, stats_type
    )
    return LabelAndValue(TOTAL_XP_TITLE, formatted_value)


def __get_language_xp_line(
    language: str, language_stats: Dict[str, int], stats_type: str
) -> LabelAndValue:
    """Get label and formatted value for language xp.

    Something along the lines of ("Java", "lvl  19 (  580,523 XP)")
    """
    xp = language_stats[CODE_STATS_LANGUAGES_XP_KEY]
    recent_xp_supplier = lambda: language_stats[CODE_STATS_LANGUAGES_NEW_XP_KEY]
    formatted_value = __get_formatted_value(xp, recent_xp_supplier, stats_type)
    return LabelAndValue(language, formatted_value)


def get_language_xp_lines(
    code_stats_response: Dict[str, Any], stats_type: str
) -> List[LabelAndValue]:
    """Get list of labels and formatted values for languages.

    Decide which languages to include and return something like:
    [
        ("Java", "lvl  19 (  580,523 XP)"),
        ("Python", "lvl   7 (   82,719 XP)"),
    ]
    """
    if stats_type == STATS_TYPE_RECENT_XP:
        # Only considering languages with recent xp
        top_languages = list(
            takewhile(
                lambda t: t[1][CODE_STATS_LANGUAGES_NEW_XP_KEY] > 0,
                sorted(
                    code_stats_response[CODE_STATS_LANGUAGES_KEY].items(),
                    key=lambda t: t[1][CODE_STATS_LANGUAGES_NEW_XP_KEY],
                    reverse=True,
                )[:TOP_LANGUAGES_COUNT],
            ),
        )
        if not top_languages:
            return NO_RECENT_XP_LINES
    else:
        top_languages = sorted(
            code_stats_response[CODE_STATS_LANGUAGES_KEY].items(),
            key=lambda t: t[1][CODE_STATS_LANGUAGES_XP_KEY],
            reverse=True,
        )[:TOP_LANGUAGES_COUNT]
    return [
        __get_language_xp_line(language, stats, stats_type)
        for language, stats in top_languages
    ]


def get_adjusted_line(title_and_value: LabelAndValue) -> str:
    """Format given label and value to single string separated by configured separator.

    Something like (label, value) -> "label ::::::::::::: value"
    """
    separation = MAX_LINE_LENGTH - (
        len(title_and_value.title) + len(title_and_value.value) + 2
    )
    separator = f" {WIDTH_JUSTIFICATION_SEPARATOR * separation} "
    return title_and_value.title + separator + title_and_value.value


def update_gist(title: str, content: str) -> bool:
    """Update gist with provided title and content.

    Use gist id and github token present in environment variables.
    Replace first file in the gist.
    """
    access_token = os.environ[ENV_VAR_GITHUB_TOKEN]
    gist_id = os.environ[ENV_VAR_GIST_ID]
    gist = Github(access_token).get_gist(gist_id)
    # Works only for single file. Should we clear all files and create new file?
    old_title = list(gist.files.keys())[0]

    # Fetch current Gist content
    current_content = gist.files[old_title].content

    # Compare with new content
    if current_content == content:
        print("Gist content is already up-to-date. Skipping update.")
        return # Return without updating

    gist.edit(title, {old_title: InputFileContent(content, title)})
    print(f"{title}\n{content}")


def get_stats() -> str:
    """Get stats for codestats user according to stats type...

    ...both extracted from environment variables.
    """
    code_stats_user_name = os.environ[ENV_VAR_CODE_STATS_USERNAME]
    code_stats_response = get_code_stats_response(code_stats_user_name)

    stats_type = os.environ[ENV_VAR_STATS_TYPE]
    total_xp_line = get_total_xp_line(code_stats_response, stats_type)
    language_xp_lines = get_language_xp_lines(code_stats_response, stats_type)

    lines = [
        get_adjusted_line(title_and_value)
        for title_and_value in [total_xp_line, *language_xp_lines]
    ]
    return "\n".join(lines)


def main():
    """Validate prerequisites, get content and update gist."""
    if not validate_and_init():
        raise RuntimeError(
            "Validations failed! See the messages above for more information"
        )

    stats_type = os.environ[ENV_VAR_STATS_TYPE]
    title = GIST_TITLE[stats_type]
    content = get_stats()
    update_gist(title, content)


if __name__ == "__main__":
    import time

    s = time.perf_counter()
    if len(sys.argv) > 1:
        # Test run
        os.environ[ENV_VAR_CODE_STATS_USERNAME] = sys.argv[2]
        os.environ[ENV_VAR_STATS_TYPE] = sys.argv[3]
        if len(sys.argv) > 4:
            # Testing gist update too
            os.environ[ENV_VAR_GIST_ID] = sys.argv[4]
            os.environ[ENV_VAR_GITHUB_TOKEN] = sys.argv[5]
            main()
        else:
            # Testing stats content only
            print(get_stats())
    else:
        # Normal run
        main()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
