Source demos/_settings.tape

Output demos/reset.gif
Output demos/reset.mp4

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

Type "# Reset base to essential packages only"
Enter
Sleep 500ms

Type@80ms "conda self reset --yes"
Enter
Wait /\$/
Sleep 3s
