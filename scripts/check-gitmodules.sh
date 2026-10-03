#!/usr/bin/env bash
# Every submodule URL in .gitmodules must point at the project's repositories
# (github.com/markjfisher/...). To test against a fork, override the URL in
# your local git config instead of committing it:
#   git config submodule.repos/fujinet-nio.url git@github.com:<you>/fujinet-nio.git
#   git submodule sync repos/fujinet-nio
set -euo pipefail

cd "$(dirname "$0")/.."
bad=$(git config -f .gitmodules --get-regexp '^submodule\..*\.url$' |
      awk '$2 !~ /^(git@github\.com:|https:\/\/github\.com\/)markjfisher\// { print "  " $0 }')
if [ -n "$bad" ]; then
    echo ".gitmodules points submodules away from markjfisher/:"
    echo "$bad"
    echo "Use 'git config submodule.<path>.url <fork>' locally; don't commit fork URLs."
    exit 1
fi
echo ".gitmodules: all $(git config -f .gitmodules --get-regexp '^submodule\..*\.url$' | wc -l) submodule URLs point at markjfisher/"
