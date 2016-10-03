from setuptools import setup

requires = [
    "flake8",
]

flake8_entry_point = "flake8.extension"

setup(
    name="flake8_truveris",
    version="0.1.0",
    description=(
        "Flake8 extension for checking Python "
        "code against Truveris's code style guide"
    ),
    author="Truveris Inc.",
    author_email="engineering@truveris.com",
    url="http://github.com/truveris/flake8-truveris",
    install_requires=requires,
    packages=['flake8_truveris'],
    entry_points={
        flake8_entry_point: [
            'T = flake8_truveris:CheckTruveris',
        ],
    },
    license='MIT',
)
