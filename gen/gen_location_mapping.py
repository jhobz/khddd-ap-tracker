"""
Temporary script to generate location_mapping.lua from the KHDDD AP world's Locations.py.
Fetches the raw Locations.py from GitHub and parses it to create the Lua mapping table.
"""
import re
import urllib.request
import os

# Fetch the raw Locations.py
url = "https://raw.githubusercontent.com/LuxMake/Archipelago-KHDDD/main/worlds/khddd/Locations.py"
response = urllib.request.urlopen(url)
content = response.read().decode('utf-8')

# Parse all location entries
# Handles both compact and multi-line formats
pattern = r'"([^"]+)":\s*KHDDDLocationData\(\s*region="([^"]+)"\s*,\s*code\s*=\s*(\d+)\s*,?\s*\)'
matches = re.findall(pattern, content)

print(f"Found {len(matches)} location entries")


def get_world_name(region):
    """Get the world name by stripping [Sora]/[Riku] from the region."""
    return re.sub(r'\s*\[(?:Sora|Riku)\]$', '', region).strip()


def get_section_name(ap_name, region):
    """Extract a clean section name from the AP location name."""
    world = get_world_name(region)
    name = ap_name

    # Strip world prefix if the AP name starts with it
    if name.startswith(world + " "):
        name = name[len(world) + 1:]

    # Strip character suffix(es): [Sora] [Riku], [Sora], or [Riku]
    name = re.sub(r'\s*\[Sora\]\s*\[Riku\]\s*$', '', name)
    name = re.sub(r'\s*\[(?:Sora|Riku)\]\s*$', '', name)

    return name.strip()


def get_category(code, region, name):
    """Categorize each location for grouping in the Lua output."""
    if 2680000 <= code < 2690000:
        return "Secret Portals"
    if region == "Levels":
        return "Levels"
    if "Lord Kyroo" in name:
        return "Lord Kyroo"
    if "Traverse Town 2" in region:
        return "TT2 Rewards"
    if region.startswith("World Map"):
        return "Special Rewards"
    if 2670000 <= code < 2680000:
        if "[Sora]" in region or region == "Destiny Islands":
            return "Sora Events"
        else:
            return "Riku Events"
    if 2650000 <= code < 2660000:
        if "[Riku]" in region:
            return "Riku Chests"
        else:
            return "Sora Chests"
    return "Other"


# Build categorized mapping
categories = {}
for ap_name, region, code_str in matches:
    code = int(code_str)
    section = get_section_name(ap_name, region)
    cat = get_category(code, region, ap_name)
    if cat not in categories:
        categories[cat] = []
    categories[cat].append((code, region, section))

# Generate Lua output
lines = []
lines.append("-- use this file to map the AP location ids to your locations")
lines.append("-- first value is the code of the target location/item and the second is the item type override")
lines.append("-- to reference a location in Pop use @ in the beginning and then path to the section")
lines.append("-- path format: @Region/Section Name")
lines.append("-- (more info: https://github.com/black-sliver/PopTracker/blob/master/doc/PACKS.md#locations)")
lines.append("")
lines.append("BASE_LOCATION_ID = 0")
lines.append("LOCATION_MAPPING = {")

cat_order = [
    "Secret Portals",
    "Sora Events",
    "Riku Events",
    "TT2 Rewards",
    "Special Rewards",
    "Sora Chests",
    "Riku Chests",
    "Lord Kyroo",
    "Levels",
    "Other",
]

for cat in cat_order:
    if cat not in categories:
        continue
    # Section header comment
    label = cat
    pad_total = 40
    pad_inner = pad_total - len(label) - 2  # -2 for the ## on each side
    pad_left = pad_inner // 2
    pad_right = pad_inner - pad_left
    lines.append(f"\t{'#' * pad_total}")
    lines.append(f"\t{'#' * pad_left} {label} {'#' * pad_right}")
    lines.append(f"\t{'#' * pad_total}")

    for code, region, section in sorted(categories[cat], key=lambda x: x[0]):
        lines.append(f'\t[{code}] = {{ {{ "@{region}/{section}" }} }},')
    lines.append("")

lines.append("}")

output = "\n".join(lines) + "\n"

# Write to file
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
output_path = os.path.join(repo_root, "scripts", "autotracking", "location_mapping.lua")

with open(output_path, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nGenerated {sum(len(v) for v in categories.values())} location mappings")
print(f"Output: {output_path}")
print()
for cat in cat_order:
    if cat in categories:
        print(f"  {cat}: {len(categories[cat])} entries")
