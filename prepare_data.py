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

# --- chart 5: proportional symbol map ---------------------------------
cent = pd.read_csv("data/postcode_centroids.csv", dtype={"POA_CODE21": str})
cent["POA_CODE21"] = cent["POA_CODE21"].str.zfill(4)
cent = cent.rename(columns={"POA_CODE21": "registered_postcode"})

sym = pc[["registered_postcode", "mean_age", "total_vehicles"]].merge(
    cent, on="registered_postcode", how="inner")

print(f"chart 5: matched {len(sym)} of {len(pc)} postcodes")
sym.round({"lon": 4, "lat": 4}).to_csv("data/postcode_symbols.csv", index=False)

# --- chart 6: bin map of electrified share -----------------------------
import json
mp = pd.read_csv("data/vehicles_postcode_motive.csv",
                 usecols=["vehicle_type", "registered_postcode",
                          "motive_power", "no_vehicles"],
                 dtype={"registered_postcode": str})
mp = mp[mp["vehicle_type"] == "Passenger vehicles"].copy()
mp["no_vehicles"] = pd.to_numeric(mp["no_vehicles"], errors="coerce").fillna(0).astype(int)
mp["registered_postcode"] = mp["registered_postcode"].str.zfill(4)

is_elec = mp["motive_power"].str.contains("electric|hybrid", case=False, na=False)

tot = mp.groupby("registered_postcode")["no_vehicles"].sum().rename("total")
ele = mp[is_elec].groupby("registered_postcode")["no_vehicles"].sum().rename("electrified")
pcm = pd.concat([tot, ele], axis=1).fillna(0).reset_index()

cent6 = pd.read_csv("data/postcode_centroids.csv", dtype={"POA_CODE21": str})
cent6["POA_CODE21"] = cent6["POA_CODE21"].str.zfill(4)
pcm = pcm.merge(cent6.rename(columns={"POA_CODE21": "registered_postcode"}),
                on="registered_postcode", how="inner")
print(f"chart 6: {len(pcm)} of {len(tot)} postcodes matched to a centroid")

CELL = 1.0        # degrees per bin -> ~41 bins across Australia

pcm["gx"] = (pcm["lon"] // CELL).astype(int)
pcm["gy"] = (pcm["lat"] // CELL).astype(int)

hx = (pcm.groupby(["gx", "gy"])
         .agg(total=("total", "sum"),
              electrified=("electrified", "sum"),
              postcodes=("registered_postcode", "size"))
         .reset_index())

hx = hx[hx["total"] >= 500]
hx["share"] = (hx["electrified"] / hx["total"] * 100).round(2)

feats = []
for row in hx.itertuples():
    x0, y0 = row.gx * CELL, row.gy * CELL
    x1, y1 = x0 + CELL, y0 + CELL
    feats.append({
        "type": "Feature",
        "properties": {"share": row.share, "total": int(row.total),
                       "postcodes": int(row.postcodes)},
        "geometry": {"type": "Polygon",
             "coordinates": [[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]]}
    })

with open("data/ev_hex.geojson", "w") as f:
    json.dump({"type": "FeatureCollection", "features": feats}, f)

print("bins:", len(feats), "| share range:", hx.share.min(), "-", hx.share.max())
print(hx.share.quantile([.2, .4, .6, .8]).round(1))

# --- charts 9-11: shelf vs driveway by decade ---------------------------
df["build_decade"] = (df["year_of_manufacture"] // 10 * 10).astype(int).astype(str) + "s"
dec = df.groupby("build_decade")["no_vehicles"].sum().reset_index()
dec.columns = ["build_decade", "vehicles"]
dec.to_csv("data/fleet_by_decade.csv", index=False)
cast = pd.read_csv("data/hot_wheels_castings.csv")
DECADES = [f"{d}s" for d in range(1920, 2030, 10)]

shelf = (cast["real_car_decade"].value_counts()
         .reindex(DECADES, fill_value=0).rename("castings"))
road = (dec.set_index("build_decade")["vehicles"]
        .reindex(DECADES, fill_value=0).rename("vehicles"))

comp = pd.concat([shelf, road], axis=1).reset_index(names="decade")
comp["shelf_share"] = (comp["castings"] / comp["castings"].sum() * 100).round(2)
comp["road_share"] = (comp["vehicles"] / comp["vehicles"].sum() * 100).round(2)
comp["diff"] = (comp["shelf_share"] - comp["road_share"]).round(2)
comp.to_csv("data/decade_compare.csv", index=False)

# --- chart 10: paired waffle, 1 square = 1 in 100 ---
def to_hundred(vals):
    tot = sum(vals)
    exact = [v / tot * 100 for v in vals]
    base = [int(e) for e in exact]
    for i in sorted(range(len(vals)), key=lambda i: -(exact[i] - base[i]))[:100 - sum(base)]:
        base[i] += 1
    return base

waffle = []
for side, col in (("Shelf", "castings"), ("Road", "vehicles")):
    i = 0
    for name, k in zip(comp["decade"], to_hundred(comp[col].tolist())):
        for _ in range(k):
            waffle.append({"side": side, "decade": name,
                           "row": i // 10, "col": i % 10})
            i += 1
pd.DataFrame(waffle).to_csv("data/decade_waffle.csv", index=False)

print(comp[["decade", "shelf_share", "road_share", "diff"]].to_string(index=False))
print("waffle rows:", len(waffle))

# --- fallback: same measure by state ---
st = df.groupby("state_abb").agg(
    total_vehicles=("no_vehicles", "sum"),
    age_sum=("age_weighted", "sum")
).reset_index()
st["mean_age"] = (st["age_sum"] / st["total_vehicles"]).round(2)
st[["state_abb", "mean_age", "total_vehicles"]] \
    .to_csv("data/state_mean_age.csv", index=False)

print("postcodes:", len(pc), "| states:", len(st), "| decades:", len(dec))
print("mean age range:", pc.mean_age.min(), "-", pc.mean_age.max())