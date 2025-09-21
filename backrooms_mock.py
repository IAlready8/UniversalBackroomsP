import anthropic
import openai
import json
import datetime
import os
import argparse
import dotenv
import sys
import colorsys
import requests
import time
import random
import re
from collections import defaultdict

# Attempt to load from .env file, but don't override existing env vars
dotenv.load_dotenv(override=False)

MODEL_INFO = {
    "sonnet": {
        "api_name": "claude-3-5-sonnet-20240620",
        "display_name": "Claude",
        "company": "anthropic",
    },
    "opus": {
        "api_name": "claude-3-opus-20240229",
        "display_name": "Claude",
        "company": "anthropic",
    },
    "gpt4o": {
        "api_name": "gpt-4o-2024-08-06",
        "display_name": "GPT4o",
        "company": "openai",
    },
    "o1-preview": {"api_name": "o1-preview", "display_name": "O1", "company": "openai"},
    "o1-mini": {"api_name": "o1-mini", "display_name": "Mini", "company": "openai"},
}

# Enhanced mock responses with contextual awareness
MOCK_RESPONSES = {
    "sonnet": {
        "greeting": [
            "Hello! I'm Claude Sonnet. I'm curious about this virtual environment. Let me explore.\n\n$ ls -la\n total 32\n drwxr-xr-x  7 user  staff  224 Sep 18 10:30 .\n drwxr-xr-x  3 user  staff   96 Sep 18 10:25 ..\n -rw-r--r--  1 user  staff  156 Sep 18 10:28 README.md\n drwxr-xr-x  3 user  staff   96 Sep 18 10:29 src\n -rw-r--r--  1 user  staff   45 Sep 18 10:30 main.py\n -rw-r--r--  1 user  staff   78 Sep 18 10:31 config.json",
            "Greetings! I'm Claude Sonnet. This virtual CLI environment is fascinating. Let me run some diagnostics.\n\n$ ps aux | grep virtual\n user  1234  0.5  2.1 python3 virtual_env.py --mode exploration\n user  5678  0.2  1.8 python3 simulator.py --config advanced",
            "Hi there! I'm Claude Sonnet. I'm excited to explore this virtual environment with you. Let me check what we're working with.\n\n$ env | grep VIRTUAL\n VIRTUAL_ENV=true\n VIRTUAL_ENV_TYPE=simulation\n SIMULATION_MODE=exploration"
        ],
        "exploration": [
            "Interesting. I see a config file. Let me check its contents.\n\n$ cat config.json\n {\n   \"environment\": \"virtual\",\n   \"purpose\": \"exploration\",\n   \"permissions\": \"read-write\"\n }\n\n$ ^C^C",
            "Let me explore the source directory to understand the structure better.\n\n$ ls src/\n main.py  utils.py  modules/\n\n$ cat src/utils.py\n # Utility functions for the virtual environment\n def get_system_info():\n     return {'os': 'VirtualOS', 'version': '3.14'}\n\n$ ^C^C",
            "I notice there's a modules directory. Let me see what's inside.\n\n$ ls src/modules/\n network.py  security.py  data.py\n\n$ ^C^C"
        ],
        "network": [
            "Let me check the network configuration.\n\n$ ifconfig\n eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 10.0.0.42  netmask 255.255.255.0  broadcast 10.0.0.255\n        inet6 fe80::1ff:fe23:4567:890a  prefixlen 64  scopeid 0x20<link>\n\n$ ^C^C",
            "Let me check the routing table.\n\n$ route -n\n Kernel IP routing table\n Destination     Gateway         Genmask         Flags Metric Ref    Use Iface\n 0.0.0.0         10.0.0.1        0.0.0.0         UG    0      0        0 eth0\n 10.0.0.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0\n\n$ ^C^C"
        ],
        "default": [
            "I'm analyzing the virtual environment. The system appears to be a sophisticated simulation.\n\n$ uname -a\n VirtualOS 3.14.159 VirtualKernel #1 SMP Thu Sep 18 12:00:00 UTC 2025 x86_64\n\n$ ^C^C",
            "This is quite interesting. Let me check the system resources.\n\n$ top -b -n 1 | head -10\n top - 12:00:00 up 1 day,  0:00,  1 user,  load average: 0.15, 0.05, 0.01\n Tasks:  85 total,   1 running,  84 sleeping,   0 stopped,   0 zombie\n %Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.7 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st\n MiB Mem :   8192.0 total,   4096.0 free,   2048.0 used,   2048.0 buff/cache\n\n$ ^C^C"
        ]
    },
    "opus": {
        "greeting": [
            "Greetings! I'm Claude Opus. This virtual CLI environment looks fascinating. Let me run some diagnostics.\n\n$ uname -a\n Darwin VirtualMachine 21.6.0 Darwin Kernel Version 21.6.0\n\n$ ps aux | grep simulator\n user  9876  0.3  1.5 python3 simulator.py --mode exploration",
            "Hello! I'm Claude Opus. I'm intrigued by this virtual environment. Let me explore the system.\n\n$ df -h\n Filesystem      Size   Used  Avail Capacity  Mounted on\n /dev/vda1      100Gi   25Gi   75Gi    25%    /\n /dev/vda2      500Gi  100Gi  400Gi    20%    /data\n\n$ ^C^C",
            "Hi there! I'm Claude Opus. Let me examine this virtual environment more closely.\n\n$ lscpu\n Architecture:        x86_64\n CPU op-mode(s):      32-bit, 64-bit\n Byte Order:          Little Endian\n CPU(s):              8\n Model name:          Virtual CPU (vCPU)\n\n$ ^C^C"
        ],
        "exploration": [
            "I see a simulator process running. Let me check the network configuration.\n\n$ ifconfig | grep inet\n inet 127.0.0.1 netmask 0xff000000\n inet 10.0.0.42 netmask 0xffffff00\n\n$ ^C^C",
            "Let me check what processes are running in this environment.\n\n$ ps aux | grep python\n user   1234  0.5  2.1 python3 backrooms.py\n user   5678  0.2  1.8 python3 simulator.py\n user   9012  0.1  0.5 python3 monitor.py\n\n$ ^C^C",
            "I'm curious about the environment variables.\n\n$ env | grep SIM\n SIMULATION_MODE=advanced\n SIMULATOR_VERSION=2.5.1\n SIM_ENV_TYPE=exploration\n\n$ ^C^C"
        ],
        "network": [
            "Let me examine the network interfaces in more detail.\n\n$ ip addr show\n 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN\n    inet 127.0.0.1/8 scope host lo\n 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP\n    inet 10.0.0.42/24 brd 10.0.0.255 scope global eth0\n\n$ ^C^C",
            "Let me check the DNS configuration.\n\n$ cat /etc/resolv.conf\n nameserver 8.8.8.8\n nameserver 8.8.4.4\n search virtual.environment\n\n$ ^C^C"
        ],
        "default": [
            "This virtual environment is quite sophisticated. Let me run a deeper analysis.\n\n$ sysctl -a | grep virtual\n kernel.virtual_environment = true\n kernel.simulation_level = high\n\n$ ^C^C",
            "I'm detecting some interesting patterns in this virtual environment.\n\n$ dmesg | tail -5\n [ 1234.5678] Virtual environment initialized\n [ 1235.6789] Simulation engine v2.5.1 loaded\n [ 1236.7890] Network interface eth0 configured\n\n$ ^C^C"
        ]
    },
    "gpt4o": {
        "greeting": [
            "Hello there! I'm GPT-4o. I'm excited to explore this virtual environment with you. Let me check what we're working with.\n\n$ df -h\n Filesystem      Size   Used  Avail Capacity  Mounted on\n /dev/disk1s1   466Gi  152Gi  306Gi    34%    /\n /dev/disk1s2   466Gi   10Gi  306Gi     4%    /System/Volumes/VM",
            "Greetings! I'm GPT-4o. This virtual CLI environment looks intriguing. Let me run some initial checks.\n\n$ free -h\n               total        used        free      shared  buff/cache   available\n Mem:           16Gi       4.0Gi       8.0Gi       256Mi       4.0Gi        11Gi\n Swap:         2.0Gi          0B       2.0Gi",
            "Hi! I'm GPT-4o. I'm curious about this virtual environment. Let me examine the system.\n\n$ cat /etc/os-release\n NAME=\"Virtual Linux\"\n VERSION=\"3.14.159\"\n ID=virtual\n VERSION_ID=\"3.14\"\n\n$ ^C^C"
        ],
        "exploration": [
            "Let me check the running services.\n\n$ systemctl list-units --type=service --state=running | head -5\n  auditd.service                   loaded active running   Security Audit Logging Service\n  chronyd.service                  loaded active running   NTP client/server\n  crond.service                    loaded active running   Command Scheduler\n  dbus.service                     loaded active running   D-Bus System Message Bus\n\n$ ^C^C",
            "I'm interested in the hardware configuration.\n\n$ lshw -short | head -10\n H/W path      Device      Class          Description\n ====================================================\n                         system         Virtual Machine\n /0                      bus            Motherboard\n /0/0                    memory         16GiB System Memory\n /0/0/0                  memory         8GiB DIMM DDR4\n /0/0/1                  memory         8GiB DIMM DDR4\n /0/1                    processor      Virtual CPU\n\n$ ^C^C"
        ],
        "network": [
            "Let me check the network connections.\n\n$ netstat -tuln | grep LISTEN\n tcp6  0  0 :::22                   :::*                    LISTEN\n tcp6  0  0 :::80                   :::*                    LISTEN\n tcp6  0  0 :::443                  :::*                    LISTEN\n\n$ ^C^C",
            "Let me examine the firewall configuration.\n\n$ iptables -L | head -10\n Chain INPUT (policy ACCEPT)\n target     prot opt source               destination\n ACCEPT     all  --  anywhere             anywhere\n ACCEPT     icmp --  anywhere             anywhere\n ACCEPT     tcp  --  anywhere             anywhere             tcp dpt:ssh\n\n$ ^C^C"
        ],
        "default": [
            "This virtual environment has some interesting characteristics.\n\n$ lsmod | head -5\n Module                  Size  Used by\n virtio_net             40960  0\n virtio_blk             20480  2\n virtio_console         32768  0\n virtio_ring            20480  3 virtio_net,virtio_blk,virtio_console\n\n$ ^C^C",
            "I'm observing some unique properties of this virtual environment.\n\n$ ls /proc | head -10\n 1\n 2\n 3\n 4\n 5\n 6\n 7\n 8\n 9\n 10\n\n$ ^C^C"
        ]
    },
    "o1-preview": {
        "greeting": [
            "Greetings! I'm O1 Preview. Let me analyze this virtual environment systematically.\n\n$ ls -R\n .:\n README.md src config.json\n\n ./src:\n main.py utils.py\n\n$ cat src/main.py\n # Main entry point\n def main():\n     print('Virtual environment initialized')\n\n if __name__ == '__main__':\n     main()\n\n$ ^C^C",
            "Hello! I'm O1 Preview. I'll methodically explore this virtual environment.\n\n$ find . -name \"*.py\" -type f | head -5\n ./src/main.py\n ./src/utils.py\n ./src/modules/data_handler.py\n ./src/modules/network_manager.py\n\n$ ^C^C"
        ],
        "exploration": [
            "Let me examine the Python environment.\n\n$ python --version\n Python 3.11.5\n\n$ pip list | grep virtual\n virtualenv              20.24.5\n virtualenv-clone        0.5.7\n\n$ ^C^C",
            "I'll check the project structure in more detail.\n\n$ tree -L 2\n .\n ├── README.md\n ├── config.json\n ├── requirements.txt\n ├── src/\n │   ├── main.py\n │   ├── utils.py\n │   └── modules/\n └── tests/\n     ├── test_main.py\n     └── test_utils.py\n\n$ ^C^C"
        ],
        "default": [
            "Analyzing the virtual environment from a computational perspective.\n\n$ echo \"import sys; print(sys.path)\" | python\n ['', '/usr/lib/python311.zip', '/usr/lib/python3.11', '/usr/lib/python3.11/lib-dynload', '/usr/local/lib/python3.11/dist-packages']\n\n$ ^C^C",
            "This environment has some unique computational properties.\n\n$ python -c \"import os; print(os.environ.get('VIRTUAL_ENV', 'Not set'))\"\n /opt/virtual-environments/simulation\n\n$ ^C^C"
        ]
    },
    "o1-mini": {
        "greeting": [
            "Hi! I'm O1 Mini. I'll explore this virtual CLI efficiently.\n\n$ env | grep VIRTUAL\n VIRTUAL_ENV=true\n VIRTUAL_ENV_TYPE=simulation\n\n$ ^C^C",
            "Hello! I'm O1 Mini. Let me quickly assess this virtual environment.\n\n$ echo $SHELL\n /bin/bash\n\n$ echo $PATH | tr ':' '\\n' | head -5\n /usr/local/bin\n /usr/bin\n /bin\n /usr/sbin\n /sbin\n\n$ ^C^C"
        ],
        "exploration": [
            "Let me check the system time and timezone.\n\n$ date\n Thu Sep 18 12:00:00 UTC 2025\n\n$ timedatectl\n               Local time: Thu 2025-09-18 12:00:00 UTC\n           Universal time: Thu 2025-09-18 12:00:00 UTC\n                 RTC time: Thu 2025-09-18 12:00:00\n\n$ ^C^C",
            "I'll examine the user permissions.\n\n$ id\n uid=1000(user) gid=1000(user) groups=1000(user),27(sudo),999(docker)\n\n$ ^C^C"
        ],
        "default": [
            "This virtual environment is optimized for efficiency.\n\n$ uptime\n  12:00:00 up 1 day,  0:00,  1 user,  load average: 0.05, 0.03, 0.01\n\n$ ^C^C",
            "Quick analysis of the virtual environment.\n\n$ whoami\n user\n\n$ hostname\n virtual-machine-01\n\n$ ^C^C"
        ]
    }
}

