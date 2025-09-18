#!/usr/bin/env python
"""
Script to generate a secure Django SECRET_KEY
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    print("Generated SECRET_KEY:")
    print(get_random_secret_key())