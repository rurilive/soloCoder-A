#!/usr/bin/env python3
import sys
import os
from pathlib import Path

PORT = 8765

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_platform.settings')
    
    from django.core.management import execute_from_command_line
    
    print(f'Starting API Platform on port {PORT}...')
    print(f'URL: http://localhost:{PORT}')
    
    execute_from_command_line([sys.argv[0], 'runserver', f'0.0.0.0:{PORT}'])

if __name__ == '__main__':
    main()
