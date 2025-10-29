from typing import Any, Dict, List, Optional, TYPE_CHECKING

try:  # Optional plotting dependencies
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.figure import Figure
except ImportError:  # pragma: no cover - graceful degradation
    plt = None  # type: ignore[assignment]
    sns = None  # type: ignore[assignment]
    if TYPE_CHECKING:  # for type checkers
        from matplotlib.figure import Figure  # pragma: no cover
    else:
        Figure = Any  # type: ignore[assignment]


def _ensure_plotting_backend() -> None:
    if plt is None or sns is None:
        raise RuntimeError(
            "matplotlib/seaborn 未安装，无法生成图表。请在运行环境中安装 `matplotlib` 和 `seaborn` 后重试。"
        )


def create_scatter_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    _ensure_plotting_backend()
    fig, ax = plt.subplots()
    sns.scatterplot(data=data, x=x, y=y, hue=hue, ax=ax)
    sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)

    return fig


def create_bar_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    _ensure_plotting_backend()
    fig, ax = plt.subplots()
    sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax)
    # sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    # plt.xticks(rotation=90)

    return fig


def create_line_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    _ensure_plotting_backend()
    fig, ax = plt.subplots()
    sns.lineplot(data=data, x=x, y=y, hue=hue, ax=ax)
    sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)

    return fig


def create_empty_plot() -> Figure:
    _ensure_plotting_backend()
    fig, ax = plt.subplots()
    return fig
