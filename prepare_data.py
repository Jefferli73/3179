import pandas as pd

REF_YEAR = 2025  # census date: 31 January 2025

df = pd.read_csv(
    "data/vehicles_postcode_year_make.csv",
    usecols=["vehicle_type", "state_abb", "registered_postcode",
             "year_of_manufacture", "make", "no_vehicles"],
    dtype={"registered_postcode": str}
)

# passenger vehicles only — keeps the story about cars, not trucks and buses
df = df[df["vehicle_type"] == "Passenger vehicles"]

# force numeric; anything unconvertible becomes NaN
df["year_of_manufacture"] = pd.to_numeric(df["year_of_manufacture"], errors="coerce")
df["no_vehicles"] = pd.to_numeric(df["no_vehicles"], errors="coerce")

before = len(df)
df = df.dropna(subset=["year_of_manufacture", "no_vehicles"])
print("dropped non-numeric rows:", before - len(df))

df["year_of_manufacture"] = df["year_of_manufacture"].astype(int)
df["no_vehicles"] = df["no_vehicles"].astype(int)

# drop unusable rows
df = df[df["no_vehicles"] > 0]
df = df[df["year_of_manufacture"].between(1900, REF_YEAR)]

df["age"] = REF_YEAR - df["year_of_manufacture"]
df["age_weighted"] = df["age"] * df["no_vehicles"]
df["registered_postcode"] = df["registered_postcode"].astype(str).str.zfill(4)

# --- chart 4: mean vehicle age by postcode ---
pc = df.groupby("registered_postcode").agg(
    total_vehicles=("no_vehicles", "sum"),
    age_sum=("age_weighted", "sum")
).reset_index()
pc["mean_age"] = (pc["age_sum"] / pc["total_vehicles"]).round(2)
pc = pc[pc["total_vehicles"] >= 100]        # suppress tiny, noisy postcodes
pc[["registered_postcode", "mean_age", "total_vehicles"]] \
    .to_csv("data/postcode_mean_age.csv", index=False)

# --- fallback: same measure by state ---
st = df.groupby("state_abb").agg(
    total_vehicles=("no_vehicles", "sum"),
    age_sum=("age_weighted", "sum")
).reset_index()
st["mean_age"] = (st["age_sum"] / st["total_vehicles"]).round(2)
st[["state_abb", "mean_age", "total_vehicles"]] \
    .to_csv("data/state_mean_age.csv", index=False)

# --- charts 9-11: fleet by build decade ---
df["build_decade"] = (df["year_of_manufacture"] // 10 * 10).astype(int).astype(str) + "s"
dec = df.groupby("build_decade")["no_vehicles"].sum().reset_index()
dec.columns = ["build_decade", "vehicles"]
dec.to_csv("data/fleet_by_decade.csv", index=False)

print("postcodes:", len(pc), "| states:", len(st), "| decades:", len(dec))
print("mean age range:", pc.mean_age.min(), "-", pc.mean_age.max())