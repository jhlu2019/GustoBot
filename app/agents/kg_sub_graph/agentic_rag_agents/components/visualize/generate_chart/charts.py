from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure


def create_scatter_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    fig, ax = plt.subplots()
    sns.scatterplot(data=data, x=x, y=y, hue=hue, ax=ax)
    sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)

    return fig


def create_bar_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    fig, ax = plt.subplots()
    sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax)
    # sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    # plt.xticks(rotation=90)

    return fig


def create_line_plot(
    data: List[Dict[str, Any]], x: str, y: str, hue: Optional[str] = None
) -> Figure:
    fig, ax = plt.subplots()
    sns.lineplot(data=data, x=x, y=y, hue=hue, ax=ax)
    sns.move_legend(plt.gca(), "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)

    return fig


def create_empty_plot() -> Figure:
    fig, ax = plt.subplots()
    return fig
