import os
import sys

def main():
    print("Bootstrapping QueryBridge Enterprise...")
    os.system("docker-compose -f docker-compose.yml up -d")
    print("System started.")

if __name__ == "__main__":
    main()
