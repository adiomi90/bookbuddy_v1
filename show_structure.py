#!/usr/bin/env python3
import os

def print_tree(start_path='.', prefix='', exclude_dirs=None, max_depth=3):
    if exclude_dirs is None:
        exclude_dirs = {'venv', '__pycache__', '.git', '.pytest_cache', 'node_modules'}
    
    if max_depth < 0:
        return
    
    try:
        items = sorted(os.listdir(start_path))
    except PermissionError:
        return
    
    items = [i for i in items if i not in exclude_dirs]
    
    for i, item in enumerate(items):
        path = os.path.join(start_path, item)
        is_last = (i == len(items) - 1)
        current_prefix = '└── ' if is_last else '├── '
        
        if os.path.isdir(path):
            print(f"{prefix}{current_prefix}{item}/")
            new_prefix = prefix + ('    ' if is_last else '│   ')
            print_tree(path, new_prefix, exclude_dirs, max_depth - 1)
        else:
            print(f"{prefix}{current_prefix}{item}")

if __name__ == '__main__':
    print(".")
    print_tree()