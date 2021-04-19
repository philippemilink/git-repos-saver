import gitlab # https://python-gitlab.readthedocs.io
import github # https://pygithub.readthedocs.io
import yaml # https://pyyaml.org/
import argparse
import os
import sys
import requests

GITHUB_REPO = "github"
GITLAB_REPO = "gitlab"

SSH_AGENT = "ssh-agent bash -c '"
GIT_SSH_PARAMS = 'GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "'
GIT_CLONE = 'git clone --mirror '
GIT_FETCH = "git fetch --prune"


def handle_repo(root_folder, ssh_key_path, repo):
	if repo['type'] == GITHUB_REPO:
		folder = create_repo_folder(root_folder, GITHUB_REPO)
		handle_github_repo(folder, ssh_key_path, repo)
	elif repo['type'] == GITLAB_REPO:
		folder = create_repo_folder(root_folder, GITLAB_REPO)
		handle_gitlab_repo(folder, ssh_key_path, repo)
	else:
		raise Exception("Unknown repository type.")


def handle_github_repo(save_folder, ssh_key_path, repo):
	gh = github.Github(repo['token'])

	projects = gh.get_user().get_repos();
	for p in projects:
		save_project(save_folder, p.full_name, p.ssh_url, ssh_key_path)

	# also save starred repositories:
	starred = gh.get_user().get_starred();
	for s in starred:
		save_project(save_folder, s.full_name, s.ssh_url, ssh_key_path)


def handle_gitlab_repo(save_folder, ssh_key_path, repo):
	gl = gitlab.Gitlab('http://gitlab.com', private_token=repo['token'])

	private_projects = gl.projects.list(visibility='private', all=True)
	for p in private_projects:
		save_project(save_folder, p.path_with_namespace, p.ssh_url_to_repo, ssh_key_path)

	public_projects = gl.projects.list(visibility="public", owned=True, all=True)
	for p in public_projects:
		save_project(save_folder, p.path_with_namespace, p.ssh_url_to_repo, ssh_key_path)

	starred = gl.projects.list(starred=True, all=True)
	for s in starred:
		save_project(save_folder, s.path_with_namespace, s.ssh_url_to_repo, ssh_key_path)


def create_repo_folder(root_folder, name):
	folder = os.path.join(root_folder, name)

	if not os.path.isdir(folder):
		# returns nothing, let's hope it will raise an exception if something went wrong:
		os.makedirs(folder)

	return folder


def save_project(save_folder, name, ssh_url, ssh_key_path):
	print(name)

	save_folder_repo = os.path.join(save_folder, name)

	return_code = 0

	if not os.path.isdir(save_folder_repo):
		return_code = os.system(git_clone_cmd(save_folder, save_folder_repo, ssh_url, ssh_key_path))
	else:
		return_code = os.system(git_fetch_cmd(save_folder_repo, ssh_key_path))

	if return_code != 0:
		raise Exception("Getting repository '{}' failed with code {}.".format(
			save_folder_repo, return_code
		))


def git_clone_cmd(save_folder, save_folder_repo, ssh_url, ssh_key_path):
	cd = 'cd ' + save_folder
	ssh_add = "ssh-add " + ssh_key_path + ";"
	git_clone = GIT_CLONE + ssh_url + " " + save_folder_repo

	return cd + " && " + SSH_AGENT + ssh_add + " " + GIT_SSH_PARAMS + " " + git_clone + "'"


def git_fetch_cmd(save_folder_repo, ssh_key_path):
	cd = 'cd ' + save_folder_repo
	ssh_add = "ssh-add " + ssh_key_path + ";"

	return cd + " && " + SSH_AGENT + ssh_add + " " + GIT_SSH_PARAMS + " " + GIT_FETCH + "'"


cli_parser = argparse.ArgumentParser()
cli_parser.add_argument("config_file", help="Configuration file in YAML format")
args = cli_parser.parse_args();

config_file = open(args.config_file, 'r')
config = yaml.load(config_file, Loader=yaml.FullLoader)

for repo in config['repos']:
	handle_repo(config['save_folder'], config['ssh_key'], repo)

if config['healthcheck_url'] is not None and config['healthcheck_url'] != "":
	requests.get(config['healthcheck_url'])
