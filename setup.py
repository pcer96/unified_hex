from setuptools import setup, find_packages

setup(
    name="unified-hex-harvest",
    version="1.0.0",
    description="Centralized experiment analysis library for Harvest Hex notebooks",
    author="Your Team",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "plotly>=5.0.0",
        "pandas-gbq",
        "scipy",
        "slack-sdk",
        "kaleido",
        "matplotlib",
        # Add other dependencies from your current notebook
    ],
    python_requires=">=3.8",
)
