set -euo pipefail
test -z "${GITHUB_TOKEN:-}"
test -z "${GH_TOKEN:-}"
git init .
git remote add origin https://github.com/StegVerse-org/LLM-adapter.git
env -u GITHUB_TOKEN -u GH_TOKEN git fetch --depth=1 origin "${BASE_SHA}" "${HEAD_SHA}"
git checkout --detach "${HEAD_SHA}"
