"""
WCAG Compliance Checker

This module provides utilities for checking WCAG 2.1 AA compliance in HTML content.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
import colorsys

# Configure logging
logger = logging.getLogger(__name__)

def check_wcag_compliance(soup: BeautifulSoup) -> List[Dict]:
    """
    Check WCAG 2.1 AA compliance and fix issues.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of issues found and fixed
    """
    issues = []
    
    # Check for color contrast issues
    contrast_issues = check_color_contrast(soup)
    issues.extend(contrast_issues)
    
    # Check for proper heading structure
    heading_issues = check_heading_structure(soup)
    issues.extend(heading_issues)
    
    # Check for keyboard accessibility
    keyboard_issues = check_keyboard_accessibility(soup)
    issues.extend(keyboard_issues)
    
    return issues

def check_color_contrast(soup: BeautifulSoup) -> List[Dict]:
    """
    Check color contrast ratios for WCAG 2.1 AA compliance.
    Minimum ratio required is 4.5:1 for normal text and 3:1 for large text.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of color contrast issues found and fixed
    """
    issues = []
    
    # Get all elements with foreground and background colors
    elements_with_styles = soup.select('[style*="color"], [style*="background"], [class*="bg-"], [class*="text-"]')
    
    for element in elements_with_styles:
        # Extract styles
        style = element.get('style', '')
        classes = element.get('class', [])
        
        # Extract colors from styles
        bg_color = extract_background_color(style, classes)
        fg_color = extract_foreground_color(style, classes)
        
        if bg_color and fg_color:
            # Calculate contrast ratio
            contrast_ratio = calculate_contrast_ratio(bg_color, fg_color)
            
            # Check if it meets WCAG AA requirements
            is_large_text = is_large_text_element(element)
            required_ratio = 3.0 if is_large_text else 4.5
            
            if contrast_ratio < required_ratio:
                # Fix the contrast issue by adjusting the colors
                new_fg_color = improve_contrast(bg_color, fg_color, required_ratio)
                
                # Update the element's color
                if 'style' in element.attrs:
                    element['style'] = re.sub(r'color:\s*[^;]+', f'color: {new_fg_color}', element['style'])
                else:
                    element['style'] = f'color: {new_fg_color}'
                
                issues.append({
                    'type': 'color_contrast',
                    'element': str(element.name),
                    'original_contrast': contrast_ratio,
                    'improved_contrast': calculate_contrast_ratio(bg_color, new_fg_color),
                    'action': 'fixed'
                })
    
    return issues

def extract_background_color(style: str, classes: List[str]) -> Optional[str]:
    """Extract background color from style or classes"""
    # Try to extract from inline style
    bg_match = re.search(r'background(-color)?:\s*([^;]+)', style)
    if bg_match:
        return bg_match.group(2).strip()
    
    # If not in style, check for tailwind classes
    for cls in classes:
        if cls.startswith('bg-'):
            # Minimal Tailwind color mapping
            tailwind_colors = {
                'bg-slate-900': '#0F172A',
                'bg-slate-800': '#1E293B',
                'bg-slate-200': '#E2E8F0',
                'bg-slate-100': '#F1F5F9',
                'bg-white': '#FFFFFF',
                'bg-black': '#000000',
                'bg-gray-900': '#111827',
                'bg-gray-100': '#F3F4F6',
                'bg-red-500': '#EF4444',
                'bg-green-500': '#22C55E',
                'bg-blue-500': '#3B82F6',
            }
            return tailwind_colors.get(cls, '#0F172A')  # Default to dark background
    
    return '#0F172A'  # Default background color

def extract_foreground_color(style: str, classes: List[str]) -> Optional[str]:
    """Extract foreground color from style or classes"""
    # Try to extract from inline style
    fg_match = re.search(r'color:\s*([^;]+)', style)
    if fg_match:
        return fg_match.group(1).strip()
    
    # If not in style, check for tailwind classes
    for cls in classes:
        if cls.startswith('text-'):
            # Minimal Tailwind color mapping
            tailwind_colors = {
                'text-slate-900': '#0F172A',
                'text-slate-800': '#1E293B', 
                'text-slate-200': '#E2E8F0',
                'text-slate-100': '#F1F5F9',
                'text-white': '#FFFFFF',
                'text-black': '#000000',
                'text-gray-900': '#111827',
                'text-gray-100': '#F3F4F6',
                'text-red-500': '#EF4444',
                'text-green-500': '#22C55E',
                'text-blue-500': '#3B82F6',
            }
            return tailwind_colors.get(cls, '#F8FAFC')  # Default to light text
    
    return '#F8FAFC'  # Default text color

def calculate_contrast_ratio(bg_color: str, fg_color: str) -> float:
    """
    Calculate the contrast ratio between two colors.
    
    Args:
        bg_color: Background color in hex
        fg_color: Foreground color in hex
        
    Returns:
        Contrast ratio (higher is better, WCAG AA requires 4.5:1 minimum)
    """
    # Convert hex to RGB
    bg_rgb = hex_to_rgb(bg_color)
    fg_rgb = hex_to_rgb(fg_color)
    
    # Calculate relative luminance
    bg_luminance = calculate_luminance(bg_rgb)
    fg_luminance = calculate_luminance(fg_rgb)
    
    # Calculate contrast ratio
    lighter = max(bg_luminance, fg_luminance)
    darker = min(bg_luminance, fg_luminance)
    
    return (lighter + 0.05) / (darker + 0.05)

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Handle shorthand hex
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    # Convert to RGB
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        logger.warning(f"Invalid hex color: {hex_color}, defaulting to black")
        return (0, 0, 0)  # Default to black in case of invalid hex

def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance from RGB values"""
    # Convert RGB to sRGB
    srgb = [x / 255.0 for x in rgb]
    
    # Apply gamma correction
    rgb_linear = []
    for val in srgb:
        if val <= 0.03928:
            rgb_linear.append(val / 12.92)
        else:
            rgb_linear.append(((val + 0.055) / 1.055) ** 2.4)
    
    # Calculate luminance
    return 0.2126 * rgb_linear[0] + 0.7152 * rgb_linear[1] + 0.0722 * rgb_linear[2]

