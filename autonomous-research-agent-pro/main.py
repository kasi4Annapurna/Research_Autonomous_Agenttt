import argparse
from rich.console import Console
from rich.markdown import Markdown
from app.agent.graph import run_research
from app.memory.store import load

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Autonomous Research Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--memory", action="store_true")
    args = parser.parse_args()

    if args.memory:
        records = load()
        console.print(f"Stored searches: {len(records)}")
        for r in records[-10:]:
            console.print(f"- {r['timestamp']} | {r['query']}")
        return

    if not args.query:
        parser.error("Provide a research query or use --memory")

    console.print("[bold]Autonomous Research Agent[/bold]")
    console.print("Planning -> parallel search -> extraction -> deduplication -> synthesis")
    result = run_research(args.query, args.pdf)
    console.print(Markdown(open(result["markdown_path"], encoding="utf-8").read()))
    console.print(f"\nMarkdown: {result['markdown_path']}")
    if result["pdf_path"]:
        console.print(f"PDF: {result['pdf_path']}")

if __name__ == "__main__":
    main()
