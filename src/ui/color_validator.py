"""
Color Validator Module

Provides utilities to validate colors for color-blind accessibility.
Implements WCAG 2.1 AA contrast ratio calculations and color-blind simulations.
"""

from typing import Dict, Tuple, List, Optional
import colorsys


class ColorValidator:
    """
    Validate colors for color-blind accessibility.
    
    Features:
    - WCAG 2.1 AA contrast ratio validation
    - Color-blind simulation (deuteranopia, protanopia, tritanopia)
    - Detection of problematic color combinations
    - Audit report generation
    """
    
    # WCAG 2.1 AA minimum contrast ratios
    MIN_CONTRAST_RATIO_NORMAL_TEXT = 4.5
    MIN_CONTRAST_RATIO_LARGE_TEXT = 3.0
    MIN_CONTRAST_RATIO_UI_COMPONENTS = 3.0
    
    # Red-green problematic combinations to avoid
    # These are colors that appear similar to color-blind users
    PROBLEMATIC_PAIRS = [
        ((255, 0, 0), (0, 255, 0)),      # Pure red / pure green (MOST problematic)
        ((255, 0, 0), (0, 128, 0)),      # Pure red / dark green
        ((255, 99, 71), (144, 238, 144)), # Tomato / light green
        ((178, 34, 34), (34, 139, 34)),  # Firebrick / forest green
        ((220, 20, 60), (0, 100, 0)),    # Crimson / dark green
        ((244, 67, 54), (76, 175, 80)),  # Material red / material green
    ]
    
    # Additional distinguishability checks
    MIN_ABSOLUTE_DIFFERENCE = 30  # Minimum RGB difference to be distinguishable
    
    def __init__(self):
        """Initialize the color validator."""
        # Color transformation matrices for simulations
        self._init_simulation_matrices()
    
    def _init_simulation_matrices(self):
        """Initialize simulation matrices for different types of color blindness."""
        # Simulate deuteranopia (green-blind) - most common
        self.deuteranopia_matrix = [
            [0.625, 0.375, 0.0],
            [0.7, 0.3, 0.0],
            [0.0, 0.3, 0.7]
        ]
        
        # Simulate protanopia (red-blind)
        self.protanopia_matrix = [
            [0.567, 0.433, 0.0],
            [0.558, 0.442, 0.0],
            [0.0, 0.242, 0.758]
        ]
        
        # Simulate tritanopia (blue-blind) - rarest
        self.tritanopia_matrix = [
            [0.95, 0.05, 0.0],
            [0.0, 0.433, 0.567],
            [0.0, 0.475, 0.525]
        ]
    
    def get_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """
        Calculate relative luminance for contrast ratio.
        
        Uses WCAG 2.1 formula:
        L = 0.2126 * R + 0.7152 * G + 0.0722 * B
        where R, G, B are linearized (gamma-corrected)
        
        Args:
            rgb: Color as (R, G, B) tuple (0-255)
            
        Returns:
            Relative luminance value (0.0 to 1.0)
        """
        def linearize(channel: int) -> float:
            """Linearize sRGB channel value."""
            c = channel / 255.0
            if c <= 0.03928:
                return c / 12.92
            else:
                return ((c + 0.055) / 1.055) ** 2.4
        
        r_linear = linearize(rgb[0])
        g_linear = linearize(rgb[1])
        b_linear = linearize(rgb[2])
        
        return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
    
    def calculate_contrast_ratio(self, foreground: Tuple[int, int, int],
                                  background: Tuple[int, int, int]) -> float:
        """
        Calculate WCAG contrast ratio between two colors.
        
        Formula: (L1 + 0.05) / (L2 + 0.05)
        where L1 is the lighter color's luminance
        
        Args:
            foreground: Foreground color (R, G, B)
            background: Background color (R, G, B)
            
        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        l1 = self.get_luminance(foreground)
        l2 = self.get_luminance(background)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def validate_contrast(self, foreground: Tuple[int, int, int],
                          background: Tuple[int, int, int],
                          min_ratio: float = None) -> Tuple[bool, float]:
        """
        Check if two colors meet WCAG contrast requirements.
        
        Args:
            foreground: Foreground color (R, G, B)
            background: Background color (R, G, B)
            min_ratio: Minimum required ratio (default: 4.5 for normal text)
            
        Returns:
            Tuple of (passes, actual_ratio)
        """
        if min_ratio is None:
            min_ratio = self.MIN_CONTRAST_RATIO_NORMAL_TEXT
        
        ratio = self.calculate_contrast_ratio(foreground, background)
        return ratio >= min_ratio, ratio
    
    def get_color_difference(self, color1: Tuple[int, int, int],
                             color2: Tuple[int, int, int]) -> float:
        """
        Calculate the overall difference between two colors.
        
        Uses Euclidean distance in RGB space.
        
        Args:
            color1: First color (R, G, B)
            color2: Second color (R, G, B)
            
        Returns:
            Color difference value
        """
        return ((color1[0] - color2[0]) ** 2 +
                (color1[1] - color2[1]) ** 2 +
                (color1[2] - color2[2]) ** 2) ** 0.5
    
    def validate_color_pair(self, color1: Tuple[int, int, int],
                            color2: Tuple[int, int, int]) -> bool:
        """
        Check if two colors are distinguishable for color-blind users.
        
        Args:
            color1: First color (R, G, B)
            color2: Second color (R, G, B)
            
        Returns:
            True if colors are distinguishable
        """
        # Check against known problematic pairs
        for pair in self.PROBLEMATIC_PAIRS:
            if ((color1 == pair[0] or color1 == pair[1]) and
                (color2 == pair[0] or color2 == pair[1])):
                return False
        
        # Check if colors are too similar
        min_diff = self.MIN_ABSOLUTE_DIFFERENCE
        r_diff = abs(color1[0] - color2[0])
        g_diff = abs(color1[1] - color2[1])
        b_diff = abs(color1[2] - color2[2])
        
        # At least one channel should have significant difference
        if r_diff < min_diff and g_diff < min_diff and b_diff < min_diff:
            return False
        
        # Check if colors appear similar to color-blind users
        color1_deut = self.simulate_deuteranopia(color1)
        color2_deut = self.simulate_deuteranopia(color2)
        
        deut_diff = self.get_color_difference(color1_deut, color2_deut)
        if deut_diff < min_diff:
            return False
        
        # Also check for protanopia
        color1_prot = self.simulate_protanopia(color1)
        color2_prot = self.simulate_protanopia(color2)
        
        prot_diff = self.get_color_difference(color1_prot, color2_prot)
        if prot_diff < min_diff:
            return False
        
        return True
    
    def validate_color_pair_with_reason(self, color1: Tuple[int, int, int],
                                         color2: Tuple[int, int, int]) -> Tuple[bool, str]:
        """
        Check if two colors are distinguishable with detailed reason.
        
        Args:
            color1: First color (R, G, B)
            color2: Second color (R, G, B)
            
        Returns:
            Tuple of (passes, reason)
        """
        # Check against known problematic pairs
        for pair in self.PROBLEMATIC_PAIRS:
            if ((color1 == pair[0] or color1 == pair[1]) and
                (color2 == pair[0] or color2 == pair[1])):
                return False, f"Colors match known problematic pair: {pair[0]} and {pair[1]}"
        
        # Check if colors are too similar
        min_diff = self.MIN_ABSOLUTE_DIFFERENCE
        r_diff = abs(color1[0] - color2[0])
        g_diff = abs(color1[1] - color2[1])
        b_diff = abs(color1[2] - color2[2])
        
        if r_diff < min_diff and g_diff < min_diff and b_diff < min_diff:
            return False, "Colors are too similar in RGB values"
        
        # Check deuteranopia simulation
        color1_deut = self.simulate_deuteranopia(color1)
        color2_deut = self.simulate_deuteranopia(color2)
        deut_diff = self.get_color_difference(color1_deut, color2_deut)
        
        if deut_diff < min_diff:
            return False, f"Colors appear similar to deuteranopic (green-blind) users (distance: {deut_diff:.1f})"
        
        # Check protanopia simulation
        color1_prot = self.simulate_protanopia(color1)
        color2_prot = self.simulate_protanopia(color2)
        prot_diff = self.get_color_difference(color1_prot, color2_prot)
        
        if prot_diff < min_diff:
            return False, f"Colors appear similar to protanopic (red-blind) users (distance: {prot_diff:.1f})"
        
        return True, "Colors are distinguishable for all types of color blindness"
    
    def simulate_deuteranopia(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with deuteranopia (green-blind).
        
        Args:
            rgb: Color as (R, G, B) tuple (0-255)
            
        Returns:
            Simulated color as (R, G, B) tuple
        """
        return self._apply_matrix(rgb, self.deuteranopia_matrix)
    
    def simulate_protanopia(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with protanopia (red-blind).
        
        Args:
            rgb: Color as (R, G, B) tuple (0-255)
            
        Returns:
            Simulated color as (R, G, B) tuple
        """
        return self._apply_matrix(rgb, self.protanopia_matrix)
    
    def simulate_tritanopia(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with tritanopia (blue-blind).
        
        Args:
            rgb: Color as (R, G, B) tuple (0-255)
            
        Returns:
            Simulated color as (R, G, B) tuple
        """
        return self._apply_matrix(rgb, self.tritanopia_matrix)
    
    def _apply_matrix(self, rgb: Tuple[int, int, int],
                      matrix: List[List[float]]) -> Tuple[int, int, int]:
        """
        Apply a transformation matrix to a color.
        
        Args:
            rgb: Original color (R, G, B)
            matrix: 3x3 transformation matrix
            
        Returns:
            Transformed color (R, G, B)
        """
        r = matrix[0][0] * rgb[0] + matrix[0][1] * rgb[1] + matrix[0][2] * rgb[2]
        g = matrix[1][0] * rgb[0] + matrix[1][1] * rgb[1] + matrix[1][2] * rgb[2]
        b = matrix[2][0] * rgb[0] + matrix[2][1] * rgb[1] + matrix[2][2] * rgb[2]
        
        # Clamp to valid range
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        
        return (r, g, b)
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_audit_report(self, colors: Dict[str, Tuple[int, int, int]],
                               title: str = "Color Accessibility Audit Report") -> str:
        """
        Generate a detailed accessibility audit report.
        
        Args:
            colors: Dictionary of color names to RGB tuples
            title: Report title
            
        Returns:
            Formatted audit report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(title)
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        total_colors = len(colors)
        issues = []
        
        # Check each color
        lines.append("COLOR BREAKDOWN:")
        lines.append("-" * 40)
        for name, rgb in colors.items():
            hex_color = self.rgb_to_hex(rgb)
            lines.append(f"  {name}: {hex_color} ({rgb})")
            
            # Check for problematic colors (pure red/green)
            if rgb in [(255, 0, 0), (0, 255, 0), (128, 0, 0), (0, 128, 0)]:
                issues.append(f"  ⚠️  {name}: Pure red or green may be problematic")
        
        lines.append("")
        lines.append("PAIRWISE VALIDATION:")
        lines.append("-" * 40)
        
        color_names = list(colors.keys())
        for i in range(len(color_names)):
            for j in range(i + 1, len(color_names)):
                name1, name2 = color_names[i], color_names[j]
                color1, color2 = colors[name1], colors[name2]
                passes, reason = self.validate_color_pair_with_reason(color1, color2)
                
                if not passes:
                    issues.append(f"  ❌ {name1} vs {name2}: {reason}")
                else:
                    lines.append(f"  ✓ {name1} vs {name2}: Distinguishable")
        
        lines.append("")
        lines.append("CONTRAST RATIO CHECKS (vs white background):")
        lines.append("-" * 50)
        
        white = (255, 255, 255)
        for name, rgb in colors.items():
            passes, ratio = self.validate_contrast(rgb, white)
            status = "✓" if passes else "❌"
            lines.append(f"  {status} {name}: {ratio:.2f}:1 {'(passes)' if passes else '(FAILS <4.5:1)'}")
        
        lines.append("")
        
        if issues:
            lines.append("ISSUES FOUND:")
            lines.append("-" * 40)
            for issue in issues:
                lines.append(issue)
        else:
            lines.append("✓ NO ISSUES FOUND - All colors are color-blind safe")
        
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 40)
        lines.append("  - Use patterns/shapes in addition to color for important information")
        lines.append("  - Test with real color-blind users when possible")
        lines.append("  - Consider providing a high-contrast mode option")
        lines.append("  - Double-check colors in actual rendering environment")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"Report generated with ColorValidator")
        lines.append("=" * 80)
        
        return "\n".join(lines)

# Convenience function
def validate_color_pair(color1: Tuple[int, int, int],
                        color2: Tuple[int, int, int]) -> bool:
    """
    Quick validation of two colors for color-blind accessibility.
    
    Args:
        color1: First color (R, G, B)
        color2: Second color (R, G, B)
        
    Returns:
        True if colors are distinguishable
    """
    validator = ColorValidator()
    return validator.validate_color_pair(color1, color2)