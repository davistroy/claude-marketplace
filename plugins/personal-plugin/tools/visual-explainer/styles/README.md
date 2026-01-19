# Visual Explainer Style Configuration Guide

This directory contains style configuration files that control the visual appearance of generated concept explanation images.

## Bundled Styles

| Style | File | Description |
|-------|------|-------------|
| **Professional Clean** | `professional-clean.json` | Modern, clean digital illustration with generous white space and clear hierarchy |
| **Professional Sketch** | `professional-sketch.json` | Hand-rendered watercolor and graphite sketch with warm, approachable aesthetics |

## Style Schema (v1.2)

Style files use JSON format with the following major sections:

### Root Fields

```json
{
  "SchemaVersion": "1.2",
  "StyleName": "Visual_Explainer_[YourStyleName]",
  "StyleIntent": "Brief description of the style's purpose and mood",
  "BlendSources": {
    "Original": "Source inspiration or style basis",
    "Adapted": "How it's been adapted for visual explanations"
  }
}
```

### ModelAndOutputProfiles

Defines target AI model and supported resolutions:

```json
{
  "ModelAndOutputProfiles": {
    "TargetModelHint": "gemini-2.0-flash-exp",
    "ResolutionProfiles": {
      "Landscape4K": { "Width": 3200, "Height": 1800, "AspectRatio": "16:9", "UseCase": "Presentations" },
      "SquareHQ": { "Width": 1800, "Height": 1800, "AspectRatio": "1:1", "UseCase": "Social media" },
      "Portrait4K": { "Width": 1800, "Height": 3200, "AspectRatio": "9:16", "UseCase": "Mobile" }
    }
  }
}
```

### Medium

Describes the artistic medium and rendering approach:

```json
{
  "Medium": {
    "PrimaryStyle": "CleanDigitalIllustration",
    "RenderingApproach": "ProfessionalGraphicDesign",
    "Aesthetic": ["Modern", "Clean", "Approachable"],
    "Background": {
      "Type": "CleanMinimal",
      "BaseColor": "#FFFFFF"
    }
  }
}
```

### ColorSystem

Defines the color palette and usage rules:

```json
{
  "ColorSystem": {
    "PaletteMode": "Flexible",
    "Background": {
      "Base": "#FFFFFF",
      "Role": "Description of background usage"
    },
    "PrimaryColors": [
      {
        "Name": "Color Name",
        "Hex": "#1E3A5F",
        "Role": "How this color is used",
        "UsageGuidance": "When to apply this color"
      }
    ],
    "SecondaryColors": [...],
    "ColorUsageRules": {
      "DominantMood": "Description of overall color mood",
      "WhiteSpace": "Generous",
      "ProhibitedHues": ["Neon colors", "Muddy browns"]
    }
  }
}
```

### Typography and TextStyle

Controls text appearance and rules:

```json
{
  "Typography": {
    "PrimaryTypeface": {
      "Name": "Clean Sans Serif",
      "Weights": ["Bold", "Medium", "Regular"],
      "CharacterTraits": "Friendly, approachable, modern"
    }
  },
  "TextStyle": {
    "GlobalTextPolicy": {
      "AllowedText": ["Headlines", "Labels", "Annotations"],
      "LegibilityRequirement": "PerfectlyLegibleCorrectSpellingNoGarbledCharacters"
    },
    "TextColorRules": {
      "Headlines": ["#1E3A5F"],
      "BodyText": ["#64748B"]
    },
    "DoNot": ["Script fonts", "3D effects", "Garbled pseudo-text"]
  }
}
```

### PromptRecipe (Critical Section)

This section contains the actual prompts injected into image generation:

```json
{
  "PromptRecipe": {
    "StylePrefix": "Opening style description for every prompt",
    "CoreStylePrompt": "Detailed style characteristics to include",
    "ColorConstraintPrompt": "Specific color palette instructions",
    "TextEnforcementPrompt": "Rules for any text in the image",
    "NegativePrompt": "Things to explicitly avoid",
    "QualityChecklist": [
      "Verification criteria for generated images"
    ]
  }
}
```

**PromptRecipe fields are combined during generation:**
1. `StylePrefix` + user's concept description
2. `CoreStylePrompt` added for style characteristics
3. `ColorConstraintPrompt` enforces palette
4. `TextEnforcementPrompt` ensures legible text
5. `NegativePrompt` sent as negative prompt parameter
6. `QualityChecklist` used during evaluation

## Creating Custom Styles

### Step 1: Copy an Existing Style

Start from `professional-clean.json` or `professional-sketch.json` as a template.

### Step 2: Update Metadata

```json
{
  "StyleName": "Visual_Explainer_YourStyleName",
  "StyleIntent": "Your style's purpose and mood description"
}
```

### Step 3: Customize Color Palette

Update `ColorSystem.PrimaryColors` and `ColorSystem.SecondaryColors` with your brand colors:

```json
{
  "PrimaryColors": [
    {
      "Name": "Your Brand Blue",
      "Hex": "#YOUR_HEX",
      "Role": "How you want this color used"
    }
  ]
}
```

### Step 4: Update PromptRecipe

The `PromptRecipe` section has the most impact on output. Update:

- `StylePrefix`: Your opening style description
- `CoreStylePrompt`: Key visual characteristics
- `ColorConstraintPrompt`: Update hex values to match your palette
- `NegativePrompt`: Add anything you want to avoid

### Step 5: Validate and Test

1. Ensure JSON is valid (use a JSON validator)
2. Run a test generation with `--style /path/to/your-style.json`
3. Review output and iterate on `PromptRecipe`

## Style Selection Priority

When using the visual-explainer tool:

1. **Explicit path**: `--style /path/to/custom.json` - loads your file
2. **Named bundled style**: `--style professional-clean` - loads from this directory
3. **Default**: If no style specified, uses `professional-clean`

## Tips for Effective Styles

1. **Be specific in prompts**: Vague prompts produce inconsistent results
2. **Include negative prompts**: Explicitly state what to avoid
3. **Test with diverse concepts**: A good style works across different topics
4. **Balance constraints**: Too restrictive limits creativity; too loose loses consistency
5. **Update QualityChecklist**: These criteria guide the evaluation phase

## Schema Version History

| Version | Changes |
|---------|---------|
| 1.2 | Added Portrait4K resolution, expanded PromptRecipe |
| 1.1 | Added StyleControls section |
| 1.0 | Initial schema |
