"""
Generates ultra-sleek, professional hacker cipher decryption headers for Dark and Light modes.
Starts with cryptographic hashes and resolves into 'JAVED HUSSAIN' with glowing neon trails.
"""

def build_svg(is_dark=True):
    target = "JAVED HUSSAIN"
    bg_fill = "#0d1117" if is_dark else "#f6f8fa"
    border_col = "#30363d" if is_dark else "#d0d7de"
    text_fixed = "#c9d1d9" if is_dark else "#1f2328"
    text_muted = "#8b949e" if is_dark else "#57606a"
    accent_green = "#39d353" if is_dark else "#1a7f37"
    accent_cyan = "#00f7ff" if is_dark else "#0969da"
    accent_blue = "#58a6ff" if is_dark else "#218bff"
    accent_purple = "#bc8cff" if is_dark else "#8250df"

    total_time = 12.0
    resolve_step = 0.22

    keyframes_css = []
    tspans_svg = []
    x_cursor = 185

    for i, char in enumerate(target):
        if char == " ":
            x_cursor += 18
            continue

        c_id = f"c{i}"
        resolve_time = 0.5 + i * resolve_step
        p1 = ((resolve_time * 0.3) / total_time) * 100
        p2 = ((resolve_time * 0.6) / total_time) * 100
        p3 = ((resolve_time * 0.85) / total_time) * 100
        p_res = (resolve_time / total_time) * 100
        p_rst = ((total_time - 0.7) / total_time) * 100

        glow_style = f"drop-shadow(0 0 7px rgba(57,211,83,0.85))" if is_dark else "none"

        kf = f"""
      @keyframes decrypt_{c_id} {{
        0%, {p1 - 0.1:.1f}% {{ opacity: 0.5; fill: {accent_cyan}; }}
        {p1:.1f}%, {p2 - 0.1:.1f}% {{ opacity: 0.7; fill: {accent_blue}; }}
        {p2:.1f}%, {p3 - 0.1:.1f}% {{ opacity: 0.85; fill: {accent_green}; }}
        {p_res:.1f}%, {p_rst:.1f}% {{ opacity: 1; fill: {accent_green}; filter: {glow_style}; }}
        {p_rst + 0.1:.1f}%, 100%   {{ opacity: 0.4; fill: {accent_cyan}; }}
      }}"""
        keyframes_css.append(kf)
        tspans_svg.append(f"""    <tspan class="char-{c_id}" x="{x_cursor}">{char}</tspan>""")
        x_cursor += 22

    all_kf = "\n".join(keyframes_css)
    all_tspans = "\n".join(tspans_svg)
    class_selectors = "\n".join(f"      .char-c{i} {{ animation: decrypt_c{i} {total_time}s infinite; }}" for i in range(len(target)) if target[i] != " ")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 145" width="100%" height="145">
  <defs>
    <linearGradient id="cyber-border" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{border_col}" stop-opacity="0.2" />
      <stop offset="30%" stop-color="{accent_green}" stop-opacity="0.8" />
      <stop offset="70%" stop-color="{accent_cyan}" stop-opacity="0.8" />
      <stop offset="100%" stop-color="{border_col}" stop-opacity="0.2" />
    </linearGradient>

    <style>
      .term-prompt {{ font-family: ui-monospace, "JetBrains Mono", Menlo, monospace; font-size: 11px; fill: {text_muted}; }}
      .term-cmd    {{ fill: {accent_blue}; font-weight: 600; }}
      .term-green  {{ fill: {accent_green}; font-weight: 700; }}
      .term-cyan   {{ fill: {accent_cyan}; }}
      .fixed-text  {{ font-family: ui-monospace, "JetBrains Mono", monospace; font-size: 32px; font-weight: 700; fill: {text_fixed}; }}
      .cipher-text {{ font-family: ui-monospace, "JetBrains Mono", Consolas, monospace; font-size: 32px; font-weight: 800; }}
      
      @keyframes blink-cursor {{
        0%, 100% {{ opacity: 1; }}
        50%      {{ opacity: 0; }}
      }}
      .cursor {{ animation: blink-cursor 0.9s infinite; fill: {accent_green}; }}
      
{all_kf}
      
{class_selectors}
    </style>
  </defs>

  <!-- Clean Cyber Terminal Frame -->
  <rect x="1" y="1" width="838" height="143" rx="8" fill="{bg_fill}" stroke="{border_col}" stroke-width="1.2" />
  <line x1="80" y1="1" x2="760" y2="1" stroke="url(#cyber-border)" stroke-width="2" />
  
  <!-- Corner Reticles -->
  <path d="M12 20 V12 H20" fill="none" stroke="{accent_green}" stroke-width="1.5" />
  <path d="M828 20 V12 H820" fill="none" stroke="{accent_cyan}" stroke-width="1.5" />
  <path d="M12 125 V133 H20" fill="none" stroke="{accent_green}" stroke-width="1.5" />
  <path d="M828 125 V133 H820" fill="none" stroke="{accent_cyan}" stroke-width="1.5" />

  <!-- Top Terminal CLI Status -->
  <g transform="translate(32, 28)">
    <text class="term-prompt">
      <tspan class="term-green">root@sec-ops</tspan>:<tspan class="term-cyan">~#</tspan> 
      <tspan class="term-cmd">./decrypt_identity.sh</tspan> 
      --target <tspan fill="#e3b341">iamjaved026</tspan> 
      <tspan fill="{text_muted}">[0x7F2A_CIPHER_RESOLVED]</tspan>
    </text>
  </g>

  <!-- Middle Main Line: Hi, I'm JAVED HUSSAIN -->
  <g transform="translate(32, 78)">
    <text class="fixed-text" x="0" y="0">Hi, I'm</text>
    
    <text class="cipher-text" y="0">
{all_tspans}
    </text>

    <!-- Glowing Terminal Cursor -->
    <rect x="{x_cursor + 6}" y="-26" width="14" height="30" rx="2" class="cursor" />
  </g>

  <!-- Bottom Telemetry Badges -->
  <g transform="translate(32, 120)" class="term-prompt">
    <circle cx="4" cy="-4" r="3" fill="{accent_green}" />
    <text x="14" y="0" fill="{accent_green}">SECURITY RESEARCHER</text>
    
    <text x="175" y="0" fill="{border_col}">|</text>
    <text x="190" y="0" fill="{accent_blue}">68 REPOSITORIES VAULT</text>

    <text x="365" y="0" fill="{border_col}">|</text>
    <text x="380" y="0" fill="{accent_purple}">355 VERIFIED COMMITS</text>

    <text x="555" y="0" fill="{border_col}">|</text>
    <text x="570" y="0" fill="{accent_green}">STATUS: COMPILED_ONLINE</text>
  </g>
</svg>"""

if __name__ == "__main__":
    with open("d:/Projects/portofilio/github/my/v2/assets/header-cipher-dark.svg", "w", encoding="utf-8") as f:
        f.write(build_svg(is_dark=True))
    with open("d:/Projects/portofilio/github/my/v2/assets/header-cipher-light.svg", "w", encoding="utf-8") as f:
        f.write(build_svg(is_dark=False))
    # Also default header-cipher.svg
    with open("d:/Projects/portofilio/github/my/v2/assets/header-cipher.svg", "w", encoding="utf-8") as f:
        f.write(build_svg(is_dark=True))
    print("Generated header-cipher-dark.svg and header-cipher-light.svg successfully!")
