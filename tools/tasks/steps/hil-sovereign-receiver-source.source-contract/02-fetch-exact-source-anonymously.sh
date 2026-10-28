git init .
git remote add origin https://github.com/StegVerse-org/LLM-adapter.git
git -c http.extraheader= fetch --depth 1 origin "$SOURCE_SHA"
git checkout --detach FETCH_HEAD
