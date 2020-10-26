#!/usr/bin/env python3
import argparse
import os
import shutil
import sys

import requests
from demisto_sdk.commands.common.tools import run_command, print_error, print_success


def main():
    parser = argparse.ArgumentParser(description='Deploy a pack from a contribution PR to a branch')
    parser.add_argument('-p', '--pr_number', help='Contrib PR number')
    parser.add_argument('-b', '--branch', help='The contrib branch')
    parser.add_argument('-c', '--contrib_repo', help='The contrib repo')
    args = parser.parse_args()

    pr_number = args.pr_number
    repo = args.contrib_repo
    branch = args.branch
    pack_dir_name = get_pack_dir(branch, pr_number, repo)
    if not pack_dir_name:
        print_error('Did not find a pack in the PR')
        sys.exit(1)

    pack_dir = f'Packs/{pack_dir_name}'
    str_dir_names = ''
    try:
        for pack_dir in pack_dir_name:
            if os.path.isdir(f'Packs/{pack_dir}'):
                # Remove existing pack
                shutil.rmtree(f'Packs/{pack_dir}')
            str_dir_names += f' Packs/{pack_dir}'

        commands = [
            f'git remote add {repo} git@github.com:{repo}/content.git',
            f'git fetch {repo} {branch}',
            f'git checkout {repo}/{branch}{str_dir_names}'
        ]

        for command in commands:
            print(f'Running command {command}')
            run_command(command, is_silenced=False)
    except Exception as e:
        print_error(f'Failed to deploy contributed pack to base branch: {e}')
        sys.exit(1)

    print_success(f'Successfully updated the base branch with the contrib pack {pack_dir_name}')


def get_pack_dir(branch: str, pr_number: str, repo: str):
    """
    Get a pack dir name from a contribution pull request changed files
    Args:
        branch: The contrib branch
        pr_number: The contrib PR
        repo: The contrib repo

    Returns:
        A list of
        packs dir name, if found.
    """

    page = 1
    list_packs_dir_name = []
    while True:
        response = requests.get(f'https://api.github.com/repos/demisto/content/pulls/{pr_number}/files',
                                params={'page': str(page)})
        response.raise_for_status()
        files = response.json()
        if not files:
            break
        for pr_file in files:
            if pr_file['filename'].startswith('Packs/'):
                pack_dir_name = pr_file['filename'].split('/')[1]
                if pack_dir_name not in list_packs_dir_name:
                    list_packs_dir_name.append(pack_dir_name)
        page += 1

    print(f'Copy the changes from the contributor branch {repo}/{branch} in the pack {list_packs_dir_name}')
    return list_packs_dir_name


if __name__ == '__main__':
    main()