def is_large_text_element(element) -> bool:
    """
    Determine if the element contains large text (18pt+ or 14pt+ bold).
    Large text has a lower contrast requirement.
    
    Args:
        element: HTML element to check
        
    Returns:
        True if the element contains large text
    """
    style = element.get('style', '')
    
    # Check font size
    font_size_match = re.search(r'font-size:\s*(\d+)(px|pt|rem|em)', style)
    if font_size_match:
        size = int(font_size_match.group(1))
        unit = font_size_match.group(2)
        
        if unit == 'pt':
            return size >= 18
        elif unit == 'px':
            return size >= 24  # 18pt ≈ 24px
        elif unit == 'rem' or unit == 'em':
            return size >= 1.5  # 18pt ≈ 1.5rem
    
    # Check font weight for bold text
    font_weight_match = re.search(r'font-weight:\s*(\d+|bold|bolder)', style)
    if font_weight_match:
        weight = font_weight_match.group(1)
        if weight == 'bold' or weight == 'bolder' or (weight.isdigit() and int(weight) >= 700):
            # If bold, check for 14pt+ (bold)
            if font_size_match:
                size = int(font_size_match.group(1))
                unit = font_size_match.group(2)
                
                if unit == 'pt':
                    return size >= 14
                elif unit == 'px':
                    return size >= 18.67  # 14pt ≈ 18.67px
                elif unit == 'rem' or unit == 'em':
                    return size >= 1.17  # 14pt ≈ 1.17rem
    
    # Check if element is a heading which typically has larger text
    return element.name in ['h1', 'h2', 'h3']

def improve_contrast(bg_color: str, fg_color: str, target_ratio: float) -> str:
    """
    Improve contrast between background and foreground colors.
    
    Args:
        bg_color: Background color
        fg_color: Foreground color
        target_ratio: Target contrast ratio
        
    Returns:
        Improved foreground color
    """
    # Convert hex to RGB
    bg_rgb = hex_to_rgb(bg_color)
    fg_rgb = hex_to_rgb(fg_color)
    
    # Calculate current contrast ratio
    current_ratio = calculate_contrast_ratio(bg_color, fg_color)
    
    # If already meets target, return original
    if current_ratio >= target_ratio:
        return fg_color
    
    # Calculate relative luminance of background
    bg_luminance = calculate_luminance(bg_rgb)
    
    # Determine if we need to go lighter or darker
    go_lighter = bg_luminance < 0.5
    
    # Convert to HSL for easier manipulation
    h, l, s = colorsys.rgb_to_hls(fg_rgb[0]/255, fg_rgb[1]/255, fg_rgb[2]/255)
    
    # Try incremental lightness changes until we meet contrast
    original_l = l
    step = 0.05 if go_lighter else -0.05
    
    # Loop until we achieve target contrast or reach lightness limits
    for _ in range(20):  # Limit iterations to prevent infinite loop
        # Adjust lightness
        l = max(0.05, min(0.95, l + step))
        
        # Convert back to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        # Create hex color
        new_fg_color = f"#{r:02x}{g:02x}{b:02x}"
        
        # Check contrast
        new_ratio = calculate_contrast_ratio(bg_color, new_fg_color)
        if new_ratio >= target_ratio:
            return new_fg_color
        
        # If we've gone too far in lightness, we need to try adjusting saturation
        if (go_lighter and l >= 0.95) or (not go_lighter and l <= 0.05):
            break
    
    # If adjusting lightness didn't work, reset and try adjusting saturation
    l = original_l
    original_s = s
    
    for _ in range(5):  # Limit iterations
        # Reduce saturation to increase contrast
        s = max(0, s - 0.2)
        
        # Convert back to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        # Create hex color
        new_fg_color = f"#{r:02x}{g:02x}{b:02x}"
        
        # Check contrast
        new_ratio = calculate_contrast_ratio(bg_color, new_fg_color)
        if new_ratio >= target_ratio:
            return new_fg_color
    
    # If all else fails, return black or white based on background
    return "#FFFFFF" if bg_luminance < 0.5 else "#000000"

