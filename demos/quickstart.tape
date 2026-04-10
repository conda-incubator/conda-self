Source demos/_settings.tape

Output demos/quickstart.gif
Output demos/quickstart.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Check base environment protection"
Enter
Sleep 500ms

Type@80ms "conda doctor base-protection"
Enter
Wait /\$/
Sleep 2s

Type "# Install a plugin"
Enter
Sleep 500ms

Type@80ms "conda self install --yes conda-index"
Enter
Wait /\$/
Sleep 3s

Type "# Update all plugins"
Enter
Sleep 500ms

Type@80ms "conda self update --yes"
Enter
Wait /\$/
Sleep 3s

Type "# Reset to essentials"
Enter
Sleep 500ms

Type@80ms "conda self reset --yes"
Enter
Wait /\$/
Sleep 3s
