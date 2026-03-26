"""
Serving Agent CLI

命令行接口，提供配置生成、验证和构建功能。
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from serving_agent.config import parse_config, validate_config
from serving_agent.assembler import ProjectAssembler
from serving_agent.pypto_codegen import Qwen3KernelGenerator

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Serving Agent - 自动生成轻量级 LLM 推理服务"""
    pass


@main.command()
@click.argument("config", type=click.Path(exists=True))
@click.option(
    "--output", "-o", type=click.Path(), default="./generated_server", help="输出目录"
)
def generate(config: str, output: str):
    """
    生成推理服务

    示例:
        serving-agent generate config.toml --output ./my_server
    """
    try:
        console.print(f"[bold blue]Parsing config:[/bold blue] {config}")
        serving_config = parse_config(config)

        console.print("[bold blue]Validating config...[/bold blue]")
        spec = validate_config(serving_config)

        # 显示配置摘要
        _display_config_summary(spec)

        # 生成 PyPTO 内核
        console.print("\n[bold blue]Generating PyPTO kernels...[/bold blue]")
        kernel_gen = Qwen3KernelGenerator(variant=spec.config.model.variant)
        kernel_dir = Path(output) / "kernels"
        kernel_paths = kernel_gen.compile_all(str(kernel_dir))
        console.print(f"[green]✓[/green] Generated {len(kernel_paths)} kernels")

        # 组装项目
        console.print("\n[bold blue]Assembling project...[/bold blue]")
        assembler = ProjectAssembler()
        assembler.assemble(spec, Path(output))
        console.print(f"[green]✓[/green] Project assembled to {output}")

        console.print("\n[bold green]✓ Generation complete![/bold green]")
        console.print(f"\nTo build and run:\n  cd {output}\n  cargo build --release\n  cargo run --release")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.argument("config", type=click.Path(exists=True))
def validate(config: str):
    """
    验证配置文件

    示例:
        serving-agent validate config.toml
    """
    try:
        console.print(f"[bold blue]Validating:[/bold blue] {config}")
        serving_config = parse_config(config)
        spec = validate_config(serving_config)

        console.print("[bold green]✓ Config is valid![/bold green]\n")
        _display_config_summary(spec)

    except Exception as e:
        console.print(f"[bold red]Validation failed:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.argument("project", type=click.Path(exists=True))
def build(project: str):
    """
    构建生成的项目

    示例:
        serving-agent build ./my_server
    """
    try:
        import subprocess

        project_path = Path(project)
        console.print(f"[bold blue]Building project:[/bold blue] {project}")

        # 运行 cargo build
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print("[bold red]Build failed:[/bold red]")
            console.print(result.stderr)
            raise click.Abort()

        console.print("[bold green]✓ Build complete![/bold green]")
        console.print(f"\nExecutable: {project_path}/target/release/llm_server")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


def _display_config_summary(spec):
    """显示配置摘要"""
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    config = spec.config

    # 模型配置
    table.add_row("Model", f"{config.model.name}-{config.model.variant}")
    table.add_row("Weights Path", config.model.weights_path)

    # 硬件配置
    table.add_row("Backend", config.hardware.backend_type)
    table.add_row("Device ID", str(config.hardware.device_id))
    table.add_row("NPUs per Node", str(config.hardware.npus_per_node))
    table.add_row("Nodes", str(config.hardware.nodes))
    table.add_row("Total Devices", str(spec.total_devices))

    # 并行配置
    table.add_row("Tensor Parallel", str(config.parallel.tensor_parallel_size))
    table.add_row("Pipeline Parallel", str(config.parallel.pipeline_parallel_size))

    # 功能特性
    table.add_row("KV Cache", config.features.kv_cache)
    table.add_row("Batching", config.features.batching)
    table.add_row("Quantization", config.features.quantization)

    console.print(table)


if __name__ == "__main__":
    main()
