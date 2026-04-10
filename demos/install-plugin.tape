Source demos/_settings.tape

Output demos/install-plugin.gif
Output demos/install-plugin.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Install a conda plugin into the base environment"
Enter
Sleep 500ms

Type@80ms "conda self install --yes conda-index"
Enter
Wait /\$/
Sleep 3s

Type "# Inline channel specs are rejected"
Enter
Sleep 500ms

Type@80ms "conda self install conda-forge::some-plugin"
Enter
Wait /\$/
Sleep 3s
