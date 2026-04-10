Source demos/_settings.tape

Output demos/install-plugin.gif
Output demos/install-plugin.mp4

Hide
Type `source demos/_setup.sh`
Enter
Wait /\$/
# Pre-update conda so the install step only shows the plugin
Type `conda update --yes --quiet --override-frozen conda 2>&1 | tail -1`
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
