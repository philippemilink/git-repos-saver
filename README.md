# git-repos-saver

A Python script to save Git repositories from GitHub.com and GitLab instances.


## Installation

Requires at least Python 3.9.

```sh
pip install -r requirements.txt
```


## Configuration

Create an SSH key and register it in your GitHub and/or GitLab settings. This key
must not have a passphrase.

You need an access token from each forge:
- for GitLab, the token needs the scopes `read_api` and `read_repository`,
- for GitHub, the token needs the scope `repo`.

Copy the `config.yaml.dist` into `config.yaml` and adapt the configuration.

You can provide an URL to be pinged after all forges are saved.


## Execution

```sh
python script.py config.yaml
```

