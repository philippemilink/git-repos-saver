# git-repos-saver

A Python script to save Git repositories from GitHub.com, GitLab instances and
Forgejo instances.


## Installation

Requires at least Python 3.10.

```sh
pip install -r requirements.txt
```


## Configuration

Create an SSH key and register it in your forge settings. This key must not
have a passphrase.

You need an access token from each forge:
- for GitLab, a legacy token needs the scopes `read_api` and `read_repository`
  and a fine-grained token needs the scopes `Group > Projects > Project > Read`
  and `User > Projects > Project > Read`;
- for GitHub, the token needs the scope `repo`;
- for Forgejo, the token needs the scopes `user > Read` and `repository > Read`.

Copy the `config.yaml.dist` into `config.yaml` and adapt the configuration.

You can provide an URL to be pinged after all forges are saved.


## Execution

```sh
python script.py config.yaml
```
