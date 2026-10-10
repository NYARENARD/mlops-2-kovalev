from __future__ import annotations

import requests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10 


def fetch_hourly_temperature(latitude: float, longitude: float, timeout: int = REQUEST_TIMEOUT) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m",
    }
    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_dataframe(hours: list[str], temps: list[float]) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(hours),
            "temperature_c": temps,
        }
    )
    df = df.sort_values("time").reset_index(drop=True)
    return df


def save_plot(df: pd.DataFrame, path: str) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["temperature_c"], marker="o")
    plt.xticks(rotation=45)
    plt.title("Температура в Москве (24 часа)")
    plt.xlabel("Время")
    plt.ylabel("°C")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    data = fetch_hourly_temperature(latitude=55.75, longitude=37.61)

    hours = data["hourly"]["time"][:24]
    temps = data["hourly"]["temperature_2m"][:24]

    df = build_dataframe(hours, temps)
    df.to_csv("temperature_24h.csv", index=False)
    print("Сохранено в temperature_24h.csv")

    save_plot(df, "temperature_24h.png")
    print("Сохранено в temperature_24h.png")


if __name__ == "__main__":
    main()