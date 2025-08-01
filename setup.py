from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="sq-slack-sync",
    version="0.1.0",
    author="Squadcast",
    author_email="support@squadcast.com",
    description="A tool to sync Squadcast on-call schedules with Slack user groups",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SquadcastHub/sq-slack-sync",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
)
