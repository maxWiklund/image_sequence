from setuptools import setup
import image_sequence

setup(
    name="image_sequence",
    version=image_sequence.__version__,
    packages=["tests", "image_sequence"],
    url="",
    license="Apache License 2.0",
    author="Max Wiklund",
    author_email="info@maxwiklund.com",
    description="Library for representing file sequences.",
    py_modules=["image_sequence"],
)
