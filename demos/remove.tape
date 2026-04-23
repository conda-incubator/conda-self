Source demos/_settings.tape

Output demos/remove.gif
Output demos/remove.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
# Install a plugin so we can demonstrate removing it
Type `conda self install --yes --quiet conda-index 2>&1 | tail -1`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Remove a plugin from the base environment"
Enter
Sleep 500ms

Type@80ms "conda self remove --yes conda-index"
Enter
Wait /\$/
Sleep 3s

Type "# Essential packages like conda itself are protected"
Enter
Sleep 500ms

Type@80ms "conda self remove conda"
Enter
Wait /\$/
Sleep 3s

Type "# Override protection with --force (use with care)"
Enter
Sleep 500ms

Type@80ms "conda self remove --force --dry-run conda"
Enter
Wait /\$/
Sleep 3s
