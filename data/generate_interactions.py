# Synthetic User Interaction Telemetry Generator
# Generates realistic streaming clickstream events with user personas and temporal decay

import random
import datetime
import pandas as pd
from typing import List, Dict, Optional


USER_PERSONAS = {
    "SciFi_Binger": {
        "preferred_genres": ["Sci-Fi & Fantasy", "Action & Adventure", "Anime"],
        "watch_prob_boost": 0.85,
        "like_prob": 0.40,
        "completion_mean": 88.0,
    },
    "Crime_Mystery_Fan": {
        "preferred_genres": ["Crime & Docuseries", "Thriller & Mystery", "Drama"],
        "watch_prob_boost": 0.80,
        "like_prob": 0.35,
        "completion_mean": 82.0,
    },
    "Comedy_Casual": {
        "preferred_genres": ["Comedy", "Stand-up Comedy", "Romance"],
        "watch_prob_boost": 0.75,
        "like_prob": 0.25,
        "completion_mean": 65.0,
    },
    "Documentary_Scholar": {
        "preferred_genres": ["Docuseries", "Documentaries", "Crime & Docuseries"],
        "watch_prob_boost": 0.80,
        "like_prob": 0.45,
        "completion_mean": 90.0,
    },
    "General_Viewer": {
        "preferred_genres": ["Drama", "Action & Adventure", "Comedy", "Thriller & Mystery"],
        "watch_prob_boost": 0.50,
        "like_prob": 0.20,
        "completion_mean": 70.0,
    },
}


def generate_synthetic_interactions(
    titles_df: pd.DataFrame,
    num_users: int = 150,
    min_interactions_per_user: int = 5,
    max_interactions_per_user: int = 30,
    days_back: int = 90,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic user telemetry logs adhering to persona preferences and viewing behavior.
    """
    random.seed(seed)
    now = datetime.datetime.now(datetime.timezone.utc)
    interactions: List[Dict] = []

    available_titles = titles_df.to_dict(orient="records")
    if not available_titles:
        return pd.DataFrame(columns=["user_id", "show_id", "interaction_type", "watch_duration_pct", "timestamp"])

    persona_names = list(USER_PERSONAS.keys())

    for user_idx in range(1, num_users + 1):
        user_id = f"user_{user_idx:04d}"
        persona_name = random.choice(persona_names)
        persona = USER_PERSONAS[persona_name]

        n_events = random.randint(min_interactions_per_user, max_interactions_per_user)
        user_seen_titles = set()

        for _ in range(n_events):
            # Candidate selection biased by genre affinity
            if random.random() < persona["watch_prob_boost"]:
                # Pick title matching preferred genre
                matching_candidates = [
                    t for t in available_titles 
                    if any(g.lower() in t.get("listed_in", "").lower() for g in persona["preferred_genres"])
                ]
                title = random.choice(matching_candidates) if matching_candidates else random.choice(available_titles)
            else:
                title = random.choice(available_titles)

            show_id = str(title["show_id"])
            if show_id in user_seen_titles:
                continue
            user_seen_titles.add(show_id)

            # Determine interaction type
            r = random.random()
            if r < persona["like_prob"]:
                interaction_type = "like"
                watch_pct = max(10.0, min(100.0, random.gauss(persona["completion_mean"], 10.0)))
            elif r < persona["like_prob"] + 0.15:
                interaction_type = "save"
                watch_pct = max(0.0, min(50.0, random.gauss(20.0, 15.0)))
            elif r < 0.90:
                interaction_type = "watch"
                # Bimodal distribution: either quick bounce or full watch
                if random.random() < 0.25:
                    watch_pct = max(1.0, min(30.0, random.uniform(2.0, 25.0)))
                else:
                    watch_pct = max(30.0, min(100.0, random.gauss(persona["completion_mean"], 12.0)))
            else:
                interaction_type = "skip"
                watch_pct = max(0.5, min(10.0, random.uniform(0.5, 8.0)))

            # Random timestamp within past days_back days
            offset_seconds = random.randint(0, days_back * 86400)
            event_time = now - datetime.timedelta(seconds=offset_seconds)

            interactions.append({
                "user_id": user_id,
                "show_id": show_id,
                "interaction_type": interaction_type,
                "watch_duration_pct": round(watch_pct, 2),
                "timestamp": event_time.isoformat()
            })

    df = pd.DataFrame(interactions)
    df.sort_values(by=["user_id", "timestamp"], ascending=[True, True], inplace=True)
    return df


if __name__ == "__main__":
    import os
    raw_path = os.path.join(os.path.dirname(__file__), "raw", "netflix_titles.csv")
    if os.path.exists(raw_path):
        tdf = pd.read_csv(raw_path)
        idf = generate_synthetic_interactions(tdf)
        out_path = os.path.join(os.path.dirname(__file__), "synthetic_interactions.csv")
        idf.to_csv(out_path, index=False)
        print(f"Generated {len(idf)} interaction events to {out_path}")
