Source demos/_settings.tape

Output demos/base-protection.gif
Output demos/base-protection.mp4

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

Type "# Check if your base environment is protected"
Enter
Sleep 500ms

Type@80ms "conda doctor base-protection"
Enter
Wait /\$/
Sleep 3s

Type "# Enable protection: clone base, reset to essentials, freeze"
Enter
Sleep 500ms

Type@80ms "conda doctor base-protection --fix --yes"
Enter
Wait /\$/
Sleep 3s

Type "# Verify protection status"
Enter
Sleep 500ms

Type@80ms "conda doctor base-protection"
Enter
Wait /\$/
Sleep 3s
