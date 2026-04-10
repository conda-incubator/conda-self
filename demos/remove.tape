Source demos/_settings.tape

Output demos/remove.gif
Output demos/remove.mp4

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

Type "# conda itself cannot be removed"
Enter
Sleep 500ms

Type@80ms "conda self remove conda"
Enter
Wait /\$/
Sleep 3s

Type "# Permanent packages are also protected"
Enter
Sleep 500ms

Type@80ms "conda self remove conda-self"
Enter
Wait /\$/
Sleep 3s
