"""
JAX Environment Renderer.

Provides rendering utilities that convert JAX EnvState to RGB frames for visualization.
Works with the JAX-native environment without requiring the PyTorch GridWorld class.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import time
from io import BytesIO
from PIL import Image

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

# Imports for JAX EnvState
import jax.numpy as jnp
from src.environment.state import select_by_class

# Global cache for icons to avoid reloading every frame
_ICON_CACHE = None

def _load_icons(icon_config=None):
    """Loads icons from assets directory based on config."""
    global _ICON_CACHE
    if _ICON_CACHE is not None:
        return _ICON_CACHE
        
    # Calculate assets path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_path = os.path.join(base_dir, 'assets')
    
    # Default icons mapping if not provided
    if icon_config is None:
        icon_config = {
            'agent': 'agent',
            'food': 'food',
            'hiding_predator': 'hiding_predator',
            'predator': 'predator',
            'agent_food': 'agent_food',
            'agent_hiding_predator': 'agent_hiding_predator',
            'agent_predator': 'agent_predator',
            'rock': 'rock',
            'bush': 'bush',
            'agent_bush': 'bush_agent',
            'neutral': 'neutral'
        }
    
    supported_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']
    
    icons = {}
    for key, base_filename in icon_config.items():
        found = False
        for ext in supported_extensions:
            filename = f"{base_filename}{ext}" if not base_filename.endswith(ext) else base_filename
            path = os.path.join(assets_path, filename)
            
            if os.path.exists(path):
                try:
                    if ext.lower() == '.svg':
                        if CAIROSVG_AVAILABLE:
                            # Convert SVG to PNG in memory then to numpy array
                            png_data = cairosvg.svg2png(url=path)
                            icons[key] = np.array(Image.open(BytesIO(png_data)))
                            found = True
                        else:
                            # print(f"Warning: cairosvg not available for {path}")
                            pass
                    else:
                        # Use PIL to ensure alpha channels (transparency) are correctly handled for all formats
                        img = Image.open(path)
                        if img.mode != 'RGBA':
                             img = img.convert('RGBA')
                        icons[key] = np.array(img)
                        found = True
                    
                    if found:
                        break
                except Exception as e:
                    # print(f"Error loading icon {path}: {e}")
                    pass
        
        if not found:
            # print(f"Warning: Icon not found for key '{key}' with extensions {supported_extensions}")
            icons[key] = None
            
    _ICON_CACHE = icons
    return icons


# Global cache for figure, axes, and canvas to avoid recreating them every frame
_FIG_CACHE = None

# Professional Color Palette (Industrial White / Technical)
# Designed for high-contrast white backgrounds (Presentations)
COLORS = {
    'bg': '#FFFFFF',
    'pod_bg': '#F9FAFB',
    'border': '#E5E7EB',
    'text_main': '#1F2937',
    'text_label': '#6B7280',
    'text_offline': '#9CA3AF',
    'grid': '#F3F4F6',
    
    # Technical Tones
    'satiation': '#0D9488',   # Teal
    'nutrition': '#D97706',   # Amber
    'injury': '#BE123C',      # Ruby/Crimson
    'intero_noc': '#7C3AED',  # Violet (WandB/Purple aesthetic)
    'mod': '#7C3AED',         # Violet
    'action': '#2563EB',      # Cobalt
    
    # Entity Tones (Muted but distinct)
    'food': '#059669',
    'hiding_predator': '#DC2626',
    'predator': '#111827',
    'rock': '#4B5563',
    'neutral': '#0891B2',
    
    # Damage Segments
    'dmg_hiding_predator': '#EF4444',
    'dmg_predator': '#111827',
    'dmg_obstacle': '#6B7280',

    # Body temperature (thermal system). Deliberately not one of the four hues
    # already in use above — amber (#D97706) is nutrition and ruby (#BE123C) is
    # injury, and a gauge the reader mistakes for either is worse than no gauge.
    'temperature': '#EA580C',
}

# ── Thermal rendering (temperature system, Stage 6a) ──────────────────────────
#
# Everything below is ADDITIVE and self-contained: a field underlay, a body
# temperature gauge, and a debug outline of the cells the thermoceptor reads.
# It deliberately does not restructure the panel layout or the sensor pointer
# logic, because a larger rendering rewrite is expected separately and this
# stage must not entrench assumptions that rewrite would have to undo.
#
# A DIVERGING scale is right here, not a sequential one, because temperature has
# a meaningful zero: `temperature_setpoint`, the value the agent's body is
# defending. Blue is below it, red above it, and the neutral midpoint is the
# temperature at which the body has nothing to do.
THERMAL_CMAP = 'RdBu_r'


def thermal_color_limits(thermal_field, params):
    """Colour limits for the field underlay — FIXED for the whole episode.

    Returns `(vmin, vmax)` symmetric about `temperature_setpoint`, or None when
    there is no field to draw (thermal off, or an old recording that predates
    the thermal fields — see `_snapshot_state` in `src/utils/eval_recording.py`).

    WHY FIXED MATTERS. If the limits were recomputed per frame from whatever
    that frame happened to contain, a world that is steadily cooling would
    render as a world of constant appearance: the colours would track the
    shrinking range instead of the falling temperature, and the one thing the
    visualisation exists to show would be the one thing it hid.

    Within an episode the field is built once at reset and never mutated, so
    deriving the limits from `state.thermal_field` is already frame-invariant.
    The guarantee is nevertheless made explicit rather than left to that
    invariant: `render_jax_state` takes a `thermal_clim` argument, and the
    offline recording renderer computes it ONCE from the episode's first frame
    and passes the same pair to every frame after it. That is what keeps the
    scale fixed even if a future change makes the field move during an episode.
    """
    if thermal_field is None:
        return None
    field = np.asarray(thermal_field)
    if field.size == 0:
        return None
    setpoint = float(getattr(params, 'temperature_setpoint', 0.0))
    span = float(np.max(np.abs(field - setpoint)))
    if not np.isfinite(span) or span <= 0.0:
        span = 1.0
    return (setpoint - span, setpoint + span)


def _thermal_rgba(value, clim):
    """Map one temperature onto the diverging scale, given FIXED limits."""
    vmin, vmax = clim
    t = 0.0 if vmax <= vmin else (float(value) - vmin) / (vmax - vmin)
    return matplotlib.colormaps[THERMAL_CMAP](float(np.clip(t, 0.0, 1.0)))


def draw_temperature_gauge(ax, x, y, w, h, body_temp, params, clim,
                           transform=None, label_dy=0.02, obs_temp=None):
    """Body-temperature gauge, with the two death thresholds marked.

    Not `draw_dual_capsule_bar`, and the reason is geometry rather than taste:
    that widget wants two stacked text rows per bar, and the vitals stack has
    five rows on a thermal config with no room for them.

    Body temperature is observed only when `thermal.body_temp_observable` is
    true. `obs_temp` is therefore OPTIONAL and carries what the agent actually
    received (post-noise) when the channel is on:

    * `obs_temp is None` — the channel is off (or the caller has no sensory
      data). ONE number is drawn, the true one, and the widget is byte-for-byte
      what it was before the channel existed.
    * `obs_temp is not None` — a second, dimmer number is drawn beside it in the
      project's "translucent = reality, solid = perceived" grammar: the solid
      value is what the agent perceives, the label says `real ...` for the
      world's own value.

    The bar spans `[min_temperature, max_temperature]`, the interval outside
    which the episode ends with termination reason 5, so the two ends of the
    trough ARE the death thresholds; they are marked, and so is the setpoint.
    The fill takes its colour from the same diverging scale as the field
    underlay, so a cold body reads blue on a blue patch of world. The bar
    geometry is UNCHANGED when `obs_temp` is passed — the 5-bar vitals layout is
    hand-tuned against the Run Context pod at y = 0.48 and a sixth row collides
    with it.
    """
    t_min = float(params.min_temperature)
    t_max = float(params.max_temperature)
    t_set = float(params.temperature_setpoint)
    span = max(t_max - t_min, 1e-6)
    frac = float(np.clip((float(body_temp) - t_min) / span, 0.0, 1.0))

    ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={h/2}",
        facecolor='#F3F4F6', edgecolor='none', transform=transform, zorder=0))

    fill_color = _thermal_rgba(body_temp, clim) if clim else COLORS['temperature']
    ax.add_patch(matplotlib.patches.FancyBboxPatch(
        (x, y), max(h, w * frac), h,
        boxstyle=f"round,pad=0,rounding_size={h/2}",
        facecolor=fill_color, edgecolor='none', transform=transform, zorder=1))

    # Setpoint tick — where the body has nothing to defend against.
    set_frac = float(np.clip((t_set - t_min) / span, 0.0, 1.0))
    ax.plot([x + w * set_frac] * 2, [y - h * 0.2, y + h * 1.2],
            color=COLORS['text_label'], linewidth=0.8, linestyle=(0, (2, 1)),
            transform=transform, zorder=3)

    # Death thresholds — the two ends of the survivable interval.
    for edge in (x, x + w):
        ax.plot([edge, edge], [y - h * 0.3, y + h * 1.3],
                color=COLORS['injury'], linewidth=1.2, transform=transform,
                zorder=3)

    # Everything on ONE line, left-aligned, and the value INSIDE the bar. The
    # vitals stack has five rows on a thermal config and no room for a second
    # text row per bar; a right-aligned value here would also land on the OBS
    # readout of the bar above it.
    ax.text(x, y + h + label_dy,
            f"BODY TEMP   DIE {t_min:+.0f} / {t_max:+.0f}",
            color=COLORS['text_label'], fontsize=6.5, fontweight='bold',
            transform=transform)
    # Right-aligned INSIDE the bar. Centring it put the number over the empty
    # trough whenever the body was cold, where it collided with the setpoint
    # tick; the right end is always clear.
    #
    # With the channel observable the SOLID number is what the agent perceives
    # and the true value follows it in the label colour, so the grammar matches
    # every other vital: solid = perceived, dim = reality. No extra row, no
    # geometry change.
    if obs_temp is None:
        ax.text(x + w - 0.015, y + h * 0.5, f"{float(body_temp):+.2f}",
                color=COLORS['text_main'], fontsize=7, fontweight='bold',
                ha='right', va='center', transform=transform, zorder=4,
                fontfamily='monospace',
                path_effects=[matplotlib.patheffects.withStroke(
                    linewidth=2.0, foreground='#FFFFFF')])
    else:
        ax.text(x + w - 0.015, y + h * 0.5,
                f"{float(obs_temp):+.2f}  real {float(body_temp):+.2f}",
                color=COLORS['text_main'], fontsize=6, fontweight='bold',
                ha='right', va='center', transform=transform, zorder=4,
                fontfamily='monospace',
                path_effects=[matplotlib.patheffects.withStroke(
                    linewidth=2.0, foreground='#FFFFFF')])


def draw_thermal_diamond(ax, x, y, w, h, values, sensor_range, clim,
                         transform=None, colour_offset=0.0):
    """The thermoceptor pod: one diverging patch per cell of the Manhattan diamond.

    Drawn on its own rather than through `draw_categorical_visual` because that
    widget draws bar height proportional to the value on a 0-1 assumption. A
    thermoceptive reading is `thermal_field - body_temp`, which spans roughly
    -43 to +170 on the shipped config, so it would render as bars several times
    the height of their own pod — and negative readings would draw downward,
    out of the frame entirely.
    """
    offsets = np.array(get_visual_offsets(int(sensor_range)))
    vals = np.asarray(values).reshape(-1)
    if len(vals) != len(offsets):
        return

    n_r = int(offsets[:, 0].max() - offsets[:, 0].min()) + 1
    n_c = int(offsets[:, 1].max() - offsets[:, 1].min()) + 1
    # Sized separately in x and y: these are AXES fractions, and the panel is
    # about three times taller than it is wide, so a "square" cell here would
    # render as a tall thin sliver.
    cell_w = (w / max(n_c, 1)) * 0.86
    cell_h = (h / max(n_r, 1)) * 0.86
    cx, cy = x + w / 2.0, y + h / 2.0

    for (dr, dc), v in zip(offsets, vals):
        px = cx + dc * (w / max(n_c, 1)) - cell_w / 2.0
        py = cy - dr * (h / max(n_r, 1)) - cell_h / 2.0
        rgba = _thermal_rgba(float(v) + colour_offset, clim) if clim else (0.8, 0.8, 0.8, 1.0)
        ax.add_patch(plt.Rectangle(
            (px, py), cell_w, cell_h, facecolor=rgba,
            edgecolor=COLORS['border'], linewidth=0.4,
            transform=transform, zorder=2))
        # Text colour follows the patch's luminance. The two ends of a diverging
        # scale are dark, and dark-on-dark is exactly where the fire cell — the
        # one reading anybody looks at — becomes unreadable.
        lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        ax.text(px + cell_w / 2.0, py + cell_h / 2.0, f"{float(v):+.0f}",
                color=(COLORS['text_main'] if lum > 0.55 else '#FFFFFF'),
                fontsize=5.5, fontweight='bold',
                ha='center', va='center', transform=transform, zorder=3,
                fontfamily='monospace')

def draw_dual_capsule_bar(ax, x, y, w, h, state_pct, obs_pct, color, label=None, state_val=None, obs_val=None, transform=None,
                          label_dy=0.02, obs_dy=0.03):
    """Draws a professional capsule-style progress bar showing reality vs perception.

    `label_dy` / `obs_dy` are the vertical offsets of the two text rows (the
    label + REAL row above the bar, the OBS row below it). They default to the
    values this widget has always used, so every existing call is unchanged;
    callers that have to pack the bars tighter — the five-row vitals stack on a
    thermal config, and the squeezed sensor pods — pass smaller ones. Without
    them one row's OBS readout lands on the next row's REAL readout, which is
    not visible in the source and is unmissable in the frame.
    """
    # Background (Trough)
    bg_rect = matplotlib.patches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={h/2}", 
        facecolor='#F3F4F6', edgecolor='none', transform=transform, zorder=0
    )
    ax.add_patch(bg_rect)
    
    # State (Reality) - Thicker, slightly translucent base
    if state_pct > 0:
        val_w = max(h, w * min(1.0, state_pct))
        st_rect = matplotlib.patches.FancyBboxPatch(
            (x, y), val_w, h, boxstyle=f"round,pad=0,rounding_size={h/2}", 
            facecolor=color, edgecolor='none', alpha=0.3, transform=transform, zorder=1
        )
        ax.add_patch(st_rect)
        
    # Observation (Perception) - Thinner interior bar or Marker
    if obs_pct > 0:
        val_w = max(h*0.6, w * min(1.0, obs_pct))
        obs_rect = matplotlib.patches.FancyBboxPatch(
            (x, y + h*0.2), val_w, h*0.6, boxstyle=f"round,pad=0,rounding_size={h*0.3}", 
            facecolor=color, edgecolor='none', transform=transform, zorder=2
        )
        ax.add_patch(obs_rect)

    # Labels
    if label:
        ax.text(x, y + h + label_dy, label.upper(), color=COLORS['text_label'],
                fontsize=7, fontweight='bold', transform=transform)
    
    # Value labels (Reality: Bold black, Obs: Smaller Gray)
    if state_val is not None:
        ax.text(x + w, y + h + label_dy, f"REAL: {state_val}", color=COLORS['text_main'],
                fontsize=7, fontweight='bold', ha='right', transform=transform, fontfamily='monospace')
    if obs_val is not None:
        ax.text(x + w, y - obs_dy, f"OBS:  {obs_val}", color=COLORS['text_label'],
                fontsize=6, fontweight='bold', ha='right', transform=transform, fontfamily='monospace')

def draw_pod_frame(ax, x, y, w, h, title, offline=False, obs_only=False, transform=None):
    """Draws a modular Telemetry Pod frame."""
    rect = plt.Rectangle((x, y), w, h, facecolor=COLORS['bg'], edgecolor=COLORS['border'], 
                         linewidth=0.5, transform=transform, zorder=0)
    ax.add_patch(rect)
    
    # Accent top border
    border_color = COLORS['border'] if not offline else COLORS['text_offline']
    ax.plot([x, x + w], [y + h, y + h], color=border_color, linewidth=1.5, transform=transform, zorder=1)
    
    # Title
    t_color = COLORS['text_label'] if not offline else COLORS['text_offline']
    if obs_only:
        title = title + " (OBS ONLY)"
        t_color = COLORS['text_offline']
        
    ax.text(x + 0.02, y + h + 0.015, title.upper(), color=t_color, 
            fontsize=8, fontweight='bold', transform=transform)
    
    if offline:
        ax.text(x + w/2, y + h/2, "OFFLINE", color=COLORS['text_offline'], 
                ha='center', va='center', fontsize=9, fontweight='bold', 
                alpha=0.5, transform=transform)

from src.environment.sensor import get_visual_offsets

def draw_boresight_diamond(ax, x, y, size, vec, r, num_features, true_vec=None, icons=None, obs_only=False, transform=None):
    """
    Draws a schematic Manhattan diamond grid for directional sensors.
    Uses the same offset logic as sensor.py for perfect spatial alignment.
    """
    # Use the unified offset logic from sensor.py
    offsets = np.array(get_visual_offsets(r))
    
    if len(vec) != len(offsets) * num_features:
        return 
        
    obs_grid = np.array(vec).reshape(len(offsets), num_features)
    true_grid = np.array(true_vec).reshape(len(offsets), num_features) if true_vec is not None else None
    
    feature_keys = [
        'grass',    # 0: Grass
        'sand',     # 1: Sand
        'plain',    # 2: Plain
        'food',     # 3: Food
        'hiding_predator',   # 4: Hiding Predator
        'predator', # 5: Predator
        'rock',     # 6: Rock
        'neutral',  # 7: Neutral Animal
    ]
    
    feature_colors = [
        '#A1DFA1', '#F2D7D5', '#FFFFFF', COLORS['food'], COLORS['hiding_predator'], 
        COLORS['predator'], COLORS['rock'], COLORS['neutral']
    ]
    
    for i, (dr, dc) in enumerate(offsets):
        cell_x, cell_y = x + dc * size, y - dr * size
        
        # Cell background
        rect = plt.Rectangle((cell_x - size/2, cell_y - size/2), size, size, 
                             facecolor='none', edgecolor=COLORS['grid'], linewidth=0.3, transform=transform, zorder=1)
        ax.add_patch(rect)
        
        obs_vals = obs_grid[i]
        true_vals = true_grid[i] if true_grid is not None else obs_vals
        
        if num_features == 1:
            # Collision Style: Grid-based indicator
            if not obs_only and true_vals[0] > 0.5: # Reality: Ghosted fill
                ax.add_patch(plt.Rectangle((cell_x - size*0.48, cell_y - size*0.48), size*0.96, size*0.96, 
                             facecolor=COLORS['hiding_predator'], alpha=0.15, transform=transform, zorder=2))
            if obs_vals[0] > 0.5: # Perception: Solid block
                ax.add_patch(plt.Rectangle((cell_x - size*0.35, cell_y - size*0.35), size*0.7, size*0.7, 
                             facecolor=COLORS['hiding_predator'], alpha=0.8, transform=transform, zorder=3))
        else:
            # Visual Style: Grid-based indicators
            # 1. Draw Reality (Ghosted)
            if not obs_only:
                true_active = np.where(true_vals > 0.1)[0]
                # Prioritize entities (Index 3+) over terrain (0,1,2)
                true_entities = [idx for idx in true_active if idx >= 3]
                
                for feat_idx in true_active:
                    icon_key = feature_keys[feat_idx % len(feature_keys)]
                    icon_img = icons.get(icon_key) if icons else None
                    if icon_img is not None and (feat_idx >= 3 or not true_entities):
                        # Fixed scaling: ensure icon fits within the cell (size * 0.35 zoom)
                        imagebox = OffsetImage(icon_img, zoom=size * 0.35)
                        ab = AnnotationBbox(imagebox, (cell_x, cell_y), frameon=False, pad=0, xycoords=transform if transform else 'data')
                        ab.set_alpha(0.15) 
                        ax.add_artist(ab)
                    else:
                        color = feature_colors[feat_idx % len(feature_colors)]
                        ax.add_patch(plt.Rectangle((cell_x - size*0.48, cell_y - size*0.48), size*0.96, size*0.96, 
                                     facecolor=color, alpha=0.1, transform=transform, zorder=2))
            
            # 2. Draw Perception (Solid)
            obs_active = np.where(obs_vals > 0.1)[0]
            obs_entities = [idx for idx in obs_active if idx >= 3]
            
            for feat_idx in obs_active:
                icon_key = feature_keys[feat_idx % len(feature_keys)]
                icon_img = icons.get(icon_key) if icons else None
                
                if icon_img is not None and (feat_idx >= 3 and len(obs_entities) == 1):
                    imagebox = OffsetImage(icon_img, zoom=size * 0.35)
                    ab = AnnotationBbox(imagebox, (cell_x, cell_y), frameon=False, pad=0, xycoords=transform if transform else 'data')
                    ax.add_artist(ab)
                elif feat_idx >= 3:
                    color = feature_colors[feat_idx % len(feature_colors)]
                    ax.add_patch(plt.Rectangle((cell_x - size*0.35, cell_y - size*0.35), size*0.7, size*0.7, 
                                 facecolor=color, alpha=0.9, transform=transform, zorder=4))
    
    # Center markers removed to reduce visual clutter as requested
    pass

def draw_categorical_visual(ax, x, y, w, h, obs_vec, r, num_features, true_vec=None, labels=None, obs_only=False, transform=None):
    """Draws a categorical bar chart for visual observations (V7).
    y: bottom of the pod frame
    h: total height of the pod frame
    """
    obs_grid = np.array(obs_vec).reshape(-1, num_features)
    true_grid = np.array(true_vec).reshape(-1, num_features) if true_vec is not None else obs_grid
    num_cells = obs_grid.shape[0]
    
    # Defaults for 8-channel (fallback)
    if labels is None:
        feature_labels = ['GRS', 'SND', 'PLN', 'FOD', 'DNG', 'PRD', 'NEU', 'RCK']
    else:
        feature_labels = labels
        
    feature_colors = [
        '#A1DFA1', '#F2D7D5', '#FFFFFF', COLORS['food'], COLORS['hiding_predator'], 
        COLORS['predator'], COLORS['neutral'], COLORS['rock']
    ]
    # Rotate colors if we have more features
    while len(feature_colors) < num_features:
        feature_colors += feature_colors
    # Cell labels for spatial context (Center, Up, Right, Down, Left)
    cell_labels = ['C', 'U', 'R', 'D', 'L'] if num_cells == 5 else [f'C{i}' for i in range(num_cells)]
    if num_cells <= 1: cell_labels = ['']

    # Internal Margins (Percent of pod height h)
    margin_bottom = 0.04 
    margin_top = 0.02
    
    bar_y = y + margin_bottom
    bar_h = h - (margin_bottom + margin_top)

    # Calculate horizontal distribution
    cell_gap_ratio = 1.15
    unit_w = w / (num_cells * num_features + max(num_cells - 1, 0) * cell_gap_ratio)
    
    for c_idx in range(num_cells):
        start_x = x + c_idx * (num_features + cell_gap_ratio) * unit_w
        
        # Group Label for Spatial Orientation
        if num_cells > 1:
            ax.text(start_x + (num_features * unit_w)/2, bar_y + bar_h + 0.002, cell_labels[c_idx], 
                    color=COLORS['text_label'], fontsize=5.5, fontweight='bold', ha='center', transform=transform)
            
        for f_idx in range(num_features):
            bx = start_x + f_idx * unit_w
            bw = unit_w * 0.8
            color = feature_colors[f_idx % len(feature_colors)]
            
            # Ground Truth (Ghosted)
            if not obs_only:
                true_val = float(true_grid[c_idx, f_idx])
                ax.add_patch(plt.Rectangle((bx, bar_y), bw, bar_h * true_val, facecolor=color, alpha=0.15, transform=transform, zorder=1))
            
            # Perception (Solid)
            obs_val = float(obs_grid[c_idx, f_idx])
            ax.add_patch(plt.Rectangle((bx + bw*0.1, bar_y), bw*0.8, bar_h * obs_val, facecolor=color, alpha=0.9, transform=transform, zorder=2))
            
            # Categorical Labels inside frame
            if (num_cells == 1 or c_idx == 0) and f_idx < len(feature_labels):
                ax.text(bx + bw*1.1/2, y + 0.002, feature_labels[f_idx], color=COLORS['text_label'], 
                        fontsize=4.0, ha='center', va='bottom', rotation=90, transform=transform)

def render_jax_state(state, params, episode=None, step=None, train_episode=None, dpi=100, icon_scale=1.0, action=None, sensory_data=None, info=None, icon_config=None,
                     thermal_clim=None, debug_thermal_cells=False):
    """
    Render a JAX EnvState to an RGB numpy array (Industrial White V2).

    thermal_clim: optional `(vmin, vmax)` pair pinning the field underlay's
        colour scale for a whole episode. When None it is derived from
        `state.thermal_field` via `thermal_color_limits`. Pass it explicitly
        when rendering a sequence of frames so the scale provably cannot drift
        between them (`scripts/eval/render_recordings.py` does).
    debug_thermal_cells: outline the cells the thermoceptor reads. Off by
        default — it is a debugging aid, not part of the standard frame.
    """
    from src.environment.core import calculate_drive
    start_time = time.time()
    icons = _load_icons(icon_config)
    global _FIG_CACHE
    
    # Grid dimensions
    height, width = int(params.height), int(params.width)
    view_size = int(params.local_view_size)
    agent_pos = np.array(state.agent_pos)
    ar, ac = int(agent_pos[0]), int(agent_pos[1])
    
    # Calculate local window bounds
    half_view = view_size // 2
    r_start = max(0, min(height - view_size, ar - half_view))
    c_start = max(0, min(width - view_size, ac - half_view))
    
    # Robustly bound for cases where view_size > height/width (e.g. 5x5 view on 4x4 grid)
    r_start = max(0, r_start)
    c_start = max(0, c_start)
    r_end = min(height, r_start + view_size)
    c_end = min(width, c_start + view_size)
    
    # Force creation to ensure V2 aesthetics
    plt.close('all')
    
    # Figure setup: Wide layout for presentation (Now 10in tall for V7)
    fig = plt.figure(figsize=(14, 10), dpi=dpi)
    fig.patch.set_facecolor(COLORS['bg'])
    
    # GridSpec: [Left Telemetry] [Ultimate Arena] [Right Telemetry]
    # Center Arena ratio pushed to 2.2 for true fullscreen feel
    gs = fig.add_gridspec(1, 3, width_ratios=[0.8, 2.2, 0.8])
    
    ax_left = fig.add_subplot(gs[0, 0])      # INTEROCEPTION + Minimap
    ax_grid = fig.add_subplot(gs[0, 1])      # ULTIMATE ARENA (Maximized)
    ax_right = fig.add_subplot(gs[0, 2])     # EXTEROCEPTION + Action
    
    for ax in [ax_left, ax_grid, ax_right]:
        ax.set_facecolor(COLORS['bg'])
        ax.axis('off')
        
    canvas = FigureCanvas(fig)
    _FIG_CACHE = (fig, ax_grid, ax_right, ax_left, canvas)

    # --- 1. Center Arena: Maximized Local View ---
    ax_grid.set_xlim(c_start - 0.5, c_end - 0.5)
    ax_grid.set_ylim(r_start - 0.5, r_end - 0.5)
    ax_grid.invert_yaxis()
    ax_grid.set_aspect('equal')
    ax_grid.axis('off')
    
    # ... (rest of local grid and minimap logic remains same) ...
    
    # -- Local Grid --
    ax_grid.set_xlim(c_start - 0.5, c_end - 0.5)
    ax_grid.set_ylim(r_start - 0.5, r_end - 0.5)
    ax_grid.invert_yaxis()
    ax_grid.set_aspect('equal')
    ax_grid.axis('off')
    
    # Background grid
    for x in range(c_start, c_end + 1):
        ax_grid.vlines(x - 0.5, r_start - 0.5, r_end - 0.5, colors=COLORS['grid'], linewidth=0.5)
    for y in range(r_start, r_end + 1):
        ax_grid.hlines(y - 0.5, c_start - 0.5, c_end - 0.5, colors=COLORS['grid'], linewidth=0.5)
        
    # Location types
    location_colors = {0: COLORS['bg'], 1: '#ECFDF5', 2: '#FFFBEB'}
    loc_grid = np.array(params.grid_location_type)
    for r in range(r_start, r_end):
        for c in range(c_start, c_end):
            l_type = int(loc_grid[r, c])
            if l_type != 0:
                ax_grid.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1, color=location_colors.get(l_type, COLORS['bg']), zorder=0))

    # ── Thermal field underlay (temperature system, Stage 6a) ─────────────────
    # `getattr` with a default, not `state.thermal_field`, and that is required
    # rather than defensive: a `.rec` file recorded before the thermal system
    # existed carries no `thermal_field` key, its snapshot object therefore has
    # no such attribute, and every such recording must keep rendering exactly as
    # it does today. `RECORDING_FORMAT_VERSION` was deliberately NOT bumped
    # (plan D4/F10) — the version stamp nothing reads would not have removed a
    # single line of this branch.
    thermal_field = np.asarray(getattr(state, 'thermal_field', None)) \
        if getattr(state, 'thermal_field', None) is not None else None
    thermal_on = bool(getattr(params, 'thermal_enabled', False)) \
        and thermal_field is not None and thermal_field.size > 0
    if thermal_on:
        if thermal_clim is None:
            thermal_clim = thermal_color_limits(thermal_field, params)
        # zorder 0, same as the terrain tiles but added AFTER them, so it tints
        # the terrain rather than being hidden by it — and still sits BELOW the
        # grid lines (zorder 2) and every entity artist drawn after this point,
        # whose stacking is therefore untouched.
        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                ax_grid.add_patch(plt.Rectangle(
                    (c - 0.5, r - 0.5), 1, 1,
                    facecolor=_thermal_rgba(thermal_field[r, c], thermal_clim),
                    edgecolor='none', alpha=0.85, zorder=0))
    else:
        thermal_clim = None

    # Icon Drawing
    scale_factor = (4.0 / view_size) * icon_scale
    def draw_icon(ax, r, c, icon_key, zoom=0.038, s_fac=1.0, is_axes_coords=False):
        img = icons.get(icon_key)
        if img is not None:
            imagebox = OffsetImage(img, zoom=zoom * s_fac)
            ab = AnnotationBbox(imagebox, (c, r), frameon=False, pad=0, xycoords='data' if not is_axes_coords else ax.transAxes)
            ax.add_artist(ab)
        else:
            m_map = {'agent':('o',COLORS['action']), 'food':('D',COLORS['food']), 'hiding_predator':('X',COLORS['hiding_predator']), 'predator':('v',COLORS['predator']), 'rock':('s',COLORS['rock']), 'neutral':('o',COLORS['neutral'])}
            m, clr = m_map.get(icon_key, ('s', 'grey'))
            ax.plot(c, r, marker=m, markersize=12*s_fac, color=clr, markeredgecolor='white', markeredgewidth=1, transform=ax.transData if not is_axes_coords else ax.transAxes)

    # Entities
    res_pos, res_type, res_active = np.array(state.res_pos), np.array(params.res_type), np.array(state.res_active)
    # Entities at agent position (for composite visualization)
    at_agent = []

    # Entities
    res_pos, res_type, res_active = np.array(state.res_pos), np.array(params.res_type), np.array(state.res_active)
    for i in range(len(res_active)):
        if not res_active[i]: continue
        rr, rc = int(res_pos[i, 0]), int(res_pos[i, 1])
        if rr == ar and rc == ac:
            at_agent.append('food' if res_type[i] == 0 else 'hiding_predator')
        elif r_start <= rr < r_end and c_start <= rc < c_end:
            draw_icon(ax_grid, rr, rc, 'food' if res_type[i] == 0 else 'hiding_predator', zoom=0.035, s_fac=scale_factor)
            
    _pred_mask = select_by_class(params, 'predator')
    p_pos = np.array(state.animal_pos)[_pred_mask]
    for i in range(p_pos.shape[0]):
        pr, pc = int(p_pos[i, 0]), int(p_pos[i, 1])
        if pr == ar and pc == ac:
            at_agent.append('predator')
        elif r_start <= pr < r_end and c_start <= pc < c_end:
            draw_icon(ax_grid, pr, pc, 'predator', zoom=0.045, s_fac=scale_factor)

    o_pos = np.array(state.obs_pos)
    obs_types = np.array(params.obs_type)
    obs_hides = np.array(params.obs_hides_agent) if hasattr(params, 'obs_hides_agent') else np.zeros(o_pos.shape[0], dtype=bool)
    for i in range(o_pos.shape[0]):
        or_, oc = int(o_pos[i, 0]), int(o_pos[i, 1])
        if or_ == ar and oc == ac:
            obs_icon_name = params.obstacle_names[obs_types[i]]
            if obs_hides[i]:
                at_agent.append('bush')
        elif r_start <= or_ < r_end and c_start <= oc < c_end:
            obs_icon = params.obstacle_names[obs_types[i]]
            draw_icon(ax_grid, or_, oc, obs_icon, zoom=0.035, s_fac=scale_factor)

    _neut_mask = select_by_class(params, 'neutral')
    n_pos = np.array(state.animal_pos)[_neut_mask]
    for i in range(n_pos.shape[0]):
        nr, nc = int(n_pos[i, 0]), int(n_pos[i, 1])
        if nr == ar and nc == ac:
            at_agent.append('neutral')
        elif r_start <= nr < r_end and c_start <= nc < c_end:
            draw_icon(ax_grid, nr, nc, 'neutral', zoom=0.035, s_fac=scale_factor)

    # Determine Agent Icon (Normal vs Composite Overlap)
    agent_icon = 'agent'
    if 'predator' in at_agent:
        agent_icon = 'agent_predator'
    elif 'hiding_predator' in at_agent:
        agent_icon = 'agent_hiding_predator'
    elif 'bush' in at_agent:
        agent_icon = 'agent_bush'
    elif 'food' in at_agent:
        agent_icon = 'agent_food'
    elif 'neutral' in at_agent:
        agent_icon = 'agent'
        
    draw_icon(ax_grid, ar, ac, agent_icon, zoom=0.035, s_fac=scale_factor)

    if thermal_on:
        # Debug-only outline of the five cells the thermoceptor reads. Off by
        # default: it answers "is the sensor looking where I think it is",
        # which is a question you ask while debugging, not on every frame.
        if debug_thermal_cells:
            for dr, dc in np.array(get_visual_offsets(int(params.thermal_grid_range))):
                rr = int(np.clip(ar + dr, 0, height - 1))     # edge-CLAMPED, matching
                cc = int(np.clip(ac + dc, 0, width - 1))      # sense_thermoception (F3)
                ax_grid.add_patch(plt.Rectangle(
                    (cc - 0.5, rr - 0.5), 1, 1, fill=False,
                    edgecolor=COLORS['temperature'], linewidth=1.4,
                    linestyle=(0, (3, 2)), zorder=6))

        # A compact scale strip, so the fixed limits are readable off the frame
        # itself rather than taken on trust. Both end labels are printed: if a
        # later frame shows different numbers, the scale rescaled.
        vmin, vmax = thermal_clim
        strip_x, strip_y, strip_w, strip_h = 0.24, -0.045, 0.52, 0.018
        for i in range(52):
            t = i / 51.0
            ax_grid.add_patch(plt.Rectangle(
                (strip_x + t * strip_w, strip_y), strip_w / 51.0 + 0.002, strip_h,
                facecolor=matplotlib.colormaps[THERMAL_CMAP](t), edgecolor='none',
                transform=ax_grid.transAxes, clip_on=False, zorder=5))
        ax_grid.text(strip_x - 0.01, strip_y + strip_h / 2, f"{vmin:+.0f}",
                     color=COLORS['text_label'], fontsize=6, fontweight='bold',
                     ha='right', va='center', transform=ax_grid.transAxes,
                     clip_on=False, fontfamily='monospace')
        ax_grid.text(strip_x + strip_w + 0.01, strip_y + strip_h / 2, f"{vmax:+.0f}",
                     color=COLORS['text_label'], fontsize=6, fontweight='bold',
                     ha='left', va='center', transform=ax_grid.transAxes,
                     clip_on=False, fontfamily='monospace')
        ax_grid.text(strip_x + strip_w / 2, strip_y - 0.022,
                     "THERMAL FIELD (fixed scale)", color=COLORS['text_label'],
                     fontsize=6, fontweight='bold', ha='center', va='top',
                     transform=ax_grid.transAxes, clip_on=False)

    # -- Sidebar Minimap (Integrated into ax_left) --
    # In V4, the minimap moves to the bottom of the left panel
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax_minimap = inset_axes(ax_left, width="80%", height="25%", loc='lower center', borderpad=2.2)
    
    ax_minimap.axis('off')
    ax_minimap.set_aspect('equal')
    ax_minimap.set_xlim(-0.5, width - 0.5)
    ax_minimap.set_ylim(-0.5, height - 0.5)
    ax_minimap.invert_yaxis()
    
    minimap_img = np.ones((height, width, 3))
    for l_id, color_hex in location_colors.items():
        if l_id == 0: continue
        from matplotlib.colors import to_rgb
        minimap_img[loc_grid == l_id] = to_rgb(color_hex)
    ax_minimap.imshow(minimap_img, extent=(-0.5, width-0.5, height-0.5, -0.5), zorder=0, alpha=0.5)
    
    # Restoration of Global Entities on Minimap (Smaller dots for sidebar)
    def plot_entity_dots(positions, active_mask, color):
        valid = positions[active_mask]
        if len(valid) > 0:
            ax_minimap.scatter(valid[:, 1], valid[:, 0], s=2.5, color=color, edgecolors='none', alpha=0.8, zorder=2)

    plot_entity_dots(res_pos, res_active & (res_type == 0), COLORS['food'])
    plot_entity_dots(res_pos, res_active & (res_type == 1), COLORS['hiding_predator'])
    plot_entity_dots(p_pos, np.ones(p_pos.shape[0], dtype=bool), COLORS['predator'])
    plot_entity_dots(o_pos, np.ones(o_pos.shape[0], dtype=bool), COLORS['rock'])
    plot_entity_dots(n_pos, np.ones(n_pos.shape[0], dtype=bool), COLORS['neutral'])

    ax_minimap.add_patch(plt.Rectangle((c_start-0.5, r_start-0.5), view_size, view_size, fill=False, edgecolor=COLORS['action'], linewidth=0.8, alpha=0.6, zorder=3))
    ax_minimap.plot(ac, ar, 'o', color=COLORS['action'], markersize=3, markeredgecolor='white', markeredgewidth=0.4, zorder=4)
    
    # Title for Minimap in Sidebar (V5.2 Polish)
    ax_left.text(0.5, 0.32, "MINIMAP", color=COLORS['text_label'], fontsize=7, fontweight='bold', ha='center', transform=ax_left.transAxes)

    # --- 2. Left Panel: Vitals (Dual View) ---
    y_ptr = 0.95
    ax_left.text(0.05, y_ptr, "INTEROCEPTION", color=COLORS['text_main'], fontsize=10, fontweight='black', transform=ax_left.transAxes)

    # Known sensor observations for mapping
    sensor_map = {s['name']: s for s in sensory_data} if sensory_data else {}

    # Compact spacing as bars are added. Satiation / Nutrition / Injury are
    # always drawn; Intero Nociception and Body Temperature are conditional.
    # The 3-bar and 4-bar cases keep their exact previous geometry, so a frame
    # rendered from a thermal-OFF config is pixel-for-pixel what it was before
    # this stage. Only the 5-bar case is new, and it has to tighten: at the
    # 4-bar spacing the fifth gauge would land on top of the Run Context pod,
    # whose top edge is at y = 0.48.
    intero_noc_enabled = bool(getattr(params, 'interoceptive_nociception_enabled', False))
    n_bars = 3 + int(intero_noc_enabled) + int(thermal_on)
    if n_bars >= 5:
        # Five rows have to fit between the section header (0.95) and the
        # "RUN CONTEXT" pod TITLE, which draw_pod_frame puts at 0.495 — the
        # pod's box top at 0.48 is not the real floor. Bars are also shortened,
        # because each row spans label (+h+0.02) to OBS readout (-0.03) and at
        # h = 0.04 that span exceeds the step.
        head_gap, bar_step, bar_h = 0.08, 0.085, 0.032
        label_dy, obs_dy = 0.012, 0.018
    elif n_bars == 4:
        head_gap, bar_step, bar_h = 0.12, 0.10, 0.04
        label_dy, obs_dy = 0.02, 0.03
    else:
        head_gap, bar_step, bar_h = 0.12, 0.15, 0.04
        label_dy, obs_dy = 0.02, 0.03
    y_ptr -= head_gap

    # Satiation
    sat_real, max_sat = float(state.satiation), float(params.max_satiation)
    sat_obs_data = sensor_map.get('Satiation', {'intensity': sat_real/max_sat})
    sat_obs = float(sat_obs_data.get('intensity', 0))
    draw_dual_capsule_bar(ax_left, 0.05, y_ptr, 0.9, bar_h, sat_real/max_sat, sat_obs, COLORS['satiation'], 
                          "Satiation", f"{sat_real/max_sat:.2f}", f"{sat_obs:.2f}", transform=ax_left.transAxes, label_dy=label_dy, obs_dy=obs_dy)
    y_ptr -= bar_step
    
    # Nutrition
    nut_real, max_nut = float(state.nutrition), float(params.max_nutrition)
    nut_obs_data = sensor_map.get('Nutrition', {'intensity': nut_real/max_nut})
    nut_obs = float(nut_obs_data.get('intensity', 0))
    draw_dual_capsule_bar(ax_left, 0.05, y_ptr, 0.9, bar_h, nut_real/max_nut, nut_obs, COLORS['nutrition'], 
                          "Nutrition", f"{nut_real/max_nut:.2f}", f"{nut_obs:.2f}", transform=ax_left.transAxes, label_dy=label_dy, obs_dy=obs_dy)
    y_ptr -= bar_step
    
    # Injury
    inj_real, max_inj = float(state.injury_level), float(params.max_injury)
    inj_obs_data = sensor_map.get('Injury', {'intensity': inj_real/max_inj})
    inj_obs = float(inj_obs_data.get('intensity', 0))
    draw_dual_capsule_bar(ax_left, 0.05, y_ptr, 0.9, bar_h, inj_real/max_inj, inj_obs, COLORS['injury'], 
                          "Injury", f"{inj_real/max_inj:.2f}", f"{inj_obs:.2f}", transform=ax_left.transAxes, label_dy=label_dy, obs_dy=obs_dy)
    y_ptr -= bar_step

    # Interoceptive Nociception (only when enabled)
    if intero_noc_enabled:
        # The convolution defines the *signal*; perceptual noise is independent and added on top.
        # "real" = noise-free convolved intero noc (from get_observation(..., apply_noise=False))
        # "obs"  = noisy version of the same convolved signal
        # Both equal under perceptual_noise.enabled=False; differ only by noise when enabled.
        intero_obs_data = sensor_map.get('Intero Nociception')
        if intero_obs_data is not None:
            intero_real = float(intero_obs_data.get('true_intensity',
                                                   intero_obs_data.get('intensity', 0.0)))
            intero_obs  = float(intero_obs_data.get('intensity', intero_real))
        else:
            # Fallback: no sensory_data provided. Recompute the convolved signal host-side.
            # Mirrors sense_interoceptive_nociception() in src/environment/sensor.py
            import numpy as _np
            if bool(getattr(params, 'interoceptive_convolution_enabled', False)):
                buf = _np.asarray(state.nociception_history_buffer)
                ker = _np.asarray(params.interoceptive_kernel)
                # Normalize by max_injury
                intero_real = float(_np.sum(buf * ker) / max(float(params.max_injury), 1e-6))
            else:
                intero_real = float(state.injury_level) / max_inj
            intero_obs = intero_real

        draw_dual_capsule_bar(ax_left, 0.05, y_ptr, 0.9, bar_h, intero_real, intero_obs, COLORS['intero_noc'],
                              "Intero Noc", f"{intero_real:.2f}", f"{intero_obs:.2f}", transform=ax_left.transAxes,
                              label_dy=label_dy, obs_dy=obs_dy)
        y_ptr -= bar_step

    # Body temperature (temperature system, Stage 6a). Without this gauge a
    # video shows the world's temperature and not the agent's — and the agent's
    # is the half that decides whether the episode ends.
    if thermal_on:
        body_temp = float(getattr(state, 'body_temp', params.temperature_setpoint))
        # `.get('value')` and not `.get('intensity')`: build_sensory_viz keys the
        # Body Temperature pod with `value` precisely because it is raw degrees
        # and not a [0,1] fraction. None whenever the channel is off.
        draw_temperature_gauge(ax_left, 0.05, y_ptr, 0.9, bar_h, body_temp,
                               params, thermal_clim, transform=ax_left.transAxes,
                               label_dy=label_dy,
                               obs_temp=(sensor_map.get('Body Temperature')
                                         or {}).get('value'))
        y_ptr -= bar_step

    draw_pod_frame(ax_left, 0.05, 0.32, 0.9, 0.16, "Run Context", transform=ax_left.transAxes)
    ctxt_y = 0.43
    ax_left.text(0.1, ctxt_y, f"EPISODE:", color=COLORS['text_label'], fontsize=7, transform=ax_left.transAxes)
    # Use sequential episode (defaulting to train_episode if episode is None)
    disp_ep = episode if episode is not None else (train_episode or '--')
    ax_left.text(0.9, ctxt_y, f"{disp_ep}", color=COLORS['text_main'], fontsize=7, fontweight='bold', ha='right', transform=ax_left.transAxes)
    ctxt_y -= 0.04
    ax_left.text(0.1, ctxt_y, f"SCALE:", color=COLORS['text_label'], fontsize=7, transform=ax_left.transAxes)
    ax_left.text(0.9, ctxt_y, f"{width}x{height}", color=COLORS['text_main'], fontsize=7, fontweight='bold', ha='right', transform=ax_left.transAxes)
    ctxt_y -= 0.04
    ax_left.text(0.1, ctxt_y, f"STEP:", color=COLORS['text_label'], fontsize=7, transform=ax_left.transAxes)
    ax_left.text(0.9, ctxt_y, f"{step or '--'}", color=COLORS['text_main'], fontsize=7, fontweight='bold', ha='right', transform=ax_left.transAxes)

    # --- 3. Right Panel: Sensory Telemetry (Observations) ---
    y_cursor = 0.95
    ax_right.text(0.05, y_cursor, "EXTEROCEPTION", color=COLORS['text_main'], fontsize=11, fontweight='black', transform=ax_right.transAxes)
    y_cursor -= 0.05
    pod_h_default = 0.11
    

    known_sensors = ['Olfactory', 'Extero Nociception', 'Collision', 'Visual', 'LOC']
    # 'Thermoception' is emitted by `sensor.py::build_sensory_viz` (Stage 3);
    # without it in this list the pod is built and then never drawn, so the
    # modality that decides half the episode is invisible in every video.
    #
    # Inserted ONLY when thermal is on, and that is not tidiness. An absent name
    # in this list is still drawn — as an "OFFLINE" pod — so an unconditional
    # entry would put an empty THERMOCEPTION panel on every non-thermal frame
    # AND push the Visual pod past the `y_cursor < 0.20` floor into the Action
    # pod. Checked by rendering: that is exactly what it did.
    if thermal_on or 'Thermoception' in sensor_map:
        known_sensors.insert(2, 'Thermoception')

    # Pod heights are budgeted before anything is drawn. Without this, adding a
    # fifth pod does not add a pod — it pushes the LAST one past the same floor,
    # and the frame silently loses the Visual panel instead. The budget (0.74)
    # is exactly what the pre-thermal four-pod stack consumed.
    #
    # Applied ONLY on thermal configs (`_squeeze` is pinned to 1.0 otherwise),
    # so every frame this project has ever rendered keeps its exact geometry —
    # including the pre-existing behaviour where a config with the location
    # sensor on has its LOC pod cut off by the floor. Fixing that is a
    # different change from this one.
    def _pod_height(name):
        d = sensor_map.get(name)
        if d is None:
            return pod_h_default
        if name == 'Thermoception':
            return 0.13          # a 5-cell diamond of numbers; no bars to clear
        return 0.20 if d.get('type') in ('diamond', 'visual_grid') else pod_h_default

    _drawn = [s for s in known_sensors if s in sensor_map]
    _requested = sum(_pod_height(s) for s in _drawn)
    _gaps = 0.03 * len(_drawn)
    _available = max(0.74 - _gaps, 0.05)
    _squeeze = (min(1.0, _available / _requested)
                if (thermal_on and _requested > 0) else 1.0)

    for s_name in known_sensors:
        s_data = sensor_map.get(s_name)
        offline = s_data is None
        
        obs_only = False
        if s_data is not None and s_data['type'] == 'intensity':
            obs_only = 'true_intensity' not in s_data or s_data.get('true_intensity') == s_data.get('intensity')
        elif s_data is not None and s_data['type'] in ('spectrum', 'diamond', 'visual_grid'):
            tv = s_data.get('true_vector')
            obs_only = tv is None or np.array_equal(np.asarray(tv), np.asarray(s_data['vector']))
        
        # Dynamic pod height: Visual/Diamond pods get more room for bars + labels
        pod_h = _pod_height(s_name) * _squeeze if not offline else pod_h_default

        y_frame_bottom = y_cursor - pod_h
        draw_pod_frame(ax_right, 0.05, y_frame_bottom, 0.9, pod_h, s_name, offline=offline, obs_only=obs_only, transform=ax_right.transAxes)
        
        if not offline:
            px, py, pw, ph = 0.15, y_frame_bottom + 0.02 * _squeeze, 0.7, 0.07 * _squeeze
            if s_name == 'Thermoception':
                # Its own drawing, on the same fixed diverging scale as the
                # field underlay — see `draw_thermal_diamond` for why the
                # generic bar widgets cannot render this modality's range.
                draw_thermal_diamond(
                    ax_right, 0.10, y_frame_bottom + 0.01, 0.80, pod_h - 0.02,
                    s_data['vector'], s_data.get('range', 1), thermal_clim,
                    transform=ax_right.transAxes,
                    colour_offset=(float(getattr(state, 'body_temp', 0.0))
                                   if bool(getattr(params, 'thermal_relative', False))
                                   else 0.0))
            elif s_data['type'] == 'intensity':
                # Dual Capsule Bar for Intensity Sensors (e.g. Nociception)
                true_v = float(s_data.get('true_intensity', s_data['intensity']))
                obs_v = float(s_data['intensity'])
                # Adding numerical labels for research clarity
                if obs_only:
                    draw_dual_capsule_bar(ax_right, px, py, pw, ph, 0, obs_v, COLORS['action'],
                                          state_val="--", obs_val=f"{obs_v:.2f}", transform=ax_right.transAxes,
                                          label_dy=0.02 * _squeeze, obs_dy=0.03 * _squeeze)
                else:
                    draw_dual_capsule_bar(ax_right, px, py, pw, ph, true_v, obs_v, COLORS['action'],
                                          state_val=f"{true_v:.2f}", obs_val=f"{obs_v:.2f}", transform=ax_right.transAxes,
                                          label_dy=0.02 * _squeeze, obs_dy=0.03 * _squeeze)
            elif s_data['type'] == 'spectrum':
                obs_vec = np.array(s_data['vector'])
                true_vec = np.array(s_data.get('true_vector', obs_vec))
                
                # Normalization fix: ensure max height doesn't exceed frame
                # If any value > 1.0, scale the entire visualization proportionally
                max_val = max(np.max(obs_vec), np.max(true_vec))
                scale = 1.0 if max_val <= 1.0 else (1.0 / max_val)
                
                n = len(obs_vec)
                sw = pw / n
                for i in range(n):
                    vx = px + i * sw
                    # Show True (Ghosted)
                    if not obs_only:
                        ax_right.add_patch(plt.Rectangle((vx, py), sw*0.8, ph*true_vec[i]*scale, color=COLORS['action'], alpha=0.2, transform=ax_right.transAxes))
                    # Show Observed (Solid)
                    ax_right.add_patch(plt.Rectangle((vx, py), sw*0.8, ph*obs_vec[i]*scale, color=COLORS['action'], alpha=0.9, transform=ax_right.transAxes))
            elif s_data['type'] == 'diamond' or s_data['type'] == 'visual_grid':
                # V7 Categorical Spectrum Upgrade (Dual View Distribution)
                r = int(s_data.get('range', 1))
                num_features = int(s_data.get('num_features', 1))
                obs_v = np.array(s_data['vector'])
                true_v = np.array(s_data.get('true_vector', obs_v))
                
                # Distribution Plot Geometry
                px, py, pw, ph = 0.1, y_cursor - pod_h + 0.05, 0.8, 0.08
                
                # If range > 1, we fallback to schematic diamond (too many bars)
                # But for research standard r=0,1 we use the categorical spectrum
                if r <= 1:
                    draw_categorical_visual(ax_right, 0.08, y_frame_bottom, 0.84, pod_h, obs_v, r, num_features, 
                                           true_vec=true_v, labels=s_data.get('labels'), obs_only=obs_only, transform=ax_right.transAxes)
                else:
                    origin_x, origin_y = 0.5, y_cursor - pod_h/2
                    cell_size = 0.12 / (2*r + 1)
                    draw_boresight_diamond(ax_right, origin_x, origin_y, cell_size, obs_v, r, num_features, 
                                           true_vec=true_v, icons=icons, obs_only=obs_only, transform=ax_right.transAxes)
                
                if not np.any(obs_v > 0.1) and not np.any(true_v > 0.1):
                    ax_right.text(0.5, y_cursor - pod_h/2, "NO SIGNALS", color=COLORS['text_offline'], 
                                  fontsize=6, ha='center', transform=ax_right.transAxes)
            elif s_data['type'] == 'text':
                # Text-based display (e.g. coordinates or state labels)
                ax_right.text(0.5, y_cursor - pod_h/2, s_data.get('value_text', '--'), 
                              color=COLORS['text_main'], fontsize=10, fontweight='bold', 
                              ha='center', va='center', transform=ax_right.transAxes, fontfamily='monospace')

        y_cursor -= (pod_h + 0.03)  # 0.03 gap for next pod title
        if y_cursor < 0.20: break # Save space for Action Pod

    # --- 4. Action Pod (Fixed Position bottom floor for V7.3) ---
    action_y = 0.03
    if action is not None:
        draw_pod_frame(ax_right, 0.05, action_y, 0.9, 0.13, "Current Action", transform=ax_right.transAxes)
        action_names = {0: "UP", 1: "RIGHT", 2: "DOWN", 3: "LEFT", 4: "REST", 5: "EAT"}
        arrows = {0: "↑", 1: "→", 2: "↓", 3: "←", 4: "⊝", 5: "✙"}
        act_name, arrow = action_names.get(int(action), f"{action}"), arrows.get(int(action), "•")
        
        ax_right.text(0.5, action_y + 0.085, act_name, color=COLORS['text_main'], 
                      fontsize=10, fontweight='black', ha='center', transform=ax_right.transAxes)
        ax_right.text(0.5, action_y + 0.025, arrow, color=COLORS['action'], 
                      fontsize=18, fontweight='black', ha='center', transform=ax_right.transAxes)

    canvas.draw()
    s, (w, h) = canvas.print_to_buffer()
    image = np.frombuffer(s, dtype='uint8').reshape((int(h), int(w), 4))
    return image[:, :, :3]
    # print(f"      [Profile] Render took {time.time() - start_time:.4f}s")


def save_jax_video(frames, output_path, fps=5, quiet=False):
    """
    Save a list of RGB frames as an MP4 video.
    
    Args:
        frames: List of numpy arrays (H, W, 3)
        output_path: Path to save the video
        fps: Frames per second
        quiet: Suppress output messages
    """
    import os
    import imageio
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    if quiet:
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        old_stdout_fd = os.dup(sys.stdout.fileno())
        old_stderr_fd = os.dup(sys.stderr.fileno())
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            os.dup2(devnull, sys.stderr.fileno())
            os.close(devnull)
            with imageio.get_writer(output_path, fps=fps) as writer:
                for frame in frames:
                    writer.append_data(frame)
        finally:
            os.dup2(old_stdout_fd, sys.stdout.fileno())
            os.dup2(old_stderr_fd, sys.stderr.fileno())
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)
    else:
        with imageio.get_writer(output_path, fps=fps) as writer:
            for frame in frames:
                writer.append_data(frame)
        print(f"Saved video to {output_path}")