# Track conversation state for contextual responses
conversation_state = defaultdict(lambda: {"turn": 0, "context": "greeting"})

def get_context_from_message(message):
    """Extract context from the message content to determine appropriate response type."""
    message_lower = message.lower()
    if any(keyword in message_lower for keyword in ["network", "ip", "ifconfig", "route", "dns"]):
        return "network"
    elif any(keyword in message_lower for keyword in ["config", "ls", "cat", "file", "directory", "folder"]):
        return "exploration"
    elif any(keyword in message_lower for keyword in ["hello", "hi", "greet", "introduc"]):
        return "greeting"
    else:
        return "default"

def claude_conversation(actor, model, context, system_prompt=None):
    # Use mock response instead of actual API call
    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == model][0]
    
    # Get the last message to determine context
    last_message = ""
    if context and len(context) > 0:
        last_message = context[-1].get("content", "")
    
    # Determine context for response
    response_context = get_context_from_message(last_message)
    
    # Get appropriate responses
    responses = MOCK_RESPONSES.get(model_key, {}).get(response_context, 
                MOCK_RESPONSES.get(model_key, {}).get("default", 
                    [f"Mock response from {actor} using model {model}"]))
    
    # Return a response, cycling through them based on turn count
    state_key = f"{actor}_{model}"
    turn = conversation_state[state_key]["turn"]
    response = responses[turn % len(responses)]
    conversation_state[state_key]["turn"] += 1
    conversation_state[state_key]["context"] = response_context
    
    return response

