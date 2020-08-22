<p align='center'>
  <img src="art/codestats-box.png">
  <h3 align="center">codestats-box-python</h3>
  <p align="center">💻 Update a pinned gist to contain your Code::Stats stats</p>
  <p align="center">
    <img src="https://github.com/aksh1618/codestats-box-python/workflows/Update%20gist%20with%20Code::Stats%20stats/badge.svg?branch=master" alt="Update gist with Code::Stats stats">
  </p>
</p>

---

> 📌✨ For more pinned-gist projects like this one, check out: https://github.com/matchai/awesome-pinned-gists

## 🎒 Prep Work

0. Make sure you have a Code::Stats account! (Get one at https://codestats.net/ if you don't!)
1. Create a new public GitHub Gist (https://gist.github.com/)
2. Create a token with the `gist` scope and copy it. (https://github.com/settings/tokens/new)
3. Copy the `API token`

## 🖥 Project Setup

1. Fork this repo
2. Go to your fork's `Settings` > `Secrets` > `Add a new secret` for each environment secret (below)

## 🤫 Environment Secrets

- **GH_TOKEN:** The GitHub token generated above.
- **GIST_ID:** The ID portion from your gist url:

  `https://gist.github.com/aksh1618/`**`ce5221fc5f3739d2c81ce7db99f17519`**.

  (Alternatively this can be put directly in `.github/workflows/codestats.yml` as it is public anyway.)
- **CODE_STATS_USERNAME:** Your [Code::Stats](https://codestats.net) username. (This can also be put directly in the yml)

- **STATS_TYPE:** (Optional) Type of stats, supported values:

  - `level-xp`: (Default) Shows total and language XPs with level, sorted by XP:

      ```none
      💻 My Code::Stats XP (Top Languages)
      Total XP :::::::::::::::::::::: lvl  26 (1,104,152 XP)
      Java :::::::::::::::::::::::::: lvl  19 (  580,523 XP)
      ```

  - `recent-xp`: Shows total and language XPs with level and recent xp, sorted by recent XP:

      ```none
      💻 My Code::Stats XP (Recent Languages)
      Total XP ::::::::::::: lvl  26 (1,104,152 XP) (+1,874)
      Python ::::::::::::::: lvl   7 (   82,719 XP) (+1,789)
      ```

  - `xp`: Shows total and language XPs, sorted by XP:

      ```none
      💻 My Code::Stats XP (Top Languages)
      Total XP :::::::::::::::::::::::::::::::: 1,104,152 XP
      Java ::::::::::::::::::::::::::::::::::::   580,523 XP
      ```

  (This can also be put directly in `.github/workflows/codestats.yml`)

## 🤓 Hacking

```bash
# setup
pipenv install --dev
# testing
# only content
pipenv run python codestats_box.py test <codestats-user> <stats-type>
# content and gist update
pipenv run python codestats_box.py test <codestats-user> <stats-type> <gist-id> <github-token>
# example
# pipenv run python codestats_box.py test aksh recent-xp ce5221fc5f3739d2c81ce7db99f17519 cf9181618bf1618253d17161843f71a2bb161850
```
