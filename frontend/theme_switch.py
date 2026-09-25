import os
import glob

replacements = {
    # Backgrounds
    "bg-white": "bg-slate-900/50 backdrop-blur-xl",
    "bg-slate-50": "bg-slate-950",
    "bg-slate-100": "bg-slate-800",
    "bg-slate-200": "bg-slate-700",
    
    # Borders
    "border-slate-200": "border-white/10",
    "border-slate-300": "border-white/20",
    
    # Text colors
    "text-slate-900": "text-white",
    "text-slate-800": "text-slate-200",
    "text-slate-600": "text-slate-400",
    "text-slate-500": "text-slate-400",
    "text-slate-400": "text-slate-500",
    
    # Primary Accent (Blue -> Hot Pink/Magenta)
    "bg-blue-50": "bg-pink-500/10",
    "bg-blue-100": "bg-pink-500/20",
    "bg-blue-500": "bg-pink-500",
    "bg-blue-600": "bg-pink-600",
    "bg-blue-700": "bg-pink-700",
    "text-blue-500": "text-pink-400",
    "text-blue-600": "text-pink-500",
    "text-blue-700": "text-pink-400",
    "ring-blue-500": "ring-pink-500",
    "border-blue-200": "border-pink-500/30",
    "border-blue-500": "border-pink-500",
    
    # Shadows
    "shadow-sm": "shadow-lg shadow-pink-500/5",
    
    # Specific component tweaks for the "Wave" theme
    "bg-emerald-500": "bg-pink-500",
    "bg-emerald-50 ": "bg-pink-500/10 ",
    "text-emerald-700": "text-pink-400",
    "border-emerald-200": "border-pink-500/30",
}

def apply_theme():
    # Find all JSX files
    files = glob.glob("src/**/*.jsx", recursive=True)
    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content
        
        # We need to sort by length descending to prevent partial replacements 
        # (e.g. replacing 'bg-blue-50' inside 'bg-blue-500')
        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        
        for k in sorted_keys:
            v = replacements[k]
            new_content = new_content.replace(k, v)
            
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {filepath}")

if __name__ == "__main__":
    apply_theme()
