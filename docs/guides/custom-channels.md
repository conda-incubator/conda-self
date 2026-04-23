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

## Why inline specs are rejected

`conda self install conda-forge::my-plugin` is not supported.
Inline channel specs would cause inconsistencies between install
and update operations -- the channel would apply to the install
but not to future updates, leading to unexpected solver behavior.

Instead, configure channels once and let all operations use the
same configuration.

## Channel priority

Channels are searched in the order they appear in your configuration.
The first channel with a matching package wins (in strict mode) or
packages from all channels are considered (in flexible mode).

You can inspect channels with [conda info](inv:conda:std:doc#commands/info) or by showing config values:

```bash
conda config --show channels
conda config --show channel_priority
```

## Private channels

For private channels that require authentication (e.g. on
anaconda.org or prefix.dev), configure tokens via:

```bash
conda token set <token> -c https://my-channel.example.com
```

Or use conda's standard authentication mechanisms. conda-self
inherits all authentication settings from your [conda configuration](inv:conda:std:doc#configuration).

## Multiple channels

If a plugin is available on multiple channels, conda will use the
one with highest priority:

```bash
conda config --add channels conda-forge -n base
conda config --add channels my-company-channel -n base

# my-company-channel has higher priority (added last)
conda self install my-plugin
```