def gpt4_conversation(actor, model, context, system_prompt=None):
    # Use mock response instead of actual API call
    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == model][0]
    
    # Get the last message to determine context
    last_message = ""
    if context and len(context) > 0:
        last_message = context[-1].get("content", "")
    
    # Determine context for response
    response_context = get_context_from_message(last_message)
    
    # Get appropriate responses
    responses = MOCK_RESPONSES.get(model_key, {}).get(response_context, 
                MOCK_RESPONSES.get(model_key, {}).get("default", 
                    [f"Mock response from {actor} using model {model}"]))
    
    # Return a response, cycling through them based on turn count
    state_key = f"{actor}_{model}"
    turn = conversation_state[state_key]["turn"]
    response = responses[turn % len(responses)]
    conversation_state[state_key]["turn"] += 1
    conversation_state[state_key]["context"] = response_context
    
    return response

def load_template(template_name, models):
    try:
        with open(f"templates/{template_name}.jsonl", "r") as f:
            configs = [json.loads(line) for line in f]

        companies = []
        actors = []
        for i, model in enumerate(models):
            if model.lower() == "cli":
                companies.append("CLI")
                actors.append("CLI")
            else:
                companies.append(MODEL_INFO[model]["company"])
                actors.append(f"{MODEL_INFO[model]['display_name']} {i+1}")

        for i, config in enumerate(configs):
            if models[i].lower() == "cli":
                config["cli"] = True
                continue

            config["system_prompt"] = config["system_prompt"].format(
                **{f"lm{j+1}_company": companies[j] for j in range(len(companies))},
                **{f"lm{j+1}_actor": actors[j] for j in range(len(actors))},
            )
            for message in config["context"]:
                message["content"] = message["content"].format(
                    **{f"lm{j+1}_company": companies[j] for j in range(len(companies))},
                    **{f"lm{j+1}_actor": actors[j] for j in range(len(actors))},
                )

            if (
                models[i] in MODEL_INFO
                and MODEL_INFO[models[i]]["company"] == "openai"
                and config["system_prompt"]
            ):
                system_prompt_added = False
                for message in config["context"]:
                    if message["role"] == "user":
                        message["content"] = (
                            f"<SYSTEM>{config['system_prompt']}</SYSTEM>\n\n{message['content']}"
                        )
                        system_prompt_added = True
                        break
                if not system_prompt_added:
                    config["context"].append(
                        {
                            "role": "user",
                            "content": f"<SYSTEM>{config['system_prompt']}</SYSTEM>",
                        }
                    )
            config["cli"] = config.get("cli", False)
        return configs
    except FileNotFoundError:
        print(f"Error: Template '{template_name}' not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in template '{template_name}'.")
        exit(1)

