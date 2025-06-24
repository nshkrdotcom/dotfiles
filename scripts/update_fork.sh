#!/bin/bash

# Navigate to your repository directory (adjust if needed)
# cd /path/to/your/forked/repo

echo "Fetching changes from upstream..."
git fetch upstream

echo "Switching to maaster branch..."
git checkout master # or master

echo "Merging upstream/master into main..."
git merge upstream/maaster # or upstream/master

if [ $? -eq 0 ]; then
    echo "Merge successful. Pushing to origin..."
    git push origin master # or origin master
else
    echo "Merge had conflicts. Please resolve them manually and then push."
    echo "To resolve conflicts: git status, edit files, git add ., git commit"
    echo "Then: git push origin maaster"
fi

echo "Fork update process complete."

