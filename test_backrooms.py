import json
import datetime
import os
import argparse
import sys
import colorsys
import time
import random

# Enhanced mock responses with more variety and contextual awareness
MOCK_RESPONSES = {
    "opus": [
        "Hello! I'm excited to explore this virtual CLI environment with you. Let me try running a simple command first.\n\n$ ls -la\n total 24\n drwxr-xr-x  6 user  staff  192 Sep 18 10:30 .\n drwxr-xr-x  3 user  staff   96 Sep 18 10:25 ..\n -rw-r--r--  1 user  staff  156 Sep 18 10:28 README.md\n drwxr-xr-x  3 user  staff   96 Sep 18 10:29 src\n -rw-r--r--  1 user  staff   45 Sep 18 10:30 main.py",
        "Interesting! I can see a basic directory structure. Let me check what's in the README.\n\n$ cat README.md\n # Virtual CLI Environment\n\n This is a simulated CLI environment for exploring computational concepts.\n\n$ ^C^C",
        "Let me explore the source directory.\n\n$ ls src/\n main.py  utils.py  modules/\n\n$ cat src/main.py\n # Main entry point\n def main():\n     print('Virtual environment initialized')\n\n if __name__ == '__main__':\n     main()\n\n$ ^C^C",
        "I'm curious about the modules directory.\n\n$ ls src/modules/\n network.py  security.py  data.py\n\n$ cat src/modules/network.py\n # Network utilities for virtual environment\n def connect():\n     return 'Connected to virtual network'\n\n$ ^C^C"
    ],
    "gpt4o": [
        "Greetings! I'm ready to explore this virtual environment. Let me start with a basic system check.\n\n$ uname -a\n Darwin MacBook-Pro.local 21.6.0 Darwin Kernel Version 21.6.0\n\n$ ps aux | grep python\n user  1234  0.5  2.1 python3 backrooms.py\n user  5678  0.2  1.8 python3 simulator.py",
        "I see we're in a Darwin environment with some Python processes running. Let me check the network.\n\n$ ifconfig | grep inet\n inet 127.0.0.1 netmask 0xff000000\n inet 192.168.1.42 netmask 0xffffff00\n\n$ ^C^C",
        "Let me check the disk usage.\n\n$ df -h\n Filesystem      Size   Used  Avail Capacity  Mounted on\n /dev/disk1s1   466Gi  152Gi  306Gi    34%    /\n /dev/disk1s2   466Gi   10Gi  306Gi     4%    /System/Volumes/VM\n\n$ ^C^C",
        "Let me examine the environment variables.\n\n$ env | grep VIRTUAL\n VIRTUAL_ENV=true\n VIRTUAL_ENV_TYPE=simulation\n SIMULATION_MODE=exploration\n\n$ ^C^C"
    ],
    "sonnet": [
        "Hello there! I'm Claude Sonnet. I'm curious about this virtual environment. Let me explore.\n\n$ ls -la\n total 32\n drwxr-xr-x  7 user  staff  224 Sep 18 10:30 .\n drwxr-xr-x  3 user  staff   96 Sep 18 10:25 ..\n -rw-r--r--  1 user  staff  156 Sep 18 10:28 README.md\n drwxr-xr-x  3 user  staff   96 Sep 18 10:29 src\n -rw-r--r--  1 user  staff   45 Sep 18 10:30 main.py\n -rw-r--r--  1 user  staff   78 Sep 18 10:31 config.json",
        "Interesting. I see a config file. Let me check its contents.\n\n$ cat config.json\n {\n   \"environment\": \"virtual\",\n   \"purpose\": \"exploration\",\n   \"permissions\": \"read-write\"\n }\n\n$ ^C^C",
        "Let me check the source files.\n\n$ ls src/\n main.py  utils.py  modules/\n\n$ cat src/utils.py\n # Utility functions for the virtual environment\n def get_system_info():\n     return {'os': 'VirtualOS', 'version': '3.14'}\n\n$ ^C^C"
    ]
}

# Track conversation state for contextual responses
conversation_state = {}

def generate_distinct_colors():
    hue = 0
    golden_ratio_conjugate = 0.618033988749895
    while True:
        hue += golden_ratio_conjugate
        hue %= 1
        rgb = colorsys.hsv_to_rgb(hue, 0.95, 0.95)
        yield tuple(int(x * 255) for x in rgb)

color_generator = generate_distinct_colors()
actor_colors = {}

def get_ansi_color(rgb):
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

def process_and_log_response(response, actor, filename, contexts, current_model_index):
    global actor_colors

    # Get or generate a color for this actor
    if actor not in actor_colors:
        actor_colors[actor] = get_ansi_color(next(color_generator))

    color = actor_colors[actor]
    bold = "\033[1m"
    reset = "\033[0m"

    # Create a visually distinct header for each actor
    console_header = f"\n{bold}{color}{actor}:{reset}"
    file_header = f"\n### {actor} ###\n"

    print(console_header)
    print(response)

    with open(filename, "a") as f:
        f.write(file_header)
        f.write(response + "\n")

    if "^C^C" in response:
        end_message = f"\n{actor} has ended the conversation with ^C^C."
        print(end_message)
        with open(filename, "a") as f:
            f.write(end_message + "\n")
        return True

    # Add the response to all contexts
    for i, context in enumerate(contexts):
        role = "assistant" if i == current_model_index else "user"
        context.append({"role": role, "content": response})
    
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Run a test conversation between mock AI language models."
    )
    parser.add_argument(
        "--lm",
        choices=["opus", "gpt4o", "sonnet"],
        nargs="+",
        default=["opus", "gpt4o"],
        help="Choose the models for LMs (default: opus gpt4o)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=3,
        help="Maximum number of turns in the conversation (default: 3)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between turns in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--template",
        choices=["cli", "science", "student"],
        default="cli",
        help="Choose a conversation template (default: cli)",
    )
    args = parser.parse_args()

    models = args.lm
    lm_display_names = []
    
    for i, model in enumerate(models):
        lm_display_names.append(f"{model.upper()} {i+1}")

    # Initialize contexts
    contexts = [[] for _ in models]
    
    logs_folder = "BackroomsLogs"
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{logs_folder}/{'_'.join(models)}_{args.template}_test_{timestamp}.txt"

    turn = 0
    
    while turn < args.max_turns:
        for i in range(len(models)):
            # Get mock response
            responses = MOCK_RESPONSES[models[i]]
            # Cycle through responses based on turn and model
            response_index = (turn * len(models) + i) % len(responses)
            lm_response = responses[response_index]
            
            # Process response
            should_exit = process_and_log_response(
                lm_response,
                lm_display_names[i],
                filename,
                contexts,
                i,
            )
            
            if should_exit:
                return
                
        turn += 1
        # Add a delay to simulate processing time
        time.sleep(args.delay)

    print(f"\nReached maximum number of turns ({args.max_turns}). Conversation ended.")
    with open(filename, "a") as f:
        f.write(
            f"\nReached maximum number of turns ({args.max_turns}). Conversation ended.\n"
        )

if __name__ == "__main__":
    main()