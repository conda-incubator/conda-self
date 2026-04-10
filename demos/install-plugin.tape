Source demos/_settings.tape

Output demos/install-plugin.gif
Output demos/install-plugin.mp4

Hide
Type `eval "$(pixi shell-hook -s bash -e dev)"`
Enter
Wait /\)/
Type `export PS1="$DEMO_PS1" CONDA_CHANNELS=conda-forge`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Install a conda plugin into the protected base"
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
