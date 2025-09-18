#!/usr/bin/env python3
"""
Advanced UI Control System for UniversalBackrooms
Provides a rich terminal-based interface for managing conversations and monitoring.
"""

import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import argparse
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import subprocess

try:
    import rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.tree import Tree
    from rich.align import Align
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

@dataclass
class ConversationSession:
    """Represents an active conversation session."""
    id: str
    models: List[str]
    template: str
    start_time: datetime
    log_file: str
    process: Optional[subprocess.Popen] = None
    status: str = "running"
    turn_count: int = 0

class AdvancedUI:
    """Advanced terminal UI for UniversalBackrooms control."""
    
    def __init__(self):
        self.console = Console() if HAS_RICH else None
        self.sessions: Dict[str, ConversationSession] = {}
        self.running = True
        self.refresh_rate = 1.0
        
        if not HAS_RICH:
            print("Warning: Rich library not installed. Using basic UI mode.")
            print("Install with: pip install rich")
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        missing = []
        
        try:
            import anthropic
        except ImportError:
            missing.append("anthropic")
        
        try:
            import openai
        except ImportError:
            missing.append("openai")
        
        try:
            import dotenv
        except ImportError:
            missing.append("python-dotenv")
        
        if missing:
            if self.console:
                self.console.print(f"[red]Missing dependencies: {', '.join(missing)}[/red]")
                self.console.print("Install with: pip install " + " ".join(missing))
            else:
                print(f"Missing dependencies: {', '.join(missing)}")
                print("Install with: pip install " + " ".join(missing))
            return False
        return True
    
    def get_available_models(self):
        """Get list of available models."""
        return ["sonnet", "opus", "gpt4o", "o1-preview", "o1-mini", "cli"]
    
    def get_available_templates(self):
        """Get list of available templates."""
        template_dir = Path("templates")
        if not template_dir.exists():
            return []
        
        templates = []
        for file in template_dir.glob("*.jsonl"):
            templates.append(file.stem)
        return templates
    
    def create_main_layout(self):
        """Create the main UI layout."""
        if not self.console:
            return None
        
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="sessions", ratio=1),
            Layout(name="controls", ratio=1)
        )
        
        return layout
    
    def update_header(self, layout):
        """Update the header panel."""
        if not layout:
            return
        
        header_text = Text("UniversalBackrooms Advanced Control Interface", style="bold magenta")
        layout["header"].update(Panel(Align.center(header_text), title="🏢 Control Center"))
    
    def update_sessions_panel(self, layout):
        """Update the sessions panel."""
        if not layout:
            return
        
        if not self.sessions:
            content = Text("No active sessions", style="dim")
        else:
            table = Table(title="Active Sessions")
            table.add_column("ID", style="cyan")
            table.add_column("Models", style="green")
            table.add_column("Template", style="yellow")
            table.add_column("Status", style="blue")
            table.add_column("Turns", style="magenta")
            table.add_column("Duration", style="white")
            
            for session in self.sessions.values():
                duration = datetime.now() - session.start_time
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                
                table.add_row(
                    session.id[:8],
                    " + ".join(session.models),
                    session.template,
                    session.status,
                    str(session.turn_count),
                    duration_str
                )
            
            content = table
        
        layout["sessions"].update(Panel(content, title="🗣️ Conversations"))
    
    def update_controls_panel(self, layout):
        """Update the controls panel."""
        if not layout:
            return
        
        controls_tree = Tree("Available Actions")
        controls_tree.add("🚀 Start New Conversation")
        controls_tree.add("⏸️ Pause Session")
        controls_tree.add("▶️ Resume Session")
        controls_tree.add("🛑 Stop Session")
        controls_tree.add("📊 View Logs")
        controls_tree.add("⚙️ Settings")
        controls_tree.add("❌ Exit")
        
        layout["controls"].update(Panel(controls_tree, title="🎮 Controls"))
    
    def update_footer(self, layout):
        """Update the footer panel."""
        if not layout:
            return
        
        footer_text = f"Sessions: {len(self.sessions)} | Press 'q' to quit | Time: {datetime.now().strftime('%H:%M:%S')}"
        layout["footer"].update(Panel(footer_text, style="dim"))
    
    def start_conversation(self):
        """Start a new conversation with user input."""
        if not self.console:
            return self.start_conversation_basic()
        
        self.console.print("\n[bold green]Starting New Conversation[/bold green]")
        
        # Get models
        available_models = self.get_available_models()
        self.console.print(f"Available models: {', '.join(available_models)}")
        models_input = Prompt.ask("Enter models (space-separated)", default="opus opus")
        models = models_input.split()
        
        # Validate models
        for model in models:
            if model not in available_models:
                self.console.print(f"[red]Unknown model: {model}[/red]")
                return
        
        # Get template
        available_templates = self.get_available_templates()
        if available_templates:
            self.console.print(f"Available templates: {', '.join(available_templates)}")
            template = Prompt.ask("Enter template", default="cli", choices=available_templates)
        else:
            template = "cli"
        
        # Get max turns
        max_turns = Prompt.ask("Max turns (or 'inf' for infinite)", default="inf")
        if max_turns.lower() != "inf":
            try:
                max_turns = int(max_turns)
            except ValueError:
                self.console.print("[red]Invalid number for max turns[/red]")
                return
        
        # Start the conversation
        session_id = f"session_{int(time.time())}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"BackroomsLogs/{'_'.join(models)}_{template}_{timestamp}.txt"
        
        cmd = [
            sys.executable, "backrooms.py",
            "--lm"] + models + [
            "--template", template
        ]
        
        if max_turns != "inf":
            cmd.extend(["--max-turns", str(max_turns)])
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            session = ConversationSession(
                id=session_id,
                models=models,
                template=template,
                start_time=datetime.now(),
                log_file=log_file,
                process=process
            )
            
            self.sessions[session_id] = session
            self.console.print(f"[green]Started session {session_id[:8]}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Failed to start conversation: {e}[/red]")
    
    def start_conversation_basic(self):
        """Start a new conversation in basic mode."""
        print("\nStarting New Conversation")
        print("Available models: sonnet, opus, gpt4o, o1-preview, o1-mini, cli")
        
        models_input = input("Enter models (space-separated, default: opus opus): ").strip()
        if not models_input:
            models_input = "opus opus"
        models = models_input.split()
        
        template = input("Enter template (default: cli): ").strip()
        if not template:
            template = "cli"
        
        max_turns_input = input("Max turns (default: inf): ").strip()
        if not max_turns_input:
            max_turns_input = "inf"
        
        cmd = [sys.executable, "backrooms.py", "--lm"] + models + ["--template", template]
        
        if max_turns_input.lower() != "inf":
            try:
                max_turns = int(max_turns_input)
                cmd.extend(["--max-turns", str(max_turns)])
            except ValueError:
                print("Invalid number for max turns, using infinite")
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\nConversation interrupted")
        except Exception as e:
            print(f"Failed to start conversation: {e}")
    
    def view_logs(self):
        """View available log files."""
        logs_dir = Path("BackroomsLogs")
        if not logs_dir.exists():
            if self.console:
                self.console.print("[yellow]No logs directory found[/yellow]")
            else:
                print("No logs directory found")
            return
        
        log_files = list(logs_dir.glob("*.txt"))
        if not log_files:
            if self.console:
                self.console.print("[yellow]No log files found[/yellow]")
            else:
                print("No log files found")
            return
        
        if self.console:
            table = Table(title="Available Logs")
            table.add_column("File", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="yellow")
            
            for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True):
                size = log_file.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                modified = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                table.add_row(log_file.name, size_str, modified)
            
            self.console.print(table)
        else:
            print("\nAvailable logs:")
            for i, log_file in enumerate(sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True), 1):
                size = log_file.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                modified = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"{i}. {log_file.name} ({size_str}, {modified})")
    
    def show_main_menu(self):
        """Show the main menu in basic mode."""
        while self.running:
            print("\n" + "="*50)
            print("UniversalBackrooms Advanced Control")
            print("="*50)
            print("1. Start New Conversation")
            print("2. View Logs")
            print("3. Check Dependencies")
            print("4. Run Initialization")
            print("5. Exit")
            print()
            
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                self.start_conversation_basic()
            elif choice == "2":
                self.view_logs()
            elif choice == "3":
                if self.check_dependencies():
                    print("✓ All dependencies are available")
                else:
                    print("⚠ Some dependencies are missing")
            elif choice == "4":
                try:
                    subprocess.run([sys.executable, "init.py"])
                except Exception as e:
                    print(f"Failed to run initialization: {e}")
            elif choice == "5":
                self.running = False
                print("Goodbye!")
            else:
                print("Invalid choice. Please try again.")
    
    def run_rich_interface(self):
        """Run the rich terminal interface."""
        layout = self.create_main_layout()
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while self.running:
                try:
                    self.update_header(layout)
                    self.update_sessions_panel(layout)
                    self.update_controls_panel(layout)
                    self.update_footer(layout)
                    
                    time.sleep(self.refresh_rate)
                    
                except KeyboardInterrupt:
                    if Confirm.ask("Are you sure you want to exit?"):
                        self.running = False
                    break
    
    def run(self):
        """Run the advanced UI."""
        if not self.check_dependencies():
            return
        
        if HAS_RICH and sys.stdout.isatty():
            try:
                self.console.print("[bold green]Starting Advanced UI Mode[/bold green]")
                self.console.print("Press Ctrl+C to access menu")
                time.sleep(2)
                self.run_rich_interface()
            except Exception as e:
                self.console.print(f"[red]Error in rich interface: {e}[/red]")
                self.console.print("Falling back to basic mode...")
                self.show_main_menu()
        else:
            self.show_main_menu()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Advanced UI for UniversalBackrooms")
    parser.add_argument("--basic", action="store_true", help="Force basic UI mode")
    args = parser.parse_args()
    
    if args.basic:
        global HAS_RICH
        HAS_RICH = False
    
    ui = AdvancedUI()
    ui.run()

if __name__ == "__main__":
    main()