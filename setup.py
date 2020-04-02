import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="HubLatest",
    version="0.1.2",
    author="Codex-in-Somnio",
    author_email="yyy3752@gmail.com",
    description="Script to automatically download latest release from "
                "GitHub repos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Codex-in-somnio/HubLatest",
    license='MIT',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Version Control :: Git"
    ],

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    package_data={"": ["locale/*/*/*.mo"]},
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "hublatest=hublatest.hublatest:main",
        ]
    }
)
