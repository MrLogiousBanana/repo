import os
import sys
import subprocess
import hashlib
import gzip
import bz2
import lzma
from PIL import Image, ImageDraw, ImageFont

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DEBS_DIR = os.path.join(REPO_DIR, "debs")

def hash_file(filepath):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    size = os.path.getsize(filepath)
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        "size": size,
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest()
    }

def get_control_content(deb_path):
    out = subprocess.check_output(["dpkg-deb", "-f", deb_path]).decode("utf-8", errors="ignore")
    return out.strip()

def build_packages():
    packages_entries = []
    deb_files = sorted([f for f in os.listdir(DEBS_DIR) if f.endswith(".deb")])
    
    for deb in deb_files:
        deb_path = os.path.join(DEBS_DIR, deb)
        control = get_control_content(deb_path)
        h = hash_file(deb_path)
        
        entry = control + "\n"
        entry += f"Filename: debs/{deb}\n"
        entry += f"Size: {h['size']}\n"
        entry += f"MD5sum: {h['md5']}\n"
        entry += f"SHA1: {h['sha1']}\n"
        entry += f"SHA256: {h['sha256']}\n"
        packages_entries.append(entry)
        print(f"[+] Added {deb} ({h['size']} bytes)")
        
    full_packages = "\n".join(packages_entries) + "\n"
    packages_path = os.path.join(REPO_DIR, "Packages")
    with open(packages_path, "w", encoding="utf-8") as f:
        f.write(full_packages)
        
    # Compress Packages
    with open(packages_path, "rb") as f_in:
        raw_data = f_in.read()
        
    with gzip.open(os.path.join(REPO_DIR, "Packages.gz"), "wb", compresslevel=9) as f_gz:
        f_gz.write(raw_data)
        
    with bz2.open(os.path.join(REPO_DIR, "Packages.bz2"), "wb", compresslevel=9) as f_bz2:
        f_bz2.write(raw_data)
        
    with lzma.open(os.path.join(REPO_DIR, "Packages.xz"), "wb", preset=9) as f_xz:
        f_xz.write(raw_data)
        
    print("[+] Generated Packages, Packages.gz, Packages.bz2, Packages.xz")

def build_release():
    files_to_hash = ["Packages", "Packages.gz", "Packages.bz2", "Packages.xz"]
    file_hashes = {}
    for filename in files_to_hash:
        path = os.path.join(REPO_DIR, filename)
        file_hashes[filename] = hash_file(path)
        
    release_content = """Origin: MrLogiousBanana Repo
Label: MrLogiousBanana
Suite: stable
Version: 1.0
Codename: ios
Architectures: iphoneos-arm64
Components: main
Description: MrLogiousBanana's Personal iOS 15 Rootless Repository
MD5Sum:
"""
    for fname in files_to_hash:
        h = file_hashes[fname]
        release_content += f" {h['md5']} {h['size']:>8} {fname}\n"

    release_content += "SHA1:\n"
    for fname in files_to_hash:
        h = file_hashes[fname]
        release_content += f" {h['sha1']} {h['size']:>8} {fname}\n"

    release_content += "SHA256:\n"
    for fname in files_to_hash:
        h = file_hashes[fname]
        release_content += f" {h['sha256']} {h['size']:>8} {fname}\n"

    release_path = os.path.join(REPO_DIR, "Release")
    with open(release_path, "w", encoding="utf-8") as f:
        f.write(release_content)
    print("[+] Generated Release file")

def generate_cydia_icon():
    icon_path = os.path.join(REPO_DIR, "CydiaIcon.png")
    # Generate stylish 192x192 rounded icon with gradient and custom banana logo
    img = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background gradient or vibrant sleek dark pill
    for y in range(192):
        r = int(24 + (y / 192.0) * 16)
        g = int(24 + (y / 192.0) * 16)
        b = int(28 + (y / 192.0) * 20)
        draw.line([(0, y), (192, y)], fill=(r, g, b, 255))
        
    # Draw rounded mask
    mask = Image.new("L", (192, 192), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (192, 192)], radius=42, fill=255)
    
    # Subtle glowing border
    icon_final = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    icon_final.paste(img, (0, 0), mask)
    
    draw_final = ImageDraw.Draw(icon_final)
    draw_final.rounded_rectangle([(1, 1), (190, 190)], radius=42, outline=(255, 214, 10, 180), width=3)
    
    # Draw Banana Glyph or Initial "B"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
        draw_final.text((96, 90), "🍌", fill=(255, 214, 10, 255), font=font, anchor="mm")
    except Exception:
        draw_final.ellipse([(60, 60), (132, 132)], fill=(255, 214, 10, 255))
        
    icon_final.save(icon_path)
    print(f"[+] Saved CydiaIcon.png to {icon_path}")

if __name__ == "__main__":
    build_packages()
    build_release()
    generate_cydia_icon()
