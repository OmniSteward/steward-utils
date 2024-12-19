from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="steward-utils",
    version="0.1.0",
    author="Elliott Zheng",
    author_email="admin@hypercube.top",
    description="万能智能管家工具包，包含各种实用工具，能够轻松扩展实现自己的功能",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Omni-Steward/steward-utils",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "openai",
        "json-repair"
    ]
)