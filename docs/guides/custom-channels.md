# Using custom channels

How to install plugins from custom or private channels.

## Configure channels first

conda-self uses your configured channels for all operations. Use
[conda config](inv:conda:std:doc#commands/config) to add a custom channel:

```bash
conda config --add channels my-channel -n base
```

Then install normally:

```bash
conda self install my-plugin
```

## Why channel-qualified package specs are rejected

`conda self install conda-forge::my-plugin` is not supported.
Channel-qualified package specs would cause inconsistencies between install
and update operations -- the channel would apply to the install but not to
future updates, leading to unexpected solver behavior.

Instead, configure channels once and let all operations use the
same configuration.

## Channel priority

Channels are searched in the order they appear in your configuration. With
strict channel priority, packages from lower-priority channels are not
considered when a package with the same name exists in a higher-priority
channel. With flexible priority, the solver may use lower-priority channels to
satisfy dependencies.

You can inspect channels with [conda info](inv:conda:std:doc#commands/info) or
by showing configuration values:

```bash
conda config --show channels
conda config --show channel_priority
```

## Private channels

For private channels that require authentication, install an authentication
handler such as `conda-auth`, then log in:

```bash
conda self install conda-auth
conda auth login https://my-channel.example.com --token
```

The login command prompts for the token and stores the credentials for conda.
conda-self invokes conda for package operations, so it uses the same stored
credentials.

## Multiple channels

With strict channel priority, if a plugin is available on multiple channels,
conda will use the one with highest priority:

```bash
conda config --add channels conda-forge -n base
conda config --add channels my-company-channel -n base

# my-company-channel has higher priority (added last)
conda self install my-plugin
```
