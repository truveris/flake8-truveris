from setuptools import setup

requires = [
    "flake8",
]
__pkg_version__ = "0.1"

setup(
    name="flake8_truveris",
    version=__pkg_version__,
    description=(
        "Flake8 extension for checking Python "
        "code against Truveris's code style guide"
    ),
    author="Truveris Inc.",
    author_email="engineering@truveris.com",
    url="http://github.com/truveris/flake8-truveris",
    download_url=(
        "https://github.com/truveris/flake8-truveris/tarball/{}"
        .format(__pkg_version__)
    ),
    install_requires=requires,
    packages=['flake8_truveris'],
    entry_points={
        "flake8.extension": [
            'T = flake8_truveris:CheckTruveris',
        ],
        "flake8.report": [
            'T = flake8_truveris:FormatTruveris',
        ],
    },
    classifiers=[
        "Framework :: Flake8",
    ],
    license='MIT',
)
