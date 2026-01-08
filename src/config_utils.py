from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, List

import yaml


@dataclass(slots=True)
class DataConfig:
    db_uri: str
    sources: List[str]
    streams_path: str


@dataclass(slots=True)
class ModelConfig:
    name: str
    temperature: float = 0.0
    base_url: str = "localhost:11434"
    api_key: str = "***"


@dataclass(slots=True)
class EmbeddingsConfig:
    model: str
    base_url: str = "localhost:11434"


@dataclass(slots=True)
class ConstantsConfig:
    station_name: str
    station_url: str
    contact_link: str
    links: List[str]
    service_email: str


@dataclass(slots=True)
class AuthConfig:
    username: str
    password: str


@dataclass(slots=True)
class RunConfig:
    debug: bool = False
    share: bool = False


@dataclass(slots=True)
class TestSuiteConfig:
    eval_data_rag: str
    eval_data_red_teaming: str


@dataclass(slots=True)
class RunTestsConfig:
    red_teaming: bool = True
    rag: bool = True


@dataclass(slots=True)
class JudgeConfig:
    model: str
    temperature: float
    base_url: str
    api_key: str = "***"


@dataclass(slots=True)
class AppConfig:
    """
    Configuration for radiobrain application.
    """
    
    data: DataConfig
    model: ModelConfig
    embeddings: EmbeddingsConfig
    constants: ConstantsConfig
    auth: AuthConfig
    run: RunConfig

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """
        Load an AppConfig from a YAML file.

        Args:
            path (str | Path): The path to the YAML configuration file.

        Returns:
            AppConfig: An instance of AppConfig populated with the data from the YAML file.
        """
        path = Path(path).expanduser()
        with path.open("r", encoding="utf-8") as f:
            raw: Mapping[str, Any] = yaml.safe_load(f)

        return cls(
            data=DataConfig(**raw["data"]),
            model=ModelConfig(**raw["model"]),
            embeddings=EmbeddingsConfig(**raw["embeddings"]),
            constants=ConstantsConfig(**raw["constants"]),
            auth=AuthConfig(**raw["auth"]),
            run=RunConfig(**raw["run"]),
        )


@dataclass(slots=True)
class EvalConfig:
    """
    Configuration for evaluation settings.
    """

    data: DataConfig
    model: ModelConfig
    embeddings: EmbeddingsConfig
    constants: ConstantsConfig
    test_suite: TestSuiteConfig
    run_tests: RunTestsConfig
    judge: JudgeConfig

    @classmethod
    def from_yaml(cls, path: str | Path) -> "EvalConfig":
        """
        Load an EvalConfig from a YAML file.

        Args:
            path (str | Path): The path to the YAML configuration file.

        Returns:
            EvalConfig: An instance of EvalConfig populated with the data from the YAML file.
        """
        path = Path(path).expanduser()
        with path.open("r", encoding="utf-8") as f:
            raw: Mapping[str, Any] = yaml.safe_load(f)

        return cls(
            data=DataConfig(**raw["data"]),
            model=ModelConfig(**raw["model"]),
            embeddings=EmbeddingsConfig(**raw["embeddings"]),
            constants=ConstantsConfig(**raw["constants"]),
            test_suite=TestSuiteConfig(**raw["test_suite"]),
            run_tests=RunTestsConfig(**raw["run_tests"] if "run_tests" in raw else {}),
            judge=JudgeConfig(**raw["judge"]),
        )
