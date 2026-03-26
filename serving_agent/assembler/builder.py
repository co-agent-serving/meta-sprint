"""
项目构建器

组装完整的 Rust 项目，包括 Cargo.toml、build.rs 和源代码。
"""

from pathlib import Path
from typing import List
import shutil

from jinja2 import Environment, FileSystemLoader

from serving_agent.config.validator import ConfigSpec


class ProjectAssembler:
    """
    项目组装器

    根据配置规格生成完整的 Rust 推理服务项目。
    """

    def __init__(self, template_dir: Path = None):
        """
        初始化组装器

        Args:
            template_dir: 模板目录路径
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    def assemble(self, spec: ConfigSpec, output_dir: Path) -> None:
        """
        组装项目

        Args:
            spec: 配置规格
            output_dir: 输出目录
        """
        output_dir = Path(output_dir)

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成项目结构
        self._generate_project_structure(spec, output_dir)

        # 生成 Cargo.toml
        self._generate_cargo_toml(spec, output_dir)

        # 生成 build.rs
        self._generate_build_rs(spec, output_dir)

        # 生成源代码
        self._generate_source_code(spec, output_dir)

    def _generate_project_structure(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成项目目录结构"""
        dirs = [
            output_dir / "src",
            output_dir / "src" / "model",
            output_dir / "src" / "engine",
            output_dir / "src" / "ops",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _generate_cargo_toml(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成 Cargo.toml"""
        template = self.env.get_template("Cargo.toml.j2")

        content = template.render(
            project_name=f"llm_server_{spec.config.model.name}",
            version="0.1.0",
            backend_type=spec.config.hardware.backend_type,
        )

        (output_dir / "Cargo.toml").write_text(content, encoding="utf-8")

    def _generate_build_rs(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成 build.rs"""
        template = self.env.get_template("build.rs.j2")

        content = template.render(
            backend_type=spec.config.hardware.backend_type,
            codegen_level=spec.config.backend.codegen_level,
        )

        (output_dir / "build.rs").write_text(content, encoding="utf-8")

    def _generate_source_code(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成源代码"""
        # 生成 main.rs
        self._generate_main_rs(spec, output_dir)

        # 根据后端类型生成算子实现
        if spec.config.hardware.backend_type == "pypto":
            self._generate_pypto_backend(spec, output_dir)

    def _generate_main_rs(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成 main.rs"""
        template = self.env.get_template("core/main.rs.j2")

        content = template.render(
            model_name=spec.config.model.name,
            model_variant=spec.config.model.variant,
            device_id=spec.config.hardware.device_id,
        )

        (output_dir / "src" / "main.rs").write_text(content, encoding="utf-8")

    def _generate_pypto_backend(self, spec: ConfigSpec, output_dir: Path) -> None:
        """生成 PyPTO 后端实现"""
        template = self.env.get_template("backends/pypto/ops.rs.j2")

        content = template.render(
            optimize_for=spec.config.backend.optimize_for,
            use_cache=spec.config.backend.use_cache,
        )

        (output_dir / "src" / "ops" / "pypto.rs").write_text(content, encoding="utf-8")
