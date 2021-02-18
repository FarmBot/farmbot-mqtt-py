from setuptools import setup

with open("README.md") as fh:
    long_description = fh.read()

with open("VERSION") as vers_fh:
    version = vers_fh.read()

setup(
    name="farmbot",
    version=version,
    description="Official FarmBot RPC wrapper library for Python.",
    py_modules=["farmbot"],
    package_dir={
        "": "farmbot"
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "paho-mqtt >= 1.5",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2"
        ]
    },
    url="https://github.com/farmbot-labs/farmbot-py",
    author="FarmBot, Inc.",
    author_email="contact@farmbot.io"
)
