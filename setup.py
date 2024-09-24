from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mintrans",
    version="1.0.2",
    author="Maehdakvan",
    author_email="visitanimation@google.com",
    maintainer="09u2h4n" ,
    maintainer_email="09u2h4n.y1lm42@gmail.com",
    description="Mintrans is a free API wrapper that utilizes Bing, DeepL, and Google Translate for translation purposes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DedInc/mintrans",
    project_urls={
        "Bug Tracker": "https://github.com/DedInc/mintrans/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    install_requires=["httpx"],
    python_requires=">=3.6",
)
