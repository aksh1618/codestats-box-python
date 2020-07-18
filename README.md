<p align='center'>
  <img src="art/codestats-box.png">
  <h3 align="center">codestats-box</h3>
  <p align="center">Update a pinned gist to contain your weekly Code::Stats stats</p>
</p>

---

> 📌✨ For more pinned-gist projects like this one, check out: https://github.com/matchai/awesome-pinned-gists

## 🎒 Prep Work

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
  - `recent`: (Default) Shows the past week in total as well as language wise recent xp
  - `skip-recent`: Skips the recent stats (the parts after the ` +`) and shows just the aggregate total and language XPs.

  (This can also be put directly in `.github/workflows/codestats.yml`)

## 🤓 Hacking

```bash
# setup
pipenv install --dev
# testing
pipenv run python codestats_box.py test <gist-id> <github-token> <user> <type>
# example
# pipenv run python codestats_box.py test test ce5221fc5f3739d2c81ce7db99f17519 cf9181618bf1618253d17161843f71a2bb161850 aksh recent
```
