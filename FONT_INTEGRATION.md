# Radial Font Integration Guide

## Overview
This guide explains how to integrate the Radial font into the NovelSync project.

## Font Files Required
The following Radial font files are now properly integrated in the `static/fonts/` directory:

### Available Font Files:
- `radialtrial-regular.otf` (Regular - 400)
- `radialtrial-bold.otf` (Bold - 700)
- `radialtrial-semibold.otf` (SemiBold - 600)
- `radialtrial-heavy.otf` (Heavy - 800)
- `radialtrial-black.otf` (Black - 900)
- `radialtrial-italic.otf` (Regular Italic)
- `radialtrial-bolditalic.otf` (Bold Italic)
- `radialtrial-semibolditalic.otf` (SemiBold Italic)
- `radialtrial-heavyitalic.otf` (Heavy Italic)
- `radialtrial-blackitalic.otf` (Black Italic)

## File Naming Convention
The font files follow this naming pattern:
- Regular weight: `radialtrial-regular.otf`
- Bold weight: `radialtrial-bold.otf`
- SemiBold weight: `radialtrial-semibold.otf`
- Heavy weight: `radialtrial-heavy.otf`
- Black weight: `radialtrial-black.otf`
- Italic variants: `radialtrial-*italic.otf`

## Supported Formats
- `.otf` (OpenType - current implementation)
- `.woff2` (preferred for web - smallest file size)
- `.woff` (good fallback)
- `.ttf` (fallback for older browsers)

## Integration Steps

1. **Copy Font Files**: Copy your Radial font files to `static/fonts/`
2. **Verify File Names**: Ensure the file names match the expected pattern
3. **Test the Application**: Run the application and verify the font loads correctly

## Font Usage in CSS
The font is now referenced as `'Radial'` in the CSS:
```css
body {
    font-family: 'Radial', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

## Troubleshooting

### Font Not Loading
1. Check that font files are in the correct directory (`static/fonts/`)
2. Verify file names match the expected pattern
3. Check browser developer tools for 404 errors
4. Ensure the Flask app serves static files correctly

### Fallback Fonts
If Radial font fails to load, the system will fall back to:
- `-apple-system` (macOS/iOS system font)
- `BlinkMacSystemFont` (Chrome on macOS)
- `sans-serif` (generic sans-serif font)

## Performance Notes
- `.woff2` files are preferred for better performance
- `font-display: swap` ensures text remains visible during font loading
- Font files are cached by the browser for subsequent visits

## Browser Support
- Modern browsers: `.woff2`, `.woff`, `.ttf`
- Older browsers: `.woff`, `.ttf`
- Very old browsers: `.ttf` only 