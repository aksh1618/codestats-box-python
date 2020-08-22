from collections import namedtuple
import datetime
import math
import os
import sys
from typing import Any, Dict, List
from github.InputFileContent import InputFileContent

import requests
from github import Github

TOP_LANGUAGES_COUNT = 10
WIDTH_JUSTIFICATION_SEPARATOR = ":"
RECENT_STATS_SEPARATOR = " + "
TOTAL_XP_TITLE = "Total XP"
PAST_WEEK_SUFFIX_STRING = " (past week)"
NEW_XP_SUFFIX_STRING = " (new xp)"
LEVEL_STRING_FORMAT = "lvl {level:>3} [{xp:>9,} XP]"
GIST_TITLE = "💻 My Code::Stats XP"
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

STATS_TYPE_RECENT_XP = "recent-xp"
STATS_TYPE_XP = "xp"
STATS_TYPE_LEVEL = "level-xp"
ALLOWED_STATS_TYPES = [
    STATS_TYPE_RECENT_XP,
    STATS_TYPE_XP,
    STATS_TYPE_LEVEL,
]
DEFAULT_STATS_TYPE = STATS_TYPE_LEVEL

CODE_STATS_URL_FORMAT = "https://codestats.net/api/users/{user}"
CODE_STATS_DATE_KEY = "dates"
CODE_STATS_TOTAL_XP_KEY = "total_xp"
CODE_STATS_LANGUAGES_KEY = "languages"
CODE_STATS_LANGUAGES_XP_KEY = "xps"
CODE_STATS_LANGUAGES_NEW_XP_KEY = "new_xps"

XP_TO_LEVEL = lambda xp: math.floor(0.025 * math.sqrt(xp))

TitleAndValue = namedtuple("TitleAndValue", "title value")


def validate_and_init() -> bool:
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


def get_adjusted_line(title_and_value: TitleAndValue) -> str:
    separation = MAX_LINE_LENGTH - (
        len(title_and_value.title) + len(title_and_value.value) + 2
    )
    separator = f" {WIDTH_JUSTIFICATION_SEPARATOR * separation} "
    return title_and_value.title + separator + title_and_value.value


def get_code_stats_response(user: str) -> Dict[str, Any]:
    return requests.get(CODE_STATS_URL_FORMAT.format(user=user)).json()


def get_total_xp_line(
    code_stats_response: Dict[str, Any], stats_type: str
) -> TitleAndValue:
    last_seven_days = [
        str(datetime.date.today() - datetime.timedelta(days=i)) for i in range(7)
    ]
    last_seven_days_xp = sum(
        [
            code_stats_response[CODE_STATS_DATE_KEY][day]
            for day in last_seven_days
            if day in code_stats_response[CODE_STATS_DATE_KEY]
        ]
    )
    total_xp = code_stats_response[CODE_STATS_TOTAL_XP_KEY]
    total_xp_value = ""
    if stats_type == STATS_TYPE_RECENT_XP:
        total_xp_value = f"{total_xp - last_seven_days_xp:,}" + (
            f"{RECENT_STATS_SEPARATOR}{last_seven_days_xp:,}{PAST_WEEK_SUFFIX_STRING}"
            if last_seven_days_xp > 0
            else ""
        )
    elif stats_type == STATS_TYPE_XP:
        total_xp_value = f"{total_xp:,}"
    elif stats_type == STATS_TYPE_LEVEL:
        total_xp_value = LEVEL_STRING_FORMAT.format(
            level=XP_TO_LEVEL(total_xp), xp=total_xp
        )
    return TitleAndValue(TOTAL_XP_TITLE, total_xp_value)


def __get_language_xp_line(
    language: str, language_stats: Dict[str, int], stats_type: str
) -> TitleAndValue:
    xp = language_stats[CODE_STATS_LANGUAGES_XP_KEY]
    recent_xp = language_stats[CODE_STATS_LANGUAGES_NEW_XP_KEY]
    language_xp_value = ""
    if stats_type == STATS_TYPE_RECENT_XP:
        language_xp_value = f"{xp - recent_xp:,}" + (
            f"{RECENT_STATS_SEPARATOR}{recent_xp:,}{NEW_XP_SUFFIX_STRING}"
            if recent_xp > 0
            else ""
        )
    elif stats_type == STATS_TYPE_XP:
        language_xp_value = f"{xp:,}"
    elif stats_type == STATS_TYPE_LEVEL:
        language_xp_value = LEVEL_STRING_FORMAT.format(level=XP_TO_LEVEL(xp), xp=xp)
    return TitleAndValue(language, language_xp_value)


def get_language_xp_lines(
    code_stats_response: Dict[str, Any], stats_type: str
) -> List[TitleAndValue]:
    top_languages = sorted(
        code_stats_response[CODE_STATS_LANGUAGES_KEY].items(),
        key=lambda t: t[1][CODE_STATS_LANGUAGES_XP_KEY],
        reverse=True,
    )[:TOP_LANGUAGES_COUNT]
    return [
        __get_language_xp_line(language, stats, stats_type)
        for language, stats in top_languages
    ]


def update_gist(title: str, content: str) -> bool:
    access_token = os.environ[ENV_VAR_GITHUB_TOKEN]
    gist_id = os.environ[ENV_VAR_GIST_ID]
    gist = Github(access_token).get_gist(gist_id)
    # Shouldn't necessarily work, keeping for case of single file made in hurry to get gist id.
    old_title = list(gist.files.keys())[0]
    gist.edit(title, {old_title: InputFileContent(content, title)})
    print(f"{title}\n{content}")


def main():

    if not validate_and_init():
        raise RuntimeError(
            "Validations failed! See the messages above for more information"
        )

    code_stats_user_name = os.environ[ENV_VAR_CODE_STATS_USERNAME]
    code_stats_response = get_code_stats_response(code_stats_user_name)

    stats_type = os.environ[ENV_VAR_STATS_TYPE]
    total_xp_line = get_total_xp_line(code_stats_response, stats_type)
    language_xp_lines = get_language_xp_lines(code_stats_response, stats_type)

    lines = [
        get_adjusted_line(title_and_value)
        for title_and_value in [total_xp_line, *language_xp_lines]
    ]
    content = "\n".join(lines)
    update_gist(GIST_TITLE, content)


if __name__ == "__main__":
    import time

    s = time.perf_counter()
    # test with python codestats_box.py test <gist> <github-token> <user> <type>
    if len(sys.argv) > 1:
        os.environ[ENV_VAR_GIST_ID] = sys.argv[2]
        os.environ[ENV_VAR_GITHUB_TOKEN] = sys.argv[3]
        os.environ[ENV_VAR_CODE_STATS_USERNAME] = sys.argv[4]
        os.environ[ENV_VAR_STATS_TYPE] = sys.argv[5]
    main()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