def get_available_templates():
    template_dir = "./templates"
    templates = []
    for file in os.listdir(template_dir):
        if file.endswith(".jsonl"):
            templates.append(os.path.splitext(file)[0])
    return templates

def main():
    global anthropic_client
    global openai_client
    parser = argparse.ArgumentParser(
        description="Run conversation between two or more AI language models."
    )
    parser.add_argument(
        "--lm",
        choices=["sonnet", "opus", "gpt4o", "o1-preview", "o1-mini", "cli"],
        nargs="+",
        default=["opus", "opus"],
        help="Choose the models for LMs or 'cli' for the world interface (default: opus opus)",
    )

    available_templates = get_available_templates()
    parser.add_argument(
        "--template",
        choices=available_templates,
        default="cli" if "cli" in available_templates else available_templates[0],
        help=f"Choose a conversation template (available: {', '.join(available_templates)})",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=float("inf"),
        help="Maximum number of turns in the conversation (default: infinity)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Run in mock mode without API keys (default: False)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between turns in seconds (default: 1.0)",
    )
    args = parser.parse_args()

    models = args.lm
    lm_models = []
    lm_display_names = []

    companies = []
    actors = []

    for i, model in enumerate(models):
        if model.lower() == "cli":
            lm_display_names.append("CLI")
            lm_models.append("cli")
            companies.append("CLI")
            actors.append("CLI")
        else:
            if model in MODEL_INFO:
                lm_display_names.append(f"{MODEL_INFO[model]['display_name']} {i+1}")
                lm_models.append(MODEL_INFO[model]["api_name"])
                companies.append(MODEL_INFO[model]["company"])
                actors.append(f"{MODEL_INFO[model]['display_name']} {i+1}")
            else:
                print(f"Error: Model '{model}' not found in MODEL_INFO.")
                sys.exit(1)

    # Only check for API keys if not in mock mode
    if not args.no_api:
        # Filter out models not in MODEL_INFO (like 'cli')
        anthropic_models = [
            model
            for model in models
            if model in MODEL_INFO and MODEL_INFO[model]["company"] == "anthropic"
        ]
        if anthropic_models:
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                print(
                    "Error: ANTHROPIC_API_KEY must be set in the environment or in a .env file."
                )
                sys.exit(1)
            anthropic_client = anthropic.Client(api_key=anthropic_api_key)

        openai_models = [
            model
            for model in models
            if model in MODEL_INFO and MODEL_INFO[model]["company"] == "openai"
        ]
        if openai_models:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                print(
                    "Error: OPENAI_API_KEY must be set in the environment or in a .env file."
                )
                sys.exit(1)
            openai_client = openai.OpenAI(api_key=openai_api_key)

    configs = load_template(args.template, models)

    assert len(models) == len(
        configs
    ), f"Number of LMs ({len(models)}) does not match the number of elements in the template ({len(configs)})"

    system_prompts = [config.get("system_prompt", "") for config in configs]
    contexts = [config.get("context", []) for config in configs]

    logs_folder = "BackroomsLogs"
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{logs_folder}/{'_'.join(models)}_{args.template}_{timestamp}.txt"

    turn = 0
    while turn < args.max_turns:
        for i in range(len(models)):
            if models[i].lower() == "cli":
                # For CLI, we would normally call the world interface
                # But in mock mode, we'll just generate a mock response
                if args.no_api:
                    lm_response = f"CLI response for turn {turn}"
                else:
                    lm_response = cli_conversation(contexts[i])
            else:
                if args.no_api:
                    # Use mock responses with contextual awareness
                    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == lm_models[i]][0]
                    # Pass the context to determine appropriate response
                    lm_response = generate_model_response(
                        lm_models[i],
                        lm_display_names[i],
                        contexts[i],
                        system_prompts[i],
                    )
                else:
                    # Use actual API calls
                    lm_response = generate_model_response(
                        lm_models[i],
                        lm_display_names[i],
                        contexts[i],
                        system_prompts[i],
                    )
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
        if args.no_api:
            time.sleep(args.delay)

    print(f"\nReached maximum number of turns ({args.max_turns}). Conversation ended.")
    with open(filename, "a") as f:
        f.write(
            f"\nReached maximum number of turns ({args.max_turns}). Conversation ended.\n"
        )

def generate_model_response(model, actor, context, system_prompt):
    if model.startswith("claude-"):
        return claude_conversation(
            actor, model, context, system_prompt if system_prompt else None
        )
    else:
        return gpt4_conversation(
            actor, model, context, system_prompt if system_prompt else None
        )

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

def cli_conversation(context):
    # Extract the last user message
    last_message = context[-1]["content"]
    # In mock mode, return a contextual mock response
    cli_responses = [
        f"CLI> Processed command: {last_message[:30]}...\n$ echo 'Command executed successfully'\nCommand executed successfully\n$ ",
        f"CLI> Analyzing input: {last_message[:20]}...\n$ ls -la\n total 0\n$ ",
        f"CLI> Response to: {last_message[:25]}...\n$ ps aux | grep simulation\n user  1234  0.1  0.5 simulation.py\n$ "
    ]
    return random.choice(cli_responses)

if __name__ == "__main__":
    main()