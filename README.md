# git-repos-saver
A Python script to save Git repos from GitHub and Gitlab


## Installation

```
sudo pip3 install -r requirements.txt
```


## Configuration

Create an SSH key and register it in your GitHub and Gitlab settings. This key
must not have a passphrase.

Copy the *config.yaml.dist* into *config.yaml* and adapt the configuration.

- For GitLab, the token needs the scopes `read_api` and `read_repository`.
- For GitHub, the token needs the scope `repo`.



## Execution

```
python3 script.py config.yaml
```

