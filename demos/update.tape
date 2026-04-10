Source demos/_settings.tape

Output demos/update.gif
Output demos/update.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
# Downgrade conda so the update demo shows a real upgrade
Type `conda install --yes --quiet --override-frozen conda=26.1.1 2>&1 | tail -1`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Update conda and all its plugins"
Enter
Sleep 500ms

Type@80ms "conda self update --yes"
Enter
Wait /\$/
Sleep 3s
