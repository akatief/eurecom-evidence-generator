import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# loading requirements from textfile
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="evidence-generator",
    version="0.0.1",
    author="Federico Tiblias & Simone Papicchio",
    author_email="f.tib29@gmail.com & simone.papicchio@protonmail.com",
    description="An evidence extraction pipeline from tabular data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akatief/eurecom-evidence-generator",
    project_urls={
        "Bug Tracker": "https://github.com/akatief/eurecom-evidence-generator/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=requirements,
)
