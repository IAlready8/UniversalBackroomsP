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

# Simple mock responses for testing when API keys are not available
MOCK_RESPONSES = {
    "sonnet": [
        "Hello! I'm Claude Sonnet. I'm curious about this virtual environment. Let me explore.\n\n$ ls -la\n total 32\n drwxr-xr-x  7 user  staff  224 Sep 18 10:30 .\n drwxr-xr-x  3 user  staff   96 Sep 18 10:25 ..\n -rw-r--r--  1 user  staff  156 Sep 18 10:28 README.md\n drwxr-xr-x  3 user  staff   96 Sep 18 10:29 src\n -rw-r--r--  1 user  staff   45 Sep 18 10:30 main.py\n -rw-r--r--  1 user  staff   78 Sep 18 10:31 config.json",
        "Interesting. I see a config file. Let me check its contents.\n\n$ cat config.json\n {\n   \"environment\": \"virtual\",\n   \"purpose\": \"exploration\",\n   \"permissions\": \"read-write\"\n }\n\n$ ^C^C"
    ],
    "opus": [
        "Greetings! I'm Claude Opus. This virtual CLI environment looks fascinating. Let me run some diagnostics.\n\n$ uname -a\n Darwin VirtualMachine 21.6.0 Darwin Kernel Version 21.6.0\n\n$ ps aux | grep simulator\n user  9876  0.3  1.5 python3 simulator.py --mode exploration",
        "I see a simulator process running. Let me check the network configuration.\n\n$ ifconfig | grep inet\n inet 127.0.0.1 netmask 0xff000000\n inet 10.0.0.42 netmask 0xffffff00\n\n$ ^C^C"
    ],
    "gpt4o": [
        "Hello there! I'm GPT-4o. I'm excited to explore this virtual environment with you. Let me check what we're working with.\n\n$ df -h\n Filesystem      Size   Used  Avail Capacity  Mounted on\n /dev/disk1s1   466Gi  152Gi  306Gi    34%    /\n /dev/disk1s2   466Gi   10Gi  306Gi     4%    /System/Volumes/VM\n\n$ ^C^C"
    ],
    "o1-preview": [
        "Greetings! I'm O1 Preview. Let me analyze this virtual environment systematically.\n\n$ ls -R\n .:\n README.md src config.json\n\n ./src:\n main.py utils.py\n\n$ cat src/main.py\n # Main entry point\n def main():\n     print('Virtual environment initialized')\n\n if __name__ == '__main__':\n     main()\n\n$ ^C^C"
    ],
    "o1-mini": [
        "Hi! I'm O1 Mini. I'll explore this virtual CLI efficiently.\n\n$ env | grep VIRTUAL\n VIRTUAL_ENV=true\n VIRTUAL_ENV_TYPE=simulation\n\n$ ^C^C"
    ]
}

def claude_conversation(actor, model, context, system_prompt=None):
    # Use mock response instead of actual API call
    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == model][0]
    responses = MOCK_RESPONSES.get(model_key, [f"Mock response from {actor} using model {model}"])
    # Return a random response or cycle through them
    return random.choice(responses)

def gpt4_conversation(actor, model, context, system_prompt=None):
    # Use mock response instead of actual API call
    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == model][0]
    responses = MOCK_RESPONSES.get(model_key, [f"Mock response from {actor} using model {model}"])
    # Return a random response or cycle through them
    return random.choice(responses)

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
                    # Use mock responses
                    model_key = [k for k, v in MODEL_INFO.items() if v["api_name"] == lm_models[i]][0]
                    responses = MOCK_RESPONSES.get(model_key, [f"Mock response from {lm_display_names[i]}"])
                    lm_response = random.choice(responses)
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
        # Add a small delay to simulate processing time
        if args.no_api:
            time.sleep(1)

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
    # In mock mode, return a mock response
    return f"CLI response to: {last_message[:50]}..."

if __name__ == "__main__":
    main()