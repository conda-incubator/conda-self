Source demos/_settings.tape

Output demos/reset.gif
Output demos/reset.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
# Install a plugin so reset has something to clean up
Type `conda self install --yes --quiet conda-index 2>&1 | tail -1`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Reset base to essential packages only"
Enter
Sleep 500ms

Type@80ms "conda self reset --yes"
Enter
Wait /\$/
Sleep 3s
