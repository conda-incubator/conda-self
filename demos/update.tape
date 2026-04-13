Source demos/_settings.tape

Output demos/update.gif
Output demos/update.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
# Install an older plugin so the update has something to upgrade
# (use raw conda install to avoid pinning the version in history)
Type `conda install --yes --quiet --override-frozen conda-index=0.6.0 2>&1 | tail -1`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Update conda and all plugins"
Enter
Sleep 500ms

Type@80ms "conda self update --yes --all"
Enter
Wait /\$/
Sleep 3s