def check_heading_structure(soup: BeautifulSoup) -> List[Dict]:
    """
    Check for proper heading structure (h1-h6) and fix issues.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of heading structure issues found and fixed
    """
    issues = []
    
    # Check for presence of h1
    h1_tags = soup.find_all('h1')
    if not h1_tags:
        # Find the first heading
        first_heading = soup.find(['h2', 'h3', 'h4', 'h5', 'h6'])
        if first_heading:
            # Change the first heading to h1
            new_h1 = soup.new_tag('h1')
            new_h1.string = first_heading.string
            first_heading.replace_with(new_h1)
            
            issues.append({
                'type': 'heading_structure',
                'issue': 'missing_h1',
                'action': 'converted first heading to h1',
                'element': str(first_heading)
            })
    
    # Check for heading levels skipping (e.g., h1 to h3 without h2)
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    levels = [int(h.name[1]) for h in headings]
    
    for i in range(1, len(levels)):
        # If a level is skipped (more than 1 level difference)
        if levels[i] - levels[i-1] > 1:
            heading = headings[i]
            new_level = levels[i-1] + 1
            
            # Create a new heading with the correct level
            new_heading = soup.new_tag(f'h{new_level}')
            new_heading.string = heading.string
            heading.replace_with(new_heading)
            
            issues.append({
                'type': 'heading_structure',
                'issue': 'skipped_level',
                'action': f'adjusted heading from h{levels[i]} to h{new_level}',
                'element': str(heading)
            })
    
    return issues

def check_keyboard_accessibility(soup: BeautifulSoup) -> List[Dict]:
    """
    Check for keyboard accessibility issues and fix them.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of keyboard accessibility issues found and fixed
    """
    issues = []
    
    # Check for clickable elements without keyboard access
    # 1. Elements with click handlers but no keyboard handlers
    elements_with_onclick = soup.select('[onclick]')
    for element in elements_with_onclick:
        # Check if this element is keyboard accessible (has tabindex, or is naturally focusable)
        is_focusable = (
            element.has_attr('tabindex') or 
            element.name in ['a', 'button', 'input', 'select', 'textarea'] or
            element.has_attr('role') and element['role'] in ['button', 'link', 'checkbox', 'radio']
        )
        
        if not is_focusable:
            # Make it focusable
            element['tabindex'] = '0'
            
            # Add keyboard handler if missing
            if not element.has_attr('onkeypress') and not element.has_attr('onkeydown'):
                onclick = element['onclick']
                element['onkeypress'] = f"if(event.key==='Enter'){{{onclick}}}"
            
            issues.append({
                'type': 'keyboard_accessibility',
                'issue': 'click_only',
                'action': 'added tabindex and keyboard handler',
                'element': str(element.name)
            })
    
    # 2. Interactive elements with missing or negative tabindex
    interactive_elements = soup.select('a, button, input, select, textarea, [role="button"], [role="link"]')
    for element in interactive_elements:
        if element.has_attr('tabindex') and int(element['tabindex']) < 0:
            # Negative tabindex means the element is not in the tab order
            element['tabindex'] = '0'
            issues.append({
                'type': 'keyboard_accessibility',
                'issue': 'negative_tabindex',
                'action': 'changed negative tabindex to 0',
                'element': str(element.name)
            })
    
    # 3. Links with empty href
    links_without_href = soup.select('a:not([href]), a[href=""], a[href="#"]')
    for link in links_without_href:
        # If the link has an ID, use that. Otherwise, generate one
        if not link.has_attr('id'):
            link['id'] = f"auto-id-{len(issues)}"
        
        # Set a proper href
        link['href'] = f"#{link['id']}"
        link['role'] = "button"
        
        issues.append({
            'type': 'keyboard_accessibility',
            'issue': 'empty_link',
            'action': 'added proper href and role',
            'element': 'a'
        })
    
    return issues 