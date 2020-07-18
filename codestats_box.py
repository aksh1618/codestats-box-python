from collections import namedtuple
import datetime
import os
import sys
from typing import Any, Dict, List
from github.InputFileContent import InputFileContent

import requests
from github import Github

TOP_LANGUAGES_COUNT = 10
WIDTH_JUSTIFICATION_SEPARATOR = "·"
RECENT_STATS_SEPARATOR = " + "
PAST_WEEK_SUFFIX_STRING = " (past week)"
NEW_XP_SUFFIX_STRING = " (new xp)"
GIST_TITLE_FORMAT = "📊 Code::Stats XP for {user}"
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

CODE_STATS_URL_FORMAT = "https://codestats.net/api/users/{user}"
CODE_STATS_DATE_KEY = "dates"
CODE_STATS_TOTAL_XP_KEY = "total_xp"
CODE_STATS_LANGUAGES_KEY = "languages"
CODE_STATS_LANGUAGES_XP_KEY = "xps"
CODE_STATS_LANGUAGES_NEW_XP_KEY = "new_xps"

TitleAndValue = namedtuple("TitleAndValue", "title value")


def get_adjusted_line(title_and_value: TitleAndValue) -> str:
    separation = MAX_LINE_LENGTH - (
        len(title_and_value.title) + len(title_and_value.value)
    )
    return (
        title_and_value.title
        + WIDTH_JUSTIFICATION_SEPARATOR * separation
        + title_and_value.value
    )


def get_code_stats_response(user: str) -> Dict[str, Any]:
    return requests.get(CODE_STATS_URL_FORMAT.format(user=user)).json()


def get_total_xp_line(
    code_stats_response: Dict[str, Any], past_week: bool = True
) -> TitleAndValue:
    last_seven_days = [
        str(datetime.date.today() - datetime.timedelta(days=i)) for i in range(7)
    ]
    last_seven_days_xp = sum(
        [code_stats_response[CODE_STATS_DATE_KEY][day] for day in last_seven_days]
    )
    total_xp = code_stats_response[CODE_STATS_TOTAL_XP_KEY]
    total_xp_value = (
        f"{total_xp - last_seven_days_xp:,}"
        + (
            f"{RECENT_STATS_SEPARATOR}{last_seven_days_xp:,}{PAST_WEEK_SUFFIX_STRING}"
            if last_seven_days_xp > 0
            else ""
        )
        if past_week
        else f"{total_xp:,}"
    )
    return TitleAndValue("Total XP", total_xp_value)


def __get_language_xp_line(
    language: str, language_stats: Dict[str, int], recent: bool = True
) -> TitleAndValue:
    xp = language_stats[CODE_STATS_LANGUAGES_XP_KEY]
    recent_xp = language_stats[CODE_STATS_LANGUAGES_NEW_XP_KEY]
    language_xp_value = (
        f"{xp - recent_xp:,}"
        + (
            f"{RECENT_STATS_SEPARATOR}{recent_xp:,}{NEW_XP_SUFFIX_STRING}"
            if recent_xp > 0
            else ""
        )
        if recent
        else f"{xp:,}"
    )
    return TitleAndValue(language, language_xp_value)


def get_language_xp_lines(
    code_stats_response: Dict[str, Any], recent: bool = True
) -> List[TitleAndValue]:
    top_languages = sorted(
        code_stats_response[CODE_STATS_LANGUAGES_KEY].items(),
        key=lambda t: t[1][CODE_STATS_LANGUAGES_XP_KEY],
        reverse=True,
    )[:TOP_LANGUAGES_COUNT]
    return [
        __get_language_xp_line(language, stats, recent)
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
    envs_absent = [env for env in REQUIRED_ENVS if env not in os.environ]
    if envs_absent:
        print(f"Please define {envs_absent} in your github secrets. Aborting...")
        return

    code_stats_user_name = os.environ[ENV_VAR_CODE_STATS_USERNAME]

    code_stats_response = get_code_stats_response(code_stats_user_name)

    recent_stats = (
        True
        if ENV_VAR_STATS_TYPE not in os.environ
        else os.environ[ENV_VAR_STATS_TYPE] == "recent"
    )
    total_xp_line = get_total_xp_line(code_stats_response, recent_stats)
    language_xp_lines = get_language_xp_lines(code_stats_response, recent_stats)

    lines = [
        get_adjusted_line(title_and_value)
        for title_and_value in [total_xp_line, *language_xp_lines]
    ]
    update_gist(GIST_TITLE_FORMAT.format(user=code_stats_user_name), "\n".join(lines))


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
