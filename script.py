import argparse
import os
import requests
import subprocess
import sys
import time

import gitlab # https://python-gitlab.readthedocs.io
import github # https://pygithub.readthedocs.io
import yaml # https://pyyaml.org/


FORGE_TYPE_GITHUB = "github"
FORGE_TYPE_GITLAB = "gitlab"

SSH_AGENT = "ssh-agent bash -c '"
# Quiet mode to avoid "Identity added" messages:
SSH_ADD = "ssh-add -q "
# Quiet mode to avoid 'Warning: Permanently added 'xxx' (ECDSA) to the list of known hosts.' messages:
GIT_SSH_PARAMS = 'GIT_SSH_COMMAND="ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "'
GIT_CLONE = 'git clone --mirror '
GIT_FETCH = "git fetch --prune"

has_error = False


def exec_command(cmd: str) -> int:
	execution = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	stripped_stdout = execution.stdout.rstrip()
	if len(stripped_stdout) > 0:
		print(stripped_stdout)

		if "remote: ERROR: A repository for this project does not exist yet." in stripped_stdout:
			# GitLab can have projects without repository. In such case, the
			# clone will fail. Catch this failure and ignore it.
			print("No repository cloned, because the project has no repository.")
			return 0
		if "remote: ERROR: You are not allowed to download code from this project." in stripped_stdout:
			# User may have access to a repository, but not to its code. In
			# such case, the clone will fail. Catch this failure and ignore it.
			print("No repository cloned, because you are not allowed to download the code.")
			return 0

	return execution.returncode


def get_forge_name(forge):
	if 'name' in forge:
		return forge['name']
	else:
		return forge['type']


def get_forge_exclude(forge):
	if 'exclude' in forge:
		return forge['exclude']
	else:
		return []


def handle_forge(root_folder, ssh_key_path, forge):
	if forge['type'] not in [FORGE_TYPE_GITHUB, FORGE_TYPE_GITLAB]:
		raise Exception("Forge type not supported: '{}'".format(forge['type']))

	folder = create_forge_folder(root_folder, get_forge_name(forge))

	if forge['type'] == FORGE_TYPE_GITHUB:
		handle_github_forge(folder, ssh_key_path, forge['token'], get_forge_exclude(forge))
	elif forge['type'] == FORGE_TYPE_GITLAB:
		sleep_duration = None
		if "sleep" in forge:
			sleep_duration = int(forge["sleep"])
		handle_gitlab_forge(folder, ssh_key_path, forge['url'], forge['token'], get_forge_exclude(forge), sleep_duration)


def handle_github_forge(save_folder, ssh_key_path, token, excluded_repositories):
	def _save_all(projects, title):
		print("* {}...".format(title))
		for p in projects:
			handle_repository(save_folder, p.full_name, p.ssh_url, ssh_key_path, excluded_repositories)

	print("** Saving repositories from GitHub...")

	gh = github.Github(token)

	_save_all(gh.get_user().get_repos(), "Repositories")
	_save_all(gh.get_user().get_starred(), "Starred repositories")


def handle_gitlab_forge(save_folder, ssh_key_path, forge_url, token, excluded_repositories, sleep_duration=None):
	def _save_all(projects, title):
		print("* {} repositories...".format(title))
		for p in projects:
			handle_repository(save_folder, p.path_with_namespace, p.ssh_url_to_repo, ssh_key_path, excluded_repositories)
			if sleep_duration is not None:
				time.sleep(sleep_duration)

	print("** Saving repositories from {}...".format(forge_url))

	gl = gitlab.Gitlab(forge_url, private_token=token)

	# See https://docs.gitlab.com/ee/api/members.html#roles for available roles for min_access_level
	_save_all(gl.projects.list(visibility='private', all=True), "Private")
	_save_all(gl.projects.list(visibility='internal', min_access_level=gitlab.const.REPORTER_ACCESS, all=True), "Internal")
	_save_all(gl.projects.list(visibility="public", min_access_level=gitlab.const.REPORTER_ACCESS, all=True), "Public")
	_save_all(gl.projects.list(starred=True, all=True), "Starred")


def create_forge_folder(root_folder, name):
	folder = os.path.join(root_folder, name)

	if not os.path.isdir(folder):
		# returns nothing, let's hope it will raise an exception if something went wrong:
		os.makedirs(folder)

	return folder


def handle_repository(save_folder, name, ssh_url, ssh_key_path, excluded_repositories):
	global has_error

	if name in excluded_repositories:
		print("!! Skipping {}".format(name))
		return

	print(name)

	save_folder_repo = os.path.join(save_folder, name)
	return_code = 0

	if not os.path.isdir(save_folder_repo):
		return_code = exec_command(git_clone_cmd(save_folder, save_folder_repo, ssh_url, ssh_key_path))
	else:
		return_code = exec_command(git_fetch_cmd(save_folder_repo, ssh_key_path))

	if return_code != 0:
		print("Getting repository '{}' failed with code {}.".format(
			save_folder_repo, return_code
		))
		has_error = True


def git_clone_cmd(save_folder, save_folder_repo, ssh_url, ssh_key_path):
	cd = 'cd ' + save_folder
	ssh_add = SSH_ADD + ssh_key_path + ";"
	git_clone = GIT_CLONE + ssh_url + " " + save_folder_repo

	return cd + " && " + SSH_AGENT + ssh_add + " " + GIT_SSH_PARAMS + " " + git_clone + "'"


def git_fetch_cmd(save_folder_repo, ssh_key_path):
	cd = 'cd ' + save_folder_repo
	ssh_add = SSH_ADD + ssh_key_path + ";"

	return cd + " && " + SSH_AGENT + ssh_add + " " + GIT_SSH_PARAMS + " " + GIT_FETCH + "'"


cli_parser = argparse.ArgumentParser()
cli_parser.add_argument("config_file", help="Configuration file in YAML format")
args = cli_parser.parse_args();

config_file = open(args.config_file, 'r')
config = yaml.load(config_file, Loader=yaml.FullLoader)

for forge in config['forges']:
	handle_forge(config['save_folder'], config['ssh_key'], forge)

if has_error:
	raise Exception("An error occured during the backup of (at least) one repository.")

if config['healthcheck_url'] is not None and config['healthcheck_url'] != "":
	requests.get(config['healthcheck_url'])
