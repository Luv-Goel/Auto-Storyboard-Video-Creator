import os
import sys
import time
from typing import Optional, List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.live import Live
from rich.table import Table
from rich import print as rprint

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.video_generator import VideoGenerator
from config.config import ASPECT_RATIOS

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_audio_files() -> List[str]:
    """Get list of audio files in current directory."""
    extensions = ('.mp3', '.wav', '.m4a', '.flac')
    return [f for f in os.listdir('.') if f.lower().endswith(extensions)]

def show_header():
    header_text = "[bold purple]Video Creator AI[/bold purple] - [italic]Terminal Edition[/italic]\n"
    header_text += "[dim]Transform your narration into cinematic storyboards directly from the console.[/dim]"
    console.print(Panel(header_text, border_style="purple", expand=False))

def run_tui():
    clear_screen()
    show_header()
    
    # 1. Select Audio File
    audio_files = get_audio_files()
    
    if not audio_files:
        rprint("[yellow]No audio files found in the current directory.[/yellow]")
        audio_path = Prompt.ask("Enter the full path to your audio file")
    else:
        table = Table(title="Available Audio Files", show_header=True, header_style="bold magenta")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Filename", style="green")
        
        for i, f in enumerate(audio_files, 1):
            table.add_row(str(i), f)
        
        console.print(table)
        
        choice = IntPrompt.ask(
            "Select an audio file ID or 0 to enter a custom path", 
            choices=[str(i) for i in range(len(audio_files) + 1)],
            default=1
        )
        
        if choice == 0:
            audio_path = Prompt.ask("Enter the full path to your audio file")
        else:
            audio_path = audio_files[choice - 1]

    if not os.path.exists(audio_path):
        rprint(f"[red]Error: File not found at {audio_path}[/red]")
        return

    # 2. Settings
    rprint("\n[bold cyan]Generation Settings[/bold cyan]")
    
    aspect_ratio = Prompt.ask(
        "Select Aspect Ratio", 
        choices=list(ASPECT_RATIOS.keys()), 
        default="16:9"
    )
    
    img_per_min = IntPrompt.ask("Images per minute", default=3)
    vid_per_min = IntPrompt.ask("Videos per minute", default=1)
    
    subtitles = Confirm.ask("Include burned-in subtitles?", default=False)
    
    output_name = Prompt.ask(
        "Output filename (optional, hit enter for default)", 
        default=Path(audio_path).stem + "_tui_output"
    )

    rprint("\n" + "="*40)
    rprint(f"[bold green]Starting pipeline...[/bold green]")
    rprint(f"Audio: [dim]{audio_path}[/dim]")
    rprint(f"Mode:  [dim]{aspect_ratio}, {img_per_min} img/min, {vid_per_min} vid/min[/dim]")
    rprint("="*40 + "\n")

    # 3. Execution with Rich Progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        main_task = progress.add_task("[cyan]Initializing...", total=100)
        
        def on_progress(message: str, percentage: int):
            progress.update(main_task, completed=percentage, description=f"[cyan]{message}")

        try:
            generator = VideoGenerator(
                aspect_ratio=aspect_ratio,
                progress_callback=on_progress,
                images_per_minute=img_per_min,
                videos_per_minute=vid_per_min
            )
            
            final_path = generator.generate_video(
                audio_path=audio_path,
                output_name=output_name,
                subtitles=subtitles
            )
            
            rprint(f"\n[bold green]\u2713 Success![/bold green] Video saved to: [underline]{final_path}[/underline]")
            
        except Exception as e:
            rprint(f"\n[bold red]\u2717 Error during generation:[/bold red] {str(e)}")

if __name__ == "__main__":
    try:
        run_tui()
    except KeyboardInterrupt:
        rprint("\n[yellow]Exiting...[/yellow]")
        sys.exit(0)
