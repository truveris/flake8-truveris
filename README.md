# flake8-truveris
Flake8 extension for checking and formatting Python code against Truveris's code style guide

## Usage
To install it, just run:

```shell
pip install flake8-truveris
```

Once installed, `flake8` will automatically start using it whenever it's run.

All `flake8-truveris` error codes are prefixed with a `T`, so you can adjust your `flake8` config file accordingly depending on your needs.

## Formatting

In order to have the plugin automatically format your code, you will need to call `flake8` with the `--format` flag like so:

```shell
flake8 --format=T
```
