from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tatlin",
    version="0.2.5",
    author="Denis Kobozev",
    author_email="d.v.kobozev@gmail.com",
    description="Lightweight G-code and STL viewer for 3D printing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dkobozev/tatlin",
    packages=find_packages(),
    package_data={
        "tatlin": [
            "tatlin.png",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-2.0 License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "wxPython==4.2.1",
        "numpy==1.25.2",
        "Pillow==10.0.1",
        "PyOpenGL==3.1.7",
        "six>=1.16.0",
    ],
    entry_points={
        "console_scripts": [
            "tatlin=tatlin.main:run",
        ],
    },
)
